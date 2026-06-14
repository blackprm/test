import { PlatformService } from './services/PlatformService.js';
import { StorageService } from './services/StorageService.js';
import { Game } from './core/Game.js';
import { Input } from './core/Input.js';
import { Renderer } from './core/Renderer.js';
import { FarmScene } from './scenes/FarmScene.js';
import { StealScene } from './scenes/StealScene.js';
import { ResultScene } from './scenes/ResultScene.js';

const platform = new PlatformService();
const renderer = new Renderer(platform);
const input = new Input(platform);
const storage = new StorageService(platform);
const game = new Game({ platform, renderer, input, storage });

game.registerScene('farm', new FarmScene(game));
game.registerScene('steal', new StealScene(game));
game.registerScene('result', new ResultScene(game));
game.setScene('farm');
game.start();
