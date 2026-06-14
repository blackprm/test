import { MUTATIONS, SEEDS } from '../data/config.js';

export function nowSeconds() {
  return Math.floor(Date.now() / 1000);
}

export function getSeed(seedId) {
  return SEEDS.find((seed) => seed.id === seedId);
}

export function getMutation(mutationId) {
  return MUTATIONS.find((mutation) => mutation.id === mutationId) || MUTATIONS[0];
}

export function isMature(plot, at = nowSeconds()) {
  if (!plot.seedId) return false;
  const seed = getSeed(plot.seedId);
  return !!seed && at - plot.plantedAt >= seed.growSeconds;
}

export function rollMutation(seedId, salt = Date.now()) {
  const roll = Math.abs(Math.sin((salt + seedId.length) * 12.9898) * 43758.5453) % 1;
  let cursor = 0;
  for (const mutation of MUTATIONS) {
    cursor += mutation.chance;
    if (roll <= cursor) return mutation.id;
  }
  return 'normal';
}

export function cropValue(seedId, mutationId) {
  const seed = getSeed(seedId);
  const mutation = getMutation(mutationId);
  return seed ? Math.floor(seed.value * mutation.multiplier) : 0;
}

export function upgradeCost(level) {
  return 160 + level * level * 90;
}
