ALTER TABLE portal.sistema_coordenadas ADD COLUMN unidades text;

INSERT INTO portal.widget(codigo, titulo)
    VALUES ('overviewmap', 'Mapa de Enquadramento');