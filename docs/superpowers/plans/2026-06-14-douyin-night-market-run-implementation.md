# Douyin Night Market Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `/Users/bytedance/miniprograms/测试` from the Douyin blank native mini-game template into a playable Canvas 2D MVP for 《夜市灵田：偷到就跑》.

**Architecture:** Keep the project native and engine-free. `game.js` becomes a tiny boot file, `src/main.js` starts the game, `src/core` owns loop/input/rendering, `src/scenes` owns farm/steal/result screens, `src/services` wraps Douyin APIs and local storage, and `src/data` owns economy configuration.

**Tech Stack:** 抖音小游戏 native project, JavaScript ES modules, Canvas 2D, `tt` platform API with browser-safe mocks for local reasoning, generated PNG assets.

---

## Project Facts

Real mini-game project path:

`/Users/bytedance/miniprograms/测试`

Current files:

- `/Users/bytedance/miniprograms/测试/game.js`
- `/Users/bytedance/miniprograms/测试/game.json`
- `/Users/bytedance/miniprograms/测试/project.config.json`
- `/Users/bytedance/miniprograms/测试/icon.png`

Current `project.config.json`:

- `appid`: `tt71e0075def84afb302`
- `projectname`: `测试`
- `douyinProjectType`: `native`

Version-control note:

This mini-game path is outside `/Users/bytedance/Documents/游戏`, the GitHub-tracked planning repo. During implementation, either initialize git in `/Users/bytedance/miniprograms/测试`, or sync the project into `/Users/bytedance/Documents/游戏/douyin-night-market-run` before pushing to GitHub. Do not silently lose source history.

## File Structure

Create this structure under `/Users/bytedance/miniprograms/测试`:

```text
game.js
game.json
project.config.json
icon.png
assets/
  generated/
src/
  main.js
  core/
    Game.js
    Input.js
    Renderer.js
    Scene.js
  data/
    config.js
    npcBases.js
  scenes/
    FarmScene.js
    StealScene.js
    ResultScene.js
  services/
    AdService.js
    PlatformService.js
    ShareService.js
    StorageService.js
  systems/
    economy.js
    farmState.js
```

## Task 1: Restructure Boot and Platform Layer

**Files:**
- Modify: `/Users/bytedance/miniprograms/测试/game.js`
- Create: `/Users/bytedance/miniprograms/测试/src/main.js`
- Create: `/Users/bytedance/miniprograms/测试/src/services/PlatformService.js`
- Create: `/Users/bytedance/miniprograms/测试/src/core/Renderer.js`
- Create: `/Users/bytedance/miniprograms/测试/src/core/Input.js`
- Create: `/Users/bytedance/miniprograms/测试/src/core/Scene.js`

- [ ] **Step 1: Create directories**

Run:

```bash
mkdir -p /Users/bytedance/miniprograms/测试/src/{core,data,scenes,services,systems} /Users/bytedance/miniprograms/测试/assets/generated
```

Expected: directories exist.

- [ ] **Step 2: Replace `game.js` with boot file**

Set `/Users/bytedance/miniprograms/测试/game.js` to:

```js
import './src/main.js';
```

Expected: the native project still starts through `game.js`.

- [ ] **Step 3: Add platform wrapper**

Create `/Users/bytedance/miniprograms/测试/src/services/PlatformService.js`:

