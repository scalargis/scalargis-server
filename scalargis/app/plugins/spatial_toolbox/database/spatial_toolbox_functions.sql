-- DROP FUNCTION {schema}.intersects_layers(json, text, int4, int4, int4);

CREATE OR REPLACE FUNCTION {schema}.intersects_layers(
    _layers json,
    _geom_ewkt text,
    _out_srid integer,
    _buffer integer DEFAULT 0,
    _buffer_srid integer DEFAULT 3857
)
RETURNS jsonb
LANGUAGE plpgsql
AS $function$
DECLARE
    g Geometry;

    area_geom double precision = 0;
    length_geom double precision = 0;
    _sql text;
    _r record;
    my_json jsonb;
    result_json jsonb;
    _i jsonb;
    _ii jsonb;

    _my_table_sql text;
    _my_fields_sql text;
    _where_not_null_sql text;
    _id integer = 0;
    _path text;
    _in_layer_srid integer;
    _allow_null boolean;

BEGIN
    result_json = _layers; -- using input json as template

    IF _buffer > 0 THEN
        _geom_ewkt = ST_MakeValid(
            ST_Buffer(ST_Transform(_geom_ewkt::geometry, _buffer_srid), _buffer)
        );
    END IF;

    my_json = _layers->'layers';
	--raise notice 'my json=%', my_json;

    FOR _i IN SELECT jsonb_array_elements(my_json)
    LOOP
		--raise notice '_i=%', _i;
        _my_table_sql = (_i->>'schema') || '.' || (_i->>'table');
		--raise notice 'my_table=%', _my_table_sql;
        _my_fields_sql = '';
        _where_not_null_sql = ''; -- reset by layer

        -- FIELDS LOOP
        FOR _ii IN SELECT jsonb_array_elements(_i->'fields')
        LOOP
			--raise notice '_ii=%', _ii;
            _my_fields_sql = _my_fields_sql || ',' || (_ii->>'field');

            -- check allowNull (default TRUE)
            _allow_null := COALESCE((_ii->>'allowNull')::boolean, TRUE);

            IF _allow_null = FALSE THEN
                IF _where_not_null_sql <> '' THEN
                    _where_not_null_sql := _where_not_null_sql || ' AND ';
                END IF;

                _where_not_null_sql := _where_not_null_sql ||
                    format('%I IS NOT NULL', _ii->>'field');
            END IF;
        END LOOP;

        IF length(_my_fields_sql) > 0 THEN  -- need cut first char
            _my_fields_sql = right(_my_fields_sql, -1);
        END IF;

		--raise notice 'my_fields_sql=%', _my_fields_sql;

        -- SRID of layer
        SELECT srid INTO _in_layer_srid
        FROM geometry_columns
        WHERE f_table_schema = (_i->>'schema')
          AND f_table_name = (_i->>'table')
          AND f_geometry_column = (_i->>'geom_field');
		--raise notice '_in_layer_srid=%', _in_layer_srid;

        IF _in_layer_srid = 0 THEN
            EXECUTE format(
                'SELECT ST_SRID(%I) FROM %I.%I LIMIT 1',
                _i->>'geom_field',
                _i->>'schema',
                _i->>'table'
            ) INTO _in_layer_srid;
			--raise notice '_in_layer_srid=%', _in_layer_srid;
        END IF;

        g = ST_Transform(_geom_ewkt::Geometry, _in_layer_srid);

        area_geom = ST_Area(g);
        length_geom = ST_Length(g);
		--raise notice 'g=%', g::text;

        -- BUILD FINAL WHERE CONDITION
        -- base: ST_INTERSECTS
        -- + NOT NULL (if exists)
		-- + filter (if exists)
        DECLARE
            _where_sql text;
			_layer_filter text;
        BEGIN
			_layer_filter := _i->>'filter';

            _where_sql := format(
                'ST_INTERSECTS(%I, %L)',
                _i->>'geom_field',
                g::text
            );

            IF _where_not_null_sql <> '' THEN
                _where_sql := _where_sql || ' AND ' || _where_not_null_sql;
            END IF;

			IF _layer_filter IS NOT NULL AND trim(_layer_filter) <> '' THEN
				_where_sql := _where_sql || ' AND (' || _layer_filter || ')';
			END IF;

            -- FINAL QUERY
            IF length(_my_fields_sql) = 0 THEN
                _sql = format('
                    WITH t AS (
                        SELECT ST_Union(ST_Intersection(%1$I, %2$L)) AS geom
                        FROM %3$s
                        WHERE %4$s
                    )
                    SELECT row_number() OVER () id, t.*,
                        ST_Dimension(geom) dimension,
                        ST_AsEWKT(ST_Transform(geom,%5$s)) geom,
                        ST_Area(geom) area,
                        ST_Length(geom) length,
                        CASE
                            WHEN ST_Dimension(geom) = 2 AND %6$s > 0 THEN (ST_Area(geom)*100)/%6$s
                            WHEN ST_Dimension(geom) = 1 AND %7$s > 0 THEN (ST_Length(geom)*100)/%7$s
                            ELSE 0 END AS percent
                    FROM t',
                    _i->>'geom_field',
                    g::text,
                    _my_table_sql,
                    _where_sql,
                    _out_srid,
                    area_geom,
                    length_geom
                );
            ELSE
                _sql = format('
                    WITH t AS (
                        SELECT %1$s,
                               ST_Union(ST_Intersection(%2$I, %3$L)) AS geom
                        FROM %4$s
                        WHERE %5$s
                        GROUP BY %1$s
                        ORDER BY %1$s
                    )
                    SELECT row_number() OVER () id, t.*,
                        ST_Dimension(geom) dimension,
                        ST_AsEWKT(ST_Transform(geom,%6$s)) geom,
                        ST_Area(geom) area,
                        ST_Length(geom) length,
                        CASE
                            WHEN ST_Dimension(geom) = 2 AND %7$s > 0 THEN (ST_Area(geom)*100)/%7$s
                            WHEN ST_Dimension(geom) = 1 AND %8$s > 0 THEN (ST_Length(geom)*100)/%8$s
                            ELSE 0 END AS percent
                    FROM t',
                    _my_fields_sql,
                    _i->>'geom_field',
                    g::text,
                    _my_table_sql,
                    _where_sql,
                    _out_srid,
                    area_geom,
                    length_geom
                );
            END IF;
        END;

		--raise notice '_sql=%', _sql;

        -- EXECUTE
        FOR _r IN EXECUTE _sql LOOP
			--raise notice '_r=%', jsonb_agg(_r)->>0; --> first element.
            _path = '{layers,'|| _id::text ||',results}'; -- constructing path to results array
			--raise notice 'result value before insert:%', result_json::jsonb#>_path::text[];

            IF jsonb_array_length(result_json#>_path::text[]) = 0 THEN
                result_json = jsonb_set(result_json,_path::text[], jsonb_agg(_r));
				--raise notice '(new) result_json=%', result_json;
            ELSE
                result_json = jsonb_set(
                    result_json,
                    _path::text[],
                    (result_json#>_path::text[] || jsonb_agg(_r))
                );
				--raise notice '(add to) result_json=%', result_json;
            END IF;
        END LOOP;

        _id = _id + 1; -- id nb of element increment
		--raise notice '-----------------------------------------------------------------------------';

		-- add geom to result (buffered)
        result_json = jsonb_set(
            result_json,
            '{output_geom}',
            to_jsonb(ST_AsEWKT(ST_Transform(_geom_ewkt,_out_srid)))
        );

    END LOOP;

    RETURN jsonb_pretty(result_json);
END
$function$;

-- Permissions

ALTER FUNCTION {schema}.intersects_layers(json, text, int4, int4, int4) OWNER TO postgres;
GRANT ALL ON FUNCTION {schema}.intersects_layers(json, text, int4, int4, int4) TO public;
GRANT ALL ON FUNCTION {schema}.intersects_layers(json, text, int4, int4, int4) TO postgres;