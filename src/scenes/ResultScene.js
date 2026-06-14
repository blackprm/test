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
    if (this.result.success && this.game.shareService) {
      input.addTapZone('share-result', 24, renderer.height - 166, renderer.width - 48, 48, () => this.shareResult());
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

  shareResult() {
    const message = this.game.shareService.buildStealMessage(this.result);
    this.game.shareService.share(message);
  }

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
    if (this.result.success && this.game.shareService) {
      renderer.roundRect(24, renderer.height - 166, renderer.width - 48, 48, 8, '#eb5e55');
      renderer.text('分享偷菜战报', renderer.width / 2, renderer.height - 142, 17, '#ffffff', 'center');
    }
    renderer.roundRect(24, renderer.height - 104, renderer.width - 48, 48, 8, '#3a86ff');
    renderer.text('回到我的摊位', renderer.width / 2, renderer.height - 80, 17, '#ffffff', 'center');
  }
}
