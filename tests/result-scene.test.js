import test from 'node:test';
import assert from 'node:assert/strict';
import { ResultScene } from '../src/scenes/ResultScene.js';

function createResultScene(adService = null) {
  const tapZones = new Map();
  const sceneCalls = [];
  const game = {
    adService,
    input: {
      clear: () => tapZones.clear(),
      addTapZone: (id, _x, _y, _w, _h, onTap) => tapZones.set(id, onTap),
    },
    renderer: { width: 390, height: 844 },
    setScene(name) {
      sceneCalls.push(name);
    },
  };
  return { scene: new ResultScene(game), tapZones, sceneCalls };
}

test('ResultScene always provides a way back to farm', () => {
  const { scene, tapZones, sceneCalls } = createResultScene();

  scene.enter({ success: true, reward: 70, gems: 1, targetName: '灯笼摊主', optionLabel: '普通作物', canRetry: false });
  tapZones.get('back-farm')();

  assert.deepEqual(sceneCalls, ['farm']);
  assert.equal(tapZones.has('retry-ad'), false);
});

test('ResultScene rewarded retry returns to steal scene', async () => {
  const adCalls = [];
  const { scene, tapZones, sceneCalls } = createResultScene({
    async showRewardAd(placement) {
      adCalls.push(placement);
      return { rewarded: true };
    },
  });

  scene.enter({ success: false, reward: 0, gems: 0, targetName: '星瓜富商', optionLabel: '夜市宝箱', canRetry: true });
  await tapZones.get('retry-ad')();

  assert.deepEqual(adCalls, ['retrySteal']);
  assert.deepEqual(sceneCalls, ['steal']);
});

test('ResultScene success can share steal result', () => {
  const shareCalls = [];
  const { scene, tapZones } = createResultScene();
  scene.game.shareService = {
    buildStealMessage(result) {
      return `${result.targetName}-${result.optionLabel}`;
    },
    share(message) {
      shareCalls.push(message);
    },
  };

  scene.enter({ success: true, reward: 98, gems: 1, targetName: '灯笼摊主', optionLabel: '变异作物', canRetry: false });
  tapZones.get('share-result')();

  assert.deepEqual(shareCalls, ['灯笼摊主-变异作物']);
});
