from app.modules.print.controllers import output_title


def test_the_form_title_names_the_row():
    assert output_title('Planta Livre', {'titulo_val': ' Muro do quintal '}) == 'Muro do quintal'


def test_an_empty_or_missing_form_title_keeps_the_print_title():
    assert output_title('Planta Livre', {'titulo_val': '  '}) == 'Planta Livre'
    assert output_title('Planta Livre', {'nome': 'x'}) == 'Planta Livre'
    assert output_title('Planta Livre', None) == 'Planta Livre'
    assert output_title('Planta Livre', ['titulo_val']) == 'Planta Livre'
