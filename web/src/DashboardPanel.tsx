import React, {useEffect, useState} from "react";

const API = "https://ws9dklzhac.execute-api.ap-southeast-2.amazonaws.com";

type Execution = {
  execution_id: string;
  status: string;
  timestamp: string;
  source_key: string;
  error: string;
  record_count: number;
};

type KnowledgeResult = {
  text: string;
  score?: number;
  source_uri?: string;
};

type Props = {
  tab: "diagnostics" | "knowledge";
  getToken: () => Promise<string>;
};

export default function DashboardPanel({tab, getToken}: Props) {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KnowledgeResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function api(path: string, payload?: object) {
    const token = await getToken();
    const res = await fetch(API + path, {
      method: payload ? "POST" : "GET",
      headers: {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
      },
      ...(payload ? {body: JSON.stringify(payload)} : {})
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || `Request failed (${res.status})`);
    }
    return data;
  }

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const data = await api("/diagnostics?limit=25");
      setExecutions(data.executions || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Diagnostics failed");
    } finally {
      setLoading(false);
    }
  }

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim() || loading) return;
    setLoading(true);
    setError("");
    try {
      const data = await api("/knowledge", {query: query.trim()});
      setResults(data.results || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (tab === "diagnostics") void refresh();
  }, [tab]);

  return (
    <section className="dashboard-panel">
      <header className="dashboard-header">
        <div>
          <h1>{tab === "diagnostics" ? "Execution Diagnostics" : "Knowledge Base"}</h1>
          <p>
            {tab === "diagnostics"
              ? "Recent customer-ingestion execution results"
              : "Search troubleshooting SOPs and known errors"}
          </p>
        </div>
        {tab === "diagnostics" && (
          <button className="dashboard-button" onClick={refresh} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </button>
        )}
      </header>

      {error && <p className="error" role="alert">{error}</p>}

      {tab === "diagnostics" ? (
        <div className="dashboard-content">
          <div className="dashboard-stats">
            <div>Total <strong>{executions.length}</strong></div>
            <div>Successful <strong>{executions.filter(x => x.status === "SUCCEEDED").length}</strong></div>
            <div>Failed <strong>{executions.filter(x => x.status === "FAILED").length}</strong></div>
          </div>

          {executions.length === 0 && !loading && <p>No executions returned.</p>}

          {executions.map(item => (
            <article className="dashboard-card" key={item.execution_id}>
              <div className="dashboard-card-heading">
                <b>{item.source_key}</b>
                <span className={item.status === "SUCCEEDED" ? "status-ok" : "status-fail"}>
                  {item.status}
                </span>
              </div>
              <p>{new Date(item.timestamp).toLocaleString()}</p>
              <p>Records processed: {item.record_count}</p>
              {item.error && <p className="error">{item.error}</p>}
              <small>Execution: {item.execution_id}</small>
            </article>
          ))}
        </div>
      ) : (
        <div className="dashboard-content">
          <form className="knowledge-search" onSubmit={search}>
            <input
              aria-label="Search knowledge base"
              placeholder="e.g. How do I fix SCHEMA_MISMATCH?"
              value={query}
              maxLength={1000}
              onChange={e => setQuery(e.target.value)}
            />
            <button disabled={loading || !query.trim()}>
              {loading ? "Searching..." : "Search"}
            </button>
          </form>

          {results.map((item, i) => (
            <article className="dashboard-card" key={i}>
              <div className="dashboard-card-heading">
                <b>Document {i + 1}</b>
                {typeof item.score === "number" && (
                  <span>Score: {item.score.toFixed(3)}</span>
                )}
              </div>
              <p className="knowledge-text">{item.text}</p>
              {item.source_uri && <small className="source-uri">{item.source_uri}</small>}
            </article>
          ))}
          <p className="dashboard-note">Retrieved SOPs are synthetic. Verify before taking operational action.</p>
        </div>
      )}
    </section>
  );
}
