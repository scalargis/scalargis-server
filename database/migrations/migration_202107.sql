ALTER TABLE portal.user ADD COLUMN auth_token character varying;
ALTER TABLE portal.user ADD COLUMN auth_token_expire timestamp without time zone;


-- Table: portal.roles_groups
-- DROP TABLE portal.roles_groups;
CREATE TABLE portal.roles_groups
(
  group_id integer,
  role_id integer,
  CONSTRAINT roles_groups_role_id_fkey FOREIGN KEY (role_id)
      REFERENCES portal.role (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT roles_groups_group_id_fkey FOREIGN KEY (group_id)
      REFERENCES portal."group" (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE portal.roles_groups
  OWNER TO postgres;


-- Foreign Key: portal.user_viewer_session_viewer_id_fkey
-- ALTER TABLE portal.user_viewer_session DROP CONSTRAINT user_viewer_session_viewer_id_fkey;
ALTER TABLE portal.user_viewer_session
  ADD CONSTRAINT user_viewer_session_viewer_id_fkey FOREIGN KEY (viewer_id)
      REFERENCES portal.viewers (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE CASCADE;

-- Foreign Key: portal.user_viewer_session_user_id_fkey
-- ALTER TABLE portal.user_viewer_session DROP CONSTRAINT user_viewer_session_user_id_fkey;
ALTER TABLE portal.user_viewer_session
  ADD CONSTRAINT user_viewer_session_user_id_fkey FOREIGN KEY (user_id)
      REFERENCES portal."user" (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE CASCADE;

-- Foreign Key: portal.viewers_roles_role_id_fkey
-- ALTER TABLE portal.viewers_roles DROP CONSTRAINT viewers_roles_role_id_fkey;
ALTER TABLE portal.viewers_roles
  ADD CONSTRAINT viewers_roles_role_id_fkey FOREIGN KEY (role_id)
      REFERENCES portal.role (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE CASCADE;

-- Foreign Key: portal.viewers_roles_viewer_id_fkey
-- ALTER TABLE portal.viewers_roles DROP CONSTRAINT viewers_roles_viewer_id_fkey;
ALTER TABLE portal.viewers_roles
  ADD CONSTRAINT viewers_roles_viewer_id_fkey FOREIGN KEY (viewer_id)
      REFERENCES portal.viewers (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE CASCADE;