import { useConnectors } from "../hooks/useConnectors";
import { useQuery } from "@tanstack/react-query";
import { getConnectorCapabilities, getConnectorEvidence } from "../api/client";

export function Connectors() {
  const { connectors, isLoading, error, probe, isProbing } = useConnectors();

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Connectors</h2>
      {isLoading ? <p>Loading...</p> : error ? <p className="text-error">Error: {error.message}</p> : (
        <ul className="space-y-2">
          {connectors.map((c) => (
            <li key={c.id} className="flex flex-col gap-2 p-3 border rounded">
              <div className="flex justify-between items-start">
                <div>
                  <span className="font-medium">{c.name}</span>
                  <div className="text-xs text-gray-500">{c.transport}</div>
                </div>
                <div className="flex gap-2 items-center">
                  <button
                    onClick={() => probe(c.id)}
                    disabled={isProbing}
                    className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm"
                  >
                    Probe
                  </button>
                </div>
              </div>
              <CapabilitySummary connectorId={c.id} />
              <ConnectorEvidence connectorId={c.id} />
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
  const verified = data?.capabilities.filter((c) => (c.evidence?.count ?? 0) > 0).length ?? 0;
  return <span className="text-xs text-gray-500">{unknown} unknown · {verified} evidence-backed</span>;
}

function ConnectorEvidence({ connectorId }: { connectorId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["connector-evidence", connectorId],
    queryFn: () => getConnectorEvidence(connectorId),
    enabled: !!connectorId,
  });

  if (isLoading) return <span className="text-xs text-gray-500">Loading evidence...</span>;
  if (!data?.evidence?.length) return <span className="text-xs text-gray-400">No evidence recorded</span>;

  return (
    <div className="pl-2 border-l-2 border-gray-200">
      <h4 className="text-xs font-bold mb-1 uppercase tracking-wider text-gray-600">Evidence</h4>
      <ul className="space-y-1 text-xs">
        {data.evidence.map((e) => (
          <li key={e.id} className="p-2 border rounded bg-gray-50">
            <div className="flex justify-between items-center">
              <span className="font-medium">{e.capability_name}</span>
              <span className="text-xs text-gray-500">{e.evidence_type}</span>
            </div>
            {e.artifact_sha256 && (
              <div className="text-[10px] text-gray-500 font-mono truncate">
                SHA-256: {e.artifact_sha256}
              </div>
            )}
            {e.notes && <div className="text-[10px] text-gray-500">{e.notes}</div>}
          </li>
        ))}
      </ul>
    </div>
  );
}
