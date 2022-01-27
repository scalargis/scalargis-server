Alter table portal.mapa add column show_homepage integer;
alter table portal.mapa add column img_homepage text;

ALTER TABLE portal.document_directory ADD COLUMN allow_upload boolean;
ALTER TABLE portal.document_directory ADD COLUMN upload_anonymous boolean;
ALTER TABLE portal.document_directory ADD COLUMN upload_overwrite boolean;
ALTER TABLE portal.document_directory ADD COLUMN upload_generate_filename boolean;
ALTER TABLE portal.document_directory ADD COLUMN allow_delete boolean;
ALTER TABLE portal.document_directory ADD COLUMN delete_anonymous boolean;

-- API Toponimia - cut troco by geometry
CREATE OR REPLACE FUNCTION toponimia.split_via_troco(IN _troco_id integer, IN _geom_ewkt geometry)
  RETURNS json AS
$BODY$
declare
	_mysql text;
	_json json;
	_intersects boolean = FALSE;
	_geom_collec geometry;
	_geom_troco geometry;
	_row geometry;
	_vias record;
	_inserted_troco_id integer;
begin
	_json = '{"split":false}'::json;
	_geom_ewkt = St_snaptogrid(st_transform(_geom_ewkt, 3763),0.01);
	Select geom into _geom_troco from toponimia.via_troco where id = _troco_id;
	If _geom_troco Is Null Then
		Return '{"split":false, "intersects":false, "input":false}'::json;
	End If;


	Select st_intersects(_geom_troco, _geom_ewkt) into _intersects;
	If not _intersects Then
		return '{"split":false, "intersects":false, "input":true}'::json;
	End If;

	select st_split(_geom_troco,_geom_ewkt) into _geom_collec;

	If _geom_collec Is Null Then
		Return '{"split":false, "intersects":true, "input":true}'::json;
	End If;

	For _vias in Select * From toponimia.via_x_via_troco Where via_troco_id = _troco_id Loop -- each via
		For _row In Select (St_dump(_geom_collec)).geom Loop -- each splited geoms
			With inserted as (
				INSERT INTO toponimia.via_troco (geom) VALUES (St_Multi(_row)) returning *
			)
			INSERT INTO toponimia.via_x_via_troco (via_id, via_troco_id) Select _vias.via_id, inserted.id From inserted;
		End loop;
	End loop;

	DELETE FROM toponimia.via_x_via_troco WHERE via_troco_id = _troco_id;
	DELETE FROM toponimia.via_troco WHERE id = _troco_id;

	Return '{"split":true, "intersects":true, "input":true}'::json;
end;
$BODY$
  LANGUAGE plpgsql VOLATILE;

