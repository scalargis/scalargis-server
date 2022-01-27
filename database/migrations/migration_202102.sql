-- Table: portal.user_viewer_session
-- DROP TABLE portal.user_viewer_session;
CREATE TABLE portal.user_viewer_session
(
  user_id integer,
  viewer_id integer,
  id serial NOT NULL,
  config_json text,
  id_user_create integer,
  id_user_update integer,
  config_version character varying(10),
  created_at timestamp without time zone,
  updated_at timestamp without time zone,
  CONSTRAINT user_viewer_session_pkey PRIMARY KEY (id),
  CONSTRAINT user_viewer_session_user_id_fkey FOREIGN KEY (user_id)
      REFERENCES portal."user" (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT user_viewer_session_viewer_id_fkey FOREIGN KEY (viewer_id)
      REFERENCES portal.viewers (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT user_viewer_session_user_id_viewer_id_key UNIQUE (user_id, viewer_id)
)
WITH (
  OIDS=FALSE
);

ALTER TABLE portal.tipo_planta ADD COLUMN form_fields json;
ALTER TABLE portal.planta ADD COLUMN form_fields json;