```js
export class PlatformService {
  constructor(runtime = globalThis.tt) {
    this.runtime = runtime || null;
  }

  getSystemInfo() {
    if (this.runtime && this.runtime.getSystemInfoSync) {
      return this.runtime.getSystemInfoSync();
    }
    return { windowWidth: 390, windowHeight: 844, pixelRatio: 1 };
  }

  createCanvas() {
    if (this.runtime && this.runtime.createCanvas) {
      return this.runtime.createCanvas();
    }
    if (typeof document !== 'undefined') {
      const canvas = document.createElement('canvas');
      document.body.appendChild(canvas);
      return canvas;
    }
    throw new Error('Canvas runtime unavailable');
  }

  createImage() {
    if (this.runtime && this.runtime.createImage) return this.runtime.createImage();
    if (typeof Image !== 'undefined') return new Image();
    return null;
  }

  onTouchStart(handler) {
    if (this.runtime && this.runtime.onTouchStart) this.runtime.onTouchStart(handler);
  }

  onTouchMove(handler) {
    if (this.runtime && this.runtime.onTouchMove) this.runtime.onTouchMove(handler);
  }

  onTouchEnd(handler) {
    if (this.runtime && this.runtime.onTouchEnd) this.runtime.onTouchEnd(handler);
  }

  requestAnimationFrame(handler) {
    if (typeof requestAnimationFrame !== 'undefined') return requestAnimationFrame(handler);
    return setTimeout(() => handler(Date.now()), 16);
  }

  setStorageSync(key, value) {
    if (this.runtime && this.runtime.setStorageSync) return this.runtime.setStorageSync(key, value);
    if (typeof localStorage !== 'undefined') localStorage.setItem(key, JSON.stringify(value));
  }

  getStorageSync(key) {
    if (this.runtime && this.runtime.getStorageSync) return this.runtime.getStorageSync(key);
    if (typeof localStorage !== 'undefined') {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    }
    return null;
  }
}
```

- [ ] **Step 4: Add renderer**

Create `/Users/bytedance/miniprograms/测试/src/core/Renderer.js`:

```js
export class Renderer {
  constructor(platform) {
    this.platform = platform;
    this.info = platform.getSystemInfo();
    this.canvas = platform.createCanvas();
    this.canvas.width = this.info.windowWidth;
    this.canvas.height = this.info.windowHeight;
    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width;
    this.height = this.canvas.height;
  }

  clear(color = '#172033') {
    this.ctx.fillStyle = color;
    this.ctx.fillRect(0, 0, this.width, this.height);
  }

  text(value, x, y, size = 20, color = '#ffffff', align = 'left') {
    this.ctx.fillStyle = color;
    this.ctx.font = `${size}px sans-serif`;
    this.ctx.textAlign = align;
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(value, x, y);
  }

  roundRect(x, y, width, height, radius, color) {
    const r = Math.min(radius, width / 2, height / 2);
    const ctx = this.ctx;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + width, y, x + width, y + height, r);
    ctx.arcTo(x + width, y + height, x, y + height, r);
    ctx.arcTo(x, y + height, x, y, r);
    ctx.arcTo(x, y, x + width, y, r);
    ctx.closePath();
    ctx.fill();
  }
}
```

- [ ] **Step 5: Add input router**

Create `/Users/bytedance/miniprograms/测试/src/core/Input.js`:

```js
export class Input {
  constructor(platform) {
    this.handlers = [];
    platform.onTouchStart((event) => this.dispatch(event));
  }

  addTapZone(id, x, y, width, height, onTap) {
    this.handlers.push({ id, x, y, width, height, onTap });
  }

  clear() {
    this.handlers = [];
  }

  dispatch(event) {
    const touch = event.touches && event.touches[0];
    if (!touch) return;
    const x = touch.clientX;
    const y = touch.clientY;
    for (const handler of this.handlers) {
      const hit = x >= handler.x && x <= handler.x + handler.width && y >= handler.y && y <= handler.y + handler.height;
      if (hit) {
        handler.onTap();
        return;
      }
    }
  }
}
```

- [ ] **Step 6: Add scene base**

Create `/Users/bytedance/miniprograms/测试/src/core/Scene.js`:

```js
export class Scene {
  constructor(game) {
    this.game = game;
  }

  enter() {}

  exit() {}

  update(_dt) {}

  render(_renderer) {}
}
```

## Task 2: Add Config, Storage, and Economy

**Files:**
- Create: `/Users/bytedance/miniprograms/测试/src/data/config.js`
- Create: `/Users/bytedance/miniprograms/测试/src/data/npcBases.js`
- Create: `/Users/bytedance/miniprograms/测试/src/services/StorageService.js`
- Create: `/Users/bytedance/miniprograms/测试/src/systems/economy.js`
- Create: `/Users/bytedance/miniprograms/测试/src/systems/farmState.js`

