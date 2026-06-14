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
