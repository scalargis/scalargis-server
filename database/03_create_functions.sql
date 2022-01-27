SET search_path = public, pg_catalog;

-- Function: portal.generate_emissao_planta_number()
-- DROP FUNCTION portal.generate_emissao_planta_number();
CREATE OR REPLACE FUNCTION portal.generate_emissao_planta_number()
  RETURNS integer AS
$BODY$
DECLARE
    new_num_emissao integer := null;
BEGIN
    SELECT INTO new_num_emissao COALESCE(max(num_emissao)+1, 1)
	FROM portal.emissao_planta_number
	WHERE ano_emissao = date_part('year', CURRENT_DATE);

    INSERT INTO portal.emissao_planta_number (num_emissao, ano_emissao)
		VALUES (new_num_emissao, date_part('year', CURRENT_DATE));


    RETURN new_num_emissao;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;


-- Function: portal.get_fullsearch(text, integer, real)
-- DROP FUNCTION portal.get_fullsearch(text, integer, real);
CREATE OR REPLACE FUNCTION portal.get_fullsearch(
    IN filter text,
    IN maxrows integer DEFAULT 18,
    IN min_similarity real DEFAULT 0)
  RETURNS TABLE(id bigint, tipo text, nome text, similarity real, geom_json text) AS
$BODY$
declare
	f text;
	fts text;
	mysql text;
begin
	f = unaccent(filter);
	fts = replace(f,' ','&');
	fts = rtrim(fts,'&');
	fts = ltrim(fts,'&');

	mysql = ' SELECT row_number() over() as id, * FROM (
	        (with q as
		((
		SELECT tipo, txt::text AS nome, similarity(txt, '''||f||''') as similarity, geom
		FROM portal.tsearch t
		)
		union all
		(
		select tipo, txt::text AS nome , 0.900009::real as similarity, geom
		from portal.tsearch t
		where str @@ to_tsquery('''||fts||''')
		))
		select tipo, nome, max(similarity), geom from q
		group by tipo,nome,geom having max(similarity) > ' || min_similarity::text ||'
		order by  max(similarity) desc)) as tab';

	if (maxrows>0) Then mysql = mysql || ' Limit ' || maxrows::text; end if;

	return query execute mysql;

end;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


-- Function: portal.get_gazetteer_fullsearch(text, integer, real)
-- DROP FUNCTION portal.get_gazetteer_fullsearch(text, integer, real);
CREATE OR REPLACE FUNCTION portal.get_gazetteer_fullsearch(
    IN filter text,
    IN maxrows integer DEFAULT 18,
    IN min_similarity real DEFAULT 0)
  RETURNS TABLE(id bigint, tipo text, nome text, extra_info text, similarity real, geom_json text) AS
$BODY$
declare
	f text;
	fts text;
	mysql text;
begin
	f = unaccent(filter);
	fts = replace(f,' ','&');
	fts = rtrim(fts,'&');
	fts = ltrim(fts,'&');

	mysql = ' SELECT row_number() over() as id, * FROM (
	        (with q as
		((
		SELECT tipo, txt::text AS nome, extra_info::text as extra_info, similarity(txt, '''||f||''') as similarity, geom
		FROM portal.gazetteer_tsearch t
		)
		union all
		(
		select tipo, txt::text AS nome, extra_info::text as extra_info, 0.900009::real as similarity, geom
		from portal.gazetteer_tsearch t
		where str @@ to_tsquery('''||fts||''')
		))
		select tipo, nome, extra_info, max(similarity), geom from q
		group by tipo, nome, extra_info, geom having max(similarity) > ' || min_similarity::text ||'
		order by  max(similarity) desc)) as tab';

	if (maxrows>0) Then mysql = mysql || ' Limit ' || maxrows::text; end if;

	return query execute mysql;

end;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


-- Function: portal.get_groups_layouts_json()
-- DROP FUNCTION portal.get_groups_layouts_json();
CREATE OR REPLACE FUNCTION portal.get_groups_layouts_json()
  RETURNS jsonb AS
$BODY$
DECLARE
	r record;
	my_json jsonb;
BEGIN
    my_json = '{"lev":0,"id":0,"code":"WKTApp_plantas","title": "Group Layouts","parent_id": null,"children":[]}'::jsonb;

	    FOR r IN SELECT * from portal.get_groups_layouts_json_table() where lev = 1 order by id
	    LOOP
			my_json = jsonb_set(my_json,'{children}', (my_json->'children' || r.json));
	    END LOOP;
	Raise Notice '%',my_json;
	Return my_json;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;


