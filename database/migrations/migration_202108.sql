DROP FUNCTION portal.get_platform_day_stats(text);

-- Function: portal.get_platform_day_stats(text, integer)
-- DROP FUNCTION portal.get_platform_day_stats(text, integer);
CREATE OR REPLACE FUNCTION portal.get_platform_day_stats(IN _op_type_code text, IN _owner_id integer)
  RETURNS TABLE(stats text) AS
$BODY$
begin

return query select (
	with daycount as (
		select date_trunc('day', data_ref)::date as dt,ao.nome as tipo_op,  count(*) as c from portal.audit_viewer_log avl
		left join portal.audit_operacao ao on (avl.operation_id = ao.id)
		left join portal.viewers vw on (avl.id_viewer = vw.id)
		where ao.codigo like _op_type_code
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
ALTER FUNCTION portal.get_platform_day_stats(text, integer)
  OWNER TO postgres;



-- ALTER TABLE portal.viewers DROP COLUMN img_icon;
ALTER TABLE portal.viewers ADD COLUMN img_icon character varying;

-- ALTER TABLE portal.viewers DROP COLUMN styles;
ALTER TABLE portal.viewers ADD COLUMN styles text;
-- ALTER TABLE portal.viewers DROP COLUMN scripts;
ALTER TABLE portal.viewers ADD COLUMN scripts text;

-- ALTER TABLE portal.viewers DROP COLUMN custom_script;
ALTER TABLE portal.viewers ADD COLUMN custom_script text;
-- ALTER TABLE portal.viewers DROP COLUMN custom_style;
ALTER TABLE portal.viewers ADD COLUMN custom_style text;

-- ALTER TABLE portal.planta DROP COLUMN owner_id;
ALTER TABLE portal.planta ADD COLUMN owner_id integer;
ALTER TABLE portal.planta
  ADD CONSTRAINT planta_user_owner_id_fkey FOREIGN KEY (owner_id)
      REFERENCES portal."user" (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION;

-- ALTER TABLE portal.tipo_planta DROP COLUMN owner_id;
ALTER TABLE portal.tipo_planta ADD COLUMN owner_id integer;
ALTER TABLE portal.tipo_planta
  ADD CONSTRAINT tipo_planta_user_owner_id_fkey FOREIGN KEY (owner_id)
      REFERENCES portal."user" (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION;