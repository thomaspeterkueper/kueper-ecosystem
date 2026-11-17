import test from "node:test";
import assert from "node:assert/strict";
import {simulateGridAware} from "./grid-dispatch.mjs";
const storage = {batteryCapacity:0,batteryPower:0,batteryEfficiency:1,
  hydrogenCapacity:0,hydrogenPower:0,hydrogenEfficiency:1};
test("limited import leaves unmet demand",()=>{
 const r=simulateGridAware([{demand:10,generation:0}],storage,{importLimit:4,exportLimit:0});
 assert.equal(r.imported,4);assert.equal(r.unserved,6);assert.equal(r.residual,0);
});
test("limited export curtails remaining generation",()=>{
 const r=simulateGridAware([{demand:0,generation:10}],storage,{importLimit:0,exportLimit:3});
 assert.equal(r.exported,3);assert.equal(r.curtailed,7);assert.equal(r.residual,0);
});
test("zero grid limits reproduce islanded energy balance",()=>{
 const r=simulateGridAware([{demand:5,generation:0}],storage,{importLimit:0,exportLimit:0});
 assert.equal(r.unserved,5);assert.equal(r.imported,0);
});
test("reject invalid limits and inputs",()=>{
 assert.throws(()=>simulateGridAware([{demand:1,generation:0}],storage,{importLimit:-1,exportLimit:0}));
 assert.throws(()=>simulateGridAware([{demand:-1,generation:0}],storage,{importLimit:1,exportLimit:0}));
});
