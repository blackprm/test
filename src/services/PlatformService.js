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
