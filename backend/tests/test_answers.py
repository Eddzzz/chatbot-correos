from datetime import datetime, timezone

from app.answers.public import compose_answer
from app.data_access.public import QueryResult


def test_tracking_is_a_spanish_sentence_grounded_in_the_row():
    result = QueryResult([{'source': 'certi', 'tracking_code': 'DEMO-CERTI-001',
        'status': 'Registrado ficticio', 'destination': 'La Paz'}], 'fixture', datetime.now(timezone.utc))
    answer = compose_answer('r', 's', result)
    assert 'El registro DEMO-CERTI-001' in answer.answer
    assert 'figura con el estado «Registrado ficticio»' in answer.answer
    assert answer.rows == result.rows
