-------------------- ---------------------------------------------   Load data   -------------------- ---------------------------------------------

-------------------- ---------------------------------------------   setup
Set search_path to toponimia,toponymy, cartografia, public, pg_catalog;
---------------------------------------------------------------------

-- delete data:
delete from lugar;
delete from localizador_endereco;
delete from endereco;
delete from via;
delete from toponimo;
delete from via_x_via_troco;
delete from via_troco;
delete from descritor_postal;
delete from descritor_postal_ctt;


-- restart sequences:
Alter Sequence toponimo_id_seq Restart with 1;
Alter Sequence lugar_id_seq Restart with 1;
Alter Sequence via_id_seq Restart with 1;
Alter Sequence via_troco_id_seq Restart with 1;
Alter Sequence descritor_postal_id_seq Restart with 1;
Alter Sequence localizador_endereco_id_seq Restart with 1;
Alter Sequence endereco_id_seq Restart with 1;
Alter Sequence descritor_postal_ctt_id_seq Restart with 1;

--------------------------------------------------------------------------------------------------------------------- descritor_postal
Insert into descritor_postal select id,cp4,cp3,cp_alf from postal_code;
Insert into descritor_postal_ctt select * from postal_code_ctt;

--------------------------------------------------------------------------------------------------------------------- lugares + toponimo
--select * from toponymy.place limit 5;
-- select * from toponimo_estado

-- load place name in toponimo
Alter Sequence toponimo_id_seq Restart with 1;
Insert into toponimo (nome, estado_id, origem, origem_id)
select name,1,'toponymy.place',id from toponymy.place;


--select * from toponimo
-----------------------------------------------------------
-- load place
-- select * from lugar_estado

--Insert into lugar (estado_id, toponimo_id, origem, origem_id,geom)
--select 1,topo.id,'toponymy.place',place.id, (st_dump(geom)).geom from toponymy.place place join toponimo topo on (place.id = topo.origem_id);

-- project, get only points
Insert into lugar (tipo_id, estado_id, toponimo_id, origem, origem_id, dicofre, geom)
select 8,1,topo.id,'toponymy.place',place.id, dicofre, st_centroid(st_transform(geom,3763))::geometry(Point,3763)
from toponymy.place place join toponimo topo on (place.id = topo.origem_id);
--Where st_geometrytype(geom) = 'ST_MultiPoint';


--select l.id l_id,t.id as t_id, nome from lugar l join toponimo t on (l.toponimo_id = t.id)


--------------------------------------------------------------------------------------------------------------------- via + toponimo

-- select * from toponymy.road_name limit 10
-- select * from via_tipos
-- select distinct road_type from road_name
-- select * from via_estados

---------------- insert  nomes das vias  into toponimo
Insert into toponimo (nome, estado_id, origem, origem_id)
select road_name,1,'toponymy.road_name.rvv', rvv_cod from toponymy.road_name;


---------------- insert via
Insert into via (estado_id, tipo, primeira_preposicao, titulo, segunda_preposicao, identificador_ctt, origem, origem_id, toponimo_id)
select null, road_type, first_preposition, title, second_preposition, ctt_art_cod, 'topony.road_name.id',r.id, topo.id
from road_name r join  toponimo topo on (rvv_cod = topo.origem_id) order by r.id;


---------------- insert troços
--select * from road_centerline limit 10
--select * from road_centerline cl join road_name rn on (cl.road_name_id = rn.id) limit 10

insert into via_troco (origem_id, origem, geom )
select id, 'road_centerline.id', st_transform(geom,3763) from road_centerline order by id;

---------------- insert relation via - via-troco
Insert into via_x_via_troco (via_id, via_troco_id)
Select rn.id,rc.id
from road_name rn join road_centerline rc on (rn.id = rc.road_name_id) where rc.road_name_id is not null
order by rc.id asc;

---------------- via_x_freguesia
--select * from road_name_x_freguesia limit 10

Insert into via_x_freguesia
Select rn.id,f.dicofre
from road_name rn join road_name_x_freguesia f on (rn.id = f.road_name_id)
order by rn.id asc;




--------------------------------------------------------------------------------------------------------------------- endereco
--select * from road_locator where road_name_id is null limit 10
--select * from via limit 10
-- select * from

--select * from postal_code where id = 202

-- endereco
Insert into endereco (dicofre, descritor_postal_cp3,descritor_postal_cp4, descritor_postal_cpalf , via_id, origem, origem_id, geom)
select dicofre, cp3,cp4,cp_alf, road_name_id, 'road_locator', id , st_centroid(st_transform(geom, 3763))
from road_locator;

-- localizador_endreco (ie números)
Insert into localizador_endereco (endereco_id, designador_localizador,designador_ordem)
select  e.id ,locator, 1
from road_locator rl join endereco e on (rl.id = e.origem_id);

---------------------------------------------------------------------------------------------------- teste sub endereços
-- select * from endereco e join localizador_endereco le on (e.id = le.endereco_id) where via_id = 1

-- insert 2 fraccções via = 1 , endereco = 9638
with ii as (
insert into endereco (dicofre, endereco_principal_id, via_id, origem, origem_id, geom)
values ('081103',9638, 1, -1,-1, ST_GeomFromEWKT('SRID=3763;POINT(-38286 -280102)'::geometry(point,3763)))
returning id as inserted_id)
Insert into localizador_endereco (endereco_id, designador_localizador,designador_ordem) select inserted_id,'frac 1',1 from ii;


with ii as (
insert into endereco (dicofre, endereco_principal_id, via_id, origem, origem_id, geom)
values ('081103',9638, 1, -1,-1, ST_GeomFromEWKT('SRID=3763;POINT(-38286 -280100)'::geometry(point,3763)))
returning id as inserted_id)
Insert into localizador_endereco (endereco_id, designador_localizador,designador_ordem) select inserted_id,'frac 2',1 from ii;

--insert second localizador to "endereco_id": 14974,"designador_localizador": "Lt 99",
insert into localizador_endereco(endereco_id, designador_localizador,designador_ordem) values(14974,'outra designação',2);

