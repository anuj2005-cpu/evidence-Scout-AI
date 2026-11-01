import { useEffect, useState } from "react";
import {
  Activity, ArrowRight, BadgeCheck, BookOpen, CheckCircle, CheckCircle2, CircleHelp,
  Clock3, ExternalLink, FileSearch, GitBranch, Globe, HelpCircle, Info, LoaderCircle,
  Search, ShieldCheck, Sparkles, TriangleAlert, XCircle
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const verdictInfo = {
  "Supported": { icon: CheckCircle2, className: "supported", detail: "The model found signals consistent with support." },
  "Refuted": { icon: XCircle, className: "refuted", detail: "The model found signals consistent with contradiction." },
  "Not Enough Evidence": { icon: CircleHelp, className: "insufficient", detail: "Available model inputs may not be enough to decide." },
  "Conflicting Evidence/Cherrypicking": { icon: TriangleAlert, className: "conflicting", detail: "Signals may point in different directions." }
};

function App() {
  const [claim, setClaim] = useState("");
  const [autoRetrieve, setAutoRetrieve] = useState(true);
  const [evidenceText, setEvidenceText] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [apiStatus, setApiStatus] = useState("checking");

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => setApiStatus(data.status === "ok" ? "online" : "offline"))
      .catch(() => setApiStatus("offline"));
  }, []);

  async function verifyClaim(event) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!claim.trim()) {
      setError("Enter a claim or headline first.");
      return;
    }

    if (!autoRetrieve && !evidenceText.trim()) {
      setError("Please enter supporting evidence, or enable auto-retrieval.");
      return;
    }

    setBusy(true);
    try {
      const payload = {
        claim: claim.trim(),
        evidence: (!autoRetrieve && evidenceText.trim()) ? [
          {
            text: evidenceText.trim(),
            source_url: sourceUrl.trim() || null,
            source_medium: "Web",
            claim_date: null,
            evidence_date: null,
            question: ""
          }
        ] : [],
        auto_retrieve: autoRetrieve
      };

      const response = await fetch(`${API_BASE}/api/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || data.message || "The verification request failed.");
      }
      setResult(data);
    } catch (e) {
      setError(e.message || "Could not reach the TruthGraph API. Check that the backend is running.");
    } finally {
      setBusy(false);
    }
  }

  const verdict = result?.verdict ? verdictInfo[result.verdict] : null;
  const VerdictIcon = verdict?.icon;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><GitBranch size={23} strokeWidth={2.4} /></div>
          <div><div className="brand-name">TruthGraph</div><div className="brand-caption">CLAIM INTELLIGENCE</div></div>
        </div>
        <div className="sidebar-rule" />
        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active"><ShieldCheck size={18} /> Claim verification</div>
        <div className="nav-item muted"><BookOpen size={18} /> Evidence explorer <span className="soon">LATER</span></div>
        <div className="nav-item muted"><Clock3 size={18} /> Recent checks <span className="soon">LATER</span></div>
        <div className="sidebar-bottom">
          <div className="status-card">
            <div className="status-head"><span className={`status-dot ${apiStatus}`} /> API status</div>
            <strong>{apiStatus === "online" ? "Connected" : apiStatus === "checking" ? "Checking…" : "Not connected"}</strong>
            <p>{apiStatus === "online" ? "Backend health check passed." : "Start the FastAPI server to enable verification."}</p>
          </div>
          <div className="sidebar-foot"><span className="tiny-mark">TG</span> Evidence first. Conclusions second.</div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="breadcrumb">Workspace <span>/</span> <strong>Claim verification</strong></div>
          <div className="topbar-right"><span className="mode-pill"><span className="mode-dot" /> MODEL WORKSPACE</span></div>
        </header>

        <section className="hero">
          <div className="eyebrow"><Sparkles size={14} /> YOUR FACT-CHECKING WORKSPACE</div>
          <h1>Follow the evidence.<br /><span>Understand the claim.</span></h1>
          <p className="hero-copy">Submit a statement to extract signals, analyze evidence from the live web, and estimate factual support.</p>
        </section>

        <section className="workspace-grid">
          <div className="input-card panel">
            <div className="card-head">
              <div>
                <div className="mini-heading">STATEMENT INPUT</div>
                <h2>Claim to evaluate</h2>
              </div>
              <span className="step-pill">STEP 01</span>
            </div>

            <form onSubmit={verifyClaim}>
              <label htmlFor="claim">CLAIM OR HEADLINE</label>
              <textarea
                id="claim"
                value={claim}
                onChange={e => setClaim(e.target.value)}
                maxLength={3000}
                placeholder="Example: India won the ICC Men's T20 World Cup in 2024…"
              />

              {/* Auto Retrieve Toggle */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  padding: "10px 14px",
                  marginTop: "12px",
                  background: "#f1f5f9",
                  borderRadius: "8px",
                  cursor: "pointer"
                }}
                onClick={() => setAutoRetrieve(!autoRetrieve)}
              >
                <input
                  type="checkbox"
                  id="autoRetrieveCheckbox"
                  checked={autoRetrieve}
                  onChange={e => setAutoRetrieve(e.target.checked)}
                  style={{ width: "16px", height: "16px", cursor: "pointer" }}
                />
                <label htmlFor="autoRetrieveCheckbox" style={{ margin: 0, cursor: "pointer", fontSize: "13px", fontWeight: 600, color: "#1e293b" }}>
                  🌐 Auto-retrieve live evidence from web (Recommended)
                </label>
              </div>

              {!autoRetrieve && (
                <div style={{ marginTop: "14px", padding: "12px", border: "1px dashed #cbd5e1", borderRadius: "8px" }}>
                  <label htmlFor="evidence">MANUAL SUPPORTING EVIDENCE</label>
                  <textarea
                    id="evidence"
                    rows={3}
                    value={evidenceText}
                    onChange={e => setEvidenceText(e.target.value)}
                    placeholder="Paste evidence text from your source..."
                  />

                  <label htmlFor="sourceUrl" style={{ marginTop: "8px" }}>SOURCE URL (OPTIONAL)</label>
                  <input
                    id="sourceUrl"
                    type="url"
                    value={sourceUrl}
                    onChange={e => setSourceUrl(e.target.value)}
                    placeholder="https://example.com/article"
                  />
                </div>
              )}

              <div className="form-actions" style={{ marginTop: "16px" }}>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => { setClaim(""); setEvidenceText(""); setSourceUrl(""); setResult(null); setError(""); }}
                >
                  Clear text
                </button>
              </div>

              <button className="verify-button" type="submit" disabled={busy}>
                {busy ? <><LoaderCircle className="spin" size={18} /> Retrieving evidence & analyzing…</> : <>Verify claim <ArrowRight size={18} /></>}
              </button>

              <div className="privacy-note">
                <ShieldCheck size={15} /> Your claim is analyzed by the 47-feature Random Forest intelligence pipeline.
              </div>
            </form>

            {error && (
              <div className="error-box">
                <TriangleAlert size={18} />
                <div><strong>Could not verify this claim</strong><p>{error}</p></div>
              </div>
            )}
          </div>

          <div className="process-panel">
            <div className="mini-heading">HOW IT WORKS</div>
            <div className="process-step">
              <div className="step-icon"><Search size={18} /></div>
              <div><strong>01 · Input</strong><p>A statement enters the verification pipeline.</p></div>
            </div>
            <div className="step-line" />
            <div className="process-step">
              <div className="step-icon"><Globe size={18} /></div>
              <div><strong>02 · Web Retrieval</strong><p>Live factual snippets & sources are gathered from the web.</p></div>
            </div>
            <div className="step-line" />
            <div className="process-step">
              <div className="step-icon"><Activity size={18} /></div>
              <div><strong>03 · Analyze</strong><p>47 signals (NLI, polarity, temporal) are extracted for inference.</p></div>
            </div>
            <div className="step-line" />
            <div className="process-step">
              <div className="step-icon"><BadgeCheck size={18} /></div>
              <div><strong>04 · Explainable Verdict</strong><p>Read model prediction, decision rationale, and evidence signals.</p></div>
            </div>
            <div className="pipeline-note">
              <Globe size={16} /><span>Live Web Evidence Retrieval & XAI Active.</span>
            </div>
          </div>
        </section>

        {result && (
          <section className="results-section">
            <div className="results-heading">
              <div>
                <div className="eyebrow"><BadgeCheck size={14} /> ANALYSIS RESPONSE</div>
                <h2>Verification result</h2>
              </div>
              <span className="response-tag">API RESPONSE</span>
            </div>

            {/* Verdict Card */}
            <div className={`verdict-card ${verdict?.className || ""}`}>
              <div className="verdict-symbol">
                {VerdictIcon ? <VerdictIcon size={25} /> : <BadgeCheck size={25} />}
              </div>
              <div className="verdict-main">
                <div className="mini-heading">PREDICTED VERDICT</div>
                <h3>{result.verdict || "Prediction returned"}</h3>
                <p>{verdict?.detail || "Review the model output alongside evidence."}</p>
              </div>
              {typeof result.confidence === "number" && (
                <div className="confidence">
                  <strong>{(result.confidence * 100).toFixed(1)}%</strong>
                  <span>model score</span>
                </div>
              )}
            </div>

            {/* MODERN EXPLAINABLE VERDICT CARD */}
            {result.explanation && (
                <div style={{
                    marginTop: "20px",
                    padding: "24px",
                    borderRadius: "16px",
                    background: "#ffffff",
                    border: "1px solid #e2e8f0",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.03)"
                  }}>
                    {/* Section Header */}
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <div style={{ background: "#eff6ff", padding: "8px", borderRadius: "10px", color: "#2563eb", display: "flex" }}>
                          <Sparkles size={20} />
                        </div>
                        <div>
                          <h3 style={{ margin: 0, fontSize: "17px", fontWeight: 700, color: "#0f172a" }}>
                            Why did the model reach this verdict?
                          </h3>
                          <span style={{ fontSize: "12px", color: "#64748b" }}>EXPLAINABLE AI (XAI) BREAKDOWN</span>
                        </div>
                      </div>
                      <span style={{
                        fontSize: "11px",
                        fontWeight: 700,
                        letterSpacing: "0.5px",
                        background: "#f1f5f9",
                        color: "#475569",
                        padding: "4px 10px",
                        borderRadius: "20px"
                      }}>
                        47 SIGNALS ANALYZED
                      </span>
                    </div>

                    {/* Plain English Headline Callout */}
                    <div style={{
                      padding: "16px",
                      borderRadius: "12px",
                      background: result.verdict === "Supported" ? "#f0fdf4" : result.verdict === "Refuted" ? "#fef2f2" : "#f8fafc",
                      borderLeft: `4px solid ${result.verdict === "Supported" ? "#22c55e" : result.verdict === "Refuted" ? "#ef4444" : "#f59e0b"}`,
                      marginBottom: "20px"
                    }}>
                      <div style={{ fontSize: "15px", fontWeight: 700, color: "#1e293b", marginBottom: "4px" }}>
                        {result.explanation.headline || "Decision Analysis"}
                      </div>
                      <div style={{ fontSize: "13.5px", color: "#475569", lineHeight: 1.5 }}>
                        {result.explanation.takeaway}
                      </div>
                    </div>

                    {/* Visual Signal Distribution Bar */}
                    <div style={{ marginBottom: "20px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", fontWeight: 600, color: "#64748b", marginBottom: "8px" }}>
                        <span>EVIDENCE STANCE DISTRIBUTION</span>
                        <span>{result.evidence?.length || 0} Sources Retrieved</span>
                      </div>
                      <div style={{ display: "flex", height: "10px", borderRadius: "6px", overflow: "hidden", background: "#f1f5f9" }}>
                        <div style={{
                          width: `${((result.explanation.signals?.supporting_count || 0) / Math.max(1, result.evidence?.length || 1)) * 100}%`,
                          background: "#22c55e",
                          transition: "width 0.4s ease"
                        }} title="Supporting" />
                        <div style={{
                          width: `${((result.explanation.signals?.contradicting_count || 0) / Math.max(1, result.evidence?.length || 1)) * 100}%`,
                          background: "#ef4444",
                          transition: "width 0.4s ease"
                        }} title="Contradicting" />
                        <div style={{
                          width: `${((result.explanation.signals?.neutral_count || 0) / Math.max(1, result.evidence?.length || 1)) * 100}%`,
                          background: "#94a3b8",
                          transition: "width 0.4s ease"
                        }} title="Neutral / Context" />
                      </div>
                    </div>

                    {/* 3 Intuitive Signal Cards */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", marginBottom: "20px" }}>
                      <div style={{ padding: "14px", borderRadius: "10px", background: "#f8fafc", border: "1px solid #f1f5f9" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#16a34a", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>
                          <CheckCircle size={15} /> SUPPORTING SIGNALS
                        </div>
                        <div style={{ fontSize: "20px", fontWeight: 800, color: "#0f172a" }}>
                          {result.explanation.signals?.supporting_count || 0}
                        </div>
                        <div style={{ fontSize: "11px", color: "#64748b" }}>Sources confirming the claim</div>
                      </div>

                      <div style={{ padding: "14px", borderRadius: "10px", background: "#f8fafc", border: "1px solid #f1f5f9" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#dc2626", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>
                          <XCircle size={15} /> CONFLICTING SIGNALS
                        </div>
                        <div style={{ fontSize: "20px", fontWeight: 800, color: "#0f172a" }}>
                          {result.explanation.signals?.contradicting_count || 0}
                        </div>
                        <div style={{ fontSize: "11px", color: "#64748b" }}>Sources refuting the claim</div>
                      </div>

                      <div style={{ padding: "14px", borderRadius: "10px", background: "#f8fafc", border: "1px solid #f1f5f9" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#2563eb", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>
                          <Globe size={15} /> DOMAIN DIVERSITY
                        </div>
                        <div style={{ fontSize: "20px", fontWeight: 800, color: "#0f172a" }}>
                          {result.explanation.signals?.domain_diversity || 1}
                        </div>
                        <div style={{ fontSize: "11px", color: "#64748b" }}>Independent source domain(s)</div>
                      </div>
                    </div>

                    {/* Key Findings Checklist */}
                    {result.explanation.findings && (
                      <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "14px" }}>
                        <div style={{ fontSize: "12px", fontWeight: 700, color: "#64748b", marginBottom: "8px", letterSpacing: "0.5px" }}>
                          KEY OBSERVATIONS
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                          {result.explanation.findings.map((f, i) => (
                            <div key={i} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", color: "#334155" }}>
                              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#3b82f6" }} />
                              {f}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                {/* Key Drivers List */}
                {result.explanation.key_drivers && (
                  <div>
                    <div style={{ fontSize: "12px", fontWeight: 700, color: "#64748b", marginBottom: "8px" }}>KEY CONTRIBUTING SIGNALS</div>
                    <ul style={{ margin: 0, paddingLeft: "18px", color: "#475569", fontSize: "13px", lineHeight: 1.6 }}>
                      {result.explanation.key_drivers.map((driver, idx) => (
                        <li key={idx}>{driver}</li>
                      ))}
                    </ul>
                  </div>
                )}
            {/* Class Scores */}
            {result.scores && (
              <div className="scores-panel panel" style={{ marginTop: "20px" }}>
                <h3>Class scores</h3>
                {Object.entries(result.scores).map(([label, score]) => (
                  <div className="score-row" key={label}>
                    <div className="score-label">{label}</div>
                    <div className="score-track">
                      <div className="score-fill" style={{ width: `${Math.max(0, Math.min(1, Number(score))) * 100}%` }} />
                    </div>
                    <div className="score-number">{(Number(score) * 100).toFixed(1)}%</div>
                  </div>
                ))}
              </div>
            )}

            {/* Live Web Evidence Sources Section with Stance Badges */}
            {result.evidence && result.evidence.length > 0 && (
              <div className="panel" style={{ marginTop: "20px", padding: "20px", borderRadius: "12px", background: "#ffffff", border: "1px solid #e2e8f0" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
                  <Globe size={20} color="#2563eb" />
                  <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "#1e293b" }}>
                    Retrieved Evidence Sources & Stance ({result.evidence.length})
                  </h3>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                  {result.evidence.map((item, idx) => {
                    const isSupport = item.polarity === "SUPPORT";
                    const isContradict = item.polarity === "CONTRADICT";
                    const badgeBg = isSupport ? "#dcfce7" : isContradict ? "#fee2e2" : "#f1f5f9";
                    const badgeColor = isSupport ? "#15803d" : isContradict ? "#b91c1c" : "#475569";

                    return (
                      <div key={idx} style={{ padding: "14px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                          <span style={{ fontSize: "11px", fontWeight: 700, padding: "3px 8px", borderRadius: "4px", background: badgeBg, color: badgeColor }}>
                            {item.polarity || "NEUTRAL CONTEXT"}
                          </span>
                          <span style={{ fontSize: "12px", color: "#64748b", fontWeight: 600 }}>
                            {item.source_title || "Web Source"}
                          </span>
                        </div>
                        <div style={{ color: "#334155", fontSize: "13.5px", lineHeight: 1.6, marginBottom: "8px" }}>
                          "{item.text}"
                        </div>
                        {item.source_url && (
                          <a
                            href={item.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: "#2563eb", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "5px", fontSize: "12px", fontWeight: 600 }}
                          >
                            <span>Open source article</span>
                            <ExternalLink size={13} />
                          </a>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="disclaimer">
              <ShieldCheck size={17} />
              <p>Model output is a prediction, not proof. Verify the underlying sources before relying on a verdict.</p>
            </div>
          </section>
        )}

        <footer>
          <span>TRUTHGRAPH · EVIDENCE-BASED MISINFORMATION INTELLIGENCE</span>
          <span>Predictions require evidence and context.</span>
        </footer>
      </main>
    </div>
  );
}

export default App;