- [ ] **Step 1: Add game config**

Create `/Users/bytedance/miniprograms/测试/src/data/config.js`:

```js
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
```

- [ ] **Step 2: Add NPC bases**

Create `/Users/bytedance/miniprograms/测试/src/data/npcBases.js`:

```js
export const NPC_BASES = [
  { name: '灯笼摊主', risk: 0.15, reward: 70 },
  { name: '星瓜富商', risk: 0.35, reward: 160 },
  { name: '暴走菜贩', risk: 0.55, reward: 320 },
];
```

- [ ] **Step 3: Add storage**

Create `/Users/bytedance/miniprograms/测试/src/services/StorageService.js`:

```js
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
```

- [ ] **Step 4: Add economy helpers**

Create `/Users/bytedance/miniprograms/测试/src/systems/economy.js`:

```js
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
```

- [ ] **Step 5: Add farm state actions**

Create `/Users/bytedance/miniprograms/测试/src/systems/farmState.js`:

```js
import { getSeed, isMature, nowSeconds, rollMutation, cropValue, upgradeCost } from './economy.js';

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

export function harvestPlot(state, plotIndex) {
  const plot = state.plots[plotIndex];
  if (!plot || !isMature(plot) || plot.harvested) return 0;
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
```

## Task 3: Add Game Loop and Farm Scene

**Files:**
- Create: `/Users/bytedance/miniprograms/测试/src/core/Game.js`
- Create: `/Users/bytedance/miniprograms/测试/src/scenes/FarmScene.js`
- Modify: `/Users/bytedance/miniprograms/测试/src/main.js`

- [ ] **Step 1: Add game controller**

Create `/Users/bytedance/miniprograms/测试/src/core/Game.js`:

```js
export class Game {
  constructor({ platform, renderer, input, storage, adService = null, shareService = null }) {
    this.platform = platform;
    this.renderer = renderer;
    this.input = input;
    this.storage = storage;
    this.adService = adService;
    this.shareService = shareService;
    this.state = storage.load();
    this.scenes = new Map();
    this.currentScene = null;
    this.currentSceneName = '';
    this.lastFrameAt = Date.now();
    this.running = false;
  }

  registerScene(name, scene) {
    this.scenes.set(name, scene);
  }

  setScene(name, params = {}) {
    const next = this.scenes.get(name);
    if (!next) throw new Error(`Scene not registered: ${name}`);
    if (this.currentScene) this.currentScene.exit();
    this.input.clear();
    this.currentSceneName = name;
    this.currentScene = next;
    this.currentScene.enter(params);
  }

  save() {
    this.storage.save(this.state);
  }

  start() {
    if (this.running) return;
    this.running = true;
    const tick = () => {
      const now = Date.now();
      const dt = Math.min(0.1, (now - this.lastFrameAt) / 1000);
      this.lastFrameAt = now;
      if (this.currentScene) {
        this.currentScene.update(dt);
        this.currentScene.render(this.renderer);
      }
      this.platform.requestAnimationFrame(tick);
    };
    tick();
  }
}
```

- [ ] **Step 2: Add farm scene**

Create `/Users/bytedance/miniprograms/测试/src/scenes/FarmScene.js`:

