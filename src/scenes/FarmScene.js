import { Scene } from '../core/Scene.js';
import { cropValue, getMutation, getSeed, isMature, nowSeconds, upgradeCost } from '../systems/economy.js';
import { harvestPlot, plantSeed, upgradeStall } from '../systems/farmState.js';

const FARM_ASSETS = {
  background: 'assets/generated/night-market-bg.png',
  pet: 'assets/generated/icon-pet.png',
  seeds: {
    carrot: 'assets/generated/icon-carrot.png',
    mushroom: 'assets/generated/icon-mushroom.png',
    starMelon: 'assets/generated/icon-star-melon.png',
  },
};

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

  render(renderer) {
    renderer.clear('#182235');
    renderer.loadImage('night-market-bg', FARM_ASSETS.background);
    renderer.drawImage('night-market-bg', 0, 0, renderer.width, renderer.height);
    renderer.text('夜市灵田：偷到就跑', 22, 38, 24, '#ffe6a3');
    renderer.text(`金币 ${this.game.state.gold}  基因 ${this.game.state.gems}`, 22, 72, 18, '#ffffff');
    renderer.text(`摊位 Lv.${this.game.state.stallLevel}  陷阱 ${this.game.state.traps}  守田宠物 Lv.${this.game.state.petLevel}`, 22, 100, 15, '#b9d2ff');
    renderer.text(this.message, 22, 132, 15, '#ffffff');
    renderer.loadImage('pet-guard', FARM_ASSETS.pet);
    renderer.drawImage('pet-guard', renderer.width - 76, 28, 52, 52);

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
      const assetId = `seed-${plot.seedId}`;
      renderer.loadImage(assetId, FARM_ASSETS.seeds[plot.seedId]);
      renderer.drawImage(assetId, x + cardW / 2 - 28, y + 12, 56, 56);
      renderer.text(seed.name, x + cardW / 2, y + 76, 15, '#ffffff', 'center');
      renderer.text(mutation.name, x + cardW / 2, y + 96, 12, mutation.id === 'normal' ? '#9bb2d8' : '#ffd166', 'center');
      renderer.text(mature ? `可收 ${value}` : '成长中', x + cardW / 2, y + 112, 12, mature ? '#66f0a6' : '#8fa8d8', 'center');
    });

    renderer.roundRect(22, renderer.height - 160, renderer.width - 44, 48, 8, '#eb5e55');
    renderer.text('偷菜冲刺 30 秒', renderer.width / 2, renderer.height - 136, 18, '#ffffff', 'center');
    renderer.roundRect(22, renderer.height - 100, renderer.width - 44, 48, 8, '#3a86ff');
    renderer.text(`升级摊位 ${upgradeCost(this.game.state.stallLevel)} 金币`, renderer.width / 2, renderer.height - 76, 17, '#ffffff', 'center');
  }
}