-- Function: portal.get_groups_layouts_json_table()
-- DROP FUNCTION portal.get_groups_layouts_json_table();
CREATE OR REPLACE FUNCTION portal.get_groups_layouts_json_table()
  RETURNS TABLE(lev integer, id integer, parent_id integer, json jsonb) AS
$BODY$
DECLARE
    r record;
    my_json jsonb;
    tree_level integer = 0;
    myint integer;
    mystr text;
    tmp_json json;
    tmp2_json json;
    lev_iter integer;
BEGIN

    Drop  table if exists groups_layouts_json;
    Create temp table groups_layouts_json as select 0::integer lev, 0::integer as id,0::integer as parent_id, null::jsonb as json where 1=0;

    Drop table if exists tmp_tipo_planta;
    create temp table tmp_tipo_planta as select tp.id,codigo code,titulo title,tp.parent_id
      from portal.tipo_planta tp;

	Loop
	tree_level = tree_level + 1;

	    FOR r IN SELECT * from tmp_tipo_planta order by id
	    LOOP
		my_json = to_jsonb(row_to_json(r));
		If r.parent_id is null then


			insert into groups_layouts_json (lev,id,parent_id,json)
			values (tree_level,r.id,r.parent_id,my_json);
			Delete from tmp_tipo_planta tp where tp.id = r.id;
			continue;
		else
			if (select count(*) from groups_layouts_json gl where gl.id = r.parent_id) > 0 then
			        Select gl.lev into myint from groups_layouts_json gl where gl.id = r.parent_id;
				insert into groups_layouts_json (lev,id,parent_id,json)
				values (myint+1,r.id,r.parent_id,my_json);

				Delete from tmp_tipo_planta tp where tp.id = r.id;
			end if;

		end if;



	    END LOOP;

	--Raise notice 'level loop % end', tree_level;
	EXIT WHEN (select count(*) from tmp_tipo_planta)  = 0;
	Exit When tree_level > 4;
	End loop;




	------------------------------------------------------------------------------------------------- Need to insert plantas as group 's children ...first
	FOR r IN SELECT * from  groups_layouts_json
	LOOP

		if (Select count(p.json) FROM
		  portal.get_layouts_json_table() p
		  right join portal.plantas_tipos_plantas ptp on (ptp.planta_id = p.id)
		  right join groups_layouts_json tp on ( ptp.tipo_planta_id = tp.id )
		  where tp.id = r.id) > 0 then
			SELECT array_to_json(array_agg(p.json)) into tmp_json
			FROM
			  portal.get_layouts_json_table() p
			  right join portal.plantas_tipos_plantas ptp on (ptp.planta_id = p.id)
			  right join groups_layouts_json tp on ( ptp.tipo_planta_id = tp.id )
			  where tp.id = r.id;
		else
			tmp_json = NULL;
		end if;


		If tmp_json is not null Then
			my_json = r.json || to_jsonb('{"children":[]}'::json);
			my_json = jsonb_set(my_json,'{children}', to_jsonb(tmp_json));
			--raise notice '%',my_json;
			update groups_layouts_json gl set json = my_json where gl.id = r.id;
		End if;
	End Loop;


	------------------------------------------------------------------------------------------------- insert group in parent group's  children
	Select max(gl.lev) into lev_iter from groups_layouts_json gl;
	Loop
	--raise notice 'level %',lev_iter;
		FOR r IN SELECT distinct gl.parent_id from  groups_layouts_json gl where gl.lev = lev_iter
		Loop
			SELECT array_to_json(array_agg(gl.json)) into tmp_json
			from  groups_layouts_json gl where gl.parent_id = r.parent_id;
			--raise notice '%',tmp_json;

			Select gl.json into my_json from groups_layouts_json gl where gl.id = r.parent_id;

			if (my_json ? 'children') then
				tmp2_json = (my_json -> 'children') || to_jsonb(tmp_json);
				my_json = jsonb_set(my_json,'{children}', to_jsonb(tmp2_json));
				update groups_layouts_json as gl set json = my_json where gl.id = r.parent_id;
			else
				my_json = my_json || to_jsonb('{"children":[]}'::json);
				my_json = jsonb_set(my_json,'{children}', to_jsonb(tmp_json));
				update groups_layouts_json as gl set json = my_json where gl.id = r.parent_id;
			end if;



			--raise notice '%',my_json;


		End loop;
	lev_iter = lev_iter -1;
	Exit when lev_iter = 1;
	End loop;




	Return query select * from groups_layouts_json;
