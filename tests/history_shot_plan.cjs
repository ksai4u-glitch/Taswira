const assert=require('node:assert/strict'),{validateShotPlan}=require('../capture_history.cjs');
assert.equal(typeof validateShotPlan,'function','A reviewed shot plan must drive the capture sequence');
const plan={title:'Cities unfold',shots:[{chapter:'africa',scene:'zimbabwe',from:0,to:12}]};
assert.deepEqual(validateShotPlan(plan),plan.shots);
for(const shot of [{chapter:'africa',scene:'zimbabwe',from:3,to:2},{chapter:'africa',scene:'zimbabwe',from:0,to:Infinity},{chapter:'africa',scene:'zimbabwe',from:-1,to:2},{chapter:'../private',scene:'zimbabwe',from:0,to:2}])assert.throws(()=>validateShotPlan({shots:[shot]}));
assert.throws(()=>validateShotPlan({shots:[]}));console.log('PASS: explicit shot-plan validation, finite in/out times, order and safe scene identifiers.');
