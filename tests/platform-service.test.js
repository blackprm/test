import test from 'node:test';
import assert from 'node:assert/strict';
import { PlatformService } from '../src/services/PlatformService.js';

test('PlatformService falls back to default system info without tt runtime', () => {
  const platform = new PlatformService(null);

  assert.deepEqual(platform.getSystemInfo(), {
    windowWidth: 390,
    windowHeight: 844,
    pixelRatio: 1,
  });
});

test('PlatformService delegates storage to runtime when available', () => {
  const saved = new Map();
  const platform = new PlatformService({
    setStorageSync(key, value) {
      saved.set(key, value);
    },
    getStorageSync(key) {
      return saved.get(key);
    },
  });

  platform.setStorageSync('state', { gold: 120 });

  assert.deepEqual(platform.getStorageSync('state'), { gold: 120 });
});
