import { INITIAL_STATE } from '../data/config.js';

const STORAGE_KEY = 'night-market-run-state-v1';

export class StorageService {
  constructor(platform) {
    this.platform = platform;
  }

  load() {
    const saved = this.platform.getStorageSync(STORAGE_KEY);
    if (!saved) return this.createInitialState();
    return { ...this.createInitialState(), ...saved };
  }

  save(state) {
    this.platform.setStorageSync(STORAGE_KEY, state);
  }

  createInitialState() {
    return {
      ...INITIAL_STATE,
      plots: Array.from({ length: INITIAL_STATE.plotCount }, () => ({
        seedId: null,
        plantedAt: 0,
        mutationId: 'normal',
        harvested: false,
      })),
      lastBattleLog: '今晚还没人摸进你的摊位。',
    };
  }
}
