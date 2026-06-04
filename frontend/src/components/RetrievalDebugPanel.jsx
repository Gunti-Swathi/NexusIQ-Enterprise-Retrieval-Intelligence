import { formatScorePercent } from "../utils/ragDisplay";

export function RetrievalDebugPanel({ result, chunks, requestedTopK, documents = [], evidenceUnits = [] }) {
  if (!result) return null;
  const originalQuery = result.retrieval_debug?.original_query ?? "";
  const expandedQueries = (result.expanded_queries ?? []).filter((query) => query && query !== originalQuery);
  const debugChunks = result.retrieval_debug?.reranked_chunks?.length
    ? result.retrieval_debug.reranked_chunks
    : chunks?.length ? chunks : (result.selected_context ?? result.retrieved_chunks ?? []);
  const topKBefore = result.retrieval_debug?.retrieved_chunks?.length || Math.max(debugChunks.length, requestedTopK ?? 0);
  const topKAfter = result.retrieval_debug?.reranked_chunks?.length || result.selected_context?.length || result.retrieved_chunks?.length || debugChunks.length;
  const chunksSearched = documents.reduce((sum, doc) => sum + (doc.chunk_count ?? 0), 0) || result.retrieval_debug?.retrieved_chunks?.length || debugChunks.length;
  const citationById = new Map(evidenceUnits.map((chunk) => [chunk.id, chunk.citation_id]));
  return (
    <section className="answer-panel debug-panel">
      <h2>Retrieval Debug</h2>
      <dl className="debug-meta-grid">
        <MetaItem label="Original query" value={originalQuery} />
        <MetaItem label="Detected intent" value={result.query_type ?? "answer"} />
        <MetaItem label="Retrieval mode" value="Hybrid BM25 + Semantic" />
        <MetaItem label="Semantic retriever" value="ChromaDB" />
        <MetaItem label="Keyword retriever" value="BM25" />
        <MetaItem label="Reranker" value="Applied" />
        <MetaItem label="Context compression" value={result.should_compress_context ? "Applied" : "Skipped"} />
        <MetaItem label="Top K before rerank" value={topKBefore} />
        <MetaItem label="Top K after rerank" value={topKAfter} />
        <MetaItem label="Documents searched" value={documents.length || "N/A"} />
        <MetaItem label="Chunks searched" value={chunksSearched} />
        <MetaItem label="Final chunks selected" value={evidenceUnits.length || result.selected_context?.length || debugChunks.length} />
        {expandedQueries.length > 0 && (
          <MetaItem label="Expanded queries" value={expandedQueries.join(" | ")} wide />
        )}
      </dl>
      <p className="debug-note">Scores are normalized retrieval signals used for ranking and debugging. A lower retrieval score does not automatically mean the answer is unsupported.</p>
      <div className="debug-table">
        <div className="debug-row debug-head">
          <span>Source</span>
          <span>Chunk</span>
          <span>Semantic</span>
          <span>Keyword</span>
          <span>Final</span>
        </div>
        {debugChunks.map((chunk, index) => (
          <div className="debug-row" key={chunk.id}>
            <span>[{citationById.get(chunk.id) ?? chunk.source_number ?? index + 1}]</span>
            <span>{chunk.chunk_index}</span>
            <ScoreBar value={chunk.semantic_score ?? chunk.query_relevance} zeroAsUnavailable />
            <ScoreBar value={chunk.bm25_score} />
            <ScoreBar value={chunk.rerank_score ?? chunk.hybrid_score ?? chunk.score} />
          </div>
        ))}
      </div>
    </section>
  );
}

function MetaItem({ label, value, wide = false }) {
  return (
    <div className={wide ? "debug-meta-item wide" : "debug-meta-item"}>
      <dt>{label}</dt>
      <dd>{value || "n/a"}</dd>
    </div>
  );
}

function ScoreBar({ value, zeroAsUnavailable = false }) {
  const unavailable = typeof value !== "number" || Number.isNaN(value) || (zeroAsUnavailable && value <= 0);
  const score = unavailable ? 0 : Math.max(0, Math.min(1, value));
  return (
    <span className={unavailable ? "score-bar score-empty" : "score-bar"}>
      <i style={{ width: `${score * 100}%` }} />
      <b>{unavailable ? "N/A" : formatScorePercent(value)}</b>
    </span>
  );
}
