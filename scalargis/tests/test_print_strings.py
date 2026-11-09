from io import BytesIO

import pytest
from flask import Flask
from PyPDF2 import PdfReader

from app.utils import pdf_layout

PARAMS = {"default_srid": 3763, "default_mapcenter": [0, 0], "default_scale": 1000}


def layout(**values):
    strings = [{"name": name, "x": 10, "y": 10 + 10 * i, "value": value,
                "font": "Helvetica", "fontsize": 8, "fontcolor": [0, 0, 0]}
               for i, (name, value) in enumerate(values.items())]
    return [{"page_id": 100, "params": PARAMS, "strings": strings}]


def page_text(pdf):
    return PdfReader(BytesIO(pdf.getpdf())).pages[0].extract_text()


@pytest.fixture
def ctx():
    with Flask('print-strings-test').app_context():
        yield


@pytest.fixture
def marker(tmp_path):
    path = tmp_path / 'marker.txt'
    return path, "%[open(r'" + str(path) + "','w').write('x')]%"


def test_request_value_is_printed_as_text(ctx, marker):
    path, payload = marker
    pdf = pdf_layout.Pdf('A4', 'portrait')
    pdf.populate_string('requerente_val', payload)
    pdf.generate(layout(requerente_val=''))
    assert not path.exists()
    assert 'marker.txt' in page_text(pdf)


def test_layout_expression_does_not_run(ctx, marker):
    path, payload = marker
    pdf = pdf_layout.Pdf('A4', 'portrait')
    pdf.generate(layout(fixo_val=payload, outro_val='Outro'))
    assert not path.exists()
    text = page_text(pdf)
    assert 'marker.txt' not in text
    assert 'Outro' in text


def test_layout_db_var_is_filled(ctx):
    pdf = pdf_layout.Pdf('A4', 'portrait')
    pdf.db_vars['concelho'] = {'nome': 'Faro'}
    pdf.generate(layout(concelho_val="Concelho: %['concelho', 'nome']%"))
    assert 'Concelho: Faro' in page_text(pdf)
