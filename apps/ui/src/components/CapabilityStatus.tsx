import { useQuery } from "@tanstack/react-query";
import { listCapabilities } from "../api/client";

const labels: Record<string, string> = {
  SUPPORTED: "Supported",
  UNKNOWN: "Unknown",
  UNSUPPORTED: "Unsupported",
  UNAVAILABLE: "Unavailable",
};

export function CapabilityStatus() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["capabilities"], queryFn: listCapabilities });
  if (isLoading) return <p className="quiet-text">Loading capability status…</p>;
  if (isError) return <p className="quiet-text">Capability status unavailable. Retry later.</p>;
  return <div className="capability-list">
    {(data?.capabilities ?? []).filter((item) => item.name.includes("hull")).map((item) => (
      <div className="capability-row" key={`${item.connector_id ?? "internal"}:${item.name}`}>
        <div><strong>{item.name}</strong><small>{item.notes ?? "No notes."}</small></div>
        <span className={`capability-badge capability-${item.status.toLowerCase()}`}>{labels[item.status] ?? item.status}</span>
      </div>
    ))}
  </div>;
}
