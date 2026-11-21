import test from "node:test";
import assert from "node:assert/strict";
import {buildScenario, compareScenarios} from "./scenarios.mjs";
const hours=Array.from({length:72},(_,i)=>({demand:5,generation:i%24<12?10:0}));
const config={batteryCapacity:20,batteryPower:10,batteryEfficiency:.9,hydrogenCapacity:50,hydrogenPower:10,hydrogenEfficiency:.45};
test("stress scenarios preserve balance",()=>{
 for(const result of Object.values(compareScenarios(hours,config))) assert.ok(Math.abs(result.residual)<1e-8);
});
test("increased demand cannot reduce unserved energy with fixed dispatch",()=>{
 const results=compareScenarios(hours,config);
 assert.ok(results.increasedComputeDemand.unserved>=results.baseline.unserved);
});
test("generation outage zeroes selected hours",()=>{
 const result=buildScenario(hours,{outageStart:5,outageHours:3});
 assert.deepEqual(result.slice(5,8).map(x=>x.generation),[0,0,0]);
 assert.equal(result[4].generation,hours[4].generation);
});
test("rejects invalid demand multipliers",()=>assert.throws(()=>buildScenario(hours,{demandMultiplier:-1})));
