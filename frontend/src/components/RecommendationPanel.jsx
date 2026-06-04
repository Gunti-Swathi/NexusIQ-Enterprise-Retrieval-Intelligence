export function RecommendationPanel({ recommendations }) {
  return (
    <section className="answer-panel">
      <h2>Recommendations</h2>
      {recommendations.length === 0 && <p className="muted">No recommendations yet.</p>}
      {recommendations.map((item) => (
        <div className="recommendation" key={`${item.kind}-${item.chunk_id ?? item.document_id}`}>
          <strong>{item.title}</strong>
          <span>{item.kind.replace("_", " ")}</span>
          <p>{item.reason}</p>
        </div>
      ))}
    </section>
  );
}
