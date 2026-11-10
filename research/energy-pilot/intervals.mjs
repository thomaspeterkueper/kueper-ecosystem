// Read-only normalization of measured average power (MW) to hourly energy (MWh).
// Input must have explicit UTC ISO timestamps and fixed duration in minutes.
const EVIDENCE_TIERS=new Set(["synthetic","simulation","lab","operational"]);
export function hourlyEnergy(rows, {source, zone, retrievedAt, evidence} = {}) {
 if (!source?.trim() || !zone?.trim() || !Number.isFinite(Date.parse(retrievedAt)) ||
     !EVIDENCE_TIERS.has(evidence) || !Array.isArray(rows) || rows.length===0)
  throw Error("Provenance, evidence tier and data required");
 const sorted=[...rows].sort((a,b)=>Date.parse(a.start)-Date.parse(b.start));
 let lastEnd=null;const buckets=new Map();
 for(const row of sorted) {
  if(typeof row.start!=="string" || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(row.start) ||
     !Number.isFinite(Date.parse(row.start)) || ![15,30,60].includes(row.minutes) ||
     !Number.isFinite(row.mw) || row.mw<0) throw Error("Invalid UTC interval or MW");
  const start=Date.parse(row.start), end=start+row.minutes*60000;
  if(start%(row.minutes*60000)!==0 || (lastEnd!==null && start!==lastEnd))
    throw Error("Duplicate, gap, overlap or unaligned interval");
  lastEnd=end;
  const hour=new Date(Math.floor(start/3600000)*3600000).toISOString();
  const bucket=buckets.get(hour)??{energyMWh:0,coveredMinutes:0};
  bucket.energyMWh+=row.mw*row.minutes/60;
  bucket.coveredMinutes+=row.minutes;
  buckets.set(hour,bucket);
 }
 return [...buckets].map(([startUTC,b])=>{
  if(b.coveredMinutes!==60) throw Error("Incomplete hourly coverage");
  return {startUTC,energyMWh:b.energyMWh,source,zone,retrievedAt,evidence};
 });
}
