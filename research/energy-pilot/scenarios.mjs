import { simulateEnergy } from "./energy.mjs";

/** Synthetic stress cases only. Never label these as measured grid data. */
export function buildScenario(hours, { demandMultiplier = 1, generationMultiplier = 1, outageStart = -1, outageHours = 0 } = {}) {
  if (!Array.isArray(hours) || !hours.length || !Number.isFinite(demandMultiplier) || demandMultiplier < 0 ||
      !Number.isFinite(generationMultiplier) || generationMultiplier < 0 ||
      !Number.isSafeInteger(outageStart) || !Number.isSafeInteger(outageHours) || outageHours < 0)
    throw new Error("Invalid scenario");
  return hours.map((h, i) => {
    if (!Number.isFinite(h.demand) || !Number.isFinite(h.generation) || h.demand < 0 || h.generation < 0)
      throw new Error("Invalid input series");
    return { demand: h.demand * demandMultiplier,
      generation: i >= outageStart && i < outageStart + outageHours ? 0 : h.generation * generationMultiplier };
  });
}

export function compareScenarios(hours, config) {
  const cases = {
    baseline: {},
    increasedComputeDemand: { demandMultiplier: 1.25 },
    lowRenewables: { generationMultiplier: 0.2 },
    generationOutage: { outageStart: 0, outageHours: Math.min(48, hours.length) }
  };
  return Object.fromEntries(Object.entries(cases).map(([name, scenario]) =>
    [name, simulateEnergy(buildScenario(hours, scenario), config)]));
}
