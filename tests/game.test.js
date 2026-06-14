import { assert, test } from './_harness.js';
import { Game } from '../src/core/Game.js';

function createGame() {
  const calls = [];
  return {
    calls,
    game: new Game({
      platform: { requestAnimationFrame: () => {} },
      renderer: {},
      input: { clear: () => calls.push('clear') },
      storage: {
        load: () => ({ gold: 120 }),
        save: (state) => calls.push(['save', state.gold]),
      },
    }),
  };
}

test('Game setScene exits current scene, clears input, and enters next scene', () => {
  const { game, calls } = createGame();
  game.registerScene('a', { enter: () => calls.push('enter-a'), exit: () => calls.push('exit-a'), update: () => {}, render: () => {} });
  game.registerScene('b', { enter: (params) => calls.push(['enter-b', params.value]), exit: () => {}, update: () => {}, render: () => {} });

  game.setScene('a');
  game.setScene('b', { value: 7 });

  assert.deepEqual(calls, ['clear', 'enter-a', 'exit-a', 'clear', ['enter-b', 7]]);
  assert.equal(game.currentSceneName, 'b');
});

test('Game save delegates current state to storage', () => {
  const { game, calls } = createGame();

  game.state.gold = 333;
  game.save();

  assert.deepEqual(calls, [['save', 333]]);
});
