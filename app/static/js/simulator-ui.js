(function (root) {
  'use strict';

  const logic = root.CBLogic;
  const h = value => String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[char]));

  const purposeCopy = {
    gates: ['A logic gate applies a Boolean rule to binary inputs and returns a bit.', 'लॉजिक गेट द्विआधारी inputs पर Boolean नियम लगाकर output bit देता है।', 'लॉजिक गेट binary inputs पर Boolean नियम लगाकर एक output bit देता है।'],
    binary: ['Binary stores a value as bits weighted by powers of two.', 'द्विआधारी संख्या में हर bit का स्थान मान 2 की घात होता है।', 'द्विआधारी संख्या में हर bit का स्थान मान 2 की घात होता है।'],
    boolean: ['Boolean algebra rewrites logic expressions without changing their outputs.', 'Boolean algebra output बदले बिना logic expression को सरल करता है।', 'Boolean algebra output बदले बिना logic expression simplify karta hai.'],
    'half-adder': ['A Half Adder adds two one-bit inputs: XOR produces Sum and AND produces Carry.', 'Half Adder दो 1-bit inputs जोड़ता है: XOR से Sum और AND से Carry मिलता है।', 'Half Adder दो 1-bit inputs जोड़ता है: XOR से Sum और AND से Carry मिलता है।'],
    'full-adder': ['A Full Adder adds A, B and incoming carry Cin; its outputs are Sum and outgoing carry Cout.', 'Full Adder A, B और incoming carry Cin जोड़ता है; outputs Sum और Cout हैं।', 'Full Adder A, B और incoming carry Cin जोड़ता है; outputs Sum और outgoing carry Cout हैं।'],
    'mux-demux': ['A MUX routes one selected data input to Y; a DEMUX routes D to one selected output.', 'MUX चुने हुए data input को Y तक भेजता है; DEMUX, D को एक चुने हुए output तक route करता है।', 'MUX चुने हुए data input को Y तक भेजता है; DEMUX, D को एक चुने हुए output तक route करता है।'],
    'encoder-decoder': ['A simple 4:2 encoder maps one active input to a two-bit code; a 2:4 decoder reverses that mapping.', 'Simple 4:2 encoder एक active input को 2-bit code देता है; 2:4 decoder mapping उलटता है।', 'Simple 4:2 encoder एक active input को 2-bit code देता है; 2:4 decoder mapping उलटता है।'],
    'flip-flops': ['A flip-flop stores one bit; its input and active clock edge determine the next state.', 'Flip-flop एक bit store करता है; input और active clock edge अगली state तय करते हैं।', 'Flip-flop एक bit store करता है; input और active clock edge अगली state तय करते हैं।'],
    'counter-register': ['A modulo-16 counter advances through 16 states; a shift register moves stored bits one stage per clock.', 'Modulo-16 counter 16 states में चलता है; shift register हर clock पर bits को एक stage आगे बढ़ाता है।', 'Modulo-16 counter 16 states में चलता है; shift register हर clock पर bits को एक stage आगे बढ़ाता है।'],
  };

  const instructionOverrides = {
    'mux-demux': {
      en: 'Toggle MUX data and choose its S1/S0. Use the separate DEMUX D input and S1/S0 to route that input to one output.',
      hi: 'MUX के data inputs और S1/S0 बदलें। DEMUX के अलग D input और S1/S0 से input को एक चुने हुए output तक route करें।',
      hinglish: 'MUX data aur uske S1/S0 badlo. Separate DEMUX D input aur S1/S0 se input ko ek output tak route karo.',
    },
    'encoder-decoder': {
      en: 'Toggle encoder inputs: a simple encoder is defined only when exactly one input is active. Set the independent decoder address to select an output.',
      hi: 'Encoder inputs बदलें: simple encoder तभी defined है जब ठीक एक input active हो। Decoder का अलग address output चुनता है।',
      hinglish: 'Encoder inputs toggle karo: simple encoder tab defined hota hai jab exactly ek input active ho. Decoder ka separate address output choose karta hai.',
    },
    'counters-registers': {
      en: 'Clock / Step advances the modulo-16 counter; Reset returns it to 0000. The separate shift button moves the register right and inserts serial 1.',
      hi: 'Clock / Step modulo-16 counter को आगे बढ़ाता है; Reset उसे 0000 करता है। अलग shift button register को right-shift करके serial 1 डालता है।',
      hinglish: 'Clock / Step modulo-16 counter ko aage karta hai; Reset 0000 karta hai. Separate shift button register ko right shift karke serial 1 insert karta hai.',
    },
  };

  function localized(copy, locale) {
    return copy?.[locale === 'hi' ? 1 : locale === 'hinglish' ? 2 : 0] || copy?.[0] || '';
  }

  const bitButton = (key, label, initial = 0) =>
    `<button type="button" class="demo-bit" data-demo-toggle="${key}" aria-label="${h(label)}" aria-pressed="${initial ? 'true' : 'false'}">${initial}</button>`;

  function svgFigure(label, viewBox, contents) {
    return `<figure class="simulator-diagram" tabindex="0" role="group" aria-label="${h(label)}. Scroll horizontally if needed.">
      <svg viewBox="${viewBox}" role="img" aria-label="${h(label)}" focusable="false">${contents}</svg>
      <figcaption>Signal-flow schematic · live values also appear in the output below.</figcaption>
    </figure>`;
  }

  function diagram(kind) {
    const wire = '<path class="sim-wire" d="M72 77 H220 M72 137 H220 M345 107 H510"/>';
    switch (kind) {
      case 'gates':
        return svgFigure('Two binary inputs pass through the selected logic gate to output Y', '0 0 620 210', `
          <text class="sim-label" x="18" y="82" data-sim-value="a">A=0</text><text class="sim-label" x="18" y="142" data-sim-value="b">B=0</text>
          <path class="sim-wire" d="M78 77 H220 M78 137 H220 M375 107 H520"/>
          <rect class="sim-block" x="220" y="58" width="155" height="98" rx="14"/>
          <text class="sim-label" x="297" y="96" text-anchor="middle">SELECTED GATE</text>
          <text class="sim-value" x="297" y="125" text-anchor="middle" data-sim-value="gate">AND</text>
          <text class="sim-label" x="530" y="102">Y</text><text class="sim-value" x="530" y="128" data-sim-value="y">0</text>`);
      case 'half-adder':
        return svgFigure('Half Adder block: two one-bit inputs, XOR sum, and AND carry', '0 0 680 220', `
          <text class="sim-label" x="18" y="76">A</text><text class="sim-label" x="18" y="151">B</text>
          <path class="sim-wire" d="M42 70 H190 M42 145 H190 M375 82 H520 M375 145 H520"/>
          <rect class="sim-block" x="190" y="44" width="185" height="128" rx="12"/>
          <text class="sim-value" x="282" y="73" text-anchor="middle">HALF ADDER</text>
          <text class="sim-label" x="282" y="105" text-anchor="middle">Sum = A ⊕ B</text>
          <text class="sim-label" x="282" y="135" text-anchor="middle">Carry = A · B</text>
          <text class="sim-label" x="530" y="77">Sum</text><text class="sim-label" x="530" y="150">Carry</text>`);
      case 'full-adder':
        return svgFigure('Full Adder block: A, B and Cin enter; parity Sum and majority Cout leave', '0 0 760 250', `
          <text class="sim-label" x="18" y="72" data-sim-value="a">A=0</text><text class="sim-label" x="18" y="119" data-sim-value="b">B=0</text><text class="sim-label" x="18" y="166" data-sim-value="cin">Cin=0</text>
          <path class="sim-wire" d="M78 66 H190 M78 113 H190 M78 160 H190 M520 83 H628 M520 158 H628"/>
          <rect class="sim-block" x="190" y="38" width="330" height="160" rx="14"/>
          <text class="sim-value" x="355" y="72" text-anchor="middle">FULL ADDER</text>
          <text class="sim-label" x="355" y="108" text-anchor="middle">Sum = A ⊕ B ⊕ Cin</text>
          <text class="sim-label" x="355" y="140" text-anchor="middle">Cout = AB + ACin + BCin</text>
          <text class="sim-label" x="640" y="78" data-sim-value="sum">Sum=0</text><text class="sim-label" x="640" y="153" data-sim-value="cout">Cout=0</text>`);
      case 'mux-demux':
        return svgFigure('4 to 1 MUX and 1 to 4 DEMUX with selector lines S1 and S0', '0 0 800 285', `
          <text class="sim-label" x="18" y="51" data-sim-value="d0">D0=0</text><text class="sim-label" x="18" y="81" data-sim-value="d1">D1=1</text><text class="sim-label" x="18" y="111" data-sim-value="d2">D2=0</text><text class="sim-label" x="18" y="141" data-sim-value="d3">D3=0</text>
          <path class="sim-wire" d="M75 46 H174 M75 76 H174 M75 106 H174 M75 136 H174 M290 91 H358 M104 210 H174 M290 220 H350"/>
          <path class="sim-block" d="M174 30 H290 L320 91 L290 152 H174 Z"/><text class="sim-value" x="239" y="86" text-anchor="middle">4:1 MUX</text><text class="sim-label" x="239" y="112" text-anchor="middle">S1S0</text>
          <text class="sim-label" x="325" y="84" data-sim-value="mux-select">S=00</text><text class="sim-label" x="360" y="96" data-sim-value="mux-y">Y=0</text>
          <text class="sim-label" x="18" y="214" data-sim-value="demux-d">D=1</text><text class="sim-label" x="18" y="238" data-sim-value="demux-select">S=00</text>
          <path class="sim-block" d="M174 175 H290 L320 220 L290 265 H174 Z"/><text class="sim-value" x="239" y="216" text-anchor="middle">1:4 DEMUX</text><text class="sim-label" x="239" y="239" text-anchor="middle">S1S0</text>
          <path class="sim-wire" d="M320 220 H440 V183 H520 M440 220 V213 H520 M440 220 V243 H520 M440 220 V273 H520"/>
          <text class="sim-label" x="530" y="188" data-sim-value="y0">Y0=0</text><text class="sim-label" x="530" y="218" data-sim-value="y1">Y1=0</text><text class="sim-label" x="530" y="248" data-sim-value="y2">Y2=0</text><text class="sim-label" x="530" y="278" data-sim-value="y3">Y3=0</text>`);
      case 'encoder-decoder':
        return svgFigure('4 to 2 one-hot encoder and 2 to 4 decoder signal flow', '0 0 760 260', `
          <text class="sim-label" x="14" y="50" data-sim-value="i0">I0=1</text><text class="sim-label" x="14" y="82" data-sim-value="i1">I1=0</text><text class="sim-label" x="14" y="114" data-sim-value="i2">I2=0</text><text class="sim-label" x="14" y="146" data-sim-value="i3">I3=0</text>
          <path class="sim-wire" d="M60 46 H142 M60 78 H142 M60 110 H142 M60 142 H142 M292 94 H342"/>
          <rect class="sim-block" x="142" y="42" width="150" height="105" rx="12"/><text class="sim-value" x="217" y="82" text-anchor="middle">4:2 ENCODER</text><text class="sim-label" x="217" y="110" text-anchor="middle" data-sim-value="enc-code">Code=00</text>
          <text class="sim-label" x="346" y="91" data-sim-value="enc-status">Valid one-hot</text>
          <text class="sim-label" x="14" y="214" data-sim-value="dec-address">A1A0=00</text><path class="sim-wire" d="M82 209 H142 M292 209 H390"/>
          <rect class="sim-block" x="142" y="174" width="150" height="70" rx="12"/><text class="sim-value" x="217" y="203" text-anchor="middle">2:4 DECODER</text><text class="sim-label" x="217" y="226" text-anchor="middle">A1,A0 → Y0..Y3</text>
          <path class="sim-wire" d="M390 186 V246 M390 186 H465 M390 206 H465 M390 226 H465 M390 246 H465"/>
          <text class="sim-label" x="475" y="190" data-sim-value="y0">Y0=1</text><text class="sim-label" x="475" y="210" data-sim-value="y1">Y1=0</text><text class="sim-label" x="475" y="230" data-sim-value="y2">Y2=0</text><text class="sim-label" x="475" y="250" data-sim-value="y3">Y3=0</text>`);
      case 'flip-flops':
        return svgFigure('Edge-triggered flip-flop with data inputs, clock, Q and complementary output', '0 0 660 220', `
          <text class="sim-label" x="20" y="78" data-sim-value="u-label">S</text><text class="sim-label" x="20" y="128" data-sim-value="v-label">R</text>
          <path class="sim-wire" d="M48 72 H188 M48 122 H188 M355 98 H520 M355 145 H520 M225 184 V164"/>
          <rect class="sim-block" x="188" y="42" width="167" height="122" rx="10"/><text class="sim-value" x="271" y="78" text-anchor="middle" data-sim-value="ff-type">SR</text><text class="sim-label" x="271" y="107" text-anchor="middle">EDGE-TRIGGERED</text><text class="sim-small" x="202" y="147">▷ CLK</text>
          <text class="sim-label" x="526" y="92" data-sim-value="q">Q=0</text><text class="sim-label" x="526" y="139" data-sim-value="qbar">Q̅=1</text><text class="sim-label" x="193" y="204">Clock edge</text>`);
      case 'counter-register':
        return svgFigure('Four-bit modulo counter with clock and reset, and a cascaded four-bit shift register', '0 0 800 270', `
          <text class="sim-label" x="18" y="52">CLK / STEP</text><text class="sim-label" x="18" y="92">RESET</text>
          <path class="sim-wire" d="M100 47 H156 M78 87 H156 M410 82 H510"/>
          <rect class="sim-block" x="156" y="31" width="254" height="102" rx="12"/><text class="sim-value" x="283" y="62" text-anchor="middle">4-BIT MOD-16 COUNTER</text><text class="sim-label" x="283" y="91" text-anchor="middle" data-sim-value="counter">Q=0000</text><text class="sim-small" x="283" y="116" text-anchor="middle">RESET → 0000</text>
          <text class="sim-label" x="518" y="78">Q3 Q2 Q1 Q0</text>
          <text class="sim-label" x="18" y="182">SERIAL IN=1</text><path class="sim-wire" d="M105 177 H132 M190 177 H218 M276 177 H304 M362 177 H390 M447 177 H510 M105 226 H420 M132 202 V226 M218 202 V226 M304 202 V226 M390 202 V226"/>
          <rect class="sim-gate" x="132" y="152" width="58" height="50" rx="5"/><rect class="sim-gate" x="218" y="152" width="58" height="50" rx="5"/><rect class="sim-gate" x="304" y="152" width="58" height="50" rx="5"/><rect class="sim-gate" x="390" y="152" width="58" height="50" rx="5"/>
          <text class="sim-label" x="161" y="182" text-anchor="middle">DFF</text><text class="sim-label" x="247" y="182" text-anchor="middle">DFF</text><text class="sim-label" x="333" y="182" text-anchor="middle">DFF</text><text class="sim-label" x="419" y="182" text-anchor="middle">DFF</text>
          <text class="sim-small" x="270" y="247" text-anchor="middle">CLK drives each stage</text><text class="sim-label" x="518" y="180" data-sim-value="register">Q=1010</text>`);
      case 'binary':
        return svgFigure('Binary place-value conversion from decimal input to weighted bits', '0 0 660 170', `
          <rect class="sim-block" x="26" y="46" width="150" height="72" rx="12"/><text class="sim-value" x="101" y="78" text-anchor="middle">DECIMAL INPUT</text><text class="sim-label" x="101" y="101" text-anchor="middle" data-sim-value="decimal">13₁₀</text>
          <path class="sim-wire" d="M176 82 H244 M425 82 H495"/><rect class="sim-block" x="244" y="46" width="181" height="72" rx="12"/><text class="sim-value" x="334" y="78" text-anchor="middle">BASE-2 PLACE VALUES</text><text class="sim-label" x="334" y="101" text-anchor="middle">2³  2²  2¹  2⁰</text><text class="sim-label" x="510" y="77" data-sim-value="binary">1101₂</text>`);
      case 'boolean':
        return svgFigure('Boolean expression and equivalent simplified expression', '0 0 660 170', `
          <rect class="sim-block" x="28" y="45" width="220" height="78" rx="12"/><text class="sim-value" x="138" y="76" text-anchor="middle" data-sim-value="expr-left">A + AB</text><text class="sim-label" x="138" y="101" text-anchor="middle">OR / AND gates</text>
          <path class="sim-wire" d="M248 84 H365"/><text class="sim-value" x="306" y="71" text-anchor="middle">≡</text><rect class="sim-block" x="365" y="45" width="220" height="78" rx="12"/><text class="sim-value" x="475" y="76" text-anchor="middle" data-sim-value="expr-right">A</text><text class="sim-label" x="475" y="101" text-anchor="middle">same output for all rows</text>`);
      default:
        return '';
    }
  }

  function controls(kind, count = 0, registerBits = [1,0,1,0]) {
    if (kind === 'gates') return `<div class="simulator-controls"><span class="control-pair"><span>A</span>${bitButton('ga', 'Input A')}</span><span class="control-pair" id="gate-input-b"><span>B</span>${bitButton('gb', 'Input B')}</span><label for="demo-gate">Gate</label><select id="demo-gate"><option>AND</option><option>OR</option><option>NOT</option><option>NAND</option><option>NOR</option><option>XOR</option><option>XNOR</option></select></div>`;
    if (kind === 'binary') return `<div class="simulator-controls"><label for="demo-decimal">Decimal (0–65535)</label><input id="demo-decimal" type="number" min="0" max="65535" value="13" inputmode="numeric"></div>`;
    if (kind === 'boolean') return `<div class="simulator-controls"><label for="demo-law">Identity to verify</label><select id="demo-law"><option value="absorption">A + AB = A</option><option value="demorgan-or">¬(A+B) = ¬A·¬B</option></select></div>`;
    if (kind === 'full-adder') return `<div class="simulator-controls">${[['A','fa'],['B','fb'],['Cin','fc']].map(([name,key])=>`<span class="control-pair"><span>${name}</span>${bitButton(key, `Full Adder input ${name}`)}</span>`).join('')}</div>`;
    if (kind === 'mux-demux') return `<div class="simulator-controls simulator-controls-mux"><span class="control-set"><span class="control-set-label">MUX data inputs</span>${[0,1,2,3].map(i=>`<span class="control-pair"><span>D${i}</span>${bitButton(`d${i}`, `MUX data input D${i}`, i===1?1:0)}</span>`).join('')}</span><label for="demo-selector">MUX select S1S0</label><select id="demo-selector"><option value="00">00</option><option value="01">01</option><option value="10">10</option><option value="11">11</option></select><span class="control-pair"><span>DEMUX D</span>${bitButton('demux-d','DEMUX data input D',1)}</span><label for="demo-demux-selector">DEMUX select S1S0</label><select id="demo-demux-selector"><option value="00">00</option><option value="01">01</option><option value="10">10</option><option value="11">11</option></select></div>`;
    if (kind === 'encoder-decoder') return `<div class="simulator-controls simulator-controls-mux"><span class="control-set"><span class="control-set-label">Encoder inputs (one-hot)</span>${[0,1,2,3].map(i=>`<span class="control-pair"><span>I${i}</span>${bitButton(`enc-i${i}`, `Encoder input I${i}`, i===0?1:0)}</span>`).join('')}</span><label for="demo-address">Decoder address A1A0</label><select id="demo-address"><option value="00">00</option><option value="01">01</option><option value="10">10</option><option value="11">11</option></select><span class="control-pair"><span>Decoder enable</span>${bitButton('dec-enable','Decoder enable',1)}</span></div>`;
    if (kind === 'flip-flops') return `<div class="simulator-controls"><label for="demo-ff-type">Flip-flop type</label><select id="demo-ff-type"><option>SR</option><option>JK</option><option>D</option><option>T</option></select><span class="control-pair"><span>Current Q</span>${bitButton('ffq','Current state Q')}</span><span class="control-pair"><span data-fflabel="u">S</span>${bitButton('ffu','Flip-flop input S or J or D or T')}</span><span class="control-pair" id="ff-input-v"><span data-fflabel="v">R</span>${bitButton('ffv','Flip-flop input R or K')}</span><button class="btn btn-outline" id="demo-clock" type="button">Clock edge</button></div>`;
    if (kind === 'counter-register') return `<div class="simulator-controls"><span class="control-pair"><span>Four-bit state</span><output id="counter-state" aria-live="polite">${count.toString(2).padStart(4,'0')}</output></span><button class="btn btn-outline" id="counter-step" type="button">Clock / Step</button><button class="btn btn-outline" id="counter-reset" type="button">Reset</button></div><div class="simulator-controls register-controls"><span class="control-pair"><span>Shift-register state</span><output id="register-state" aria-live="polite">${registerBits.join('')}</output></span><button class="btn btn-outline" id="register-shift" type="button">Clock: shift right (serial 1)</button></div>`;
    return `<p class="small muted">Use the dedicated Half Adder Lab for all input combinations and its complete highlighted truth table.</p><a class="btn btn-dark" href="#lab">Open Half Adder Lab <span>↗</span></a>`;
  }

  function render(lesson, mode, count = 0, registerBits = [1,0,1,0], locale = 'en') {
    const kind = lesson.demo_kind;
    const instructions = instructionOverrides[kind]?.[locale] || mode.demo_instructions;
    return `<section class="lesson-demo-card" id="lesson-simulator" tabindex="-1" role="region" aria-labelledby="simulator-heading">
      <div class="simulator-heading"><div><p class="eyebrow">INTERACTIVE EXPERIMENT</p><h3 id="simulator-heading">${kind === 'half-adder' ? 'Half Adder simulator' : 'Try the simulator'}</h3></div><span class="live-indicator"><i></i> LIVE</span></div>
      <p class="simulator-purpose">${h(localized(purposeCopy[kind], locale))}</p>
      <p class="simulator-instructions">${h(instructions)}</p>
      ${diagram(kind)}
      ${controls(kind, count, registerBits)}
      <p class="simulator-output" id="demo-output" aria-live="polite" role="status"></p>
      <p class="simulator-reference-note">The matching truth/state table and worked example are included in this lesson below.</p>
    </section>`;
  }

  function setDiagram(values) {
    Object.entries(values).forEach(([key, value]) => {
      document.querySelectorAll(`#lesson-detail [data-sim-value="${key}"]`).forEach(node => {
        node.textContent = String(value);
      });
    });
  }

  function pressed(key) {
    return document.querySelector(`#lesson-detail [data-demo-toggle="${key}"]`)?.textContent.trim() === '1' ? 1 : 0;
  }

  function update(lesson) {
    if (!lesson || document.querySelector('#lesson-detail')?.hidden) return;
    const kind = lesson.demo_kind;
    const out = document.querySelector('#lesson-detail #demo-output');
    if (!out) return;
    if (kind === 'gates') {
      const a = pressed('ga'), b = pressed('gb'), name = document.querySelector('#demo-gate').value;
      const y = logic.gate(name, a, b);
      document.querySelector('#gate-input-b').hidden = name === 'NOT';
      setDiagram({ a: `A=${a}`, b: `B=${b}`, gate: name, y: `Y=${y}` });
      out.textContent = `${name} · A=${a}${name === 'NOT' ? '' : `, B=${b}`} → Y=${y}`;
    } else if (kind === 'binary') {
      const input = document.querySelector('#demo-decimal');
      const n = Number(input.value);
      const valid = input.value !== '' && Number.isInteger(n) && n >= 0 && n <= 65535;
      const binary = valid ? n.toString(2) : '';
      setDiagram({ decimal: valid ? `${n}₁₀` : '—', binary: valid ? `${binary}₂` : '—' });
      out.textContent = valid ? `${n}₁₀ = ${binary}₂ · ${binary.split('').reverse().map((v,i)=>v==='1'?`2^${i}`:null).filter(Boolean).reverse().join(' + ') || '0'}` : 'Enter a whole number from 0 to 65535.';
    } else if (kind === 'boolean') {
      const law = document.querySelector('#demo-law').value;
      const left = law === 'absorption' ? 'A + AB' : '¬(A+B)';
      const right = law === 'absorption' ? 'A' : '¬A · ¬B';
      setDiagram({ 'expr-left': left, 'expr-right': right });
      out.textContent = `${left} = ${right}. Compare all four input rows in the reference table below.`;
    } else if (kind === 'full-adder') {
      const a = pressed('fa'), b = pressed('fb'), cin = pressed('fc');
      const {sum, cout} = logic.fullAdder(a, b, cin);
      setDiagram({ a:`A=${a}`, b:`B=${b}`, cin:`Cin=${cin}`, sum:`Sum=${sum}`, cout:`Cout=${cout}` });
      out.textContent = `A=${a}, B=${b}, Cin=${cin} · Sum=${sum} · Cout=${cout}`;
    } else if (kind === 'mux-demux') {
      const data = [0,1,2,3].map(i => pressed(`d${i}`));
      const muxSelect = document.querySelector('#demo-selector').value;
      const demuxSelect = document.querySelector('#demo-demux-selector').value;
      const demuxD = pressed('demux-d');
      const y = logic.mux4(data, muxSelect);
      const outputs = logic.demux1to4(demuxD, demuxSelect);
      const values = { 'mux-select':`S=${muxSelect}`, 'mux-y':`Y=${y}`, 'demux-d':`D=${demuxD}`, 'demux-select':`S=${demuxSelect}` };
      data.forEach((value,i)=>values[`d${i}`]=`D${i}=${value}`);
      outputs.forEach((value,i)=>values[`y${i}`]=`Y${i}=${value}`);
      setDiagram(values);
      out.textContent = `MUX S=${muxSelect} selects D${parseInt(muxSelect,2)}=${y}, so Y=${y}. DEMUX S=${demuxSelect}, D=${demuxD} → Y0..Y3=${outputs.join('')}.`;
    } else if (kind === 'encoder-decoder') {
      const inputs = [0,1,2,3].map(i => pressed(`enc-i${i}`));
      const encoded = logic.encode4to2(inputs);
      const address = document.querySelector('#demo-address').value;
      const outputs = logic.decode2to4(address, pressed('dec-enable'));
      const values = { 'enc-code':encoded.valid?`Code=${encoded.code.join('')}`:'Code=undefined', 'enc-status':encoded.valid?'Valid one-hot':'Invalid / undefined', 'dec-address':`A1A0=${address}` };
      inputs.forEach((value,i)=>values[`i${i}`]=`I${i}=${value}`);
      outputs.forEach((value,i)=>values[`y${i}`]=`Y${i}=${value}`);
      setDiagram(values);
      out.textContent = `${encoded.valid?`Encoder I${encoded.index} → ${encoded.code.join('')}.`:`Encoder undefined: ${encoded.reason}`} Decoder ${address}, enable=${pressed('dec-enable')} → Y0..Y3=${outputs.join('')}.`;
    } else if (kind === 'flip-flops') {
      const type = document.querySelector('#demo-ff-type').value;
      const labels = { SR:['S','R'], JK:['J','K'], D:['D',null], T:['T',null] }[type];
      document.querySelectorAll('#lesson-detail [data-fflabel]').forEach(node=>{
        const index = node.dataset.fflabel === 'u' ? 0 : 1;
        node.textContent = labels[index] || '';
        node.hidden = !labels[index];
      });
      const second = document.querySelector('#ff-input-v');
      second.hidden = !labels[1];
      document.querySelector('#lesson-detail [data-demo-toggle="ffu"]').setAttribute('aria-label',`Flip-flop input ${labels[0]}`);
      document.querySelector('#lesson-detail [data-demo-toggle="ffv"]').setAttribute('aria-label',`Flip-flop input ${labels[1] || 'not used'}`);
      const q = pressed('ffq');
      setDiagram({ 'ff-type':type, 'u-label':labels[0], 'v-label':labels[1] || '', q:`Q=${q}`, qbar:`Q̅=${1-q}` });
      out.textContent = `${type} flip-flop · Q=${q}. Set the input, then press Clock edge to see Q⁺.`;
    } else if (kind === 'counter-register') {
      const count = Number(document.querySelector('#counter-state').textContent);
      const bits = document.querySelector('#register-state').textContent;
      setDiagram({counter:`Q=${count.toString(2).padStart(4,'0')}`,register:`Q=${bits}`,reset:'RESET' });
      out.textContent = `Counter Q=${count.toString(2).padStart(4,'0')}₂ (${count}); shift register Q=${bits}.`;
    } else if (kind === 'half-adder') {
      out.textContent = 'Use the Half Adder Lab for interactive inputs and the complete truth table.';
    }
  }

  function clockFlipFlop(lesson) {
    if (!lesson || lesson.demo_kind !== 'flip-flops') return;
    const type = document.querySelector('#demo-ff-type').value;
    const qButton = document.querySelector('#lesson-detail [data-demo-toggle="ffq"]');
    const q = Number(qButton.textContent.trim());
    const result = logic.flipFlopNext(type, q, pressed('ffu'), pressed('ffv'));
    if (result.valid) {
      qButton.textContent = String(result.nextQ);
      qButton.setAttribute('aria-pressed', String(Boolean(result.nextQ)));
    }
    update(lesson);
    const out = document.querySelector('#lesson-detail #demo-output');
    out.textContent = result.valid
      ? `${type}: ${result.reason} · Q=${q} → Q⁺=${result.nextQ}`
      : result.reason;
  }

  root.CBSimulatorUI = Object.freeze({ render, update, clockFlipFlop });
}(window));
