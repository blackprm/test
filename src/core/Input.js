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
