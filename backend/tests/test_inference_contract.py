import json

import httpx

from app.inference.public import LocalLanguageModel
from app.settings import Settings


async def test_qwen_chat_template_has_one_initial_system_message():
    def respond(request):
        body = json.loads(request.content)
        assert [message['role'] for message in body['messages']] == ['system', 'user']
        assert 'DEMO-CERTI-001' in body['messages'][0]['content']
        assert body['messages'][1]['content'] == '¿Y su estado?'
        return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps({
            'operation': 'tracking', 'tracking_code': 'DEMO-CERTI-001'})}}]})

    model = LocalLanguageModel(Settings())
    await model.client.aclose()
    model.client = httpx.AsyncClient(base_url='http://llama.test/', transport=httpx.MockTransport(respond))
    try:
        decision = await model.interpret('¿Y su estado?', context={'tracking_code': 'DEMO-CERTI-001'})
        assert decision.operation == 'tracking'
    finally:
        await model.close()
