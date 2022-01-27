--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.2
-- Dumped by pg_dump version 9.6.2

-- Started on 2018-06-05 16:01:14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
--  Create extension
--
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;

--
--  Create extension for full-text search support
--
CREATE EXTENSION unaccent;
CREATE TEXT SEARCH CONFIGURATION pt ( COPY = portuguese );
ALTER TEXT SEARCH CONFIGURATION pt ALTER MAPPING FOR hword, hword_part, word WITH unaccent, portuguese_stem;
CREATE EXTENSION pg_trgm;

CREATE SCHEMA common;
CREATE SCHEMA portal;
CREATE SCHEMA cartabase;
CREATE SCHEMA cartografia;
CREATE SCHEMA planeamento;
CREATE SCHEMA toponymy;
CREATE SCHEMA toponimia;


--
-- Schema: COMMON
--

SET search_path = common, pg_catalog;

CREATE TABLE freguesia_local
(
  id integer NOT NULL,
  geom public.geometry(MultiPolygon,3763),
  dicofre character varying(254),
  freguesia character varying(254),
  concelho character varying(254),
  distrito character varying(254),
  taa character varying(254),
  area_ea_ha double precision,
  area_t_ha double precision,
  des_simpli character varying(254)
);
CREATE SEQUENCE freguesia_local_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE freguesia_local_id_seq OWNED BY freguesia_local.id;
ALTER TABLE ONLY freguesia_local ALTER COLUMN id SET DEFAULT nextval('freguesia_local_id_seq'::regclass);
ALTER TABLE ONLY freguesia_local
    ADD CONSTRAINT freguesia_local_pkey PRIMARY KEY (id);
ALTER TABLE ONLY freguesia_local
    ADD CONSTRAINT freguesia_local_dicofre_key UNIQUE (dicofre);


--
-- Schema: cartabase
--

SET search_path = cartabase, pg_catalog;

CREATE TABLE topo (
    ogc_fid integer NOT NULL,
    wkb_geometry public.geometry(Point,3763),
    refname character varying,
    txtmemo character varying,
    mslink_odb double precision,
    descr character varying
);
CREATE SEQUENCE topo_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE topo_ogc_fid_seq OWNED BY topo.ogc_fid;
ALTER TABLE ONLY topo ALTER COLUMN ogc_fid SET DEFAULT nextval('topo_ogc_fid_seq'::regclass);
ALTER TABLE ONLY topo
    ADD CONSTRAINT topo_pkey PRIMARY KEY (ogc_fid);


--
-- Schema: CARTOGRAFIA
--

SET search_path = cartografia, pg_catalog;

CREATE TABLE freguesia (
    id integer NOT NULL,
    geom public.geometry(MultiPolygon,3763),
    dicofre character varying(254),
    freguesia character varying(254),
    concelho character varying(254),
    distrito character varying(254),
    taa character varying(254),
    area_ea_ha double precision,
    area_t_ha double precision,
    des_simpli character varying(254)
);
CREATE SEQUENCE freguesia_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE freguesia_id_seq OWNED BY freguesia.id;
ALTER TABLE ONLY freguesia ALTER COLUMN id SET DEFAULT nextval('freguesia_id_seq'::regclass);
ALTER TABLE ONLY freguesia
    ADD CONSTRAINT freguesia_pkey PRIMARY KEY (id);
ALTER TABLE ONLY freguesia
    ADD CONSTRAINT freguesia_dicofre_key UNIQUE (dicofre);

--
-- Schema: PLANEAMENTO
--

SET search_path = planeamento, pg_catalog;

CREATE TABLE dinamica_plano (
    id integer NOT NULL,
    nome text,
    nome_abrev character varying(255),
    data_procedimento date,
    diploma_procedimento character varying(255),
    dr_procedimento character varying(255),
    deposito character varying(255),
    data_publicacao date,
    diploma_publicacao character varying(255),
    dr_publicacao character varying(255),
    descricao text,
    anulado boolean,
    plano_id integer,
    tipo_alteracao_plano_id integer,
    estado_plano_id integer,
    id_user_ins integer,
    data_ins date,
    ordem integer
);
CREATE SEQUENCE dinamica_plano_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE dinamica_plano_id_seq OWNED BY dinamica_plano.id;
ALTER TABLE ONLY dinamica_plano ALTER COLUMN id SET DEFAULT nextval('dinamica_plano_id_seq'::regclass);
ALTER TABLE ONLY dinamica_plano
    ADD CONSTRAINT dinamica_plano_pkey PRIMARY KEY (id);


CREATE TABLE documento_plano (
    id integer NOT NULL,
    nome text,
    nome_abrev character varying(255),
    descricao text,
    url text,
    ficheiro character varying(255),
    ficheiro_original character varying(255),
    url_mapa text,
    anulado boolean,
    plano_id integer,
    dinamica_plano_id integer,
    id_user_ins integer,
    data_ins date,
    ordem integer
);
CREATE SEQUENCE documento_plano_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE documento_plano_id_seq OWNED BY documento_plano.id;
ALTER TABLE ONLY documento_plano ALTER COLUMN id SET DEFAULT nextval('documento_plano_id_seq'::regclass);
ALTER TABLE ONLY documento_plano
    ADD CONSTRAINT documento_plano_pkey PRIMARY KEY (id);


