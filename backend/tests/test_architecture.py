import ast
from pathlib import Path


def test_module_boundaries_and_database_ownership():
    modules = {'identity', 'policies', 'conversation', 'operations', 'analytics', 'data_access', 'inference', 'answers', 'audit'}
    for file in Path('app').rglob('*.py'):
        tree = ast.parse(file.read_text(encoding='utf-8'))
        own = file.parts[1]
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''
                if module.startswith('psycopg'):
                    assert own == 'data_access', file
                parts = module.split('.')
                if own in modules and len(parts) >= 3 and parts[0] == 'app' and parts[1] in modules and parts[1] != own:
                    assert parts[2] == 'public', (file, module)


def test_no_sql_business_in_other_modules():
    for file in Path('app').rglob('*.py'):
        if file.parts[1] != 'data_access':
            tree = ast.parse(file.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    assert not node.value.lstrip().upper().startswith(('SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ')), file
