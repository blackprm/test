export class AdService {
  constructor(platform, { mockEnabled = true } = {}) {
    this.platform = platform;
    this.mockEnabled = mockEnabled;
  }

  showRewardAd(placement) {
    if (this.mockEnabled) return Promise.resolve({ rewarded: true, placement, mock: true });
    return Promise.resolve({ rewarded: false, placement, mock: false });
  }
}
