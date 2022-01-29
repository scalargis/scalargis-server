import unittest
from app.database import db
from app.main import app
from app.main import configure_app, setup_security
from app.models.files import *
from app.models.mapas import *

# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://postgres:password@localhost:5432/scalargis_tests"

configure_app(app)

db.init_app(app)
setup_security(app)

app.app_context().push()

class TestApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        #print(app.config['SQLALCHEMY_DATABASE_URI'])

        db.engine.execute('CREATE EXTENSION IF NOT EXISTS postgis')
        db.engine.execute('CREATE SCHEMA IF NOT EXISTS portal')

        db.drop_all()
        db.create_all()

    def test_orders_by_customer_blank(self):
        results = []
        self.assertEqual(results, [])

    '''
    def test_lookup(self):
        document = DocumentDirectory(codigo='test')
        db.session.add(document)
        #db.session.commit()
        documents = DocumentDirectory.query.all()
        assert document in documents
        print("NUMBER OF ENTRIES:")
        print(len(documents))
    '''

    def test_create_map(self):
        mapa = Mapa(codigo="mapa1", titulo="Planta 1")
        db.session.add(mapa)

        db.session.commit()

    def test_create_tipo_planta(self):
        tipo1 = TipoPlanta(codigo="tipo1", titulo="Tipo Planta1")
        db.session.add(tipo1)

        tipo2 = TipoPlanta(codigo="tipo2", titulo="Tipo Planta2")
        db.session.add(tipo2)

        db.session.commit()

        mapa = db.session.get(Mapa, 1)
        tipos = TipoPlanta.query.all()

        print("adsfsdfsdfs")
        print(len(tipos))

        ordem = 0
        for tipo_planta in tipos:
            ordem = ordem + 1
            pt = MapaTipoPlanta(mapa = mapa, tipo_planta = tipo_planta, ordem=ordem)
            db.session.add(pt)

        db.session.commit()

        mapa = db.session.get(Mapa, 1)
        tipos = TipoPlanta.query.all()

        for t in mapa.tipos_plantas:
            db.session.delete(t)

        ordem = 5
        for tipo_planta in tipos:
            ordem = ordem + 1
            pt = mapa.tipos_plantas.append(MapaTipoPlanta(tipo_planta = tipo_planta, ordem=ordem))
            #db.session.add(pt)

        db.session.commit()


    def test_create_document_with_rule(self):
        document = DocumentDirectory(codigo='test', path='/fake_path')
        db.session.add(document)
        rule1 = DocumentDirectoryRule(filtro='fake_filter1')
        document.rules.append(rule1)

        rule2 = DocumentDirectoryRule(filtro='fake_filter2')
        document.rules.append(rule2)

        db.session.commit()

        documents = DocumentDirectory.query.all()
        # assert document in documents
        self.assertIn(document, documents)

        rules = DocumentDirectoryRule.query.all()
        self.assertIn(rule1, rules)
        self.assertIn(rule2, rules)

        self.assertEqual(document, rules[1].document_directory)

        print("Number of Documents:")
        print(len(documents))

        print("Number of Document Rules:")
        print(len(rules))

    def test_create_mapa_planta(self):
        #mapa = Mapa(codigo="mapa1", titulo="Planta 1")
        #db.session.add(mapa)
        #mapa = db.session.query(Mapa).filter(Mapa.id == 1).first()
        mapa = db.session.get(Mapa, 1)

        planta = Planta(codigo="planta1", titulo="Planta 1", escala=2000)
        db.session.add(planta)

        mapa_planta = MapaPlanta(ordem=1)
        mapa_planta.mapa = mapa
        mapa_planta.planta = planta

        db.session.commit()

