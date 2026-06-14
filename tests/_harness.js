const tests = [];

function format(value) {
  try {
    return JSON.stringify(value);
  } catch (_error) {
    return String(value);
  }
}

function isObject(value) {
  return value !== null && typeof value === 'object';
}

function isDeepEqual(actual, expected) {
  if (Object.is(actual, expected)) return true;
  if (Array.isArray(actual) || Array.isArray(expected)) {
    if (!Array.isArray(actual) || !Array.isArray(expected) || actual.length !== expected.length) return false;
    return actual.every((value, index) => isDeepEqual(value, expected[index]));
  }
  if (!isObject(actual) || !isObject(expected)) return false;
  const actualKeys = Object.keys(actual);
  const expectedKeys = Object.keys(expected);
  if (actualKeys.length !== expectedKeys.length) return false;
  return expectedKeys.every((key) => Object.prototype.hasOwnProperty.call(actual, key) && isDeepEqual(actual[key], expected[key]));
}

export function assert(value, message = 'Expected value to be truthy') {
  if (!value) throw new Error(message);
}

assert.equal = (actual, expected, message = '') => {
  if (!Object.is(actual, expected)) {
    throw new Error(message || `Expected ${format(actual)} to equal ${format(expected)}`);
  }
};

assert.deepEqual = (actual, expected, message = '') => {
  if (!isDeepEqual(actual, expected)) {
    throw new Error(message || `Expected ${format(actual)} to deeply equal ${format(expected)}`);
  }
};

export function test(name, fn) {
  tests.push({ name, fn });
}

export async function runTests() {
  let failed = 0;
  for (const item of tests) {
    try {
      await item.fn();
      console.log(`ok - ${item.name}`);
    } catch (error) {
      failed += 1;
      console.error(`not ok - ${item.name}`);
      console.error(error && error.stack ? error.stack : error);
    }
  }
  if (failed > 0) throw new Error(`${failed} test(s) failed`);
  console.log(`${tests.length} test(s) passed`);
}
