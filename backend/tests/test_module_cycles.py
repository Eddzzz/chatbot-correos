import ast
from pathlib import Path


def test_business_modules_have_no_dependency_cycles_or_external_sql_drivers():
    modules = {'identity', 'policies', 'conversation', 'operations', 'analytics', 'data_access', 'inference', 'answers', 'audit'}
    edges = {module: set() for module in modules}
    for file in Path('app').rglob('*.py'):
        owner = file.parts[1]
        for node in ast.walk(ast.parse(file.read_text(encoding='utf-8'))):
            imports = ([node.module or ''] if isinstance(node, ast.ImportFrom) else
                       [alias.name for alias in node.names] if isinstance(node, ast.Import) else [])
            for module in imports:
                if module.split('.')[0] in {'psycopg', 'psycopg_pool'}:
                    assert owner == 'data_access', file
                parts = module.split('.')
                if owner in modules and len(parts) > 1 and parts[0] == 'app' and parts[1] in modules and parts[1] != owner:
                    edges[owner].add(parts[1])

    def visit(module, ancestors):
        assert module not in ancestors, f'Dependencia circular: {ancestors} -> {module}'
        for dependency in edges[module]:
            visit(dependency, ancestors | {module})

    for module in modules:
        visit(module, set())
