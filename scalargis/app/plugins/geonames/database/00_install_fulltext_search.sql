CREATE EXTENSION pg_trgm SCHEMA public;
CREATE EXTENSION unaccent SCHEMA public;

CREATE TEXT SEARCH CONFIGURATION pt ( COPY = portuguese );
ALTER TEXT SEARCH CONFIGURATION pt ALTER MAPPING
FOR hword, hword_part, word WITH unaccent, portuguese_stem;

--Test
SELECT * FROM ts_debug('pt', '
As bases de dados relacionais, como o PostgreSQL, existem para ajudar os utilizadores a organizar os dados e a compreender as relações entre esses dados. O PostgreSQL é uma base de dados relacional open-source apoiada por 30 anos de desenvolvimento, sendo uma das bases de dados relacionais mais consagradas disponíveis. O PostgreSQL deve a sua popularidade entre programadores e administradores à sua flexibilidade e integridade notáveis. Por exemplo, o PostgreSQL suporta consultas relacionais e não relacionais e a sua natureza open-source significa que uma comunidade dedicada de mais de 600 contribuidores melhora constantemente o sistema de base de dados.
');