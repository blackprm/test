export class ShareService {
  constructor(platform) {
    this.platform = platform;
  }

  buildStealMessage(result) {
    return `我在夜市灵田偷到${result.targetName}的${result.optionLabel}，金币+${result.reward}，基因+${result.gems}！`;
  }

  share(message) {
    if (this.platform && this.platform.shareAppMessage) {
      this.platform.shareAppMessage({ title: message });
      return { shared: true, message };
    }
    return { shared: false, message };
  }
}