CREATE TABLE estado_plano (
    id integer NOT NULL,
    codigo character varying(255),
    nome character varying(500),
    descricao text,
    id_user_ins integer,
    data_ins date
);
CREATE SEQUENCE estado_plano_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE estado_plano_id_seq OWNED BY estado_plano.id;
ALTER TABLE ONLY estado_plano ALTER COLUMN id SET DEFAULT nextval('estado_plano_id_seq'::regclass);
ALTER TABLE ONLY estado_plano
    ADD CONSTRAINT estado_plano_pkey PRIMARY KEY (id);
ALTER TABLE ONLY estado_plano
    ADD CONSTRAINT estado_plano_codigo_key UNIQUE (codigo);


CREATE TABLE ficheiro_documento_plano (
    id integer NOT NULL,
    nome text,
    nome_abrev character varying(255),
    descricao text,
    url text,
    ficheiro character varying(255),
    ficheiro_original character varying(255),
    url_mapa text,
    anulado boolean,
    documento_plano_id integer,
    id_user_ins integer,
    data_ins date,
    ordem integer
);
CREATE SEQUENCE ficheiro_documento_plano_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE ficheiro_documento_plano_id_seq OWNED BY ficheiro_documento_plano.id;
ALTER TABLE ONLY ficheiro_documento_plano ALTER COLUMN id SET DEFAULT nextval('ficheiro_documento_plano_id_seq'::regclass);
ALTER TABLE ONLY ficheiro_documento_plano
    ADD CONSTRAINT ficheiro_documento_plano_pkey PRIMARY KEY (id);


CREATE TABLE plano (
    id integer NOT NULL,
    codigo character varying(255),
    nome text,
    nome_abrev character varying(255),
    deposito character varying(255),
    data_publicacao date,
    diploma_publicacao character varying(255),
    dr_publicacao character varying(255),
    descricao text,
    anulado boolean,
    tipo_plano_id integer,
    estado_plano_id integer,
    wkb_geometry public.geometry(MultiPolygon,3763),
    id_user_ins integer,
    data_ins date,
    ordem integer
);
CREATE SEQUENCE plano_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE plano_id_seq OWNED BY plano.id;
ALTER TABLE ONLY plano ALTER COLUMN id SET DEFAULT nextval('plano_id_seq'::regclass);
ALTER TABLE ONLY plano
    ADD CONSTRAINT plano_pkey PRIMARY KEY (id);
ALTER TABLE ONLY plano
    ADD CONSTRAINT plano_codigo_key UNIQUE (codigo);

CREATE TABLE tipo_alteracao_plano (
    id integer NOT NULL,
    codigo character varying(255),
    nome character varying(500),
    descricao text,
    id_user_ins integer,
    data_ins date
);
CREATE SEQUENCE tipo_alteracao_plano_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE tipo_alteracao_plano_id_seq OWNED BY tipo_alteracao_plano.id;
ALTER TABLE ONLY tipo_alteracao_plano ALTER COLUMN id SET DEFAULT nextval('tipo_alteracao_plano_id_seq'::regclass);
ALTER TABLE ONLY tipo_alteracao_plano
    ADD CONSTRAINT tipo_alteracao_plano_pkey PRIMARY KEY (id);
ALTER TABLE ONLY tipo_alteracao_plano
    ADD CONSTRAINT tipo_alteracao_plano_codigo_key UNIQUE (codigo);


CREATE TABLE tipo_plano (
    id integer NOT NULL,
    codigo character varying(255),
    nome character varying(500),
    descricao text,
    id_user_ins integer,
    data_ins date
);
CREATE SEQUENCE tipo_plano_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE tipo_plano_id_seq OWNED BY tipo_plano.id;
ALTER TABLE ONLY tipo_plano ALTER COLUMN id SET DEFAULT nextval('tipo_plano_id_seq'::regclass);
ALTER TABLE ONLY tipo_plano
    ADD CONSTRAINT tipo_plano_pkey PRIMARY KEY (id);
ALTER TABLE ONLY tipo_plano
    ADD CONSTRAINT tipo_plano_codigo_key UNIQUE (codigo);


--
-- Schema: PORTAL
--

SET search_path = portal, pg_catalog;

CREATE TABLE audit_log (
    id integer NOT NULL,
    id_ref integer,
    data_ref timestamp without time zone,
    descricao text,
    id_user integer,
    id_modulo integer,
    id_tema integer,
    operacao_id integer,
    id_mapa integer
);
CREATE SEQUENCE audit_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE audit_log_id_seq OWNED BY audit_log.id;
ALTER TABLE ONLY audit_log ALTER COLUMN id SET DEFAULT nextval('audit_log_id_seq'::regclass);
ALTER TABLE ONLY audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


CREATE TABLE audit_operacao (
    id integer NOT NULL,
    codigo character varying(50),
    nome character varying(500),
    descricao text,
    n1 double precision,
    n2 double precision,
    v1 character varying(50),
    v2 character varying(50),
    anulado boolean,
    flg_ro boolean
);
CREATE SEQUENCE audit_operacao_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE audit_operacao_id_seq OWNED BY audit_operacao.id;
ALTER TABLE ONLY audit_operacao ALTER COLUMN id SET DEFAULT nextval('audit_operacao_id_seq'::regclass);
ALTER TABLE ONLY audit_operacao
    ADD CONSTRAINT audit_operacao_pkey PRIMARY KEY (id);
ALTER TABLE ONLY audit_operacao
    ADD CONSTRAINT audit_operacao_codigo_key UNIQUE (codigo);


