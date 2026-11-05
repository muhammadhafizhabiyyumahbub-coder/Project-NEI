import { useConnectors } from "../hooks/useConnectors";
import { useQuery } from "@tanstack/react-query";
import { getConnectorCapabilities } from "../api/client";

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
              <div className="flex gap-2 items-center">
                {c.id === "solidworks2022" && <CapabilitySummary connectorId={c.id} />}
                <button
                  onClick={() => probe(c.id)}
                  disabled={isProbing}
                  className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm"
                >
                  Probe
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function CapabilitySummary({ connectorId }: { connectorId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["connector-capabilities", connectorId],
    queryFn: () => getConnectorCapabilities(connectorId),
  });
  if (isLoading) return <span className="text-xs text-gray-500">Loading capabilities...</span>;
  const unknown = data?.capabilities.filter((c) => c.status === "UNKNOWN").length ?? 0;
  return <span className="text-xs text-gray-500">{unknown} unknown</span>;
}
