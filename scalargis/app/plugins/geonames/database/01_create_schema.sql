-- Schema: geonames
-- DROP SCHEMA geognames;
CREATE SCHEMA geonames
  AUTHORIZATION postgres;

-- geonames.geographical_names definition
-- DROP TABLE geonames.geographical_names;
CREATE TABLE geonames.geographical_names (
	id int4 NOT NULL,
	geom public.geometry NULL,
	name text NULL,
    source text NULL,
    "type" text NULL,
    fs_str tsvector NULL,
    "group" text NULL,
    admin_level1 text NULL,
    admin_level2 text NULL,
    admin_level3 text NULL,
    admin_level4 text NULL,
    admin_code text NULL,
	CONSTRAINT geographical_names_pkey PRIMARY KEY (id)
);
CREATE INDEX geographical_names_geom_idx ON geonames.geographical_names USING gist (geom);

-- Permissions

ALTER TABLE geonames.geographical_names OWNER TO postgres;
GRANT ALL ON TABLE geonames.geographical_names TO postgres;