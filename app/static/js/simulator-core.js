(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.CBLogic = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function bit(value, label = 'bit') {
    if (value !== 0 && value !== 1) throw new RangeError(`${label} must be 0 or 1`);
    return value;
  }

  function address4(value) {
    if (typeof value === 'string' && /^[01]{2}$/.test(value)) value = parseInt(value, 2);
    if (!Number.isInteger(value) || value < 0 || value > 3) {
      throw new RangeError('select must be a two-bit binary string or integer 0..3');
    }
    return value;
  }

  function gate(name, a, b = 0) {
    a = bit(a, 'A');
    b = bit(b, 'B');
    switch (String(name).toUpperCase()) {
      case 'AND': return a & b;
      case 'OR': return a | b;
      case 'NOT': return 1 - a;
      case 'NAND': return 1 - (a & b);
      case 'NOR': return 1 - (a | b);
      case 'XOR': return a ^ b;
      case 'XNOR': return 1 - (a ^ b);
      default: throw new RangeError('Unsupported logic gate');
    }
  }

  function halfAdder(a, b) {
    a = bit(a, 'A');
    b = bit(b, 'B');
    return { sum: a ^ b, carry: a & b };
  }

  function fullAdder(a, b, cin) {
    a = bit(a, 'A');
    b = bit(b, 'B');
    cin = bit(cin, 'Cin');
    return {
      sum: a ^ b ^ cin,
      cout: (a & b) | (a & cin) | (b & cin),
    };
  }

  function mux4(data, select) {
    if (!Array.isArray(data) || data.length !== 4) throw new RangeError('MUX requires four data inputs');
    const checked = data.map((value, i) => bit(value, `D${i}`));
    return checked[address4(select)];
  }

  function demux1to4(input, select, enabled = 1) {
    input = bit(input, 'D');
    enabled = bit(enabled, 'Enable');
    const selected = address4(select);
    return [0, 1, 2, 3].map(i => enabled && i === selected ? input : 0);
  }

  function encode4to2(inputs) {
    if (!Array.isArray(inputs) || inputs.length !== 4) throw new RangeError('Encoder requires I0..I3');
    const checked = inputs.map((value, i) => bit(value, `I${i}`));
    const active = checked.flatMap((value, i) => value ? [i] : []);
    if (active.length !== 1) {
      return {
        valid: false,
        code: null,
        reason: active.length ? 'Multiple inputs are active; a simple encoder is undefined.' : 'No input is active; a simple encoder has no code.',
      };
    }
    const index = active[0];
    return { valid: true, index, code: [(index >> 1) & 1, index & 1], reason: '' };
  }

  function decode2to4(select, enabled = 1) {
    const address = address4(select);
    enabled = bit(enabled, 'Enable');
    return [0, 1, 2, 3].map(i => enabled && i === address ? 1 : 0);
  }

  function flipFlopNext(type, q, u, v = 0) {
    q = bit(q, 'Q');
    u = bit(u, 'input 1');
    v = bit(v, 'input 2');
    type = String(type).toUpperCase();
    if (type === 'SR') {
      if (u && v) return { valid: false, nextQ: null, reason: 'S=R=1 is invalid for this active-high SR model; Q is unchanged.' };
      return { valid: true, nextQ: u ? 1 : v ? 0 : q, reason: u ? 'Set' : v ? 'Reset' : 'Hold' };
    }
    if (type === 'JK') return { valid: true, nextQ: u ? (v ? 1 - q : 1) : (v ? 0 : q), reason: u && v ? 'Toggle' : u ? 'Set' : v ? 'Reset' : 'Hold' };
    if (type === 'D') return { valid: true, nextQ: u, reason: 'Capture D' };
    if (type === 'T') return { valid: true, nextQ: u ? 1 - q : q, reason: u ? 'Toggle' : 'Hold' };
    throw new RangeError('Unsupported flip-flop type');
  }

  function counterStep(state, { reset = false, enable = true, width = 4 } = {}) {
    if (!Number.isInteger(width) || width < 1 || width > 16) throw new RangeError('Counter width must be 1..16');
    const limit = 2 ** width;
    if (!Number.isInteger(state) || state < 0 || state >= limit) throw new RangeError('Counter state is out of range');
    if (reset) return 0;
    if (!enable) return state;
    return (state + 1) % limit;
  }

  function shiftRegisterStep(bits, serial = 1) {
    if (!Array.isArray(bits) || bits.length < 1) throw new RangeError('Register requires at least one bit');
    const checked = bits.map((value, i) => bit(value, `Q${i}`));
    serial = bit(serial, 'serial input');
    return [serial, ...checked.slice(0, -1)];
  }

  return Object.freeze({
    gate, halfAdder, fullAdder, mux4, demux1to4, encode4to2, decode2to4,
    flipFlopNext, counterStep, shiftRegisterStep,
  });
}));
