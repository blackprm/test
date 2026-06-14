import { assert, test } from './_harness.js';
import { AdService } from '../src/services/AdService.js';

test('AdService mock rewarded video resolves as rewarded', async () => {
  const service = new AdService({});

  const result = await service.showRewardAd('retrySteal');

  assert.deepEqual(result, { rewarded: true, placement: 'retrySteal', mock: true });
});
