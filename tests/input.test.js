import { assert, test } from './_harness.js';
import { Input } from '../src/core/Input.js';

test('Input dispatches tap to the first matching zone', () => {
  let touchHandler = null;
  const input = new Input({
    onTouchStart(handler) {
      touchHandler = handler;
    },
  });
  const tapped = [];

  input.addTapZone('left', 0, 0, 100, 100, () => tapped.push('left'));
  input.addTapZone('right', 120, 0, 100, 100, () => tapped.push('right'));
  touchHandler({ touches: [{ clientX: 20, clientY: 40 }] });

  assert.deepEqual(tapped, ['left']);
});

test('Input clear removes all tap zones', () => {
  let touchHandler = null;
  const input = new Input({
    onTouchStart(handler) {
      touchHandler = handler;
    },
  });
  let count = 0;

  input.addTapZone('button', 0, 0, 100, 100, () => count++);
  input.clear();
  touchHandler({ touches: [{ clientX: 20, clientY: 40 }] });

  assert.equal(count, 0);
});
