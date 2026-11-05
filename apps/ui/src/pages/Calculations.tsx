import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listFormulas, runCalculation } from "../api/client";
import type { Formula, CalcRun } from "../api/client";

const INPUTS: Record<string, { label: string; unit: string; placeholder: string }> = {
  length: { label: "Length (L)", unit: "m", placeholder: "10 m" },
  width: { label: "Width (W)", unit: "m", placeholder: "3 m" },
  height: { label: "Height (H)", unit: "m", placeholder: "1 m" },
  loa: { label: "Length overall", unit: "m", placeholder: "10 m" },
  beam: { label: "Beam", unit: "m", placeholder: "3 m" },
  draft: { label: "Draft", unit: "m", placeholder: "1 m" },
  km: { label: "KM", unit: "m", placeholder: "5 m" },
  kg: { label: "KG", unit: "m", placeholder: "2 m" },
  gm: { label: "GM", unit: "m", placeholder: "1.2 m" },
  density: { label: "Density", unit: "kg/m³", placeholder: "1025 kg/m³" },
  g: { label: "Gravity", unit: "m/s²", placeholder: "9.81 m/s²" },
  depth: { label: "Depth", unit: "m", placeholder: "10 m" },
};

function inputNames(formula: Formula): string[] {
  const variables = formula.variables ?? [];
  const names = variables.map((item) => String(item.name ?? item.key ?? "")).filter(Boolean);
  if (names.length) return names;
  if (formula.name === "box_volume" || formula.name === "box_surface_area") return ["length", "width", "height"];
  if (formula.name === "displacement_volume") return ["loa", "beam", "draft"];
  if (formula.name === "metacentric_height") return ["km", "kg"];
  if (formula.name === "initial_stability") return ["gm"];
  if (formula.name === "hydrostatic_pressure") return ["density", "g", "depth"];
  return [];
}

export function Calculations() {
  const { data: formulas, isLoading, error } = useQuery({ queryKey: ["formulas"], queryFn: () => listFormulas() });
  const [selected, setSelected] = useState<Formula | null>(null);
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [runResult, setRunResult] = useState<CalcRun | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [research, setResearch] = useState(false);
  const [running, setRunning] = useState(false);
  const [inputUnit, setInputUnit] = useState("m");

  function unitFor(name: string) {
    if (["length", "width", "height", "loa", "beam", "draft", "km", "kg", "gm", "depth"].includes(name)) return inputUnit;
    return INPUTS[name]?.unit ?? "SI";
  }

  const gmValue = selected?.name === "initial_stability" ? Number(inputs.gm) : NaN;
  const gmWarning = Number.isFinite(gmValue) && Math.abs(gmValue) > 5;

  function choose(formula: Formula) {
    setSelected(formula);
    setInputUnit("m");
    setInputs(Object.fromEntries(inputNames(formula).map((name) => [name, ""])));
    setRunResult(null);
    setRunError(null);
  }

  async function doRun() {
    if (!selected) return;
    setRunning(true); setRunError(null); setRunResult(null);
    try {
      const lengthInputs = new Set(["length", "width", "height", "loa", "beam", "draft", "km", "kg", "gm", "depth"]);
      const normalizedInputs = Object.fromEntries(Object.entries(inputs).map(([name, value]) => {
        if (!value.trim()) return [name, value];
        if (lengthInputs.has(name)) return [name, `${value.trim()} ${inputUnit}`];
        if (name === "density") return [name, `${value.trim()} kg/m^3`];
        if (name === "g") return [name, `${value.trim()} m/s^2`];
        return [name, value.trim()];
      }));
      if (selected.name === "initial_stability" && gmWarning) {
        setRunError("GM value is unusually large for an ordinary vessel. Check units and loading data before running.");
        return;
      }
      setRunResult(await runCalculation({ formula_id: selected.id, inputs: normalizedInputs, research }));
    } catch (e) { setRunError((e as Error).message); } finally { setRunning(false); }
  }

  return (
    <div className="calculation-page">
      <header className="dashboard-heading">
        <div><p className="eyebrow">Engineering core</p><h2>Calculations</h2><p className="lede">Choose one verified formula, enter each quantity in its own field, and run it with units.</p></div>
      </header>
      <div className="calculation-layout">
        <section className="workspace-panel" aria-labelledby="formula-heading">
          <div className="panel-heading"><div><p className="eyebrow">Formula library</p><h3 id="formula-heading">Available calculations</h3></div></div>
          {isLoading ? <div className="state-panel"><strong>Loading formulas...</strong><span className="sketch-line wide" /></div> : error ? <div className="state-panel error-state">Could not load formulas: {(error as Error).message}</div> : formulas?.length ? (
            <div className="formula-list">{formulas.map((formula) => <button type="button" className={`formula-row ${selected?.id === formula.id ? "selected" : ""}`} key={formula.id} onClick={() => choose(formula)}><span><strong>{formula.name.replaceAll("_", " ")}</strong><small>{formula.equation_text}</small></span><em>{formula.domain}</em></button>)}</div>
          ) : <div className="state-panel"><strong>No formulas available.</strong><span>Built-in engineering formulas will appear after backend initialization.</span></div>}
        </section>
        <section className="workspace-panel calculation-form" aria-labelledby="run-heading">
          <div className="panel-heading"><div><p className="eyebrow">Input sheet</p><h3 id="run-heading">{selected ? selected.name.replaceAll("_", " ") : "Select a formula"}</h3></div><label className="unit-system">Input unit<select aria-label="Input unit" value={inputUnit} onChange={(e) => setInputUnit(e.target.value)}><option value="m">m</option><option value="mm">mm</option><option value="cm">cm</option><option value="km">km</option></select></label></div>
          {!selected ? <div className="state-panel"><strong>Pick calculation from library.</strong><span>Each required quantity will get its own input field.</span></div> : <div className="form-body">
            <div className="input-grid">{inputNames(selected).map((name) => { const spec = INPUTS[name] ?? { label: name, unit: "SI", placeholder: "Enter value" }; return <label className="quantity-field" key={name}><span>{spec.label}<small>{unitFor(name)}</small></span><input type="number" step="any" inputMode="decimal" value={inputs[name] ?? ""} onChange={(e) => setInputs({ ...inputs, [name]: e.target.value })} placeholder={spec.placeholder.replace(/\s.+$/, "")} required /></label>; })}</div>
            {selected.name === "initial_stability" && <p className={`field-note ${gmWarning ? "warning-note" : ""}`}>GM &gt; 0: stable. GM = 0: neutral. GM &lt; 0: unstable. Values above about 5 m are unusual for ordinary vessel stability and should be checked against the vessel model, units, and loading condition.{gmWarning && " Current value is unusually large; result needs engineering review."}</p>}
            <label className="research-toggle"><input type="checkbox" checked={research} onChange={(e) => setResearch(e.target.checked)} /> Research mode, allow non-approved formulas</label>
            <button type="button" className="primary-action" onClick={doRun} disabled={running}>{running ? "Calculating..." : "Run calculation"}</button>
            {runError && <div className="state-panel error-state" role="alert">{runError}</div>}
            {runResult && <div className="result-panel"><p className="eyebrow">Verified output</p><strong>{typeof runResult.result === "object" ? JSON.stringify(runResult.result) : String(runResult.result)}</strong><span>{runResult.evidence_status} · {runResult.formula_review_status ?? "formula status unavailable"}</span></div>}
          </div>}
        </section>
      </div>
    </div>
  );
}
