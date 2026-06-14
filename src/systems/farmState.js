import { cropValue, getSeed, isMature, nowSeconds, rollMutation, upgradeCost } from './economy.js';

export function plantSeed(state, plotIndex, seedId) {
  const seed = getSeed(seedId);
  const plot = state.plots[plotIndex];
  if (!seed || !plot || plot.seedId || state.gold < seed.price) return false;
  state.gold -= seed.price;
  plot.seedId = seedId;
  plot.plantedAt = nowSeconds();
  plot.mutationId = rollMutation(seedId, plot.plantedAt);
  plot.harvested = false;
  return true;
}

export function harvestPlot(state, plotIndex, at = nowSeconds()) {
  const plot = state.plots[plotIndex];
  if (!plot || !isMature(plot, at) || plot.harvested) return 0;
  const value = cropValue(plot.seedId, plot.mutationId);
  state.gold += value;
  const collectionKey = `${plot.seedId}:${plot.mutationId}`;
  if (!state.collection.includes(collectionKey)) state.collection.push(collectionKey);
  plot.seedId = null;
  plot.plantedAt = 0;
  plot.mutationId = 'normal';
  plot.harvested = false;
  return value;
}

export function upgradeStall(state) {
  const cost = upgradeCost(state.stallLevel);
  if (state.gold < cost || state.plotCount >= 9) return false;
  state.gold -= cost;
  state.stallLevel += 1;
  state.plotCount += 1;
  state.plots.push({ seedId: null, plantedAt: 0, mutationId: 'normal', harvested: false });
  if (state.stallLevel >= 2 && !state.unlockedSeeds.includes('mushroom')) state.unlockedSeeds.push('mushroom');
  if (state.stallLevel >= 4 && !state.unlockedSeeds.includes('starMelon')) state.unlockedSeeds.push('starMelon');
  return true;
}
