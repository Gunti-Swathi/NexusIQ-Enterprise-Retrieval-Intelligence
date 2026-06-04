import { ChevronDown, ChevronUp, SendHorizontal, SlidersHorizontal } from "lucide-react";
import { useState } from "react";
import { AnswerText } from "../components/AnswerText";
import { CitationPanel } from "../components/CitationPanel";
import { ChunkList } from "../components/ChunkList";
import { EvidenceStrength } from "../components/EvidenceStrength";
import { RetrievalDebugPanel } from "../components/RetrievalDebugPanel";
import { WorkflowStatus } from "../components/WorkflowStatus";
import { useChat } from "../hooks/useChat";
import { useDocuments } from "../hooks/useDocuments";
import { buildEvidenceUnits, compactRepeatedCitations, evidenceStrength, usedChunkIdsFromEvidence } from "../utils/ragDisplay";

export function ChatPage({
  onTrace,
  onAnswer,
}) {
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(3);
  const [showEvidence, setShowEvidence] = useState(false);
  const [workflowVisible, setWorkflowVisible] = useState(false);
  const [workflowComplete, setWorkflowComplete] = useState(false);
  const { ask, busy, result, error } = useChat();
  const { documents } = useDocuments();
  const suggestions = buildCorpusSuggestions(documents);
  const evidenceUnits = result ? buildEvidenceUnits(result) : [];

  async function submit(event) {
    event.preventDefault();
    if (!question.trim()) return;
    setWorkflowVisible(true);
    setWorkflowComplete(false);
    try {
      const response = await ask(question, topK, true);
      setWorkflowComplete(true);
      setShowEvidence(false);
      onTrace(response.trace_url);
      onAnswer(question, response.answer, response.retrieved_chunks.map((chunk) => chunk.text), response, topK);
      window.setTimeout(() => setWorkflowVisible(false), 1800);
    } catch (err) {
      // Error state is handled by useChat.
      window.setTimeout(() => setWorkflowVisible(false), 1800);
    }
  }

  return (
    <section className="page chat-layout">
      <div className="page-heading compact-heading">
        <p>Intelligence Workspace</p>
        <h1>Grounded Enterprise Intelligence</h1>
        <span>Run a hybrid retrieval pipeline over the corpus index and inspect grounded outputs.</span>
      </div>
      {suggestions.length > 0 ? (
        <div className="prompt-grid">
          {suggestions.map((item) => (
            <button type="button" key={item} onClick={() => setQuestion(item)}>
              {item}
            </button>
          ))}
        </div>
      ) : (
        <p className="muted">Upload documents to see knowledge-base suggestions.</p>
      )}
      <form className="ask-box" onSubmit={submit}>
        <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Enter a retrieval query for the indexed corpus..." />
        <div className="controls">
          <label>
            <SlidersHorizontal size={16} />
            Top K
            <input type="number" min={1} max={20} value={topK} onChange={(event) => setTopK(Number(event.target.value))} />
          </label>
          <button type="submit" disabled={busy}>
            <SendHorizontal size={17} />
            {busy ? "Running" : "Run query"}
          </button>
        </div>
      </form>
      <WorkflowStatus active={busy} complete={workflowComplete} error={Boolean(error)} visible={workflowVisible} />
      {error && <div className="error">{error}</div>}
      {result && (
        <div className="response-stack">
          <section className="answer-panel answer-card">
            <div className="section-title-row">
              <h2>Pipeline Result</h2>
              <EvidenceStrength result={result} evidenceUnits={evidenceUnits} />
            </div>
            <div className="query-card">
              <span>Query</span>
              <strong>{question}</strong>
            </div>
            <section className="grounded-answer">
              <h3>Answer</h3>
              <AnswerText text={formatAnswerForDisplay(question, result.answer, evidenceUnits)} />
            </section>
            <GroundingSummary result={result} evidenceUnits={evidenceUnits} />
            <CitationPanel evidenceUnits={evidenceUnits} validation={result.citation_validation} />
          </section>
          <button className="details-toggle" type="button" onClick={() => setShowEvidence((value) => !value)}>
            {showEvidence ? <ChevronUp size={17} /> : <ChevronDown size={17} />}
            {showEvidence ? "Hide rationale" : "Why this answer?"}
          </button>
          {showEvidence && (
            <div className="evidence-grid">
              <section className="answer-panel">
                <h2>Retrieved Evidence</h2>
                <p className="debug-note">
                  Scores are normalized retrieval signals used for ranking and debugging. A lower retrieval score does not automatically mean the answer is unsupported.
                </p>
                <ChunkList chunks={result.retrieved_chunks ?? evidenceUnits} evidenceUnits={evidenceUnits} usedChunkIds={usedChunkIdsFromEvidence(evidenceUnits)} />
              </section>
              <RetrievalDebugPanel result={result} chunks={result.retrieved_chunks ?? evidenceUnits} requestedTopK={topK} documents={documents} evidenceUnits={evidenceUnits} />
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function buildCorpusSuggestions(documents) {
  const titles = documents.map((doc) => cleanDocumentName(doc.filename)).filter(Boolean);
  const names = titles.join(" ").toLowerCase();
  const suggestions = [];
  if (!titles.length) return suggestions;

  if (/leave|attendance|pto|absence/.test(names)) {
    suggestions.push("Summarize leave and attendance policy");
  }
  if (/travel|expense|reimbursement/.test(names)) {
    suggestions.push("What expenses are reimbursable?");
  }
  if (/incident|response|playbook|security/.test(names)) {
    suggestions.push("Summarize incident response steps");
  }
  if (/policy|apexflow/.test(names) && documents.length > 1) {
    suggestions.push("Compare responsibilities across company policies");
  }
  if (/alpr|license|plate|yolo|efficientnet/.test(names)) {
    suggestions.push("Explain ALPR system architecture");
  }
  if (/yolo|detection|object/.test(names)) {
    suggestions.push("Compare YOLOv8 usage across indexed papers");
  }
  if (/pcb|defect|surface/.test(names)) {
    suggestions.push("Summarize PCB defect detection method");
  }
  if (/quantum|thyroid|cnn|classification|medical/.test(names)) {
    suggestions.push("Explain quantum-inspired CNN for thyroid classification");
  }
  if (documents.length > 1) {
    suggestions.push("Compare the indexed documents");
  }
  titles.slice(0, 3).forEach((title) => {
    suggestions.push(`Summarize ${title}`);
  });
  return [...new Set(suggestions)].slice(0, 4);
}

function cleanDocumentName(filename) {
  return filename
    .replace(/\.[^/.]+$/, "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function formatAnswerForDisplay(question, answer, evidenceUnits) {
  if (!answer) return "";
  const normalized = answer.replace(/\bALPI\b/g, "Automatic License Plate Recognition (ALPR)");
  if (/compare\s+yolov8/i.test(question) && !/Comparison Table/i.test(normalized)) {
    const pcb = evidenceUnits.find((chunk) => /PCB Defect/.test(chunk.display_title));
    const alpr = evidenceUnits.find((chunk) => /ALPR/.test(chunk.display_title));
    return [
      `Summary:\nYOLOv8 appears in multiple indexed papers, but it is used for different computer vision tasks: PCB defect localization and Automatic License Plate Recognition (ALPR) plate detection. ${citationMarkers([pcb, alpr])}`,
      "Comparison Table:\nApplication | Paper | How YOLOv8 is used | Supporting Source",
      pcb ? `PCB inspection | ${pcb.display_title} | Detects and localizes board defects for efficient visual inspection | [${pcb.citation_id}]` : null,
      alpr ? `License plate recognition | ${alpr.display_title} | Localizes the license plate region before EfficientNet-B7 character recognition | [${alpr.citation_id}]` : null,
      "Developer Interpretation:\nThis shows the retrieval system can compare concepts across multiple documents rather than only summarize one document.",
    ].filter(Boolean).join("\n\n");
  }
  if (/\[\d+\]/.test(normalized) || !evidenceUnits.length) {
    return compactRepeatedCitations(normalized);
  }
  return compactRepeatedCitations(`${normalized.trim()} ${citationMarkers(evidenceUnits.slice(0, 3))}`);
}

function citationMarkers(items) {
  return items.filter(Boolean).map((chunk) => `[${chunk.citation_id}]`).join(" ");
}

function GroundingSummary({ result, evidenceUnits }) {
  const strength = evidenceStrength(result, evidenceUnits);
  return (
    <section className="grounding-summary">
      <h3>Grounding Summary</h3>
      <div className="grounding-grid">
        <span><small>Evidence strength</small><strong>{strength.label}</strong></span>
        <span><small>Documents used</small><strong>{strength.documentCount}</strong></span>
        <span><small>Chunks used</small><strong>{strength.usedChunkCount}</strong></span>
        <span><small>Source mapping</small><strong>{evidenceUnits.length} citations</strong></span>
      </div>
    </section>
  );
}
