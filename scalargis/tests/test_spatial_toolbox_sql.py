"""The spatial toolbox SQL loads as any app role: it names no owner and grants only to public."""
import os
import re

SQL = os.path.join(os.path.dirname(__file__), '..', 'app', 'plugins', 'spatial_toolbox', 'database',
                   'spatial_toolbox_functions.sql')


def _text():
    with open(SQL, encoding='utf-8') as f:
        return f.read()


def test_no_owner_change():
    assert not re.search(r'\bOWNER\s+TO\b', _text(), re.I)


def test_grants_only_to_public():
    grants = re.findall(r'\bGRANT\b.*?\bTO\s+(\w+)', _text(), re.I)
    assert grants == ['public']


def test_function_is_security_invoker():
    assert not re.search(r'\bSECURITY\s+DEFINER\b', _text(), re.I)
