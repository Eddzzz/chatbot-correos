import {test} from 'node:test';
import assert from 'node:assert/strict';
import {chatIdFromPath,chatPath} from './chatUrl.ts';

test('chat URLs preserve the identifier and reject invalid paths',()=>{
  const id='a1234567-1234-1234-abcd-123456789abc';
  assert.equal(chatIdFromPath(chatPath(id)),id);
  assert.equal(chatIdFromPath(`/c/${id}/`),id);
  for(const path of ['/', '/c/', '/c/not-a-chat', `/c/${id}/extra`, '/c/../../api']) assert.equal(chatIdFromPath(path),null);
  assert.equal(chatPath(null),'/');
});