END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


-- Function: portal.get_layouts_json()
-- DROP FUNCTION portal.get_layouts_json();
CREATE OR REPLACE FUNCTION portal.get_layouts_json()
  RETURNS jsonb AS
$BODY$
DECLARE
	r record;
	my_json jsonb;
BEGIN
    my_json = '{"typeof":"root","lev":0,"id":0,"code":"Layouts","title": "WKTApp plantas","parent_id": null,"children":[]}'::jsonb;

	    FOR r IN SELECT * from portal.get_layouts_json_table() order by id
	    LOOP
			my_json = jsonb_set(my_json,'{children}', (my_json->'children' || r.json));
	    END LOOP;
	Raise Notice '%',my_json;
	Return my_json;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;


-- Function: portal.get_layouts_json_table()
-- DROP FUNCTION portal.get_layouts_json_table();
CREATE OR REPLACE FUNCTION portal.get_layouts_json_table()
  RETURNS TABLE(id integer, parent_id integer, json jsonb) AS
$BODY$
DECLARE
	r record;
	my_json jsonb;
	tmp_json json;
	tree_level integer = 0;
	myint integer;
	mystr text;
BEGIN
	drop table if exists layouts_json;
	create temp table layouts_json as select 0::integer as id,0::integer as parent_id, null::jsonb as json where 1=0;

	drop table if exists sublayouts;
	Create temp table sublayouts as
		select -2::integer lev, pl.id, planta_id parent_id, (formato||'-'||orientacao) code,
		('Layout '|| formato||'-'||orientacao) title, 'sub_layout'::text typeof
		from  portal.planta_layouts pl;


	drop table if exists layouts;
	Create temp table layouts as
		with plantas as (
		SELECT
		  planta.* , tipo_planta.id as parent_id
		FROM
		  portal.planta
		  left join portal.plantas_tipos_plantas on (plantas_tipos_plantas.planta_id = planta.id)
		  left join portal.tipo_planta on ( plantas_tipos_plantas.tipo_planta_id = tipo_planta.id )
		  order by planta.id
		  )
		select -1::integer lev, p.id, p.parent_id, codigo code, nome title, 'layout'::text typeof
		from  plantas p;


	FOR r IN SELECT * from layouts order by id
	LOOP

		SELECT array_to_json(array_agg(sublayouts)) into tmp_json FROM sublayouts where sublayouts.parent_id = r.id;

		If tmp_json is not null Then
			my_json = to_jsonb(row_to_json(r)) || to_jsonb('{"children":[]}'::json);
			my_json = jsonb_set(my_json,'{children}', to_jsonb(tmp_json));
			Insert into layouts_json (id,parent_id,json) values (r.id,r.parent_id,my_json);
		else
			Insert into layouts_json (id,parent_id,json) values (r.id,r.parent_id,to_jsonb(row_to_json(r)));
		End if;
		--raise notice 'Layout inserted: %',r.code;
	END LOOP;

	Return query select * from layouts_json;
END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 100;


-- Function: portal.get_maps_groups_layouts_json()
-- DROP FUNCTION portal.get_maps_groups_layouts_json();
CREATE OR REPLACE FUNCTION portal.get_maps_groups_layouts_json()
  RETURNS jsonb AS
$BODY$
DECLARE
	r record;
	my_json jsonb;
BEGIN
    my_json = '{"lev":0,"id":-1000,"code":"WKTApp","title": "WKTApp Maps","parent_id": null,"children":[]}'::jsonb;

	    FOR r IN SELECT * from portal.get_maps_groups_layouts_json_table() order by id
	    LOOP
			my_json = jsonb_set(my_json,'{children}', (my_json->'children' || r.json));
	    END LOOP;
	Raise Notice '%',my_json;
	Return my_json;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;


