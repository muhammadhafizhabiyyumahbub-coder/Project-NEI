import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listEvidenceSources, searchEvidence } from "../api/client";
import type { EvidenceSearchResult } from "../api/client";

export function Evidence() {
  const { data: sources, isLoading, error } = useQuery({
    queryKey: ["evidence-sources"],
    queryFn: listEvidenceSources,
  });
  const [query, setQuery] = useState("");
  const [sourceId, setSourceId] = useState<string>("");
  const [results, setResults] = useState<EvidenceSearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  async function doSearch() {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const r = await searchEvidence(query, sourceId || undefined);
      setResults(r);
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Evidence</h2>
      <div className="mb-4">
        <h3 className="font-medium mb-2">Sources</h3>
        {isLoading ? <p>Loading...</p> : error ? <p className="text-error">Error: {error.message}</p> : (
          <ul className="space-y-2">
            {sources?.map((s) => (
              <li key={s.id} className="p-3 border rounded">
                <div className="flex justify-between">
                  <span className="font-medium">{s.title}</span>
                  <span className="text-sm text-gray-500">{s.source_type}</span>
                </div>
                <div className="text-xs text-gray-400">{s.local_file_path}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div>
        <h3 className="font-medium mb-2">Search</h3>
        <div className="flex gap-2 mb-4">
          <select value={sourceId} onChange={(e) => setSourceId(e.target.value)} className="p-2 border rounded">
            <option value="">All sources</option>
            {sources?.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
          </select>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search evidence..."
            className="flex-1 p-2 border rounded"
            onKeyDown={(e) => e.key === "Enter" && doSearch()}
          />
          <button onClick={doSearch} disabled={searching} className="px-3 py-1 bg-primary text-primary-foreground rounded">
            {searching ? "Searching..." : "Search"}
          </button>
        </div>
        {results.length > 0 && (
          <div>
            <h3 className="font-medium mb-2">Results ({results.length})</h3>
            <ul className="space-y-2">
              {results.map((r, i) => (
                <li key={i} className="p-3 border rounded">
                  <div className="text-sm">{r.text}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {r.source_title}{r.page ? ` · p.${r.page}` : ""}{r.clause ? ` · ${r.clause}` : ""}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
