import test from 'node:test';
import assert from 'node:assert/strict';
import { FarmScene } from '../src/scenes/FarmScene.js';

function createFarmScene() {
  const tapZones = new Map();
  const game = {
    state: {
      gold: 200,
      gems: 0,
      stallLevel: 1,
      traps: 1,
      petLevel: 1,
      unlockedSeeds: ['carrot'],
      plotCount: 3,
      collection: [],
      plots: [
        { seedId: null, plantedAt: 0, mutationId: 'normal', harvested: false },
        { seedId: null, plantedAt: 0, mutationId: 'normal', harvested: false },
        { seedId: null, plantedAt: 0, mutationId: 'normal', harvested: false },
      ],
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
    setScene() {},
  };
  return { scene: new FarmScene(game), game, tapZones };
}

test('FarmScene tapping empty plot plants first unlocked seed', () => {
  const { scene, game, tapZones } = createFarmScene();

  scene.enter();
  tapZones.get('plot-0')();

  assert.equal(game.state.plots[0].seedId, 'carrot');
  assert.equal(game.state.gold, 180);
  assert.equal(game.saveCount, 1);
});

test('FarmScene tapping mature plot harvests and clears it', () => {
  const { scene, game, tapZones } = createFarmScene();
  game.state.plots[0] = { seedId: 'carrot', plantedAt: 0, mutationId: 'normal', harvested: false };

  scene.enter();
  tapZones.get('plot-0')();

  assert.equal(game.state.plots[0].seedId, null);
  assert.equal(game.state.gold, 245);
  assert.deepEqual(game.state.collection, ['carrot:normal']);
});

test('FarmScene render loads background and crop art', () => {
  const { scene, game } = createFarmScene();
  const calls = [];
  game.state.plots[0] = { seedId: 'carrot', plantedAt: 0, mutationId: 'normal', harvested: false };
  const renderer = {
    width: 390,
    height: 844,
    clear: (color) => calls.push(['clear', color]),
    loadImage: (id, src) => calls.push(['loadImage', id, src]),
    drawImage: (id) => {
      calls.push(['drawImage', id]);
      return true;
    },
    roundRect: () => {},
    text: () => {},
  };

  scene.enter();
  scene.render(renderer);

  assert(calls.some((call) => call[0] === 'loadImage' && call[1] === 'night-market-bg' && call[2] === 'assets/generated/night-market-bg.png'));
  assert(calls.some((call) => call[0] === 'loadImage' && call[1] === 'seed-carrot' && call[2] === 'assets/generated/icon-carrot.png'));
  assert(calls.some((call) => call[0] === 'drawImage' && call[1] === 'seed-carrot'));
});
