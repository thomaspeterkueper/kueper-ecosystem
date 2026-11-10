import test from "node:test";
import assert from "node:assert/strict";
import {hourlyEnergy} from "./intervals.mjs";
const meta={source:"fixture:entsoe-like",zone:"TEST",retrievedAt:"2026-11-10T00:00:00Z"};
const rows=Array.from({length:4},(_,i)=>({start:`2026-11-09T00:${String(i*15).padStart(2,"0")}:00Z`,minutes:15,mw:100+i*10}));
test("converts quarter-hour MW to hourly MWh",()=>{
 const result=hourlyEnergy(rows,meta);
 assert.equal(result.length,1);assert.equal(result[0].energyMWh,115);
 assert.equal(result[0].evidence,"operational");
});
test("rejects missing quarter hour",()=>assert.throws(()=>hourlyEnergy(rows.filter((_,i)=>i!==2),meta)));
test("rejects duplicate interval",()=>assert.throws(()=>hourlyEnergy([...rows,rows[1]],meta)));
test("rejects partial hours",()=>assert.throws(()=>hourlyEnergy(rows.slice(0,3),meta)));
test("rejects non-UTC timestamps",()=>assert.throws(()=>hourlyEnergy([{...rows[0],start:"2026-11-09T01:00:00+01:00"}],meta)));
