import os
import json
from datetime import datetime

from sqlalchemy.sql import text

from app.models.common import *
from app.models.security import *
from app.models.mapas import *
from app.models.auditoria import *
from app.models.logging import *
from app.models.files import *

from app.models.domain.portal import *

from flask_security.utils import hash_password


def setup(sample_data=False):
    create_schema(False)

    filepath = os.path.join(os.path.dirname(__file__),'sql', 'load_data.sql')

    file = open(filepath)
    sql = text(file.read())

    db.session.execute(sql)

    if sample_data:
        load_sample_data(False)

    db.session.commit()


def load_sample_data(commit=True):
    #Insert user
    user = User()
    user.username = 'user'
    user.email = 'user@isp.com'
    user.password = hash_password('user')
    user.active = True
    user.confirmed_at = datetime.now()
    db.session.add(user)

    viewer_config = """{
      "checked": ["overlays", "basemaps", "osm1", "main"],
      "center": [-878528, 4465088],
      "extent": [-907574.070748367, 4446571.129897916, -849481.929251633, 4483604.870102084],
      "layers": [
      {
        "active": false,
        "bbox": "-10.1905 36.7643 -5.71298 42.1896",
        "crs": 4326,
        "description": "",
        "id": "2",
        "layers": "AU.AdministrativeBoundary",
        "opacity": 1,
        "open": false,
        "servertype": "geoserver",
        "format": "image/png",
        "crs": "EPSG:3857",
        "tiled": true,
        "title": "Portugal (CAOP)",
        "type": "WMS",
        "url": "http://mapas.dgterritorio.pt/wms-inspire/caop/continente?",
        "version": "1.3.0"
      },
      {
        "active": false,
        "bbox": "-180 -89.99892578124998 180.00000000000003 83.59960937500006",
        "crs": 4326,
        "description": "",
        "id": "3",
        "layers": "opengeo:countries",
        "opacity": 1,
        "open": false,
        "servertype": "mapserver",
        "style_color": "34,141,144,1",
        "tiled": true,
        "title": "Países",
        "type": "WFS",
        "url": "https://ahocevar.com/geoserver/wfs?",
        "version": "2.0.0"
      },
      {
        "active": false,
        "bbox": "-180 -89.99892578124998 180.00000000000003 83.59960937500006",
        "crs": 4326,
        "description": "O Lorem Ipsum é um texto modelo da indústria tipográfica e de impressão. O Lorem Ipsum tem vindo a ser o texto padrão usado por estas indústrias desde o ano de 1500, quando uma misturou os caracteres de um texto para criar um espécime de livro. Este texto não só sobreviveu 5 séculos, mas também o salto para a tipografia electrónica, mantendo-se essencialmente inalterada. Foi popularizada nos anos 60 com a disponibilização das folhas de Letraset, que continham passagens com Lorem Ipsum, e mais recentemente com os programas de publicação como o Aldus PageMaker que incluem versões do Lorem Ipsum.",
        "id": "1",
        "opacity": 1,
        "open": true,
        "title": "Limites administrativos",
        "type": "GROUP",
        "legend_url": "https://via.placeholder.com/150x300",
        "children": ["2", "3"]
      },
      {
        "active": false,
        "bbox": "-10.1905 36.7643 -5.71298 42.1896",
        "crs": 4326,
        "description": "",
        "id": "41",
        "layers": "cp:mv_0812_publicar",
        "opacity": 0.5,
        "open": false,
        "servertype": "geoserver",
        "format": "image/png",
        "tiled": true,
        "title": "São Brás de Alportel",
        "type": "WMS",
        "url": "https://dgt.wkt.pt/geoserver/cp/wms?",
        "version": "1.3.0"
      },
      {
        "active": false,
        "bbox": "-180 -89.99892578124998 180.00000000000003 83.59960937500006",
        "crs": 4326,
        "id": "4",
        "opacity": 1,
        "open": false,
        "title": "Cadastro",
        "type": "GROUP",
        "children": ["41"]
      },
      {
        "active": false,
        "bbox": "-10.1905 36.7643 -5.71298 42.1896",
        "crs": 4326,
        "description": "",
        "id": "51",
        "layers": "COS2018v1.0",
        "opacity": 1,
        "open": false,
        "servertype": "geoserver",
        "format": "image/png",
        "tiled": true,
        "title": "COS 2018",
        "type": "WMS",
        "url": "http://mapas.dgterritorio.pt/wms-inspire/cos2018v1?",
        "version": "1.3.0"
      },
      {
        "active": false,
        "bbox": "-180 -89.99892578124998 180.00000000000003 83.59960937500006",
        "crs": 4326,
        "description": "O Lorem Ipsum é um texto modelo da indústria tipográfica e de impressão. O Lorem Ipsum tem vindo a ser o texto padrão usado por estas indústrias desde o ano de 1500, quando uma misturou os caracteres de um texto para criar um espécime de livro. Este texto não só sobreviveu 5 séculos, mas também o salto para a tipografia electrónica, mantendo-se essencialmente inalterada. Foi popularizada nos anos 60 com a disponibilização das folhas de Letraset, que continham passagens com Lorem Ipsum, e mais recentemente com os programas de publicação como o Aldus PageMaker que incluem versões do Lorem Ipsum.",
        "id": "5",
        "opacity": 1,
        "open": false,
        "title": "Ambiente e Ordenamento",
        "type": "GROUP",
        "legend_url": "https://via.placeholder.com/150x300",
        "children": ["51"]
      },
      {
        "id": "61",
        "title": "OSM",
        "type": "OSM",
        "active": false,
        "opacity": 1,
        "system": true,
        "open": false
      },
      {
        "id": "62",
        "title": "ArcGIS Terrain",
        "type": "XYZ",
        "active": false,
        "opacity": 1,
        "system": true,
        "open": false,
        "url": "http://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
      },
      {
        "id": "63",
        "title": "ArcGIS Aerial",
        "type": "XYZ",
        "active": false,
        "opacity": 1,
        "system": true,
        "open": false,
        "url": "http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
      },
      {
        "id": "64",
        "title": "BING",
        "type": "BING",
        "active": false,
        "opacity": 1,
        "system": true,
        "open": false
      },
      {
        "active": false,
        "bbox": "-180 -89.99892578124998 180.00000000000003 83.59960937500006",
        "crs": 4326,
        "id": "6",
        "opacity": 1,
        "open": false,
        "title": "Bases cartográficas",
        "type": "GROUP",
        "children": ["61", "62", "63", "64"]
      },
      {
        "type": "GROUP",
        "active": true,
        "id": "overlays",
        "title": "Overlays layers",
        "opacity": 1,
        "system": true,
        "open": true,
        "children": []
      },
      {
        "type": "GROUP",
        "active": true,
        "id": "main",
        "title": "Viewer main layers",
        "opacity": 1,
        "system": true,
        "open": true,
        "children": ["1", "4", "5", "6"]
      },
      {
        "id": "osm1",
        "title": "OSM",
        "type": "OSM",
        "active": true,
        "opacity": 1,
        "system": true,
        "open": true
      },
      {
        "type": "GROUP",
        "active": true,
        "id": "basemaps",
        "title": "Basemaps layers",
        "opacity": 1,
        "system": true,
        "open": true,
        "children": ["osm1"]
      }],
      "selected_menu": "toc",
      "components": [
      {
        "id": "2",
        "name": "layer_opacity",
        "type": "LayerOpacity",
        "title": "Opacidade",
        "config_json": { "name": "Opacidade" },
        "config_version": "1.0",
        "regions": [],
        "target": "layer_tools",
        "children": []
      },
      {
        "id": "toc",
        "name": "toc",
        "type": "TOC",
        "title": "Component1",
        "config_json": { "name": "Tabela de Conteúdos" },
        "config_version": "1.0",
        "target": "mainmenu",
        "regions": ["layer_tools"],
        "children": ["2"]
      }]
    }"""

    # Insert Viewer1
    viewer1 = Viewer()
    viewer1.name = 'viewer1'
    viewer1.title = 'Viewer 1'
    viewer1.slug = 'v2'
    viewer1.is_active = True
    viewer1.is_portal = True
    viewer1.config_json = viewer_config
    db.session.add(viewer1)

    # Insert Viewer2
    viewer2 = Viewer()
    viewer2.name = 'viewer2'
    viewer2.title = 'Viewer 2'
    viewer2.slug = 'silves/viewer'
    viewer2.is_active = True
    viewer2.config_json = viewer_config
    db.session.add(viewer2)

    # Add role to viewers
    role1 = Role.query.filter_by(name='Anonymous').first()
    viewer1.roles.append(role1)

    role2 = Role.query.filter_by(name='Authenticated').first()
    viewer2.roles.append(role2)
    user.roles.append(role2)

    # Insert Component
    component1 = Component()
    component1.name = 'toc'
    component1.type = 'TOC'
    component1.title = 'Tabela de Conteúdos'
    component1.config_json = json.dumps({'name': 'Component 1'})
    component1.config_version = '1.0'
    component1.target = 'mainmenu'
    db.session.add(component1)

    component2 =  Component()
    component2.name = 'component2'
    component2.type = 'COMPONENT2'
    component2.title = 'Component 2'
    component2.config_json = json.dumps({'name': 'Component 2'})
    component2.config_version = '1.0'
    component2.target = 'main'
    db.session.add(component2)

    # Add role to component
    role = Role.query.filter_by(name='Admin').first()
    component2.roles.append(role2)

    #Add components to viewer 1
    viewer_component = ViewerComponent()
    viewer_component.viewer = viewer1
    viewer_component.component = component1
    viewer_component.is_active = True
    viewer_component.order = 1
    db.session.add(viewer_component)

    viewer_component = ViewerComponent()
    viewer_component.viewer = viewer1
    viewer_component.component = component2
    viewer_component.config_json = json.dumps({ 'name': 'Override component 2' })
    viewer_component.is_active = True
    viewer_component.order = 2
    viewer_component.target = 'main_override'
    db.session.add(viewer_component)


    #Add components to viewer 2
    viewer_component = ViewerComponent()
    viewer_component.viewer = viewer2
    viewer_component.component = component1
    viewer_component.config_json = json.dumps({'name': 'Override component 1'})
    viewer_component.is_active = True
    db.session.add(viewer_component)

    viewer_component = ViewerComponent()
    viewer_component.viewer = viewer2
    viewer_component.component = component2
    viewer_component.is_active = True
    viewer_component.target = 'main_override'
    db.session.add(viewer_component)

    print1 = Planta()
    print1.codigo = '1k'
    print1.nome = 'Planta Topográfica à escala 1:1000'
    print1.titulo = 'Planta Topográfica à escala 1:1000'
    print1.escala = 1000
    print1.srid = 3763
    db.session.add(print1)

    layout = PlantaLayout()
    layout.formato = 'A4'
    layout.orientacao = 'Portrait'
    layout.planta = print1
    db.session.add(layout)

    layout = PlantaLayout()
    layout.formato = 'A4'
    layout.orientacao = 'Landscape'
    layout.planta = print1
    db.session.add(layout)

    print2 = Planta()
    print2.codigo = 'ortos'
    print2.nome = 'Ortofotos 2020'
    print2.titulo = 'Ortofotos 2020'
    print2.escala = 5000
    print2.srid = 3763
    db.session.add(print2)

    print3 = Planta()
    print3.codigo = 'pdm_ord'
    print3.nome = 'Carta de Ordenamento do PDM'
    print3.titulo = 'Carta de Ordenamento do PDM'
    print3.escala = 10000
    print3.srid = 3763
    db.session.add(print3)

    #print2.roles.append(role2)

    group_print1 = TipoPlanta()
    group_print1.codigo = 'loc'
    group_print1.titulo = 'Plantas de Localização'
    db.session.add(group_print1)

    layout = TipoPlantaLayout()
    layout.formato = 'A4'
    layout.orientacao = 'Landscape'
    layout.tipo_planta = group_print1
    db.session.add(group_print1)

    group_print2 = TipoPlanta()
    group_print2.codigo = 'urb'
    group_print2.titulo = 'Operações Urbanísticas'
    db.session.add(group_print2)

    group_print3 = TipoPlanta()
    group_print3.codigo = 'pdm'
    group_print3.titulo = 'Plano Director Municipal'
    db.session.add(group_print3)

    pr_tp = PlantaTipoPlanta()
    pr_tp.planta = print1
    pr_tp.tipo_planta = group_print1
    pr_tp.ordem = 1
    db.session.add(pr_tp)

    pr_tp = PlantaTipoPlanta()
    pr_tp.planta = print2
    pr_tp.tipo_planta = group_print1
    pr_tp.ordem = 2
    db.session.add(pr_tp)

    pr_tp = PlantaTipoPlanta()
    pr_tp.planta = print1
    pr_tp.tipo_planta = group_print2
    pr_tp.ordem = 1
    db.session.add(pr_tp)

    pr_tp = PlantaTipoPlanta()
    pr_tp.planta = print2
    pr_tp.tipo_planta = group_print2
    pr_tp.ordem = 1
    db.session.add(pr_tp)

    pr_tp = PlantaTipoPlanta()
    pr_tp.planta = print3
    pr_tp.tipo_planta = group_print3
    pr_tp.ordem = 1
    db.session.add(pr_tp)

    ch_tp = TipoPlantaChild()
    ch_tp.tipo_planta_parent = group_print2
    ch_tp.tipo_planta_child = group_print3
    ch_tp.ordem = 1
    db.session.add(ch_tp)

    viewer_print = ViewerPrint()
    viewer_print.viewer = viewer1
    viewer_print.print = print1
    viewer_print.order = 1
    db.session.add(viewer_print)

    viewer_print = ViewerPrint()
    viewer_print.viewer = viewer1
    viewer_print.print = print2
    viewer_print.order = 2
    db.session.add(viewer_print)

    viewer_print_group = ViewerPrintGroup()
    viewer_print_group.viewer = viewer1
    viewer_print_group.print_group = group_print1
    viewer_print_group.order = 1
    db.session.add(viewer_print)

    viewer_print_group = ViewerPrintGroup()
    viewer_print_group.viewer = viewer1
    viewer_print_group.print_group = group_print2
    viewer_print_group.order = 1
    db.session.add(viewer_print)

    if commit:
        db.session.commit()


def create_schema(commit=True):
    db.engine.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    db.engine.execute('CREATE SCHEMA IF NOT EXISTS portal')

    db.drop_all()
    db.create_all()

    load_roles(None)
    load_admin_user(None)

    if commit:
        db.session.commit()


def load_roles(session):
    roles = {
        'Admin': 'Administradores da plataforma',
        'Anonymous': 'Utilizadores não autenticados',
        'Authenticated': 'Utilizadores autenticados',
    }

    for name, description in roles.items():
        role = Role()
        role.name = name
        role.description = description
        role.read_only = True
        if session:
            session.add(role)
        else:
            db.session.add(role)

    if session:
        session.commit()


def load_admin_user(session):
    user = User()
    user.username = 'admin'
    user.email = 'admin@isp.com'
    user.password = hash_password('admin')
    user.active = True
    user.confirmed_at = datetime.now()

    role = Role.query.filter_by(name='Admin').first()

    if role:
        user.roles.append(role)

    if session:
        session.commit()
