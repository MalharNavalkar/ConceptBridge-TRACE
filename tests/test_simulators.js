const assert = require('node:assert/strict');
const logic = require('../app/static/js/simulator-core.js');
let checks = 0;
function test(name, fn) {
  fn();
  checks += 1;
  console.log(`ok ${checks} - ${name}`);
}

test('all seven logic-gate rows match the Boolean definitions', () => {
  const rows = [[0,0],[0,1],[1,0],[1,1]];
  const expected = [
    {AND:0,OR:0,NAND:1,NOR:1,XOR:0,XNOR:1},
    {AND:0,OR:1,NAND:1,NOR:0,XOR:1,XNOR:0},
    {AND:0,OR:1,NAND:1,NOR:0,XOR:1,XNOR:0},
    {AND:1,OR:1,NAND:0,NOR:0,XOR:0,XNOR:1},
  ];
  rows.forEach(([a,b],i)=>Object.entries(expected[i]).forEach(([name,value])=>assert.equal(logic.gate(name,a,b),value)));
  assert.equal(logic.gate('NOT',0),1);
  assert.equal(logic.gate('NOT',1),0);
});

test('Half Adder remains correct for all four inputs', () => {
  assert.deepEqual([[0,0],[0,1],[1,0],[1,1]].map(([a,b])=>logic.halfAdder(a,b)), [
    {sum:0,carry:0},{sum:1,carry:0},{sum:1,carry:0},{sum:0,carry:1},
  ]);
});

test('Full Adder 1,1,1 yields Sum=1 and Cout=1', () => {
  assert.deepEqual(logic.fullAdder(1,1,1), {sum:1,cout:1});
});

test('Full Adder matches arithmetic for all eight input combinations', () => {
  for (let a=0;a<=1;a++) for (let b=0;b<=1;b++) for (let cin=0;cin<=1;cin++) {
    const {sum,cout}=logic.fullAdder(a,b,cin);
    assert.equal(sum+2*cout,a+b+cin);
  }
});

test('4:1 MUX returns each selected data input', () => {
  const data=[0,1,1,0];
  for (let select=0;select<4;select++) assert.equal(logic.mux4(data,select),data[select]);
  assert.equal(logic.mux4(data,'10'),1);
});

test('1:4 DEMUX routes input only to selected enabled output', () => {
  for (let select=0;select<4;select++) {
    assert.deepEqual(logic.demux1to4(1,select),[0,1,2,3].map(i=>i===select?1:0));
    assert.deepEqual(logic.demux1to4(0,select),[0,0,0,0]);
  }
  assert.deepEqual(logic.demux1to4(1,2,0),[0,0,0,0]);
});

test('4:2 encoder returns the selected one-hot code and flags undefined inputs', () => {
  for (let i=0;i<4;i++) {
    const inputs=[0,0,0,0]; inputs[i]=1;
    assert.deepEqual(logic.encode4to2(inputs),{valid:true,index:i,code:[i>>1,i&1],reason:''});
  }
  assert.equal(logic.encode4to2([0,0,0,0]).valid,false);
  assert.equal(logic.encode4to2([1,1,0,0]).valid,false);
});

test('2:4 decoder activates exactly the addressed output', () => {
  for (let i=0;i<4;i++) assert.deepEqual(logic.decode2to4(i),[0,1,2,3].map(j=>j===i?1:0));
  assert.deepEqual(logic.decode2to4('11',0),[0,0,0,0]);
});

test('SR, JK, D and T flip-flops implement valid next-state rules', () => {
  assert.deepEqual(logic.flipFlopNext('SR',0,0,0),{valid:true,nextQ:0,reason:'Hold'});
  assert.deepEqual(logic.flipFlopNext('SR',0,1,0),{valid:true,nextQ:1,reason:'Set'});
  assert.equal(logic.flipFlopNext('SR',1,1,1).valid,false);
  assert.equal(logic.flipFlopNext('JK',0,1,1).nextQ,1);
  assert.equal(logic.flipFlopNext('JK',1,1,1).nextQ,0);
  assert.equal(logic.flipFlopNext('D',0,1).nextQ,1);
  assert.equal(logic.flipFlopNext('T',0,1).nextQ,1);
  assert.equal(logic.flipFlopNext('T',1,0).nextQ,1);
});

test('four-bit counter steps, holds, resets and wraps', () => {
  assert.equal(logic.counterStep(0),1);
  assert.equal(logic.counterStep(5,{enable:false}),5);
  assert.equal(logic.counterStep(15),0);
  assert.equal(logic.counterStep(13,{reset:true}),0);
});

test('shift register moves in the displayed direction and accepts serial input', () => {
  assert.deepEqual(logic.shiftRegisterStep([1,0,1,0],1),[1,1,0,1]);
  assert.deepEqual(logic.shiftRegisterStep([1,0,1,0],0),[0,1,0,1]);
});

console.log(`# ${checks} simulator checks passed`);
