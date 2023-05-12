-- Function: {schema}.get_platform_basic_stats()
-- DROP FUNCTION {schema}.get_platform_basic_stats();
CREATE OR REPLACE FUNCTION {schema}.get_platform_basic_stats()
  RETURNS text AS
$BODY$
declare
nb_users integer;
nb_groups integer;
nb_viewers integer;
nb_ops integer;
out_json jsonb;
begin

	select count(*) into nb_users from {schema}."user";
	select count(*) into nb_groups from {schema}."role";
	select count(*) into nb_viewers from {schema}.viewers;
	select count(*) into nb_ops from {schema}.audit_log;


	Select  jsonb_build_object(
			'nb_users', nb_users,
			'nb_groups', nb_groups,
			'nb_viewers', nb_viewers,
			'nb_ops' , nb_ops
		) into out_json;



	return  out_json::text;

end;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;


-- Function: {schema}.get_platform_day_stats(text, integer)
-- DROP FUNCTION {schema}.get_platform_day_stats(text, integer);
CREATE OR REPLACE FUNCTION {schema}.get_platform_day_stats(
    IN _op_type_code text,
    IN _owner_id integer)
  RETURNS TABLE(stats text) AS
$BODY$
begin

return query select (
	with daycount as (
		select date_trunc('day', date_ref)::date as dt,ao.name as tipo_op,  count(*) as c from {schema}.audit_log avl
		left join {schema}.audit_operation ao on (avl.operation_id = ao.id)
		left join {schema}.viewers vw on (avl.id_viewer = vw.id)
		where ao.code like _op_type_code
		and (vw.owner_id = _owner_id or _owner_id IS null)
		group by 1, 2
		order by 1 asc
	)
	,
	allrows as (
		Select  jsonb_build_object(
			'date',       dt,
			'count',      c
		) as dayrow from daycount
	)
	Select jsonb_build_object(
	    'type',     'collection',
	    'values', jsonb_agg(dayrow)
	)::text as stats from allrows

);

end;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1;


-- Function: {schema}.transform_coordinates(integer, double precision, double precision, double precision)
-- DROP FUNCTION {schema}.transform_coordinates(integer, double precision, double precision, double precision);
CREATE OR REPLACE FUNCTION {schema}.transform_coordinates(
    IN p_srid integer,
    IN p_x double precision,
    IN p_y double precision,
    IN p_z double precision)
  RETURNS TABLE(srid integer, code text, name text, x double precision, y double precision, z double precision) AS
$BODY$
DECLARE
	tmprec RECORD;
	returnrec RECORD;
BEGIN
    FOR tmprec IN SELECT * FROM {schema}.coordinate_systems WHERE active IS TRUE ORDER BY "order" LOOP
	SELECT INTO returnrec s.srid, ST_Transform(ST_SetSRID(ST_MakePoint(p_x, p_y, p_z), p_srid), tmprec.srid::integer) AS point
	FROM spatial_ref_sys s where s.srid = tmprec.srid;

    	RETURN QUERY VALUES (returnrec.srid, tmprec.code, tmprec.name, ST_X(returnrec.point), ST_Y(returnrec.point), ST_Z(returnrec.point));
    END LOOP;
END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


CREATE OR REPLACE FUNCTION {schema}.generate_print_output_number()
RETURNS integer
LANGUAGE plpgsql
AS $function$
DECLARE
    new_output_number integer := null;
BEGIN
    SELECT INTO new_output_number COALESCE(max(output_number)+1, 1)
	FROM {schema}.print_output_number
	WHERE output_year= date_part('year', CURRENT_DATE);

    INSERT INTO {schema}.print_output_number (output_number, output_year)
		VALUES (new_output_number, date_part('year', CURRENT_DATE));


    RETURN new_output_number;
END;
$function$
;

