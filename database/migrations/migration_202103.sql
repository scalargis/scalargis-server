-- portal.audit_viewer_log definition
-- Drop table
-- DROP TABLE portal.audit_viewer_log;
CREATE TABLE portal.audit_viewer_log (
	id serial NOT NULL,
	id_viewer integer NULL,
	id_ref integer NULL,
	data_ref timestamp NULL,
	description text NULL,
	id_user integer NULL,
	id_module integer NULL,
	id_theme integer NULL,
	operation_id integer NULL,
	CONSTRAINT audit_viewer_log_pkey PRIMARY KEY (id)
);

INSERT INTO portal.audit_operacao(codigo, nome, flg_ro) VALUES ('I','Inserção', True);
INSERT INTO portal.audit_operacao(codigo, nome, flg_ro) VALUES ('E','Edição', True);
INSERT INTO portal.audit_operacao(codigo, nome, flg_ro) VALUES ('R','Remoção', True);
INSERT INTO portal.audit_operacao(codigo, nome, flg_ro) VALUES ('A','Anulação', True);
INSERT INTO portal.audit_operacao(codigo, nome, flg_ro) VALUES ('P','Reposição', True);
INSERT INTO portal.audit_operacao(codigo, nome, flg_ro) VALUES ('C','Consulta', True);
INSERT INTO portal.audit_operacao(codigo, nome, flg_ro) VALUES ('VM','Visualização de Mapa', True);
INSERT INTO portal.audit_operacao(codigo, nome, flg_ro) VALUES ('EP','Emissão de Planta', True);
INSERT INTO portal.audit_operacao(codigo, nome, flg_ro) VALUES ('EPM','Emissão de Planta - Merge', True);