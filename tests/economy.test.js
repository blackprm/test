import { assert, test } from './_harness.js';
import { cropValue, getSeed, isMature, upgradeCost } from '../src/systems/economy.js';

test('getSeed returns configured seed definitions', () => {
  assert.equal(getSeed('carrot').name, '灵萝卜');
  assert.equal(getSeed('starMelon').value, 360);
});

test('isMature returns true after seed grow seconds pass', () => {
  const plot = { seedId: 'carrot', plantedAt: 100, mutationId: 'normal' };

  assert.equal(isMature(plot, 119), false);
  assert.equal(isMature(plot, 120), true);
});

test('cropValue applies mutation multiplier', () => {
  assert.equal(cropValue('carrot', 'normal'), 45);
  assert.equal(cropValue('carrot', 'glow'), 81);
});

test('upgradeCost grows by level', () => {
  assert.equal(upgradeCost(1), 250);
  assert.equal(upgradeCost(3), 970);
});
