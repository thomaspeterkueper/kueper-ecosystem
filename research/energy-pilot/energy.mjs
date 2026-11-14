// Synthetic hourly electricity dispatch; all energies in kWh and powers in kW.
export function simulateEnergy(hours, config) {
  if (!Array.isArray(hours) || !hours.length) throw Error("Nonempty hours required");
  for (const key of ["batteryCapacity","batteryPower","batteryEfficiency","hydrogenCapacity","hydrogenPower","hydrogenEfficiency"]) {
    if (!Number.isFinite(config[key]) || config[key] < 0) throw Error("Invalid "+key);
  }
  if (config.batteryEfficiency <= 0 || config.batteryEfficiency > 1 ||
      config.hydrogenEfficiency <= 0 || config.hydrogenEfficiency > 1) throw Error("Efficiency outside (0,1]");
  let battery=0, hydrogen=0, unserved=0, curtailed=0, demand=0, generation=0, loss=0;
  const trace=[];
  for (const [index,h] of hours.entries()) {
    if (!Number.isFinite(h.demand) || !Number.isFinite(h.generation) || h.demand<0 || h.generation<0) throw Error("Invalid hourly energy");
    demand+=h.demand; generation+=h.generation;
    let surplus=Math.max(0,h.generation-h.demand), deficit=Math.max(0,h.demand-h.generation);
    // Store internal energy in delivered-kWh equivalents; losses occur on charge.
    const bCharge=Math.min(surplus,config.batteryPower,(config.batteryCapacity-battery)/config.batteryEfficiency);
    battery+=bCharge*config.batteryEfficiency; surplus-=bCharge; loss+=bCharge*(1-config.batteryEfficiency);
    const hCharge=Math.min(surplus,config.hydrogenPower,(config.hydrogenCapacity-hydrogen)/config.hydrogenEfficiency);
    hydrogen+=hCharge*config.hydrogenEfficiency; surplus-=hCharge; loss+=hCharge*(1-config.hydrogenEfficiency);
    const bDischarge=Math.min(deficit,config.batteryPower,battery);
    battery-=bDischarge; deficit-=bDischarge;
    const hDischarge=Math.min(deficit,config.hydrogenPower,hydrogen);
    hydrogen-=hDischarge; deficit-=hDischarge;
    curtailed+=surplus; unserved+=deficit;
    trace.push({hour:index,battery,hydrogen,unserved:deficit,curtailed:surplus});
  }
  const residual=generation-demand+unserved-curtailed-loss-battery-hydrogen;
  if (Math.abs(residual)>1e-8*Math.max(1,generation,demand)) throw Error("Energy balance violation");
  return {evidence:"synthetic",demand,generation,unserved,curtailed,loss,batteryFinal:battery,hydrogenFinal:hydrogen,residual,trace};
}
