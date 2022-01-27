SET search_path = portal, pg_catalog;

CREATE TABLE document_directory_rules
(
  id integer NOT NULL,
  doc_dir_id integer,
  mapa_id integer,
  filtro text,
  excluir text,
  excluir_dir text,
  descricao text
);
CREATE SEQUENCE document_directory_rules_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE document_directory_rules_id_seq OWNED BY document_directory_rules.id;
ALTER TABLE ONLY document_directory_rules ALTER COLUMN id SET DEFAULT nextval('document_directory_rules_id_seq'::regclass);

ALTER TABLE ONLY document_directory_rules
    ADD CONSTRAINT document_directory_rules_pkey PRIMARY KEY (id);

ALTER TABLE ONLY document_directory_rules
    ADD CONSTRAINT document_directory_id_fkey FOREIGN KEY (doc_dir_id) REFERENCES document_directory(id);

ALTER TABLE ONLY document_directory_rules
    ADD CONSTRAINT document_directory_mapa_id_fkey FOREIGN KEY (mapa_id) REFERENCES mapa(id);

CREATE INDEX fki_document_directory_id_fk
  ON document_directory_rules
  USING btree
  (doc_dir_id);

CREATE INDEX fki_mapa_id_fk
  ON document_directory_rules
  USING btree
  (mapa_id);