```js
import { Scene } from '../core/Scene.js';
import { SEEDS } from '../data/config.js';
import { cropValue, getMutation, getSeed, isMature, nowSeconds, upgradeCost } from '../systems/economy.js';
import { harvestPlot, plantSeed, upgradeStall } from '../systems/farmState.js';

export class FarmScene extends Scene {
  enter() {
    this.message = '点田格种菜，成熟后收获。';
    this.bindControls();
  }

  bindControls() {
    const { input, renderer } = this.game;
    input.clear();
    const margin = 22;
    const cardW = (renderer.width - margin * 2 - 16) / 3;
    const cardH = 118;
    this.game.state.plots.forEach((_plot, index) => {
      const col = index % 3;
      const row = Math.floor(index / 3);
      const x = margin + col * (cardW + 8);
      const y = 178 + row * (cardH + 12);
      input.addTapZone(`plot-${index}`, x, y, cardW, cardH, () => this.tapPlot(index));
    });
    input.addTapZone('steal', margin, renderer.height - 160, renderer.width - margin * 2, 48, () => this.game.setScene('steal'));
    input.addTapZone('upgrade', margin, renderer.height - 100, renderer.width - margin * 2, 48, () => this.upgrade());
  }

  tapPlot(index) {
    const plot = this.game.state.plots[index];
    if (!plot.seedId) {
      const seedId = this.game.state.unlockedSeeds[0];
      const ok = plantSeed(this.game.state, index, seedId);
      this.message = ok ? `种下了${getSeed(seedId).name}` : '金币不足，先去收菜或偷菜。';
      this.game.save();
      this.bindControls();
      return;
    }
    if (isMature(plot)) {
      const value = harvestPlot(this.game.state, index);
      this.message = value > 0 ? `收获 ${value} 金币！` : '这块田还不能收。';
      this.game.save();
      this.bindControls();
      return;
    }
    const seed = getSeed(plot.seedId);
    const left = Math.max(0, seed.growSeconds - (nowSeconds() - plot.plantedAt));
    this.message = `${seed.name} 还需 ${left} 秒成熟。`;
  }

  upgrade() {
    const cost = upgradeCost(this.game.state.stallLevel);
    const ok = upgradeStall(this.game.state);
    this.message = ok ? '摊位升级，新增一块灵田！' : `升级需要 ${cost} 金币，最多 9 块田。`;
    this.game.save();
    this.bindControls();
  }

  update() {}

  render(renderer) {
    renderer.clear('#182235');
    renderer.text('夜市灵田：偷到就跑', 22, 38, 24, '#ffe6a3');
    renderer.text(`金币 ${this.game.state.gold}  基因 ${this.game.state.gems}`, 22, 72, 18, '#ffffff');
    renderer.text(`摊位 Lv.${this.game.state.stallLevel}  陷阱 ${this.game.state.traps}  守田宠物 Lv.${this.game.state.petLevel}`, 22, 100, 15, '#b9d2ff');
    renderer.text(this.message, 22, 132, 15, '#ffffff');

    const margin = 22;
    const cardW = (renderer.width - margin * 2 - 16) / 3;
    const cardH = 118;
    this.game.state.plots.forEach((plot, index) => {
      const col = index % 3;
      const row = Math.floor(index / 3);
      const x = margin + col * (cardW + 8);
      const y = 178 + row * (cardH + 12);
      renderer.roundRect(x, y, cardW, cardH, 8, '#263855');
      if (!plot.seedId) {
        renderer.text('空田', x + cardW / 2, y + 42, 18, '#c7d8ff', 'center');
        renderer.text('点击种植', x + cardW / 2, y + 76, 13, '#8fa8d8', 'center');
        return;
      }
      const seed = getSeed(plot.seedId);
      const mutation = getMutation(plot.mutationId);
      const mature = isMature(plot);
      const value = cropValue(plot.seedId, plot.mutationId);
      renderer.text(seed.name, x + cardW / 2, y + 30, 16, '#ffffff', 'center');
      renderer.text(mutation.name, x + cardW / 2, y + 56, 13, mutation.id === 'normal' ? '#9bb2d8' : '#ffd166', 'center');
      renderer.text(mature ? `可收 ${value}` : '成长中', x + cardW / 2, y + 86, 13, mature ? '#66f0a6' : '#8fa8d8', 'center');
    });

    renderer.roundRect(22, renderer.height - 160, renderer.width - 44, 48, 8, '#eb5e55');
    renderer.text('偷菜冲刺 30 秒', renderer.width / 2, renderer.height - 136, 18, '#ffffff', 'center');
    renderer.roundRect(22, renderer.height - 100, renderer.width - 44, 48, 8, '#3a86ff');
    renderer.text(`升级摊位 ${upgradeCost(this.game.state.stallLevel)} 金币`, renderer.width / 2, renderer.height - 76, 17, '#ffffff', 'center');
  }
}
```

