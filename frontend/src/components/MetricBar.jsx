export function MetricBar({ metric }) {
  const score = metric.score ?? 0;
  const label = score >= 0.9 ? "Excellent" : score >= 0.7 ? "High" : score >= 0.45 ? "Medium" : "Low";
  const fallback = metric.reason?.toLowerCase().startsWith("local quality estimate");
  const judged = metric.reason?.toLowerCase().startsWith("gemini judge");
  const citationCoverage = metric.name === "citation_coverage";
  const judgeType = judged ? "Gemini Judge" : citationCoverage ? "Fallback Evaluator" : fallback ? "Fallback Evaluator" : "Configured Judge";
  return (
    <div className="metric">
      <div className="metric-top">
        <span>{formatMetricName(metric.name)}</span>
        <strong>{metric.score === null ? "n/a" : `${Math.round(score * 100)}%`}</strong>
      </div>
      <em>{label}</em>
      <small>{judgeType}</small>
      <div className="bar">
        <span style={{ width: `${Math.max(0, Math.min(100, score * 100))}%` }} />
      </div>
      <p>{metricExplanation(metric.name, metric.reason)}</p>
    </div>
  );
}

function formatMetricName(name = "") {
  return name.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function metricExplanation(name, reason = "") {
  const explanations = {
    faithfulness: "Checks whether the answer is supported by the retrieved evidence.",
    answer_relevancy: "Measures how directly the answer addresses the user's question.",
    context_precision: "Checks whether retrieved chunks are focused and useful.",
    context_recall: "Checks whether retrieved context has enough coverage.",
    citation_coverage: "Citation Coverage checks whether factual claims in the generated answer are linked to retrieved evidence.",
  };
  return explanations[name] ?? (reason.toLowerCase().startsWith("local quality estimate") ? cleanFallbackReason(reason) : reason);
}

function cleanFallbackReason(reason = "") {
  return reason.replace(/^Local quality estimate:\s*/i, "");
}