-- Function: portal.get_maps_groups_layouts_json_table()
-- DROP FUNCTION portal.get_maps_groups_layouts_json_table();
CREATE OR REPLACE FUNCTION portal.get_maps_groups_layouts_json_table()
  RETURNS TABLE(typeof text, id integer, parent_id integer, json jsonb) AS
$BODY$
DECLARE
    r record;
    my_json jsonb;
    tree_level integer = 0;
    myint integer;
    mystr text;
    tmp_json json;
    lev_iter integer;
BEGIN

    Drop  table if exists maps_groups_layouts_json;
    Create temp table maps_groups_layouts_json as
	select ''::text typeof, 0::integer as id,-1000::integer as parent_id, null::jsonb as json where 1=0;


    For r in select 'map'::text typeof, m.id, -1000::integer as parent_id, codigo code, titulo title from portal.mapa m order by id
    Loop
	insert into maps_groups_layouts_json (typeof, id, parent_id,json) Values ('map', r.id, -1000,row_to_json(r));
    End Loop;

	----------- Insert group plantas

	FOR r IN select * from maps_groups_layouts_json
	LOOP
		if (Select count(p.id) FROM
			portal.mapa m
			left join portal.mapas_tipos_plantas mtp on (m.id = mtp.mapa_id)
			left join (select * from portal.get_groups_layouts_json_table()) p on (mtp.tipo_planta_id = p.id)
			where m.id = r.id) > 0
		  then
			SELECT array_to_json(array_agg(p.json)) into tmp_json
			FROM
				portal.mapa m
				left join portal.mapas_tipos_plantas mtp on (m.id = mtp.mapa_id)
				left join (select * from portal.get_groups_layouts_json_table()) p on (mtp.tipo_planta_id = p.id)
				where m.id = r.id;
		else
			tmp_json = NULL;
		end if;


		If tmp_json is not null Then
			my_json = r.json || to_jsonb('{"children":[]}'::json);
			my_json = jsonb_set(my_json,'{children}', to_jsonb(tmp_json));
			--raise notice '%',my_json;
			update maps_groups_layouts_json mgl set json = my_json where mgl.id = r.id;
		End if;
	END LOOP;

	----------- Insert  plantas
	FOR r IN select * from maps_groups_layouts_json
	LOOP
		if (Select count(p.id)
			from portal.mapa m
			left join portal.mapas_plantas mp on (m.id = mp.mapa_id)
			left join (select * from portal.get_layouts_json_table()) p on (mp.planta_id = p.id)
			where m.id = r.id) > 0

		  then
			SELECT array_to_json(array_agg(p.json)) into tmp_json
			FROM portal.mapa m
			left join portal.mapas_plantas mp on (m.id = mp.mapa_id)
			left join (select * from portal.get_layouts_json_table()) p on (mp.planta_id = p.id)
			where m.id = r.id;
		else
			tmp_json = NULL;
		end if;


		If tmp_json is not null Then
		raise notice 'For layout directly associated, have children: %', r.json ? 'children';
		--raise notice 'json: %', array_length(jsonb_array_elements((r.json -> 'children')::jsonb),1);
			if not (r.json ? 'children') then
				my_json = r.json || to_jsonb('{"children":[]}'::json);
				my_json = (my_json -> 'children') || to_jsonb(tmp_json);
			else
				my_json = r.json;
				my_json = (r.json -> 'children') || to_jsonb(tmp_json);
			end if;

			my_json = jsonb_set(r.json,'{children}', my_json);
			update maps_groups_layouts_json mgl set json = my_json where mgl.id = r.id;
		End if;
	END LOOP;

	Return query select * from maps_groups_layouts_json;
END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


-- Function: portal.intersect_igt(text, integer)
-- DROP FUNCTION portal.intersect_igt(text, integer);
CREATE OR REPLACE FUNCTION portal.intersect_igt(
    IN _geom_ewkt text,
    IN _out_srid integer)
  RETURNS TABLE(rowid bigint, g1 text, g2 text, g3 text, dimensao integer, geom_ewkt text, area double precision, area_percent double precision, tipo text) AS
$BODY$
DECLARE
	--tmprec RECORD;
	--returnrec RECORD;
	data_srid integer;
	g Geometry; -- = ST_Transform(p_geom_ewkt::Geometry, 3763);

	area_geom double precision = 0;
	_sql text;