- [ ] **Step 3: Add main boot**

Create `/Users/bytedance/miniprograms/测试/src/main.js`:

```js
import { Game } from './core/Game.js';
import { Input } from './core/Input.js';
import { Renderer } from './core/Renderer.js';
import { PlatformService } from './services/PlatformService.js';
import { StorageService } from './services/StorageService.js';
import { FarmScene } from './scenes/FarmScene.js';

const platform = new PlatformService();
const renderer = new Renderer(platform);
const input = new Input(platform);
const storage = new StorageService(platform);
const game = new Game({ platform, renderer, input, storage });

game.registerScene('farm', new FarmScene(game));
game.setScene('farm');
game.start();
```

- [ ] **Step 4: Verify in Douyin Developer Tool**

Open `/Users/bytedance/miniprograms/测试` in 抖音开发者工具.

Expected:

- No import error.
- A farm screen replaces the blank template.
- Tapping plot areas plants or harvests.
- Gold changes persist after recompile.

## Task 4: Add Steal and Result Scenes

**Files:**
- Create: `/Users/bytedance/miniprograms/测试/src/scenes/StealScene.js`
- Create: `/Users/bytedance/miniprograms/测试/src/scenes/ResultScene.js`
- Modify: `/Users/bytedance/miniprograms/测试/src/main.js`

- [ ] **Step 1: Add steal scene**

Create `/Users/bytedance/miniprograms/测试/src/scenes/StealScene.js`:

```js
import { Scene } from '../core/Scene.js';
import { NPC_BASES } from '../data/npcBases.js';

const OPTIONS = [
  { id: 'crop', label: '普通作物', risk: 0.05, rewardMultiplier: 0.7, gems: 0 },
  { id: 'mutant', label: '变异作物', risk: 0.22, rewardMultiplier: 1.4, gems: 1 },
  { id: 'chest', label: '夜市宝箱', risk: 0.42, rewardMultiplier: 2.4, gems: 2 },
];

export class StealScene extends Scene {
  enter() {
    this.startedAt = Date.now();
    this.targets = NPC_BASES.slice(0, 3);
    this.bindControls();
  }

  bindControls() {
    const { input, renderer } = this.game;
    input.clear();
    const margin = 18;
    const rowH = 132;
    this.targets.forEach((target, targetIndex) => {
      OPTIONS.forEach((option, optionIndex) => {
        const x = margin + optionIndex * ((renderer.width - margin * 2 - 16) / 3 + 8);
        const y = 116 + targetIndex * rowH + 54;
        const w = (renderer.width - margin * 2 - 16) / 3;
        input.addTapZone(`steal-${targetIndex}-${option.id}`, x, y, w, 48, () => this.trySteal(target, option));
      });
    });
  }

  trySteal(target, option) {
    const risk = Math.min(0.9, target.risk + option.risk - this.game.state.petLevel * 0.01);
    const roll = Math.random();
    const success = roll > risk;
    const reward = success ? Math.floor(target.reward * option.rewardMultiplier) : 0;
    const gems = success ? option.gems : 0;
    if (success) {
      this.game.state.gold += reward;
      this.game.state.gems += gems;
      this.game.save();
    }
    this.game.setScene('result', {
      success,
      reward,
      gems,
      targetName: target.name,
      optionLabel: option.label,
      canRetry: !success,
    });
  }

  update() {
    const left = 30 - Math.floor((Date.now() - this.startedAt) / 1000);
    if (left <= 0) {
      this.game.setScene('result', {
        success: false,
        reward: 0,
        gems: 0,
        targetName: '夜市',
        optionLabel: '超时',
        canRetry: true,
      });
    }
  }

  render(renderer) {
    const left = Math.max(0, 30 - Math.floor((Date.now() - this.startedAt) / 1000));
    renderer.clear('#201527');
    renderer.text('偷菜冲刺', 22, 38, 25, '#ffe6a3');
    renderer.text(`剩余 ${left} 秒：选一个目标偷到就跑`, 22, 72, 16, '#ffffff');
    const margin = 18;
    const rowH = 132;
    const optionW = (renderer.width - margin * 2 - 16) / 3;
    this.targets.forEach((target, targetIndex) => {
      const baseY = 116 + targetIndex * rowH;
      renderer.roundRect(margin, baseY, renderer.width - margin * 2, 112, 8, '#342244');
      renderer.text(target.name, margin + 14, baseY + 24, 17, '#ffffff');
      renderer.text(`基础奖励 ${target.reward}`, renderer.width - margin - 14, baseY + 24, 14, '#ffd166', 'right');
      OPTIONS.forEach((option, optionIndex) => {
        const x = margin + optionIndex * (optionW + 8);
        const y = baseY + 54;
        renderer.roundRect(x, y, optionW, 48, 8, option.id === 'chest' ? '#b85cff' : '#465a7d');
        renderer.text(option.label, x + optionW / 2, y + 24, 12, '#ffffff', 'center');
      });
    });
  }
}
```

