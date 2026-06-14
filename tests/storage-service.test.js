import { assert, test } from './_harness.js';
import { StorageService } from '../src/services/StorageService.js';

test('StorageService creates initial farm state when nothing is saved', () => {
  const storage = new StorageService({ getStorageSync: () => null, setStorageSync: () => {} });
  const state = storage.load();

  assert.equal(state.gold, 120);
  assert.equal(state.plotCount, 3);
  assert.equal(state.plots.length, 3);
  assert.equal(state.unlockedSeeds.includes('carrot'), true);
});

test('StorageService merges saved state over defaults', () => {
  const storage = new StorageService({
    getStorageSync: () => ({ gold: 999, stallLevel: 3 }),
    setStorageSync: () => {},
  });
  const state = storage.load();

  assert.equal(state.gold, 999);
  assert.equal(state.stallLevel, 3);
  assert.equal(state.traps, 1);
});