BEGIN

	select into data_srid st_srid(geom) from portal.pdm_ord limit 1;
	raise notice 'Data SRID=%', data_srid;
	g = ST_Transform(_geom_ewkt::Geometry, data_srid);
	raise notice 'g=%', st_astext(g);
	area_geom = ST_Area(g);


	return query
		SELECT row_number() over() as rowid, * FROM (
			(with ord as(
				SELECT pdm_ord.g1, pdm_ord.g2, pdm_ord.g3, ST_Union(ST_Intersection(geom, g)) as geom
				FROM portal.pdm_ord
				WHERE ST_INTERSECTS(geom, g)
				GROUP BY pdm_ord.g1, pdm_ord.g2, pdm_ord.g3 ORDER BY pdm_ord.g1, pdm_ord.g2, pdm_ord.g3
			)
			select ord.g1::text, ord.g2::text, ord.g3::text,
			ST_Dimension(geom) dimension, ST_AsEWKT(ST_Transform(geom, _out_srid)) ewkt,
			ST_Area(geom) area, CASE ST_Dimension(geom) WHEN 2 THEN (ST_Area(geom) * 100)/area_geom ELSE 0::double precision END as percent,
			'ord'::text
			from ord)
		Union all
			(
			with cond as(
				SELECT pdm_cond.g1, pdm_cond.g2, pdm_cond.g3, ST_Union(ST_Intersection(geom, g)) as geom
				FROM portal.pdm_cond
				WHERE ST_INTERSECTS(geom, g)
				GROUP BY pdm_cond.g1, pdm_cond.g2, pdm_cond.g3 ORDER BY pdm_cond.g1, pdm_cond.g2, pdm_cond.g3
			)
			select cond.g1::text, cond.g2::text, cond.g3::text,
			ST_Dimension(geom) dimension, ST_AsEWKT(ST_Transform(geom, _out_srid)) ewkt,
			ST_Area(geom) area, CASE ST_Dimension(geom) WHEN 2 THEN (ST_Area(geom) * 100)/area_geom ELSE 0::double precision END as percent,
			'cond'::text
			from cond
			)
		Union all
			(
			with eem as(
				SELECT pdm_eem.g1, pdm_eem.g2, pdm_eem.g3, ST_Union(ST_Intersection(geom, g)) as geom
				FROM portal.pdm_eem
				WHERE ST_INTERSECTS(geom, g)
				GROUP BY pdm_eem.g1, pdm_eem.g2, pdm_eem.g3 ORDER BY pdm_eem.g1, pdm_eem.g2, pdm_eem.g3
			)
			select eem.g1::text, eem.g2::text, eem.g3::text,
			ST_Dimension(geom) dimension, ST_AsEWKT(ST_Transform(geom, _out_srid)) ewkt,
			ST_Area(geom) area, CASE ST_Dimension(geom) WHEN 2 THEN (ST_Area(geom) * 100)/area_geom ELSE 0::double precision END as percent,
			'eem'::text
			from eem
			)
		) AS tab
		;

END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


-- Function: portal.intersect_igt_svc(text, integer)
-- DROP FUNCTION portal.intersect_igt_svc(text, integer);
CREATE OR REPLACE FUNCTION portal.intersect_igt_svc(
    IN _geom_ewkt text,
    IN _out_srid integer)
  RETURNS TABLE(g1 text, g2 text, g3 text, dimensao integer, geometry geometry, area double precision, area_percent double precision, tipo text) AS
$BODY$
DECLARE
	--tmprec RECORD;
	--returnrec RECORD;
	data_srid integer;
	g Geometry; -- = ST_Transform(p_geom_ewkt::Geometry, 3763);

	area_geom double precision = 0;
	_sql text;
