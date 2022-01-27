ALTER TABLE portal."user" ADD COLUMN default_map character varying(255);

ALTER TABLE portal.planta ADD COLUMN multi_geom boolean;
ALTER TABLE portal.planta ALTER COLUMN multi_geom SET DEFAULT false;

ALTER TABLE portal.tipo_planta ADD COLUMN multi_geom boolean;
ALTER TABLE portal.tipo_planta ALTER COLUMN multi_geom SET DEFAULT false;