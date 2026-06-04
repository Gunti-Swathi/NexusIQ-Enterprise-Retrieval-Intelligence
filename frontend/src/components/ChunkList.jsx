import { cleanPreview, displayTitle, formatScorePercent } from "../utils/ragDisplay";

export function ChunkList({ chunks, evidenceUnits = [], usedChunkIds = new Set() }) {
  if (!chunks.length) return <p className="muted">No retrieved chunks yet.</p>;
  const citationById = new Map(evidenceUnits.map((chunk) => [chunk.id, chunk.citation_id]));
  return (
    <div className="chunk-list">
      {chunks.map((chunk, index) => {
        const used = usedChunkIds.has(chunk.id);
        const citationId = citationById.get(chunk.id) ?? chunk.source_number ?? index + 1;
        return (
          <article className="chunk evidence-card" key={chunk.id}>
            <header>
              <strong>[{citationId}]</strong>
              <span title={chunk.filename}>{displayTitle(chunk.filename)}</span>
              <em className={used ? "used-badge" : "unused-badge"}>Used in answer: {used ? "Yes" : "No"}</em>
            </header>
            <div className="evidence-meta">
              <ScoreLabel label="Chunk" value={chunk.chunk_index} plain />
              <ScoreLabel label="Semantic Match" value={chunk.semantic_score ?? chunk.query_relevance} zeroAsUnavailable />
              <ScoreLabel label="Keyword Match" value={chunk.bm25_score} />
              <ScoreLabel label="Final Score" value={chunk.rerank_score ?? chunk.hybrid_score ?? chunk.score} />
            </div>
            <p>{cleanPreview(chunk.text)}</p>
          </article>
        );
      })}
    </div>
  );
}

function ScoreLabel({ label, value, plain = false, zeroAsUnavailable = false }) {
  return (
    <span>
      <small>{label}</small>
      <strong>{plain ? value ?? "N/A" : formatScorePercent(value, { zeroAsUnavailable })}</strong>
    </span>
  );
}
