// Pure, read-only parser for a verified, explicitly labeled ENTSO-E-like CSV export.
// Input schema: start_utc,minutes,average_mw. This is NOT the ENTSO-E API XML format.
import {hourlyEnergy} from "./intervals.mjs";

export function parsePowerCsv(csv, provenance) {
 if(typeof csv!=="string" || !provenance || provenance.evidence!=="operational" ||
    !/^https:\/\//.test(provenance.source ?? "") || !provenance.zone || !provenance.retrievedAt)
  throw Error("Verified operational provenance required");
 const lines=csv.trim().split(/\r?\n/);
 if(lines.shift()!=="start_utc,minutes,average_mw" || !lines.length) throw Error("Unexpected CSV schema");
 const rows=lines.map(line=>{
  const parts=line.split(",");
  if(parts.length!==3 || !/^\d+$/.test(parts[1]) || parts[2].trim()==="" || !Number.isFinite(Number(parts[2])))
   throw Error("Invalid CSV row");
  return {start:parts[0],minutes:Number(parts[1]),mw:Number(parts[2])};
 });
 return hourlyEnergy(rows,provenance);
}