- [ ] **Step 2: Add result scene**

Create `/Users/bytedance/miniprograms/测试/src/scenes/ResultScene.js`:

```js
import { Scene } from '../core/Scene.js';

export class ResultScene extends Scene {
  enter(params) {
    this.result = params;
    this.bindControls();
  }

  bindControls() {
    const { input, renderer } = this.game;
    input.clear();
    input.addTapZone('back-farm', 24, renderer.height - 104, renderer.width - 48, 48, () => this.game.setScene('farm'));
    if (this.result.canRetry) {
      input.addTapZone('retry-ad', 24, renderer.height - 166, renderer.width - 48, 48, () => this.retryWithAd());
    }
  }

  async retryWithAd() {
    if (!this.game.adService) {
      this.game.setScene('steal');
      return;
    }
    const result = await this.game.adService.showRewardAd('retrySteal');
    if (result.rewarded) this.game.setScene('steal');
  }

  update() {}

  render(renderer) {
    renderer.clear(this.result.success ? '#102b24' : '#2b1620');
    const title = this.result.success ? '偷到了！' : '翻车了';
    renderer.text(title, renderer.width / 2, 110, 34, '#ffe6a3', 'center');
    renderer.text(`${this.result.targetName} - ${this.result.optionLabel}`, renderer.width / 2, 158, 18, '#ffffff', 'center');
    if (this.result.success) {
      renderer.text(`金币 +${this.result.reward}`, renderer.width / 2, 220, 26, '#66f0a6', 'center');
      renderer.text(`基因碎片 +${this.result.gems}`, renderer.width / 2, 260, 20, '#b9d2ff', 'center');
      renderer.text('我偷到稀有作物就跑了！', renderer.width / 2, 330, 18, '#ffd166', 'center');
    } else {
      renderer.text('守田宠物盯上了你。', renderer.width / 2, 220, 22, '#ffffff', 'center');
      renderer.text('看广告可以再偷一次。', renderer.width / 2, 260, 18, '#ffd166', 'center');
    }
    if (this.result.canRetry) {
      renderer.roundRect(24, renderer.height - 166, renderer.width - 48, 48, 8, '#eb5e55');
      renderer.text('看广告再偷一次', renderer.width / 2, renderer.height - 142, 17, '#ffffff', 'center');
    }
    renderer.roundRect(24, renderer.height - 104, renderer.width - 48, 48, 8, '#3a86ff');
    renderer.text('回到我的摊位', renderer.width / 2, renderer.height - 80, 17, '#ffffff', 'center');
  }
}
```

- [ ] **Step 3: Register scenes**

Update `main.js` to import and register:

