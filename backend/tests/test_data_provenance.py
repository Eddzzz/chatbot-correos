from fastapi.testclient import TestClient

from app.bootstrap import create_app
from app.settings import Settings


def test_real_backup_config_exposes_snapshot_without_connection_details():
    settings = Settings(database_url='postgresql://private:secret@localhost/private',
                        data_snapshot='2026-10-08 14:59:32')
    # Config inspection must never attempt a database connection.
    class Reader:
        pass
    with TestClient(create_app(settings, reader=Reader())) as client:
        body = client.get('/api/config').json()
    assert body == {'data_mode': 'postgres', 'inference_mode': 'local',
                    'data_snapshot': '2026-10-08 14:59:32'}
    assert 'secret' not in str(body)
