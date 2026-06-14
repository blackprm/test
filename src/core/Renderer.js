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
    this.images = new Map();
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
}
