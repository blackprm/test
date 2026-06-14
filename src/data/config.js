export const SEEDS = [
  { id: 'carrot', name: '灵萝卜', price: 20, growSeconds: 20, value: 45 },
  { id: 'mushroom', name: '灯蘑菇', price: 60, growSeconds: 45, value: 135 },
  { id: 'starMelon', name: '星瓜', price: 140, growSeconds: 80, value: 360 },
];

export const MUTATIONS = [
  { id: 'normal', name: '普通', multiplier: 1, chance: 0.72 },
  { id: 'glow', name: '发光', multiplier: 1.8, chance: 0.16 },
  { id: 'lucky', name: '招财', multiplier: 2.5, chance: 0.08 },
  { id: 'giant', name: '巨型', multiplier: 3.4, chance: 0.035 },
  { id: 'wild', name: '暴走', multiplier: 5, chance: 0.005 },
];

export const INITIAL_STATE = {
  gold: 120,
  gems: 0,
  stallLevel: 1,
  unlockedSeeds: ['carrot'],
  plotCount: 3,
  shieldUntil: 0,
  traps: 1,
  petLevel: 1,
  collection: [],
  freeStealsToday: 5,
};
