import test from "node:test";
import assert from "node:assert/strict";
import {parsePowerCsv} from "./csv-import.mjs";
const provenance={source:"https://example.org/verified-data.csv",zone:"DE",retrievedAt:"2026-11-10T00:00:00Z",evidence:"operational"};
const csv="start_utc,minutes,average_mw\n2026-11-09T00:00:00Z,30,100\n2026-11-09T00:30:00Z,30,200";
test("converts complete UTC hour with explicit provenance",()=>{
 const [r]=parsePowerCsv(csv,provenance);
 assert.equal(r.energyMWh,150);assert.equal(r.evidence,"operational");assert.equal(r.source,provenance.source);
});
test("rejects synthetic classification in operational-only import",()=>assert.throws(()=>parsePowerCsv(csv,{...provenance,evidence:"synthetic"})));
test("rejects incomplete hour",()=>assert.throws(()=>parsePowerCsv(csv.split("\n").slice(0,2).join("\n"),provenance)));
test("rejects malformed numeric values",()=>assert.throws(()=>parsePowerCsv(csv.replace("30,200","30,NaN"),provenance)));
test("rejects ambiguous timestamp",()=>assert.throws(()=>parsePowerCsv(csv.replace("2026-11-09T00:00:00Z","2026-11-09T01:00:00+01:00"),provenance)));
