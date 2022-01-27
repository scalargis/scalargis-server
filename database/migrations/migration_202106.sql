ALTER TABLE portal.viewers DROP COLUMN keywords;
ALTER TABLE portal.viewers ADD COLUMN keywords text[];

-- Table: portal.coordinate_systems
-- DROP TABLE portal.coordinate_systems;
CREATE TABLE portal.coordinate_systems
(
  id serial NOT NULL,
  code text,
  "name" text,
  description text,
  config_json text,
  "order" integer,
  id_user_create integer,
  created_at date,
  id_user_update integer,
  updated_at date,
  active boolean DEFAULT true,
  read_only boolean DEFAULT false,
  CONSTRAINT coordinate_systems_pkey PRIMARY KEY (id),
  CONSTRAINT coordinate_systems_code_key UNIQUE (code)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE portal.coordinate_systems
  OWNER TO postgres;


-- Table: portal.group
-- DROP TABLE portal.group;
CREATE TABLE portal.group
(
  id serial NOT NULL,
  name character varying(80),
  description character varying(255),
  read_only boolean,
  CONSTRAINT group_pkey PRIMARY KEY (id),
  CONSTRAINT group_name_key UNIQUE (name)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE portal.group
  OWNER TO postgres;


-- Table: portal.groups_users
-- DROP TABLE portal.groups_users;
CREATE TABLE portal.groups_users
(
  user_id integer,
  group_id integer,
  CONSTRAINT groups_users_group_id_fkey FOREIGN KEY (group_id)
      REFERENCES portal.group (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT groups_users_user_id_fkey FOREIGN KEY (user_id)
      REFERENCES portal."user" (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE portal.groups_users
  OWNER TO postgres;


-- Table: portal.permission
-- DROP TABLE portal.permission;
CREATE TABLE portal.permission
(
  id serial NOT NULL,
  name character varying(80),
  description character varying(255),
  read_only boolean,
  CONSTRAINT permission_pkey PRIMARY KEY (id),
  CONSTRAINT permission_name_key UNIQUE (name)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE portal.permission
  OWNER TO postgres;


-- Table: portal.roles_permissions
-- DROP TABLE portal.roles_permission;
CREATE TABLE portal.roles_permissions
(
  role_id integer,
  permission_id integer,
  CONSTRAINT roles_permissions_role_id_fkey FOREIGN KEY (role_id)
      REFERENCES portal.role (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT roles_permissions_permission_id_fkey FOREIGN KEY (permission_id)
      REFERENCES portal.permission (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE portal.roles_permissions
  OWNER TO postgres;

-- -------------------------------------------------------------------------------
-- Table: portal."group"
-- DROP TABLE portal."group";
CREATE TABLE portal."group"
(
  id serial NOT NULL,
  name character varying(80),
  description character varying(255),
  read_only boolean,
  CONSTRAINT group_pkey PRIMARY KEY (id),
  CONSTRAINT group_name_key UNIQUE (name)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE portal."group"
  OWNER TO postgres;


-- Table: portal.groups_users
-- DROP TABLE portal.groups_users;
CREATE TABLE portal.groups_users
(
  user_id integer,
  group_id integer,
  CONSTRAINT groups_users_group_id_fkey FOREIGN KEY (group_id)
      REFERENCES portal."group" (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT groups_users_user_id_fkey FOREIGN KEY (user_id)
      REFERENCES portal."user" (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE portal.groups_users
  OWNER TO postgres;