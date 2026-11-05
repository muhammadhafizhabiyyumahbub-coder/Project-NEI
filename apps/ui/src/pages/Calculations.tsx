import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listFormulas, runCalculation } from "../api/client";
import type { Formula, CalcRun } from "../api/client";

export function Calculations() {
  const { data: formulas, isLoading, error, refetch } = useQuery({
    queryKey: ["formulas"],
    queryFn: () => listFormulas(),
  });
  const [selected, setSelected] = useState<Formula | null>(null);
  const [inputsJson, setInputsJson] = useState("{}");
  const [runResult, setRunResult] = useState<CalcRun | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  async function doRun() {
    if (!selected) return;
    setRunning(true);
    setRunError(null);
    try {
      const parsed: Record<string, unknown> = JSON.parse(inputsJson || "{}");
      const r = await runCalculation({ formula_id: selected.id, inputs: parsed, research: true });
      setRunResult(r);
      refetch();
    } catch (e) {
      setRunError((e as Error).message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Calculations</h2>
      <div className="mb-4">
        <h3 className="font-medium mb-2">Formulas</h3>
        {isLoading ? <p>Loading...</p> : error ? <p className="text-error">Error: {error.message}</p> : (
          <ul className="space-y-2">
            {formulas?.map((f) => (
              <li key={f.id} className="p-3 border rounded">
                <div className="flex justify-between">
                  <span className="font-medium">{f.name}</span>
                  <span className="text-sm text-gray-500">{f.domain} · {f.review_status}</span>
                </div>
                <div className="text-xs text-gray-400 font-mono mt-1">{f.equation_text}</div>
                <button
                  onClick={() => { setSelected(f); setInputsJson("{}"); setRunResult(null); setRunError(null); }}
                  className="mt-2 px-2 py-1 text-sm bg-primary text-primary-foreground rounded"
                >
                  Run
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      {selected && (
        <div>
          <h3 className="font-medium mb-2">Run {selected.name}</h3>
          <div className="mb-4">
            <textarea
              value={inputsJson}
              onChange={(e) => setInputsJson(e.target.value)}
              placeholder='{"length": 10, "width": 3, "height": 1}'
              className="w-full p-2 border rounded font-mono text-sm"
              rows={3}
            />
          </div>
          <button onClick={doRun} disabled={running} className="px-3 py-1 bg-primary text-primary-foreground rounded">
            {running ? "Running..." : "Run Calculation"}
          </button>
          {runError && (
            <div className="mt-4 p-4 border rounded text-error text-sm">{runError}</div>
          )}
          {runResult && (
            <div className="mt-4 p-4 border rounded">
              <h4 className="font-medium mb-2">Result</h4>
              <div className="text-sm flex gap-4 mb-2">
                <span>Status: <span className="font-mono">{runResult.evidence_status}</span></span>
                <span>Formula status: <span className="font-mono">{runResult.formula_review_status}</span></span>
              </div>
              <pre className="text-sm">{JSON.stringify(runResult.result ?? runResult, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