BEGIN

	select into data_srid st_srid(geom) from portal.pdm_ord limit 1;
	raise notice 'Data SRID=%', data_srid;
	g = ST_Transform(_geom_ewkt::Geometry, data_srid);
	raise notice 'g=%', st_astext(g);
	area_geom = ST_Area(g);


	return query
		(with ord as(
			SELECT pdm_ord.g1, pdm_ord.g2, pdm_ord.g3, ST_Union(ST_Intersection(geom, g)) as geom
			FROM portal.pdm_ord
			WHERE ST_INTERSECTS(geom, g)
			GROUP BY pdm_ord.g1, pdm_ord.g2, pdm_ord.g3 ORDER BY pdm_ord.g1, pdm_ord.g2, pdm_ord.g3
		)
		select ord.g1::text, ord.g2::text, ord.g3::text,
		ST_Dimension(geom) dimension, (ST_Transform(geom, _out_srid)) gy,
		ST_Area(geom) area, CASE ST_Dimension(geom) WHEN 2 THEN (ST_Area(geom) * 100)/area_geom ELSE 0::double precision END as percent,
		'ord'::text
		from ord)
	Union all
		(
		with cond as(
			SELECT pdm_cond.g1, pdm_cond.g2, pdm_cond.g3, ST_Union(ST_Intersection(geom, g)) as geom
			FROM portal.pdm_cond
			WHERE ST_INTERSECTS(geom, g)
			GROUP BY pdm_cond.g1, pdm_cond.g2, pdm_cond.g3 ORDER BY pdm_cond.g1, pdm_cond.g2, pdm_cond.g3
		)
		select cond.g1::text, cond.g2::text, cond.g3::text,
		ST_Dimension(geom) dimension, (ST_Transform(geom, _out_srid)) gy,
		ST_Area(geom) area, CASE ST_Dimension(geom) WHEN 2 THEN (ST_Area(geom) * 100)/area_geom ELSE 0::double precision END as percent,
		'cond'::text
		from cond
		)
	Union all
		(
		with eem as(
			SELECT pdm_eem.g1, pdm_eem.g2, pdm_eem.g3, ST_Union(ST_Intersection(geom, g)) as geom
			FROM portal.pdm_eem
			WHERE ST_INTERSECTS(geom, g)
			GROUP BY pdm_eem.g1, pdm_eem.g2, pdm_eem.g3 ORDER BY pdm_eem.g1, pdm_eem.g2, pdm_eem.g3
		)
		select eem.g1::text, eem.g2::text, eem.g3::text,
		ST_Dimension(geom) dimension, (ST_Transform(geom, _out_srid)) gy,
		ST_Area(geom) area, CASE ST_Dimension(geom) WHEN 2 THEN (ST_Area(geom) * 100)/area_geom ELSE 0::double precision END as percent,
		'eem'::text
		from eem
		)
		;

END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


-- Function: portal.return_logs(integer)
-- DROP FUNCTION portal.return_logs(integer);
CREATE OR REPLACE FUNCTION portal.return_logs(IN nb_days integer)
  RETURNS TABLE(count bigint, logdate date, code text, descr text) AS
$BODY$
declare
	mysql text;
begin
	mysql = 'with logs as (
	    select extract(day from data_ref) dm, data_ref::date dd,codigo,nome from portal.audit_log log inner join portal.audit_operacao op on (log.operacao_id = op.id)
	),
	seri as (
	    select  (current_date - n)::date as dd
	    FROM generate_series(0, '|| nb_days::text ||', 1) as n
	)
	select count(codigo),seri.dd,codigo::text,nome::text from logs right join seri on (logs.dd=seri.dd)
	group by seri.dd,codigo,nome
	order by seri.dd,codigo';

	return query execute mysql;
end;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


-- Function: portal.return_logs_types(integer)
-- DROP FUNCTION portal.return_logs_types(integer);
CREATE OR REPLACE FUNCTION portal.return_logs_types(IN nb_days integer)
  RETURNS TABLE(logdate date, count integer, vm integer, ap integer, ep integer) AS
$BODY$
declare
	mysql text;
begin
	mysql = 'with logs as (
	select count,logdate,code from portal.return_logs('|| nb_days::text ||')
	), total as (
	select logdate::text,sum(count) from logs group by logdate order by logdate
	), vm as (
	select logdate::text,sum(count) from logs where code like ''VM'' group by logdate order by logdate
	), ap as (
	select logdate::text,sum(count) from logs where code like ''AP'' group by logdate order by logdate
	), ep as (
	select logdate::text,sum(count) from logs where code like ''EP'' group by logdate order by logdate
	)
	select total.logdate::date ,total.sum::integer count,coalesce(vm.sum::integer,0) vm,coalesce(ap.sum::integer,0) ap ,coalesce(ep.sum::integer,0) ep
	from total left join vm using (logdate) left join ap using (logdate) left join ep using (logdate)';

	return query execute mysql;
end;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


