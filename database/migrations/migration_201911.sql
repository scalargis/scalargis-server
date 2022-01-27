-- ALTER TABLE portal.tipo_planta DROP COLUMN seleccao_plantas;
ALTER TABLE portal.tipo_planta ADD COLUMN seleccao_plantas boolean;
ALTER TABLE portal.tipo_planta ALTER COLUMN seleccao_plantas SET DEFAULT true;

UPDATE portal.tipo_planta SET seleccao_plantas = TRUE;

-- ALTER TABLE portal.tipo_planta DROP COLUMN agrupar_plantas;
ALTER TABLE portal.tipo_planta ADD COLUMN agrupar_plantas boolean;
ALTER TABLE portal.tipo_planta ALTER COLUMN agrupar_plantas SET DEFAULT false;