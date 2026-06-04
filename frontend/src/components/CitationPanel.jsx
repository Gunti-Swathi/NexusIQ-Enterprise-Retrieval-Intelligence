import { useEffect, useRef, useState } from "react";
import { formatScorePercent } from "../utils/ragDisplay";

export function CitationPanel({ evidenceUnits = [], validation }) {
  const [activeSource, setActiveSource] = useState(null);
  const panelRef = useRef(null);

  useEffect(() => {
    function closeOnOtherClick(event) {
      const clickedCitation = event.target.closest?.(".source-card");
      const clickedPopover = event.target.closest?.(".source-popover");
      if (!panelRef.current?.contains(event.target) || (!clickedCitation && !clickedPopover)) {
        setActiveSource(null);
      }
    }
    document.addEventListener("mousedown", closeOnOtherClick);
    return () => document.removeEventListener("mousedown", closeOnOtherClick);
  }, []);

  return (
    <section className="source-panel" ref={panelRef}>
      <h3>Sources Used</h3>
      <div className="source-card-grid">
        {evidenceUnits.map((source) => (
          <button
            className={activeSource?.citation_id === source.citation_id ? "source-card active" : "source-card"}
            key={source.id}
            type="button"
            title={source.raw_filename}
            onMouseDown={(event) => event.stopPropagation()}
            onClick={() => setActiveSource((current) => current?.citation_id === source.citation_id ? null : source)}
          >
            <strong>[{source.citation_id}]</strong>
            <span>{source.display_title}</span>
            <small>
              Chunk {source.chunk_index} · Final {formatScorePercent(source.rerank_score ?? source.hybrid_score ?? source.score)} · Used
            </small>
          </button>
        ))}
      </div>
      {activeSource && (
        <aside className="source-popover">
          <strong>[{activeSource.citation_id}] {activeSource.display_title}</strong>
          <span>Raw file: {activeSource.raw_filename}</span>
          <span>Chunk {activeSource.chunk_index}</span>
        </aside>
      )}
      {validation && (
        <p className={validation.valid ? "validation-ok" : "validation-warn"}>
          {validation.valid ? "Sources verified against selected evidence." : validation.reason}
        </p>
      )}
    </section>
  );
}
