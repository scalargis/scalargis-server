ALTER TABLE portal.planta_layouts
DROP CONSTRAINT planta_layouts_planta_id_fkey,
ADD CONSTRAINT planta_layouts_planta_id_fkey FOREIGN KEY (planta_id)
  REFERENCES portal.planta (id) MATCH SIMPLE
  ON UPDATE NO ACTION ON DELETE CASCADE;

-- ALTER TABLE portal.planta DROP COLUMN tolerancia;
ALTER TABLE portal.planta ADD COLUMN tolerancia integer;