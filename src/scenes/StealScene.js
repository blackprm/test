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
    const optionW = (renderer.width - margin * 2 - 16) / 3;
    this.targets.forEach((target, targetIndex) => {
      OPTIONS.forEach((option, optionIndex) => {
        const x = margin + optionIndex * (optionW + 8);
        const y = 116 + targetIndex * rowH + 54;
        input.addTapZone(`steal-${targetIndex}-${option.id}`, x, y, optionW, 48, () => this.trySteal(target, option));
      });
    });
  }

  trySteal(target, option) {
    const risk = Math.min(0.9, target.risk + option.risk - this.game.state.petLevel * 0.01);
    const success = Math.random() > risk;
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
