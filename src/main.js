import { PlatformService } from './services/PlatformService.js';
import { Renderer } from './core/Renderer.js';

const platform = new PlatformService();
const renderer = new Renderer(platform);

renderer.clear('#182235');
renderer.text('夜市灵田：偷到就跑', 24, 80, 24, '#ffe6a3');
renderer.text('正在加载灵田...', 24, 120, 16, '#ffffff');