INSERT INTO portal.audit_operacao VALUES (1, 'I', 'Inserção', NULL, NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO portal.audit_operacao VALUES (2, 'E', 'Edição', NULL, NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO portal.audit_operacao VALUES (3, 'R', 'Remoção', NULL, NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO portal.audit_operacao VALUES (4, 'A', 'Anulação', NULL, NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO portal.audit_operacao VALUES (5, 'P', 'Reposição', NULL, NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO portal.audit_operacao VALUES (6, 'C', 'Consulta', NULL, NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO portal.audit_operacao VALUES (7, 'VM', 'Visualização de Mapa', NULL, NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO portal.audit_operacao VALUES (8, 'EP', 'Emissão de Planta', NULL, NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO portal.audit_operacao VALUES (9, 'AP', 'Análise de Plano', NULL, NULL, NULL, NULL, NULL, NULL, true);

CREATE TABLE catalogo_metadados (
    id integer NOT NULL,
    codigo character varying(255) NOT NULL,
    titulo character varying(500) NOT NULL,
    url_base character varying(500) NOT NULL,
    url_csw character varying(500) NOT NULL,
    descricao character varying(1024),
    autenticacao boolean,
    username character varying(255),
    password character varying(255),
    activo boolean,
    tipo character varying(50),
    portal boolean,
    xslt_results_file character varying(500),
    xslt_results text,
    data_ins timestamp without time zone,
    id_user_ins integer,
    xslt_metadata_file character varying(500),
    xslt_metadata text
);
CREATE SEQUENCE catalogo_metadados_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE catalogo_metadados_id_seq OWNED BY catalogo_metadados.id;
ALTER TABLE ONLY catalogo_metadados ALTER COLUMN id SET DEFAULT nextval('catalogo_metadados_id_seq'::regclass);
ALTER TABLE ONLY catalogo_metadados
    ADD CONSTRAINT catalogo_metadados_pkey PRIMARY KEY (id);
ALTER TABLE ONLY catalogo_metadados
    ADD CONSTRAINT catalogo_metadados_codigo_key UNIQUE (codigo);

CREATE TABLE configuracao_mapa (
    id integer NOT NULL,
    titulo character varying(255),
    config text,
    descricao text,
    id_user_ins integer,
    data_ins date
);
CREATE SEQUENCE configuracao_mapa_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE configuracao_mapa_id_seq OWNED BY configuracao_mapa.id;
ALTER TABLE ONLY configuracao_mapa ALTER COLUMN id SET DEFAULT nextval('configuracao_mapa_id_seq'::regclass);
ALTER TABLE ONLY configuracao_mapa
    ADD CONSTRAINT configuracao_mapa_pkey PRIMARY KEY (id);


CREATE TABLE contacto_mensagem (
    id integer NOT NULL,
    mapa_id integer,
    nome character varying(255),
    email character varying(255),
    mensagem text,
    user_id integer,
    data_mensagem timestamp without time zone,
    checked boolean DEFAULT false,
    closed boolean DEFAULT false,
    observacoes text,
    checked_date timestamp without time zone,
    closed_date timestamp without time zone,
    mensagem_uuid character varying
);
CREATE SEQUENCE contacto_mensagem_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE contacto_mensagem_id_seq OWNED BY contacto_mensagem.id;
ALTER TABLE ONLY contacto_mensagem ALTER COLUMN id SET DEFAULT nextval('contacto_mensagem_id_seq'::regclass);
ALTER TABLE ONLY contacto_mensagem
    ADD CONSTRAINT contacto_mensagem_pkey PRIMARY KEY (id);


CREATE TABLE document_directory (
    id integer NOT NULL,
    codigo character varying(255),
    path character varying(500),
    titulo character varying(255),
    descricao text,
    allow_upload boolean,
    upload_anonymous boolean,
    upload_overwrite boolean,
    upload_generate_filename boolean,
    allow_delete boolean,
    delete_anonymous boolean
);
CREATE SEQUENCE document_directory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE document_directory_id_seq OWNED BY document_directory.id;
ALTER TABLE ONLY document_directory ALTER COLUMN id SET DEFAULT nextval('document_directory_id_seq'::regclass);
ALTER TABLE ONLY document_directory
    ADD CONSTRAINT document_directory_pkey PRIMARY KEY (id);
ALTER TABLE ONLY document_directory
    ADD CONSTRAINT document_directory_codigo_key UNIQUE (codigo);


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


CREATE TABLE emissao_planta (
    id integer NOT NULL,
    planta_nome character varying(255),
    tipo_nome character varying(255),
    planta_id integer,
    escala integer,
    titulo character varying(500),
    nif_requerente character varying(10),
    nome_requerente character varying(255),
    data_emissao timestamp without time zone,
    geom public.geometry(Geometry,3763),
    grupo_emissao character varying(36),
    id_user_ins integer,
    data_ins date,
    numero integer,
    ano integer,
    tipo_id integer,
    mapa_id integer
);
CREATE SEQUENCE emissao_planta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE emissao_planta_id_seq OWNED BY emissao_planta.id;
ALTER TABLE ONLY emissao_planta ALTER COLUMN id SET DEFAULT nextval('emissao_planta_id_seq'::regclass);
ALTER TABLE ONLY emissao_planta
    ADD CONSTRAINT emissao_planta_pkey PRIMARY KEY (id);


CREATE TABLE emissao_planta_number (
    num_emissao integer,
    ano_emissao integer
);
ALTER TABLE ONLY emissao_planta_number
    ADD CONSTRAINT emissao_planta_number_num_emissao_ano_emissao_key UNIQUE (num_emissao, ano_emissao);


CREATE TABLE geo_t_categorias (
    id integer NOT NULL,
    code character varying(50),
    name character varying(50),
    notes character varying(255),
    n1 double precision,
    n2 double precision,
    t1 character varying(50),
    t2 character varying(50),
    read_only boolean DEFAULT false NOT NULL,
    active boolean DEFAULT true
);
CREATE SEQUENCE geo_t_categorias_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE geo_t_categorias_id_seq OWNED BY geo_t_categorias.id;
ALTER TABLE ONLY geo_t_categorias ALTER COLUMN id SET DEFAULT nextval('geo_t_categorias_id_seq'::regclass);
ALTER TABLE ONLY geo_t_categorias
    ADD CONSTRAINT geo_t_categorias_pkey PRIMARY KEY (id);
ALTER TABLE ONLY geo_t_categorias
    ADD CONSTRAINT geo_t_categorias_nome_key UNIQUE (name);
ALTER TABLE ONLY geo_t_categorias
    ADD CONSTRAINT geo_t_categorias_cod_key UNIQUE (code);


CREATE TABLE geo_t_snig_tipo_recursos (
    id integer NOT NULL,
    code character varying(50),
    name character varying(50),
    notes character varying(255),
    n1 double precision,
    n2 double precision,
    t1 character varying(50),
    t2 character varying(50),
    read_only boolean DEFAULT false NOT NULL,
    active boolean DEFAULT true
);
CREATE SEQUENCE geo_t_snig_tipo_recursos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE geo_t_snig_tipo_recursos_id_seq OWNED BY geo_t_snig_tipo_recursos.id;
ALTER TABLE ONLY geo_t_snig_tipo_recursos ALTER COLUMN id SET DEFAULT nextval('geo_t_snig_tipo_recursos_id_seq'::regclass);
ALTER TABLE ONLY geo_t_snig_tipo_recursos
    ADD CONSTRAINT geo_t_snig_tipo_recursos_pkey PRIMARY KEY (id);
ALTER TABLE ONLY geo_t_snig_tipo_recursos
    ADD CONSTRAINT geo_t_snig_tipo_recursos_cod_key UNIQUE (code);
ALTER TABLE ONLY geo_t_snig_tipo_recursos
    ADD CONSTRAINT geo_t_snig_tipo_recursos_nome_key UNIQUE (name);


CREATE TABLE geo_t_temas_inspire (
    id integer NOT NULL,
    code character varying(50),
    name character varying(255),
    notes character varying(255),
    n1 double precision,
    n2 double precision,
    t1 character varying(255),
    t2 character varying(255),
    read_only boolean DEFAULT false NOT NULL,
    active boolean DEFAULT true
);
CREATE SEQUENCE geo_t_temas_inspire_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE geo_t_temas_inspire_id_seq OWNED BY geo_t_temas_inspire.id;
ALTER TABLE ONLY geo_t_temas_inspire ALTER COLUMN id SET DEFAULT nextval('geo_t_temas_inspire_id_seq'::regclass);
ALTER TABLE ONLY geo_t_temas_inspire
    ADD CONSTRAINT geo_t_temas_inspire_pkey PRIMARY KEY (id);
ALTER TABLE ONLY geo_t_temas_inspire
    ADD CONSTRAINT geo_t_temas_inspire_cod_key UNIQUE (code);
ALTER TABLE ONLY geo_t_temas_inspire
    ADD CONSTRAINT geo_t_temas_inspire_nome_key UNIQUE (name);

CREATE TABLE geo_t_tipo_recursos (
    id integer NOT NULL,
    code character varying(50),
    name character varying(50),
    notes character varying(255),
    n1 double precision,
    n2 double precision,
    t1 character varying(50),
    t2 character varying(50),
    read_only boolean DEFAULT false NOT NULL,
    active boolean DEFAULT true
);
CREATE SEQUENCE geo_t_tipo_recursos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE geo_t_tipo_recursos_id_seq OWNED BY geo_t_tipo_recursos.id;
ALTER TABLE ONLY geo_t_tipo_recursos ALTER COLUMN id SET DEFAULT nextval('geo_t_tipo_recursos_id_seq'::regclass);
ALTER TABLE ONLY geo_t_tipo_recursos
    ADD CONSTRAINT geo_t_tipo_recursos_pkey PRIMARY KEY (id);
ALTER TABLE ONLY geo_t_tipo_recursos
    ADD CONSTRAINT geo_t_tipo_recursos_cod_key UNIQUE (code);
ALTER TABLE ONLY geo_t_tipo_recursos
    ADD CONSTRAINT geo_t_tipo_recursos_nome_key UNIQUE (name);


CREATE TABLE geo_t_tipo_servicos (
    id integer NOT NULL,
    code character varying(50),
    name character varying(50),
    notes character varying(255),
    n1 double precision,
    n2 double precision,
    t1 character varying(50),
    t2 character varying(50),
    read_only boolean DEFAULT false NOT NULL,
    active boolean DEFAULT true
);
CREATE SEQUENCE geo_t_tipo_servicos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE geo_t_tipo_servicos_id_seq OWNED BY geo_t_tipo_servicos.id;
ALTER TABLE ONLY geo_t_tipo_servicos ALTER COLUMN id SET DEFAULT nextval('geo_t_tipo_servicos_id_seq'::regclass);
ALTER TABLE ONLY geo_t_tipo_servicos
    ADD CONSTRAINT geo_t_tipo_servicos_pkey PRIMARY KEY (id);
ALTER TABLE ONLY geo_t_tipo_servicos
    ADD CONSTRAINT geo_t_tipo_servicos_cod_key UNIQUE (code);
ALTER TABLE ONLY geo_t_tipo_servicos
    ADD CONSTRAINT geo_t_tipo_servicos_nome_key UNIQUE (name);


CREATE TABLE local_rv_to_osm_types (
    highway text NOT NULL,
    local_name text
);
ALTER TABLE ONLY local_rv_to_osm_types
    ADD CONSTRAINT local_rv_to_osm_types_pkey PRIMARY KEY (highway);


CREATE TABLE log_history (
    id integer NOT NULL,
    tstamp timestamp without time zone DEFAULT now(),
    schemaname text,
    tabname text,
    operation text,
    who text DEFAULT "current_user"(),
    new_val json,
    old_val json
);
CREATE SEQUENCE log_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE log_history_id_seq OWNED BY log_history.id;
ALTER TABLE ONLY log_history ALTER COLUMN id SET DEFAULT nextval('log_history_id_seq'::regclass);


CREATE TABLE logs (
    id integer NOT NULL,
    logger character varying,
    level character varying,
    trace character varying,
    msg text,
    created_at date
);
CREATE SEQUENCE logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE logs_id_seq OWNED BY logs.id;
ALTER TABLE ONLY logs ALTER COLUMN id SET DEFAULT nextval('logs_id_seq'::regclass);
ALTER TABLE ONLY logs
    ADD CONSTRAINT logs_pkey PRIMARY KEY (id);


CREATE TABLE mapa (
    id integer NOT NULL,
    codigo character varying(255),
    titulo character varying(255),
    descricao text,
    configuracao_id integer,
    portal boolean,
    activo boolean,
    show_help boolean,
    show_credits boolean,
    show_contact boolean,
    help_html text,
    credits_html text,
    configuracao_mapa text,
    template character varying(255),
    show_widget character varying(255),
    header_html text,
    post_script text,
    show_homepage integer,
    img_homepage text,
    roles text,
    send_email_notifications_admin boolean,
    email_notifications_admin character varying
);
CREATE SEQUENCE mapa_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE mapa_id_seq OWNED BY mapa.id;
ALTER TABLE ONLY mapa ALTER COLUMN id SET DEFAULT nextval('mapa_id_seq'::regclass);
ALTER TABLE ONLY mapa
    ADD CONSTRAINT mapa_pkey PRIMARY KEY (id);
ALTER TABLE ONLY mapa
    ADD CONSTRAINT mapa_codigo_key UNIQUE (codigo);


CREATE TABLE mapas_catalogos (
    mapa_id integer NOT NULL,
    catalogo_id integer NOT NULL
);
ALTER TABLE ONLY mapas_catalogos
    ADD CONSTRAINT mapas_catalogos_pkey PRIMARY KEY (mapa_id, catalogo_id);


CREATE TABLE mapas_modulos (
    mapa_id integer NOT NULL,
    modulo_id integer NOT NULL
);
ALTER TABLE ONLY mapas_modulos
    ADD CONSTRAINT mapas_modulos_pkey PRIMARY KEY (mapa_id, modulo_id);


CREATE TABLE mapas_plantas (
    mapa_id integer NOT NULL,
    planta_id integer NOT NULL,
    ordem integer
);
ALTER TABLE ONLY mapas_plantas
    ADD CONSTRAINT mapas_plantas_pkey PRIMARY KEY (mapa_id, planta_id);

CREATE TABLE mapas_roles (
    mapa_id integer NOT NULL,
    role_id integer NOT NULL
);
ALTER TABLE ONLY mapas_roles
    ADD CONSTRAINT mapas_roles_pkey PRIMARY KEY (mapa_id, role_id);


CREATE TABLE mapas_tipos_plantas (
    mapa_id integer NOT NULL,
    tipo_planta_id integer NOT NULL,
    ordem integer
);
ALTER TABLE ONLY mapas_tipos_plantas
    ADD CONSTRAINT mapas_tipos_plantas_pkey PRIMARY KEY (mapa_id, tipo_planta_id);


CREATE TABLE mapas_widgets (
    widget_id integer NOT NULL,
    mapa_id integer NOT NULL,
    "order" integer,
    config text,
    html_content text,
    roles text,
    target character varying(255)
);
ALTER TABLE ONLY mapas_widgets
    ADD CONSTRAINT mapas_widgets_pkey PRIMARY KEY (widget_id, mapa_id);


CREATE TABLE modulo (
    id integer NOT NULL,
    codigo character varying(255),
    titulo character varying(255),
    id_user_ins integer,
    data_ins date
);
CREATE SEQUENCE modulo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE modulo_id_seq OWNED BY modulo.id;
ALTER TABLE ONLY modulo ALTER COLUMN id SET DEFAULT nextval('modulo_id_seq'::regclass);
ALTER TABLE ONLY modulo
    ADD CONSTRAINT modulo_pkey PRIMARY KEY (id);
ALTER TABLE ONLY modulo
    ADD CONSTRAINT modulo_codigo_key UNIQUE (codigo);


CREATE TABLE planta (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nome character varying(255) NOT NULL,
    titulo character varying(500),
    descricao character varying(1024),
    escala integer,
    template character varying(255),
    configuracao text,
    identificacao boolean DEFAULT false,
    marcacao_local boolean DEFAULT false,
    desenhar_local boolean DEFAULT false,
    multi_geom boolean DEFAULT false,
    emissao_livre boolean DEFAULT false,
    activo boolean,
    id_user_ins integer,
    data_ins date,
    orientacao character varying(50),
    formato character varying(50),
    titulo_emissao boolean DEFAULT false,
    srid integer,
    geom public.geometry(Geometry,3763),
    autor_emissao boolean DEFAULT false,
    guia_pagamento boolean DEFAULT false,
    finalidade_emissao boolean DEFAULT false,
    escala_livre boolean DEFAULT false,
    escalas_restritas boolean,
    escalas_restritas_lista character varying(1024),
    escala_mapa boolean DEFAULT false,
    identificacao_campos json
);
CREATE SEQUENCE planta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE planta_id_seq OWNED BY planta.id;
ALTER TABLE ONLY planta ALTER COLUMN id SET DEFAULT nextval('planta_id_seq'::regclass);
ALTER TABLE ONLY planta
    ADD CONSTRAINT planta_pkey PRIMARY KEY (id);
ALTER TABLE ONLY planta
    ADD CONSTRAINT planta_codigo_key UNIQUE (codigo);


CREATE TABLE planta_layouts (
    id integer NOT NULL,
    planta_id integer,
    formato character varying(25),
    orientacao character varying(25),
    configuracao text
);
CREATE SEQUENCE planta_layouts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE planta_layouts_id_seq OWNED BY planta_layouts.id;
ALTER TABLE ONLY planta_layouts ALTER COLUMN id SET DEFAULT nextval('planta_layouts_id_seq'::regclass);
ALTER TABLE ONLY planta_layouts
    ADD CONSTRAINT planta_layouts_pkey PRIMARY KEY (id);


CREATE TABLE plantas_roles (
    planta_id integer NOT NULL,
    role_id integer NOT NULL
);
ALTER TABLE ONLY plantas_roles
    ADD CONSTRAINT plantas_roles_pkey PRIMARY KEY (planta_id, role_id);


CREATE TABLE plantas_tipos_plantas (
    tipo_planta_id integer NOT NULL,
    planta_id integer NOT NULL,
    ordem integer
);
ALTER TABLE ONLY plantas_tipos_plantas
    ADD CONSTRAINT plantas_tipos_plantas_pkey PRIMARY KEY (tipo_planta_id, planta_id);


CREATE TABLE record_status_value (
    id integer NOT NULL,
    code character varying(50),
    name character varying(255),
    notes character varying,
    read_only boolean,
    active boolean DEFAULT true
);
CREATE SEQUENCE record_status_value_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE record_status_value_id_seq OWNED BY record_status_value.id;
ALTER TABLE ONLY record_status_value ALTER COLUMN id SET DEFAULT nextval('record_status_value_id_seq'::regclass);
ALTER TABLE ONLY record_status_value
    ADD CONSTRAINT record_status_value_pkey PRIMARY KEY (id);
ALTER TABLE ONLY record_status_value
    ADD CONSTRAINT record_status_value_code_key UNIQUE (code);


CREATE TABLE role (
    id integer NOT NULL,
    name character varying(80),
    description character varying(255),
    read_only boolean DEFAULT false
);
CREATE SEQUENCE role_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE role_id_seq OWNED BY role.id;
ALTER TABLE ONLY role ALTER COLUMN id SET DEFAULT nextval('role_id_seq'::regclass);
ALTER TABLE ONLY role
    ADD CONSTRAINT role_pkey PRIMARY KEY (id);
ALTER TABLE ONLY role
    ADD CONSTRAINT role_name_key UNIQUE (name);


CREATE TABLE roles_users (
    user_id integer,
    role_id integer
);


CREATE TABLE sistema_coordenadas (
    id integer NOT NULL,
    srid integer,
    codigo character varying(50),
    nome character varying(255),
    proj4text character varying(500),
    unidades text,
    descricao character varying(1024),
    ordem integer,
    portal boolean DEFAULT false,
    activo boolean DEFAULT false,
    data_ins timestamp without time zone,
    id_user_ins integer,
    flg_ro boolean DEFAULT false NOT NULL
);
CREATE SEQUENCE sistema_coordenadas_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE sistema_coordenadas_id_seq OWNED BY sistema_coordenadas.id;
ALTER TABLE ONLY sistema_coordenadas ALTER COLUMN id SET DEFAULT nextval('sistema_coordenadas_id_seq'::regclass);
ALTER TABLE ONLY sistema_coordenadas
    ADD CONSTRAINT sistema_coordenadas_pkey PRIMARY KEY (id);
ALTER TABLE ONLY sistema_coordenadas
    ADD CONSTRAINT sistema_coordenadas_codigo_key UNIQUE (codigo);


CREATE TABLE site_settings (
    id integer NOT NULL,
    code character varying(50),
    name character varying(255),
    notes character varying,
    setting_value text,
    read_only boolean,
    active boolean DEFAULT true
);
CREATE SEQUENCE site_settings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE site_settings_id_seq OWNED BY site_settings.id;
ALTER TABLE ONLY site_settings ALTER COLUMN id SET DEFAULT nextval('site_settings_id_seq'::regclass);
ALTER TABLE ONLY site_settings
    ADD CONSTRAINT site_settings_pkey PRIMARY KEY (id);
ALTER TABLE ONLY site_settings
    ADD CONSTRAINT site_settings_code_key UNIQUE (code);


CREATE TABLE sub_planta (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nome character varying(255) NOT NULL,
    configuracao text
);
CREATE SEQUENCE sub_planta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE sub_planta_id_seq OWNED BY sub_planta.id;
ALTER TABLE ONLY sub_planta ALTER COLUMN id SET DEFAULT nextval('sub_planta_id_seq'::regclass);
ALTER TABLE ONLY sub_planta
    ADD CONSTRAINT sub_planta_pkey PRIMARY KEY (id);
ALTER TABLE ONLY sub_planta
    ADD CONSTRAINT sub_planta_codigo_key UNIQUE (codigo);


CREATE TABLE tipo_planta (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    titulo character varying(500),
    descricao character varying(1024),
    template_flask character varying(500),
    activo boolean,
    id_user_ins integer,
    data_ins date,
    identificacao_requerente boolean DEFAULT false,
    marcacao_local boolean DEFAULT false,
    multi_geom boolean DEFAULT false,
    parent_id integer,
    geom public.geometry(Geometry,3763),
    tolerancia integer,
    show_all boolean DEFAULT false,
    seleccao_plantas boolean DEFAULT true,
    agrupar_plantas boolean DEFAULT false,
    autor_emissao boolean DEFAULT false,
    guia_pagamento boolean DEFAULT false,
    finalidade_emissao boolean DEFAULT false,
    escala_livre boolean DEFAULT false,
    escalas_restritas boolean DEFAULT false,
    escalas_restritas_lista character varying(1024) DEFAULT '1000,2000,5000,10000,20000,25000,50000'::character varying,
    escala_mapa boolean DEFAULT false,
    identificacao_campos json
);
CREATE SEQUENCE tipo_planta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE tipo_planta_id_seq OWNED BY tipo_planta.id;
ALTER TABLE ONLY tipo_planta ALTER COLUMN id SET DEFAULT nextval('tipo_planta_id_seq'::regclass);
ALTER TABLE ONLY tipo_planta
    ADD CONSTRAINT tipo_planta_pkey PRIMARY KEY (id);
ALTER TABLE ONLY tipo_planta
    ADD CONSTRAINT tipo_planta_codigo_key UNIQUE (codigo);


CREATE TABLE tipos_plantas_childs (
    tipo_planta_id integer NOT NULL,
    tipo_planta_child_id integer NOT NULL,
    ordem integer
);
ALTER TABLE ONLY tipos_plantas_childs
    ADD CONSTRAINT tipos_plantas_childs_pkey PRIMARY KEY (tipo_planta_id, tipo_planta_child_id);


CREATE TABLE "user" (
    id integer NOT NULL,
    email character varying(255),
    password character varying(255),
    active boolean,
    confirmed_at timestamp without time zone,
    username character varying(255),
    first_name character varying(255),
    last_name character varying(255),
    name character varying(255),
    last_login_at timestamp without time zone,
    current_login_at timestamp without time zone,
    last_login_ip character varying(255),
    current_login_ip character varying(255),
    login_count integer,
    default_map character varying(255)
);
CREATE SEQUENCE user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE user_id_seq OWNED BY "user".id;
ALTER TABLE ONLY "user" ALTER COLUMN id SET DEFAULT nextval('user_id_seq'::regclass);
ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);
ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_email_key UNIQUE (email);
ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


CREATE TABLE widget (
    id integer NOT NULL,
    codigo character varying(50),
    plugin character varying(255),
    titulo character varying(500),
    descricao text,
    scripts text,
    activo boolean,
    id_user_ins integer,
    data_ins date,
    config text,
    parent_id integer,
    action character varying(255),
    template text,
    target character varying(255),
    icon_css_class character varying(255),
    html_content text,
    roles text
);
CREATE SEQUENCE widget_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE widget_id_seq OWNED BY widget.id;
ALTER TABLE ONLY widget ALTER COLUMN id SET DEFAULT nextval('widget_id_seq'::regclass);
ALTER TABLE ONLY widget
    ADD CONSTRAINT widget_pkey PRIMARY KEY (id);
ALTER TABLE ONLY widget
    ADD CONSTRAINT widget_codigo_key UNIQUE (codigo);


---
--- INDEX
---

CREATE INDEX fki_document_directory_id_fk
  ON document_directory_rules
  USING btree
  (doc_dir_id);

CREATE INDEX fki_mapa_id_fk
  ON document_directory_rules
  USING btree
  (mapa_id);


---
--- SPATIAL INDEX
---

SET search_path = cartabase, pg_catalog;

CREATE INDEX topo_wkb_geometry_geom_idx ON topo USING gist (wkb_geometry);


SET search_path = cartografia, pg_catalog;

CREATE INDEX freguesia_geom_idx ON freguesia USING gist (geom);


SET search_path = planeamento, pg_catalog;

CREATE INDEX idx_plano_wkb_geometry ON plano USING gist (wkb_geometry);


SET search_path = portal, pg_catalog;

CREATE INDEX idx_emissao_planta_geom ON emissao_planta USING gist (geom);


---
--- RELATIONSHIPS CONSTRAINTS
---

SET search_path = planeamento, pg_catalog;

ALTER TABLE ONLY dinamica_plano
    ADD CONSTRAINT dinamica_plano_estado_plano_id_fkey FOREIGN KEY (estado_plano_id) REFERENCES estado_plano(id);

ALTER TABLE ONLY dinamica_plano
    ADD CONSTRAINT dinamica_plano_plano_id_fkey FOREIGN KEY (plano_id) REFERENCES plano(id);

ALTER TABLE ONLY dinamica_plano
    ADD CONSTRAINT dinamica_plano_tipo_alteracao_plano_id_fkey FOREIGN KEY (tipo_alteracao_plano_id) REFERENCES tipo_alteracao_plano(id);

ALTER TABLE ONLY documento_plano
    ADD CONSTRAINT documento_plano_dinamica_plano_id_fkey FOREIGN KEY (dinamica_plano_id) REFERENCES dinamica_plano(id);

ALTER TABLE ONLY documento_plano
    ADD CONSTRAINT documento_plano_plano_id_fkey FOREIGN KEY (plano_id) REFERENCES plano(id);

ALTER TABLE ONLY ficheiro_documento_plano
    ADD CONSTRAINT ficheiro_documento_plano_documento_plano_id_fkey FOREIGN KEY (documento_plano_id) REFERENCES documento_plano(id);

ALTER TABLE ONLY plano
    ADD CONSTRAINT plano_estado_plano_id_fkey FOREIGN KEY (estado_plano_id) REFERENCES estado_plano(id);

ALTER TABLE ONLY plano
    ADD CONSTRAINT plano_tipo_plano_id_fkey FOREIGN KEY (tipo_plano_id) REFERENCES tipo_plano(id);



SET search_path = portal, pg_catalog;

ALTER TABLE ONLY audit_log
    ADD CONSTRAINT audit_log_operacao_id_fkey FOREIGN KEY (operacao_id) REFERENCES audit_operacao(id);

ALTER TABLE ONLY emissao_planta
    ADD CONSTRAINT emissao_planta_planta_id_fkey FOREIGN KEY (planta_id) REFERENCES planta(id);

ALTER TABLE ONLY mapa
    ADD CONSTRAINT mapa_configuracao_id_fkey FOREIGN KEY (configuracao_id) REFERENCES configuracao_mapa(id);

ALTER TABLE ONLY mapas_catalogos
    ADD CONSTRAINT mapas_catalogos_catalogo_id_fkey FOREIGN KEY (catalogo_id) REFERENCES catalogo_metadados(id);

ALTER TABLE ONLY mapas_catalogos
    ADD CONSTRAINT mapas_catalogos_mapa_id_fkey FOREIGN KEY (mapa_id) REFERENCES mapa(id);

ALTER TABLE ONLY mapas_modulos
    ADD CONSTRAINT mapas_modulos_mapa_id_fkey FOREIGN KEY (mapa_id) REFERENCES mapa(id);

ALTER TABLE ONLY mapas_modulos
    ADD CONSTRAINT mapas_modulos_modulo_id_fkey FOREIGN KEY (modulo_id) REFERENCES modulo(id);

ALTER TABLE ONLY mapas_plantas
    ADD CONSTRAINT mapas_plantas_mapa_id_fkey FOREIGN KEY (mapa_id) REFERENCES mapa(id);

ALTER TABLE ONLY mapas_plantas
    ADD CONSTRAINT mapas_plantas_planta_id_fkey FOREIGN KEY (planta_id) REFERENCES planta(id);

ALTER TABLE ONLY mapas_roles
    ADD CONSTRAINT mapas_roles_mapa_id_fkey FOREIGN KEY (mapa_id) REFERENCES mapa(id);

ALTER TABLE ONLY mapas_roles
    ADD CONSTRAINT mapas_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES role(id);

ALTER TABLE ONLY tipos_plantas_childs
    ADD CONSTRAINT mapas_tipos_plantas_childs_child_id_fkey FOREIGN KEY (tipo_planta_child_id) REFERENCES tipo_planta(id);

ALTER TABLE ONLY mapas_tipos_plantas
    ADD CONSTRAINT mapas_tipos_plantas_mapa_id_fkey FOREIGN KEY (mapa_id) REFERENCES mapa(id);

ALTER TABLE ONLY mapas_tipos_plantas
    ADD CONSTRAINT mapas_tipos_plantas_tipo_planta_id_fkey FOREIGN KEY (tipo_planta_id) REFERENCES tipo_planta(id);

ALTER TABLE ONLY mapas_widgets
    ADD CONSTRAINT mapas_widgets_mapa_id_fkey FOREIGN KEY (mapa_id) REFERENCES mapa(id);

ALTER TABLE ONLY mapas_widgets
    ADD CONSTRAINT mapas_widgets_widget_id_fkey FOREIGN KEY (widget_id) REFERENCES widget(id);

ALTER TABLE portal.planta_layouts
  ADD CONSTRAINT planta_layouts_planta_id_fkey FOREIGN KEY (planta_id)
      REFERENCES planta (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE CASCADE;


ALTER TABLE ONLY plantas_roles
    ADD CONSTRAINT plantas_roles_planta_id_fkey FOREIGN KEY (planta_id) REFERENCES planta(id);

ALTER TABLE ONLY plantas_roles
    ADD CONSTRAINT plantas_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES role(id);

ALTER TABLE ONLY plantas_tipos_plantas
    ADD CONSTRAINT plantas_tipos_plantas_planta_id_fkey FOREIGN KEY (planta_id) REFERENCES planta(id);

ALTER TABLE ONLY plantas_tipos_plantas
    ADD CONSTRAINT plantas_tipos_plantas_plantas_tipo_planta_id_fkey FOREIGN KEY (tipo_planta_id) REFERENCES tipo_planta(id);

ALTER TABLE ONLY roles_users
    ADD CONSTRAINT roles_users_role_id_fkey FOREIGN KEY (role_id) REFERENCES role(id);

ALTER TABLE ONLY roles_users
    ADD CONSTRAINT roles_users_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);

ALTER TABLE ONLY tipos_plantas_childs
    ADD CONSTRAINT tipos_plantas_childs_id_fkey FOREIGN KEY (tipo_planta_id) REFERENCES tipo_planta(id);

ALTER TABLE ONLY document_directory_rules
    ADD CONSTRAINT document_directory_id_fkey FOREIGN KEY (doc_dir_id) REFERENCES document_directory(id);

ALTER TABLE ONLY document_directory_rules
    ADD CONSTRAINT document_directory_mapa_id_fkey FOREIGN KEY (mapa_id) REFERENCES mapa(id);