```js
import { StealScene } from './scenes/StealScene.js';
import { ResultScene } from './scenes/ResultScene.js';

game.registerScene('steal', new StealScene(game));
game.registerScene('result', new ResultScene(game));
```

- [ ] **Step 4: Verify steal loop**

Expected:

- Farm screen can enter steal screen.
- Steal screen resolves to result screen.
- Result screen returns to farm.
- Gold and gene fragments persist after successful steal.

## Task 5: Add Ad and Share Service Mocks

**Files:**
- Create: `/Users/bytedance/miniprograms/测试/src/services/AdService.js`
- Create: `/Users/bytedance/miniprograms/测试/src/services/ShareService.js`
- Modify: `/Users/bytedance/miniprograms/测试/src/main.js`

- [ ] **Step 1: Add ad service**

Create `AdService.js`:

```js
export class AdService {
  constructor(platform) {
    this.platform = platform;
    this.mockEnabled = true;
  }

  showRewardAd(_placement) {
    if (this.mockEnabled) return Promise.resolve({ rewarded: true });
    return Promise.resolve({ rewarded: false });
  }
}
```

- [ ] **Step 2: Add share service**

Create `ShareService.js`:

```js
export class ShareService {
  constructor(platform) {
    this.platform = platform;
  }

  share(message) {
    console.log('[share]', message);
  }
}
```

- [ ] **Step 3: Wire services**

Update `/Users/bytedance/miniprograms/测试/src/main.js` to:

```js
import { Game } from './core/Game.js';
import { Input } from './core/Input.js';
import { Renderer } from './core/Renderer.js';
import { PlatformService } from './services/PlatformService.js';
import { StorageService } from './services/StorageService.js';
import { AdService } from './services/AdService.js';
import { ShareService } from './services/ShareService.js';
import { FarmScene } from './scenes/FarmScene.js';
import { StealScene } from './scenes/StealScene.js';
import { ResultScene } from './scenes/ResultScene.js';

const platform = new PlatformService();
const renderer = new Renderer(platform);
const input = new Input(platform);
const storage = new StorageService(platform);
const adService = new AdService(platform);
const shareService = new ShareService(platform);
const game = new Game({ platform, renderer, input, storage, adService, shareService });

game.registerScene('farm', new FarmScene(game));
game.registerScene('steal', new StealScene(game));
game.registerScene('result', new ResultScene(game));
game.setScene('farm');
game.start();
```

- [ ] **Step 4: Verify retry ad path**

Expected:

- Failed steal shows retry button.
- Retry button calls `AdService.showRewardAd('retrySteal')`.
- Mock resolves as rewarded and returns player to another steal attempt.

## Task 6: Add Generated Art Pass

**Files:**
- Create: `/Users/bytedance/miniprograms/测试/assets/generated/`
- Modify: scenes to load generated images after they exist.

- [ ] **Step 1: Generate first asset set**

Generate these PNG assets:

- `icon-carrot.png`: cute glowing fantasy carrot, transparent background.
- `icon-mushroom.png`: lantern mushroom, transparent background.
- `icon-star-melon.png`: star-pattern melon, transparent background.
- `icon-pet.png`: tiny lantern spirit guard pet, transparent background.
- `night-market-bg.png`: cozy vertical night market farm stall background.

- [ ] **Step 2: Add image loader**

Update `/Users/bytedance/miniprograms/测试/src/core/Renderer.js` so the constructor initializes an image cache:

```js
    this.images = new Map();
```

Add these methods inside the `Renderer` class:

```js
  loadImage(id, src) {
    if (this.images.has(id)) return;
    const image = this.platform.createImage();
    if (!image) return;
    this.images.set(id, { image, loaded: false });
    image.onload = () => {
      const cached = this.images.get(id);
      if (cached) cached.loaded = true;
    };
    image.src = src;
  }

  drawImage(id, x, y, width, height) {
    const cached = this.images.get(id);
    if (!cached || !cached.loaded) return false;
    this.ctx.drawImage(cached.image, x, y, width, height);
    return true;
  }
```

