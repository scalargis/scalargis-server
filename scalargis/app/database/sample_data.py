import os
from datetime import datetime

from shapely.wkt import loads
from geoalchemy2 import shape

from app.models.portal import *


def load_data():
    print_element = PrintElement(
        code = 'main-map--params',
        name = 'Parâmetros de base do mapa',
        config = '''{   
          "params": {
            "default_scale":1000,
            "force_default_scale": false,
            "default_mapcenter":[1800,-294000],
            "default_srid":3763,
            "show_coords_bbox": false,
            "show_coords": {"active": true, "nb_points":2},
            "fill_map_background":true,
            "clean_arround_map":true
          }
        }''',
        id_user_create = 1,
        created_at = datetime.now()
    )
    db.session.add(print_element)

    print_element = PrintElement(
        code='main-map--geom_style',
        name='Definição da simbologia da geometria desenhada na planta',
        config='''{
          "geom_style": {
            "active": true,
            "vertice_size":0.5,
            "point_size":2,
            "point_stroke_color": [0.8,0,0,0.1],
            "point_fill_color":[0.8, 0, 0, 1],
            "line_width":3,
            "line_color":[0.8,0,0,1],
            "line_dash":false,
            "line_vertice":false,
            "polygon_stroke_width":3,
            "polygon_stroke_color":[0.85,0,0,1],
            "polygon_stroke_dash":false,
            "polygon_vertice":false,
            "polygon_fill_color":[150, 150, 150, 0]
          }
        }''',
        id_user_create = 1,
        created_at=datetime.now()
    )
    db.session.add(print_element)

    print_group = PrintGroup(
        code='igt',
        title='Instrumentos de Gestão Territorial',
        description='Instrumentos de Gestão Territorial',
        is_active=True,
        allow_drawing=True,
        location_marking=False,
        draw_location=True,
        multi_geom=True,
        show_author=False,
        payment_reference=False,
        print_purpose=False,
        restrict_scales=False,
        restrict_scales_list='1000,2000,5000,10000,20000,25000,50000',
        free_scale=False,
        map_scale=False,
        form_fields={"fields": {}, "groups": {}},
        select_prints=False,
        group_prints=False,
        geometry = None,
        tolerance_filter=None,
        show_all_prints=True,
        id_user_create=1,
        created_at=datetime.now()
    )
    db.session.add(print_group)

    print_group_child = PrintGroup(
        code='pp',
        title='PP Teste',
        description='PP Teste',
        is_active=True,
        allow_drawing=True,
        location_marking=False,
        draw_location=True,
        multi_geom=True,
        show_author=False,
        payment_reference=False,
        print_purpose=False,
        restrict_scales=False,
        restrict_scales_list='1000,2000,5000,10000,20000,25000,50000',
        free_scale=False,
        map_scale=False,
        form_fields={"fields": {}, "groups": {}},
        select_prints=False,
        group_prints=False,
        geometry = shape.from_shape(loads('POLYGON((-8.5428786277771 37.1392798099054,-8.54235291481018 37.1369534374413,-8.53924155235291 37.1375264843577,-8.5392951965332 37.1392883626134,-8.5428786277771 37.1392798099054))'), srid=PrintGroup.__srid__),
        tolerance_filter=10,
        show_all_prints=True,
        id_user_create=1,
        created_at=datetime.now()
    )
    db.session.add(print_group_child)

    print_group.print_group_child_assoc.append(PrintGroupChild(order=1, print_group_child_id=2))

    print = Print(
        id=1,
        code='livre',
        title='Planta Livre',
        description='Planta livre',
        format='A4',
        orientation='Portrait',
        location_marking=False,
        draw_location=True,
        multi_geom=True,
        free_printing=True,
        show_author=True,
        payment_reference=True,
        print_purpose=True,
        restrict_scales=True,
        restrict_scales_list='1000,2000,5000,10000,20000,25000,50000',
        free_scale=True,
        map_scale=True,
        form_fields="{\"fields\": {}, \"groups\": {}}",
        srid=3857,
        geometry=None,
        tolerance_filter=None,
        is_active=True,
        owner_id=1,
        id_user_create=1,
        created_at=datetime.now()
    )
    db.session.add(print)

    print = Print(
        id=2,
        code='pp1',
        name="PP Teste - Implantação",
        title='PP Teste - Implantação',
        description='PP Teste - Implantação',
        scale=1000,
        format='A4',
        orientation='Portrait',
        config_json=None,
        allow_drawing=True,
        location_marking=None,
        draw_location=True,
        multi_geom=True,
        free_printing=True,
        show_author=False,
        payment_reference=False,
        print_purpose=False,
        restrict_scales=True,
        restrict_scales_list='1000,2000,5000,10000,20000,25000,50000',
        free_scale=True,
        map_scale=True,
        form_fields={"fields": {}, "groups": {}},
        srid=3857,
        geometry=None,
        tolerance_filter=None,
        is_active=True,
        owner_id=1,
        id_user_create=1,
        created_at=datetime.now()
    )
    db.session.add(print)

    print = Print(
        id=3,
        code='pp2',
        name="PP Teste - Condicionantes",
        title='PP Teste - Condicionantes',
        description='PP Teste - Condicionantes',
        scale=1000,
        format='A4',
        orientation='Portrait',
        config_json=None,
        allow_drawing=True,
        location_marking=None,
        draw_location=True,
        multi_geom=True,
        free_printing=True,
        show_author=False,
        payment_reference=False,
        print_purpose=False,
        restrict_scales=True,
        restrict_scales_list='1000,2000,5000,10000,20000,25000,50000',
        free_scale=True,
        map_scale=True,
        form_fields={"fields": {}, "groups": {}},
        srid=3857,
        geometry= shape.from_shape(loads('POLYGON((-8.5404109954834 37.1391515191701,-8.54033589363098 37.1385015094338,-8.53988528251648 37.1384672982404,-8.53939175605774 37.138484403839,-8.53941321372986 37.139168624614,-8.5404109954834 37.1391515191701))'), srid=Print.__srid__),
        tolerance_filter=None,
        is_active=True,
        owner_id=1,
        id_user_create=1,
        created_at=datetime.now()
    )
    db.session.add(print)

    print_group_child.print_assoc.append(PrintGroupPrint(order=1, print_id=2))
    print_group_child.print_assoc.append(PrintGroupPrint(order=1, print_id=3))

    layout = dict(
        format='A4',
        orientation='Portrait',
        config='''[{
           "page_id": 100,
            "map":{"ll_x":25,"ll_y":50,"width":161,"height":210},
          
           "sublayouts":
             [
               {"code":"main-map--params", "active":true, "force":false},
               {"code":"main-map--basic_style", "active":true, "force":false}
             ],
        
         
           "params":{
                    "default_scale":10000
                    },
          
            "strings":
              [
               {"name":"top_title", "x":27,"y":267, "font":"Helvetica",
                 "fontsize":11, "fontcolor":[0,0,0,1], "value":
                 "Carta de áreas edificadas e carta de interfaces de áreas edificadas de Portugal Continental"},
        
               {"name":"a4", "x":143,"y":25, "font":"Helvetica",
                 "fontsize":6, "fontcolor":[0,0,0,1], "value":"Proibida a reprodução para difusão ou venda."},
                        
               {"name":"a2", "x":80,"y":35, "font":"Helvetica",
                 "fontsize":8, "fontcolor":[0,0,0,1], "value":"Sistema de Referência: PT-TM06/ETRS89"}
            ],
        
        
            "date":{"x":146,"y":31,"font":"Helvetica","fontsize":8, "prefix":"Data de impressão: ", "format":"%d-%m-%Y","active":true},
        
            "scale":{"x":161,"y":35,"font":"Helvetica","fontsize":8,"prefix":"Escala: 1/",  "active":true},
        
            "scalebar":{"x":82,"y":40, "max_width_mm": 50, "font":"Helvetica","fontsize":8,  "fontcolor":[0,0,0,1], "linewidth":1,
                               "linecolor":[0,0,0,1], "has_background": true, "backgroundcolor":[1,1,1,0.5], "active":true},
          
        
            "images":
                    [
                      {"active":true,"path":"pdf/logo_dgt.png","x":25,"y":272,"width":50},
                      {"active":true,"path":"pdf/arrow.jpg","x":177,"y":274,"width":5}			        
                    ],
          
          
            "graphics":
                    [              
                {"type":"line", "coords":[[25,50],[186,50],[186,260],[25,260],[25,50]],"line_width":1, "line_color":[0,0,0,1]}
              ]          
        }]'''
    )

    db.session.add(PrintLayout(
        **layout,
        print_id=1
    ))

    db.session.add(PrintLayout(
        **layout,
        print_id=2
    ))

    db.session.add(PrintLayout(
        **layout,
        print_id=3
    ))

    db.session.add(ViewerPrint(viewer_id=1, print_id=1))

    db.session.add(ViewerPrintGroup(viewer_id=1, print_group_id=1, order=1))