-- Function: portal.return_most_relevant_record(text, text, text)
-- DROP FUNCTION portal.return_most_relevant_record(text, text, text);
CREATE OR REPLACE FUNCTION portal.return_most_relevant_record(
    _table text,
    _returned_fields text,
    _geom_ewkt text)
  RETURNS jsonb AS
$BODY$
Declare
input_geom_srid integer;
sql text;
my_json jsonb;
BEGIN

input_geom_srid = st_srid(_geom_ewkt);

if st_dimension(_geom_ewkt) = 0 then
	raise notice 'Point input';

	sql = 'with t as ( Select ' || _returned_fields || ' from ' || _table || ' where
	st_intersects(st_transform(geom,'||input_geom_srid||'),'|| quote_literal(_geom_ewkt) ||'))
	Select array_to_json(array_agg(t)) FROM t limit 1';

	raise notice 'sql: %',sql;
	Execute sql into my_json;

elsif st_dimension(_geom_ewkt) = 1 then
	raise notice 'Line input';

	sql = 'with t as ( Select ' || _returned_fields || ' from ' || _table || ' where
	st_intersects(st_transform(geom,'||input_geom_srid||'),'|| quote_literal(_geom_ewkt) ||')
	order by st_length(st_intersection(st_transform(geom,'||input_geom_srid||'),'|| quote_literal(_geom_ewkt) ||')) desc limit 1)
	Select array_to_json(array_agg(t)) FROM t limit 1';

	raise notice 'sql: %',sql;
	Execute sql into my_json;
else
	raise notice 'Polygon input';

	sql = 'with t as ( Select ' || _returned_fields || ' from ' || _table || ' where
	st_intersects(st_transform(geom,'||input_geom_srid||'),'|| quote_literal(_geom_ewkt) ||')
	order by st_area(st_intersection(st_transform(geom,'||input_geom_srid||'),'|| quote_literal(_geom_ewkt) ||')) desc limit 1)
	Select array_to_json(array_agg(t)) FROM t limit 1';

	raise notice 'sql: %',sql;
	Execute sql into my_json;
end if;

Raise notice 'JSON: %',	my_json;
return my_json;

END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;


-- Function: portal.transform_coordinates(integer, double precision, double precision, double precision)
-- DROP FUNCTION portal.transform_coordinates(integer, double precision, double precision, double precision);
CREATE OR REPLACE FUNCTION portal.transform_coordinates(
    IN p_srid integer,
    IN p_x double precision,
    IN p_y double precision,
    IN p_z double precision)
  RETURNS TABLE(srid integer, codigo character varying, nome character varying, x double precision, y double precision, z double precision) AS
$BODY$
DECLARE
	tmprec RECORD;
	returnrec RECORD;
BEGIN
    FOR tmprec IN SELECT * FROM portal.sistema_coordenadas WHERE activo IS TRUE ORDER BY ordem LOOP
	SELECT INTO returnrec s.srid, ST_Transform(ST_SetSRID(ST_MakePoint(p_x, p_y, p_z), p_srid), tmprec.srid::integer) AS point
	FROM spatial_ref_sys s where s.srid = tmprec.srid;

    	RETURN QUERY VALUES (returnrec.srid, tmprec.codigo, tmprec.nome, ST_X(returnrec.point), ST_Y(returnrec.point), ST_Z(returnrec.point));
    END LOOP;
END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


-- Function: portal.intersects_layers(json, text, integer, integer)
-- DROP FUNCTION portal.intersects_layers(json, text, integer, integer);
CREATE OR REPLACE FUNCTION portal.intersects_layers(
    _layers json,
    _geom_ewkt text,
    _out_srid integer,
    _buffer integer DEFAULT 0)
  RETURNS jsonb AS
$BODY$
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
_geom_ewkt = st_makevalid(ST_Buffer(_geom_ewkt, _buffer));
end if;

my_json = _layers->'layers';
--raise notice 'my json=%', my_json;

For _i in select jsonb_array_elements(my_json) Loop

--raise notice '_i=%', _i;
_my_table_sql = (_i->>'schema') || '.' || (_i->>'table'); -- create table name for sql exec
raise notice 'my_table=%', _my_table_sql;
_my_fields_sql = '';

for _ii in select jsonb_array_elements(_i->'fields') Loop
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

End Loop;

Return jsonb_pretty(result_json);

END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION portal.intersects_layers(json, text, integer, integer)
  OWNER TO postgres;