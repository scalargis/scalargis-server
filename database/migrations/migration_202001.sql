ALTER TABLE portal.mapas_widgets
    ADD COLUMN target character varying(255);

ALTER TABLE portal.sistema_coordenadas
  DROP CONSTRAINT sistema_coordenadas_srid_key;