"""Tests for the IntersectLayers CSV/XLS export table builder.

Run with the venv interpreter from ``scalargis-server/scalargis``::

    ../venv/Scripts/python.exe -m pytest app/plugins/spatial_toolbox/utils/tests/test_analysis_export.py

These drive the real ``export_intersect_results`` function. The only stubs are
the three side-effect calls at the tail of that function: ``save_csv`` and
``save_xls`` (they write a file to disk) and ``send_file`` (it needs a Flask
request context). The stub for the save call captures the ``data`` table that
the function builds, so the tests assert on the true output of the code under
test, not on a re-implementation of it.

They lock down two defects from commit e04c12a:
  1. The main result row (``data['Resultados']``) must carry its group column,
     so every row keeps the 6 columns the header declares.
  2. A layer whose ``group`` name is absent from ``groups`` must not raise
     ``AttributeError``; the group cell falls back to the raw group name.
"""
import pytest

import app.plugins.spatial_toolbox.utils.analysis as analysis


@pytest.fixture
def capture_export(monkeypatch):
    """Run export_intersect_results and hand back the data table it builds."""
    box = {}

    def _capture_save(filename, data):
        box['filename'] = filename
        box['data'] = data

    monkeypatch.setattr(analysis, 'save_csv', _capture_save)
    monkeypatch.setattr(analysis, 'save_xls', _capture_save)
    monkeypatch.setattr(analysis, 'send_file', lambda *a, **k: 'SENT')

    def _run(record, out_format='csv'):
        result = analysis.export_intersect_results(record, out_format)
        assert result == 'SENT'
        return box['data']

    return _run


def _record_two_groups():
    """One layer in a known group, one layer whose group is missing.

    Titles are given as localization dicts so the run also exercises
    ``converter_field`` / ``get_localized_value_as_text`` (lang=None -> default).
    """
    return {
        'description': 'Relatorio de teste',
        'groups': [
            {'name': 'G1', 'title': {'pt': 'Grupo Um', 'default': 'Group One'}},
        ],
        'layers': [
            {
                'group': 'G1',
                'title': {'pt': 'Camada A', 'default': 'Layer A'},
                'fields': [{'field': 'cod', 'alias': 'Codigo'}],
                'results': [
                    {'area': 1.23456, 'length': 0.0, 'percent': 50.0, 'cod': 'X1'},
                    {'area': 2.0, 'length': 0.0, 'percent': 50.0, 'cod': 'X2'},
                ],
            },
            {
                # group name absent from `groups` -> group_item is None
                'group': 'GHOST',
                'title': 'Camada Orfa',
                'fields': [{'field': 'cod', 'alias': 'Codigo'}],
                'results': [
                    {'area': 5.0, 'length': 0.0, 'percent': 100.0, 'cod': 'Z9'},
                ],
            },
        ],
    }


# --- Bug 1: the main result row keeps its group column ----------------

def test_resultados_rows_keep_all_six_columns(capture_export):
    data = capture_export(_record_two_groups())

    resultados = data['Resultados']
    header = resultados[0]
    assert header == ['Grupo', 'Titulo', 'Area', 'Comprimento', '%', 'Campos'] \
        or header[0] == 'Grupo'  # header text is fixed; guard the column count below
    assert len(header) == 6

    body = resultados[1:]
    assert len(body) == 3  # two results in G1 + one in GHOST
    for row in body:
        # The defect dropped the leading group cell, leaving 5 columns and
        # shifting every value one column to the left.
        assert len(row) == 6, f'expected 6 columns, got {len(row)}: {row}'


def test_resultados_group_cell_holds_the_localized_group_title(capture_export):
    data = capture_export(_record_two_groups())
    body = data['Resultados'][1:]

    # Rows for the G1 layer carry the localized group title, not the layer title.
    assert body[0][0] == 'Group One'
    assert body[0][1] == 'Layer A'
    assert body[1][0] == 'Group One'


def test_detail_rows_do_not_gain_a_duplicate_group_cell(capture_export):
    data = capture_export(_record_two_groups())

    # The per-layer detail block is keyed by the space-stripped layer title.
    detail = data['LayerA']
    column_names = detail[0]
    assert column_names[0] == 'Grupo'
    for row in detail[1:]:
        # The defect appended the group value to this row a second time,
        # making it one cell wider than its header.
        assert len(row) == len(column_names), \
            f'detail row width {len(row)} != header width {len(column_names)}: {row}'


# --- Bug 2: a missing group must not crash the export -----------------

def test_layer_with_unknown_group_does_not_raise(capture_export):
    record = {
        'groups': [],  # nothing to match against
        'layers': [
            {
                'group': 'GHOST',
                'title': 'Camada Orfa',
                'fields': [{'field': 'cod', 'alias': 'Codigo'}],
                'results': [
                    {'area': 3.0, 'length': 0.0, 'percent': 100.0, 'cod': 'Z9'},
                ],
            },
        ],
    }

    # Before the fix this raised AttributeError on `None.get('title')`.
    data = capture_export(record)

    row = data['Resultados'][1]
    assert len(row) == 6
    assert row[0] == 'GHOST'  # falls back to the raw group name


# --- the xls path shares the same builder -----------------------------

def test_xls_path_builds_the_same_table(capture_export):
    data = capture_export(_record_two_groups(), out_format='xls')
    for row in data['Resultados'][1:]:
        assert len(row) == 6
    assert data['Resultados'][1][0] == 'Group One'
