import { simulateEnergy } from "./energy.mjs";

/**
 * Synthetic grid interface on top of the existing islanded dispatch.
 * Grid import/export are capped per hour; the original dispatch handles
 * battery/hydrogen balancing and explicit conversion losses.
 * No tariffs, grid physics, power flow, or real grid data are implied.
 */
export function simulateGridAware(hours, config, grid) {
  if (!Array.isArray(hours) || hours.length === 0) throw Error("Nonempty hours required");
  for (const key of ["importLimit", "exportLimit"]) {
    if (!Number.isFinite(grid?.[key]) || grid[key] < 0) throw Error("Invalid " + key);
  }
  const adjusted = [];
  let imported = 0, exported = 0;
  const transfers = [];
  for (const h of hours) {
    if (!Number.isFinite(h?.demand) || !Number.isFinite(h?.generation) ||
        h.demand < 0 || h.generation < 0) throw Error("Invalid hourly energy");
    // Exchange only the instantaneous mismatch. Do not assume unlimited grid capacity.
    const importKwh = Math.min(Math.max(0, h.demand - h.generation), grid.importLimit);
    const exportKwh = Math.min(Math.max(0, h.generation - h.demand), grid.exportLimit);
    imported += importKwh; exported += exportKwh;
    adjusted.push({demand: h.demand + exportKwh, generation: h.generation + importKwh});
    transfers.push({importKwh, exportKwh});
  }
  const result = simulateEnergy(adjusted, config);
  const originalDemand = hours.reduce((n, h) => n + h.demand, 0);
  const originalGeneration = hours.reduce((n, h) => n + h.generation, 0);
  const residual = originalGeneration + imported - originalDemand - exported +
    result.unserved - result.curtailed - result.loss - result.batteryFinal - result.hydrogenFinal;
  if (Math.abs(residual) > 1e-8 * Math.max(1, originalDemand, originalGeneration))
    throw Error("Grid energy balance violation");
  return { ...result, evidence: "synthetic", demand: originalDemand,
    generation: originalGeneration, imported, exported, residual,
    grid: {importLimit: grid.importLimit, exportLimit: grid.exportLimit},
    transfers };
}
