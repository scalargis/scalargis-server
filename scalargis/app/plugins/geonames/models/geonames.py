from app.database import db


class GeonamesSearchResultLegacy(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    designacao = db.Column(db.Text())
    origem = db.Column(db.Text())
    type = db.Column(db.Text())
    grupo = db.Column(db.Text())
    ilha = db.Column(db.Text())
    distrito = db.Column(db.Text())
    concelho = db.Column(db.Text())
    freguesia = db.Column(db.Text())
    dicofre = db.Column(db.Text())
    geom_wkt = db.Column(db.Text())
    similarity = db.Column(db.Float())
    search_func = db.Column(db.Text())


class GeonamesSearchResult(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Text())
    source = db.Column(db.Text())
    type = db.Column(db.Text())
    group = db.Column(db.Text())
    admin_level1 = db.Column(db.Text())
    admin_level2 = db.Column(db.Text())
    admin_level3 = db.Column(db.Text())
    admin_level4 = db.Column(db.Text())
    admin_code = db.Column(db.Text())
    geom_wkt = db.Column(db.Text())
    similarity = db.Column(db.Float())
    search_func = db.Column(db.Text())