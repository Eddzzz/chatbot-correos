from pathlib import Path

import pytest

from app.contracts import AccessContext
from app.data_access.infrastructure import PostgresReader
from app.data_access.public import QuerySpec
from app.settings import Settings


@pytest.mark.skipif(not Path('../.runtime/office-relations-import.json').exists(), reason='Requiere grafo local de relaciones importado')
async def test_metadata_inventory_is_not_cut_by_the_operational_record_limit():
    reader = PostgresReader(Settings(database_url=Path('../.runtime/institutional-dsn.txt').read_text().strip(), max_rows=1))
    principal = AccessContext(user_id='operator', permissions=frozenset({'internal_data', 'offices', 'personal_data'}), scope=('global_internal',))
    await reader.open()
    try:
        inventory = await reader.run_read(QuerySpec(template='offices_related_details', parameters={'office_id': 2}), principal)
        assert len(inventory.rows) == 65 and not inventory.truncated
        records = await reader.run_read(QuerySpec(template='offices_records_details', parameters={'office_id': 2, 'table_name': 'paquetes_ems', 'page_limit': 11, 'offset': 0}), principal)
        assert len(records.rows) == 1 and records.truncated
    finally:
        await reader.close()
