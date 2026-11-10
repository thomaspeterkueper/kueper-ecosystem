import test from "node:test";
import assert from "node:assert/strict";
import {simulateEnergy} from "./energy.mjs";
const cfg={batteryCapacity:10,batteryPower:10,batteryEfficiency:.8,hydrogenCapacity:20,hydrogenPower:10,hydrogenEfficiency:.4};
test("stores surplus and supplies later demand with explicit losses",()=>{
 const r=simulateEnergy([{demand:0,generation:10},{demand:5,generation:0}],cfg);
 assert.equal(r.unserved,0);assert.equal(r.loss,2);assert.equal(r.batteryFinal,3);assert.ok(Math.abs(r.residual)<1e-10);
});
test("reports unmet load",()=>{
 const r=simulateEnergy([{demand:20,generation:0}],cfg);assert.equal(r.unserved,20);
});
test("rejects impossible efficiency",()=>{
 assert.throws(()=>simulateEnergy([{demand:1,generation:0}],{...cfg,batteryEfficiency:1.2}));
});
test("rejects negative generation",()=>{
 assert.throws(()=>simulateEnergy([{demand:0,generation:-1}],cfg));
});
