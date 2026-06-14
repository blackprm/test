import test from 'node:test';
import assert from 'node:assert/strict';
import { harvestPlot, plantSeed, upgradeStall } from '../src/systems/farmState.js';

function makeState() {
  return {
    gold: 200,
    gems: 0,
    stallLevel: 1,
    unlockedSeeds: ['carrot'],
    plotCount: 3,
    collection: [],
    plots: [
      { seedId: null, plantedAt: 0, mutationId: 'normal', harvested: false },
      { seedId: null, plantedAt: 0, mutationId: 'normal', harvested: false },
      { seedId: null, plantedAt: 0, mutationId: 'normal', harvested: false },
    ],
  };
}

test('plantSeed spends gold and fills an empty plot', () => {
  const state = makeState();

  assert.equal(plantSeed(state, 0, 'carrot'), true);
  assert.equal(state.gold, 180);
  assert.equal(state.plots[0].seedId, 'carrot');
  assert.equal(typeof state.plots[0].plantedAt, 'number');
});

test('harvestPlot grants value and clears mature plot', () => {
  const state = makeState();
  state.plots[0] = { seedId: 'carrot', plantedAt: 0, mutationId: 'normal', harvested: false };

  const value = harvestPlot(state, 0, 25);

  assert.equal(value, 45);
  assert.equal(state.gold, 245);
  assert.equal(state.plots[0].seedId, null);
  assert.deepEqual(state.collection, ['carrot:normal']);
});

test('upgradeStall adds a plot and unlocks mushroom at level two', () => {
  const state = makeState();
  state.gold = 300;

  assert.equal(upgradeStall(state), true);
  assert.equal(state.stallLevel, 2);
  assert.equal(state.plotCount, 4);
  assert.equal(state.plots.length, 4);
  assert.equal(state.unlockedSeeds.includes('mushroom'), true);
});