- [ ] **Step 3: Replace primitive crop visuals**

In `/Users/bytedance/miniprograms/测试/src/scenes/FarmScene.js`, add this helper method inside `FarmScene`:

```js
  cropIconId(seedId) {
    if (seedId === 'carrot') return 'icon-carrot';
    if (seedId === 'mushroom') return 'icon-mushroom';
    if (seedId === 'starMelon') return 'icon-star-melon';
    return '';
  }
```

At the start of `render(renderer)`, after the stat text and before drawing plots, load the images:

```js
    renderer.loadImage('icon-carrot', 'assets/generated/icon-carrot.png');
    renderer.loadImage('icon-mushroom', 'assets/generated/icon-mushroom.png');
    renderer.loadImage('icon-star-melon', 'assets/generated/icon-star-melon.png');
```

Inside the non-empty plot rendering branch, before `renderer.text(seed.name, ...)`, add:

```js
      const iconDrawn = renderer.drawImage(this.cropIconId(plot.seedId), x + cardW / 2 - 18, y + 12, 36, 36);
      const nameY = iconDrawn ? y + 58 : y + 30;
```

Then replace:

```js
      renderer.text(seed.name, x + cardW / 2, y + 30, 16, '#ffffff', 'center');
```

with:

```js
      renderer.text(seed.name, x + cardW / 2, nameY, 16, '#ffffff', 'center');
```

In `/Users/bytedance/miniprograms/测试/src/scenes/StealScene.js`, add these image loads near the start of `render(renderer)`:

```js
    renderer.loadImage('icon-carrot', 'assets/generated/icon-carrot.png');
    renderer.loadImage('icon-mushroom', 'assets/generated/icon-mushroom.png');
    renderer.loadImage('icon-star-melon', 'assets/generated/icon-star-melon.png');
```

The first playable version may keep target buttons as text-only if icons are not loaded; `renderer.drawImage` returns `false` and the text remains readable.

- [ ] **Step 4: Verify visual fallback**

Expected:

- Game still runs if images fail to load.
- Icons appear when files are present.

## Task 7: Platform Readiness Checks

**Files:**
- Modify: `/Users/bytedance/miniprograms/测试/game.json`
- Create: `/Users/bytedance/miniprograms/测试/README.md`

- [ ] **Step 1: Keep portrait orientation**

Verify `game.json` contains:

```json
{
  "deviceOrientation": "portrait"
}
```

- [ ] **Step 2: Add runbook**

Create `README.md` with:

```md
# 夜市灵田：偷到就跑

抖音小游戏 native / 普通小游戏引擎项目。

## 打开方式

1. 打开抖音开发者工具。
2. 导入 `/Users/bytedance/miniprograms/测试`。
3. AppID: `tt71e0075def84afb302`。
4. 运行模拟器。

## 验收

- 进入后显示夜市灵田主界面。
- 可以种植、等待成熟、收获金币。
- 可以进入偷菜冲刺并结算。
- 激励视频当前为 mock，失败重试会直接成功。
```

- [ ] **Step 3: Verify developer tool**

Expected:

- Project opens as native mini-game.
- Console has no syntax/import errors.
- Basic loop is playable.

## Self-Review

Spec coverage:

- Native Canvas mini-game: Task 1 and Task 3.
- Three-minute farm loop: Task 2 and Task 3.
- Async steal sprint: Task 4.
- Reward ad priority: Task 5.
- Generated visual assets: Task 6.
- Douyin platform boundary: Task 7.

Future work outside this local-playable MVP:

- Real player snapshots: the first playable version uses NPC targets so the loop works before backend setup.
- Real rewarded video ad IDs: the first playable version uses `AdService` mock; real IDs are added after placement IDs exist in the Douyin backend.
- Side-bar revisit API: the first playable version records this as a platform integration step after the current account exposes the capability in developer tools.

Placeholder scan:

- The plan contains no `TBD` or `TODO` instructions.
- All paths point to `/Users/bytedance/miniprograms/测试`.
