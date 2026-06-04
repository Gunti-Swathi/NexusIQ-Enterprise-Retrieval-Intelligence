import { CheckCircle2, FileText, PlayCircle, Trash2, UploadCloud } from "lucide-react";
import { useState } from "react";
import { api } from "../services/api";

const MAX_FILES = 15;
const ACCEPTED_TYPES = ".pdf,.docx,.txt,.csv";
const INDEXING_STEPS = [
  "Validating files",
  "Extracting text",
  "Chunking documents",
  "Creating embeddings",
  "Writing vector index",
  "Finalizing corpus",
];

export function UploadPage() {
  const [targetCount, setTargetCount] = useState(3);
  const [queuedFiles, setQueuedFiles] = useState([]);
  const [status, setStatus] = useState("No files staged yet.");
  const [statusKind, setStatusKind] = useState("info");
  const [busy, setBusy] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [completedSteps, setCompletedSteps] = useState([]);

  function addFiles(files) {
    if (!files?.length) return;
    const incoming = Array.from(files).filter(isSupportedFile);
    const rejectedCount = files.length - incoming.length;
    const availableSlots = Math.max(0, targetCount - queuedFiles.length);
    const accepted = incoming.slice(0, availableSlots);
    const merged = [...queuedFiles, ...accepted].slice(0, targetCount);
    setQueuedFiles(merged);
    const remaining = targetCount - merged.length;
    if (rejectedCount) {
      setStatusKind("warning");
      setStatus(`Skipped ${rejectedCount} unsupported file${rejectedCount === 1 ? "" : "s"}. Use PDF, DOCX, TXT, or CSV.`);
      return;
    }
    if (incoming.length > availableSlots) {
      setStatusKind("warning");
      setStatus(`Added ${accepted.length} file${accepted.length === 1 ? "" : "s"} and ignored ${incoming.length - accepted.length} extra. This batch only accepts ${targetCount}.`);
      return;
    }
    setStatusKind(remaining === 0 ? "success" : "info");
    setStatus(remaining === 0 ? `Ready to index exactly ${targetCount} document${targetCount === 1 ? "" : "s"}.` : `Added ${accepted.length} file${accepted.length === 1 ? "" : "s"}. Add ${remaining} more document${remaining === 1 ? "" : "s"}.`);
  }

  function updateTargetCount(value) {
    const nextCount = Math.max(1, Math.min(MAX_FILES, Number(value) || 1));
    const removedCount = Math.max(0, queuedFiles.length - nextCount);
    setTargetCount(nextCount);
    setQueuedFiles((current) => current.slice(0, nextCount));
    setStatusKind(removedCount ? "warning" : "info");
    setStatus(removedCount ? `Queue target set to ${nextCount}; removed ${removedCount} extra staged file${removedCount === 1 ? "" : "s"}.` : `Queue target set to ${nextCount} document${nextCount === 1 ? "" : "s"}.`);
  }

  function removeFile(index) {
    const nextLength = queuedFiles.length - 1;
    const remaining = targetCount - nextLength;
    setQueuedFiles((current) => current.filter((_, itemIndex) => itemIndex !== index));
    setStatusKind("info");
    setStatus(`Removed one file. Add ${remaining} more document${remaining === 1 ? "" : "s"} to index this batch.`);
  }

  function clearQueue() {
    setQueuedFiles([]);
    setStatusKind("info");
    setStatus("Queue cleared.");
  }

  async function executeUpload() {
    const filesToIndex = [...queuedFiles];
    const missingCount = targetCount - filesToIndex.length;
    if (!filesToIndex.length) {
      setStatusKind("warning");
      setStatus("No files staged yet.");
      return;
    }
    setBusy(true);
    setCompletedSteps([]);
    setActiveStep(0);
    setStatusKind("info");
    setStatus("Validating files...");
    const timers = startIndexingProgress(setActiveStep, setCompletedSteps, setStatus);
    try {
      const result = await api.upload(filesToIndex);
      timers.forEach((timer) => window.clearTimeout(timer));
      setCompletedSteps(INDEXING_STEPS.map((_, index) => index));
      setActiveStep(INDEXING_STEPS.length);
      setStatusKind("success");
      setStatus(`Indexed ${result.documents.length} document${result.documents.length === 1 ? "" : "s"} successfully.`);
      setQueuedFiles((current) => current.filter((file) => !filesToIndex.includes(file)));
    } catch (err) {
      timers.forEach((timer) => window.clearTimeout(timer));
      setStatusKind("error");
      setStatus(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="page">
      <div className="page-heading">
        <p>Upload Documents</p>
        <h1>Build the local search corpus</h1>
      </div>

      <section className="upload-workflow">
        <div className="upload-step">
          <span className="step-number">1</span>
          <div>
            <h2>How many documents?</h2>
            <p>Choose the batch size first. Maximum {MAX_FILES} documents.</p>
          </div>
          <div className="doc-count-control">
            <button type="button" onClick={() => updateTargetCount(targetCount - 1)} disabled={busy || targetCount <= 1}>
              -
            </button>
            <input
              type="number"
              min="1"
              max={MAX_FILES}
              value={targetCount}
              onChange={(event) => updateTargetCount(event.target.value)}
              disabled={busy}
              aria-label="Document count"
            />
            <button type="button" onClick={() => updateTargetCount(targetCount + 1)} disabled={busy || targetCount >= MAX_FILES}>
              +
            </button>
          </div>
        </div>

        <div className="upload-step">
          <span className="step-number">2</span>
          <div>
            <h2>Add files to queue</h2>
            <p>{queuedFiles.length ? `${queuedFiles.length} file${queuedFiles.length === 1 ? "" : "s"} selected.` : "No files staged yet."}</p>
          </div>
        </div>

        <div className="upload-progress" aria-label={`${queuedFiles.length} of ${targetCount} documents selected`}>
          <div className="upload-progress-top">
            <strong>{queuedFiles.length}/{targetCount}</strong>
            <span>{queuedFiles.length ? "Ready to index selected files" : "No files staged yet"}</span>
          </div>
          <div className="upload-progress-bar">
            <span style={{ width: `${Math.min(100, (queuedFiles.length / targetCount) * 100)}%` }} />
          </div>
        </div>

        {(busy || completedSteps.length > 0) && (
          <div className="indexing-steps">
            {INDEXING_STEPS.map((step, index) => (
              <article
                className={
                  completedSteps.includes(index)
                    ? "indexing-step complete"
                    : activeStep === index
                      ? "indexing-step busy"
                      : "indexing-step"
                }
                key={step}
              >
                <span>{completedSteps.includes(index) ? <CheckCircle2 size={16} /> : index + 1}</span>
                <strong>{step}</strong>
              </article>
            ))}
          </div>
        )}

        <label className={`dropzone ${queuedFiles.length >= targetCount ? "dropzone-disabled" : ""}`}>
          <UploadCloud size={38} />
          <span>{queuedFiles.length >= targetCount ? "Queue is full" : "Choose documents"}</span>
          <small>PDF, DOCX, TXT, CSV</small>
          <input
            type="file"
            multiple
            accept={ACCEPTED_TYPES}
            disabled={busy || queuedFiles.length >= targetCount}
            onChange={(event) => {
              addFiles(event.target.files);
              event.target.value = "";
            }}
          />
        </label>

        <div className="queue-panel">
          <div className="queue-header">
            <div>
              <h2>Ready to index</h2>
              <p>{queuedFiles.length ? "These files are staged but not uploaded yet." : "No files staged yet."}</p>
            </div>
            <button className="ghost-button" type="button" onClick={clearQueue} disabled={busy || !queuedFiles.length}>
              Clear
            </button>
          </div>

          <div className="file-queue">
            {queuedFiles.map((file, index) => (
              <article className="queued-file" key={`${file.name}-${file.size}-${index}`}>
                <FileText size={20} />
                <div>
                  <strong>{file.name}</strong>
                  <span>{Math.max(1, Math.ceil(file.size / 1024))} KB</span>
                </div>
                <CheckCircle2 className="queued-check" size={18} />
                <button className="icon-button" type="button" onClick={() => removeFile(index)} disabled={busy} title="Remove file">
                  <Trash2 size={16} />
                </button>
              </article>
            ))}
          </div>

          <button className="execute-button" type="button" onClick={executeUpload} disabled={busy || !queuedFiles.length}>
            <PlayCircle size={18} />
            {uploadButtonText(busy, completedSteps.length, queuedFiles.length)}
          </button>
        </div>
      </section>

      <div className={`status-line status-${statusKind}`} aria-live="polite">
        {busy ? <span className="spinner" /> : null}
        {status}
      </div>
    </section>
  );
}

function uploadButtonText(busy, completedStepCount, queuedCount) {
  if (busy) return "Indexing...";
  if (completedStepCount > 0 && queuedCount === 0) return "Indexing complete";
  if (!queuedCount) return "Select files to continue";
  return `Index ${queuedCount} document${queuedCount === 1 ? "" : "s"}`;
}

function isSupportedFile(file) {
  return [".pdf", ".docx", ".txt", ".csv"].some((extension) => file.name.toLowerCase().endsWith(extension));
}

function startIndexingProgress(setActiveStep, setCompletedSteps, setStatus) {
  return INDEXING_STEPS.slice(1, -1).map((step, index) => {
    const nextIndex = index + 1;
    return window.setTimeout(() => {
      setCompletedSteps((current) => [...new Set([...current, nextIndex - 1])]);
      setActiveStep(nextIndex);
      setStatus(`${step}...`);
    }, 900 * nextIndex);
  });
}
