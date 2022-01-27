-- Column: allow_sharing
-- ALTER TABLE portal.sharing DROP COLUMN allow_sharing;
ALTER TABLE portal.viewers ADD COLUMN allow_sharing boolean;


-- Table: portal.contact_message
-- DROP TABLE portal.contact_message;
CREATE TABLE portal.contact_message
(
  id serial NOT NULL,
  viewer_id integer,
  name character varying(255),
  email character varying(255),
  message text,
  message_json text,
  user_id integer,
  message_date date,
  checked boolean,
  checked_date date,
  closed boolean,
  closed_date date,
  notes text,
  message_uuid text,
  CONSTRAINT contact_message_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE portal.contact_message
  OWNER TO postgres;