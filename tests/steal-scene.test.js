import { assert, test } from './_harness.js';
import { StealScene } from '../src/scenes/StealScene.js';

function createStealScene() {
  const tapZones = new Map();
  const sceneCalls = [];
  const game = {
    state: {
      gold: 100,
      gems: 0,
      petLevel: 1,
    },
    input: {
      clear: () => tapZones.clear(),
      addTapZone: (id, _x, _y, _w, _h, onTap) => tapZones.set(id, onTap),
    },
    renderer: { width: 390, height: 844 },
    saveCount: 0,
    save() {
      this.saveCount += 1;
    },
    setScene(name, params) {
      sceneCalls.push({ name, params });
    },
  };
  return { scene: new StealScene(game), game, tapZones, sceneCalls };
}

test('StealScene successful steal grants reward and opens result scene', () => {
  const originalRandom = Math.random;
  Math.random = () => 0.99;
  try {
    const { scene, game, tapZones, sceneCalls } = createStealScene();

    scene.enter();
    tapZones.get('steal-0-mutant')();

    assert.equal(game.state.gold, 198);
    assert.equal(game.state.gems, 1);
    assert.equal(game.saveCount, 1);
    assert.deepEqual(sceneCalls, [
      {
        name: 'result',
        params: {
          success: true,
          reward: 98,
          gems: 1,
          targetName: '灯笼摊主',
          optionLabel: '变异作物',
          canRetry: false,
        },
      },
    ]);
  } finally {
    Math.random = originalRandom;
  }
});

test('StealScene timeout opens retryable failed result', () => {
  const { scene, sceneCalls } = createStealScene();

  scene.enter();
  scene.startedAt = Date.now() - 31_000;
  scene.update();

  assert.deepEqual(sceneCalls, [
    {
      name: 'result',
      params: {
        success: false,
        reward: 0,
        gems: 0,
        targetName: '夜市',
        optionLabel: '超时',
        canRetry: true,
      },
    },
  ]);
});
