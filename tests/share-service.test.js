import { assert, test } from './_harness.js';
import { ShareService } from '../src/services/ShareService.js';

test('ShareService builds steal result copy', () => {
  const service = new ShareService({});

  const message = service.buildStealMessage({
    targetName: '灯笼摊主',
    optionLabel: '变异作物',
    reward: 98,
    gems: 1,
  });

  assert.equal(message, '我在夜市灵田偷到灯笼摊主的变异作物，金币+98，基因+1！');
});

test('ShareService delegates to platform share method when available', () => {
  const calls = [];
  const service = new ShareService({
    shareAppMessage(payload) {
      calls.push(payload);
    },
  });

  const result = service.share('今晚偷到就跑！');

  assert.deepEqual(calls, [{ title: '今晚偷到就跑！' }]);
  assert.deepEqual(result, { shared: true, message: '今晚偷到就跑！' });
});
