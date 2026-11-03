import { useConnectors } from "../hooks/useConnectors";

export function Connectors() {
  const { connectors, isLoading, error, probe, isProbing } = useConnectors();

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Connectors</h2>
      {isLoading ? <p>Loading...</p> : error ? <p className="text-error">Error: {error.message}</p> : (
        <ul className="space-y-2">
          {connectors.map((c) => (
            <li key={c.id} className="flex justify-between items-center p-3 border rounded">
              <div>
                <span className="font-medium">{c.name}</span>
                <div className="text-xs text-gray-500">{c.transport}</div>
              </div>
              <button
                onClick={() => probe(c.id)}
                disabled={isProbing}
                className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm"
              >
                Probe
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
