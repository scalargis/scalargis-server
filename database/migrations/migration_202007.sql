-- Table: common.concelho_local
-- DROP TABLE common.concelho_local;
CREATE TABLE common.concelho_local
(
  id serial NOT NULL,
  geom geometry(MultiPolygon,3763),
  dico character varying(254),
  concelho character varying(254),
  distrito character varying(254),
  taa character varying(254),
  area_ea_ha double precision,
  area_t_ha double precision,
  des_simpli character varying(254),
  CONSTRAINT concelho_local_pkey PRIMARY KEY (id),
  CONSTRAINT concelho_local_dico_key UNIQUE (dico)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE common.concelho_local
  OWNER TO postgres;