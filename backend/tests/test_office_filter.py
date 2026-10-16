from pathlib import Path

import pytest

from app.contracts import AccessContext
from app.data_access.infrastructure import PostgresReader
from app.data_access.public import QuerySpec
from app.settings import Settings


@pytest.mark.skipif(not Path('../.runtime/fixture-dsn.txt').exists(), reason='Requiere fixture local')
async def test_department_filter_preserves_case_and_accent_variants():
    reader = PostgresReader(Settings(database_url=Path('../.runtime/fixture-dsn.txt').read_text().strip()))
    principal = AccessContext(user_id='operator', permissions=frozenset({'internal_data', 'offices'}), scope=('global_internal',))
    await reader.open()
    try:
        result = await reader.run_read(QuerySpec(template='offices', parameters={'department': 'LA PÁZ'}), principal)
        assert len(result.rows) == 1
    finally:
        await reader.close()
