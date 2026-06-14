import './ad-service.test.js';
import './economy.test.js';
import './farm-scene.test.js';
import './farm-state.test.js';
import './game.test.js';
import './input.test.js';
import './platform-service.test.js';
import './result-scene.test.js';
import './share-service.test.js';
import './steal-scene.test.js';
import './storage-service.test.js';
import { runTests } from './_harness.js';

runTests().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  throw error;
});
