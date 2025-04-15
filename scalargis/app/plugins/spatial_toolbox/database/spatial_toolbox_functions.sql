-- DROP FUNCTION {schema}.intersects_layers(json, text, int4, int4, int4);

CREATE OR REPLACE FUNCTION {schema}.intersects_layers(_layers json, _geom_ewkt text, _out_srid integer, _buffer integer DEFAULT 0, _buffer_srid integer DEFAULT 3857)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
	--data_srid integer;
	g Geometry; -- = ST_Transform(p_geom_ewkt::Geometry, 3763);

	area_geom double precision = 0;
	_sql text;
	_r record;
	my_json jsonb;
	result_json jsonb;
	_i jsonb;
	_ii jsonb;

	_my_table_sql text;
	_my_fields_sql text;
	_id integer = 0;
	_path text;
	_in_layer_srid integer;

BEGIN
	result_json = _layers; -- using input json as template

	--data_srid = 3763;
	-- raise notice 'Data SRID=%', data_srid;
	--g = ST_Transform(_geom_ewkt::Geometry, data_srid);
	--raise notice 'g=%', st_astext(g);
	--area_geom = ST_Area(g);

	if _buffer > 0 then
	--_geom_ewkt = st_makevalid(ST_Buffer(st_transform(_geom_ewkt::geometry,3763), _buffer));
	_geom_ewkt = st_makevalid(ST_Buffer(st_transform(_geom_ewkt::geometry, _buffer_srid), _buffer));
	end if;


	my_json = _layers->'layers';
	--raise notice 'my json=%', my_json;

	For _i in select jsonb_array_elements(my_json) Loop

		--raise notice '_i=%', _i;
		_my_table_sql = (_i->>'schema') || '.' || (_i->>'table'); -- create table name for sql exec
		raise notice 'my_table=%', _my_table_sql;
		_my_fields_sql = '';

		For _ii in select jsonb_array_elements(_i->'fields') Loop
		--raise notice '_ii=%', _ii;
		_my_fields_sql = _my_fields_sql || ',' || (_ii->>'field');
		End Loop;

		if length(_my_fields_sql) > 0 then -- need cut first char
		_my_fields_sql = right(_my_fields_sql,-1);
		end if;

		raise notice 'my_fields_sql=%', _my_fields_sql;

		Select srid Into _in_layer_srid from geometry_columns where
		f_table_schema like (_i->>'schema') and f_table_name like (_i->>'table') and f_geometry_column like (_i->>'geom_field');
		raise notice '_in_layer_srid=%', _in_layer_srid;

		g = ST_Transform(_geom_ewkt::Geometry, _in_layer_srid);
		--g = ST_Transform(_geom_ewkt::Geometry, data_srid);

		area_geom = ST_Area(g);
		raise notice 'g=%', g::text;

		if length(_my_fields_sql) = 0 then
			_sql = '
			with t as(
			SELECT ST_Union(ST_Intersection('|| (_i->>'geom_field') ||', '''|| g::text ||''')) as geom
			FROM '|| _my_table_sql ||'
			WHERE ST_INTERSECTS('|| (_i->>'geom_field') ||', '''|| g::text ||''')
			)
			select row_number() over () id, t.*,
			ST_Dimension(geom) dimension, ST_ASEWKT(ST_Transform(geom,'|| _out_srid::text ||')) geom,
			ST_Area(geom) area, CASE ST_Dimension(geom) WHEN 2 THEN (ST_Area(geom) * 100)/'|| area_geom::text ||' ELSE 0::double precision END as percent
			from t';
		else
			_sql = '
			with t as(
			SELECT '|| _my_fields_sql ||', ST_Union(ST_Intersection('|| (_i->>'geom_field') ||', '''|| g::text ||''')) as geom
			FROM '|| _my_table_sql ||'
			WHERE ST_INTERSECTS('|| (_i->>'geom_field') ||', '''|| g::text ||''')
			GROUP BY '|| _my_fields_sql ||' ORDER BY '|| _my_fields_sql ||'
			)
			select row_number() over () id, t.*,
			ST_Dimension(geom) dimension, ST_ASEWKT(ST_Transform(geom,'|| _out_srid::text ||')) geom,
			ST_Area(geom) area, CASE ST_Dimension(geom) WHEN 2 THEN (ST_Area(geom) * 100)/'|| area_geom::text ||' ELSE 0::double precision END as percent
			from t';
		end if;

		raise notice '_sql=%', _sql;

		For _r In Execute _sql Loop
			--raise notice '_r=%', jsonb_agg(_r)->>0; --> first element.
			_path = '{layers,'|| _id::text ||',results}'; -- constructing path to results array
			--raise notice 'result value before insert:%', result_json::jsonb#>_path::text[];

			if jsonb_array_length(result_json::jsonb#>_path::text[]) = 0 Then
				result_json = jsonb_set(result_json,_path::text[], jsonb_agg(_r));
				--raise notice '(new) result_json=%', result_json;
			else
				result_json = jsonb_set(result_json,_path::text[], (result_json::jsonb#>_path::text[] || jsonb_agg(_r)));
				--raise notice '(add to) result_json=%', result_json;
			end if;
		End Loop;

		_id=_id+1; -- id nb of element increment
		raise notice '-----------------------------------------------------------------------------';

		-- add geom to result (buffered)
		result_json = jsonb_set(result_json,'{output_geom}'::text[], to_jsonb(ST_AsEWKT(st_transform(_geom_ewkt,_out_srid))));

	End Loop;

	Return jsonb_pretty(result_json);

END
$function$
;

-- Permissions

ALTER FUNCTION {schema}.intersects_layers(json, text, int4, int4, int4) OWNER TO postgres;
GRANT ALL ON FUNCTION {schema}.intersects_layers(json, text, int4, int4, int4) TO public;
GRANT ALL ON FUNCTION {schema}.intersects_layers(json, text, int4, int4, int4) TO postgres;