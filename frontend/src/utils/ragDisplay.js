const TITLE_MAP = [
  {
    match: /automated.*printed.*circuit.*board|pcb.*defect/i,
    title: "PCB Defect Detection with YOLOv8",
    category: "Object Detection",
  },
  {
    match: /encompassing.*yolov8.*efficientnet|automatic.*license.*plate|alpr/i,
    title: "ALPR with YOLOv8 and EfficientNet-B7",
    category: "Computer Vision",
  },
  {
    match: /qucnet|quantum.*thyroid|thyroid.*classification/i,
    title: "Quantum-Inspired CNN for Thyroid Classification",
    category: "Medical AI",
  },
];

export function displayTitle(filename = "") {
  const mapped = TITLE_MAP.find((item) => item.match.test(filename));
  if (mapped) return mapped.title;
  return filename
    .replace(/\.[^/.]+$/, "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim() || "Indexed document";
}

export function documentCategory(filename = "") {
  const mapped = TITLE_MAP.find((item) => item.match.test(filename));
  if (mapped) return mapped.category;
  if (/classification|cnn/i.test(filename)) return "Classification";
  if (/detect|yolo|object/i.test(filename)) return "Object Detection";
  return "Computer Vision";
}

export function buildEvidenceUnits(result) {
  const citationIds = new Set((result?.citations ?? []).flatMap((citation) => citation.chunk_ids ?? []));
  const selected = result?.selected_context?.length ? result.selected_context : [];
  const retrieved = result?.retrieved_chunks?.length ? result.retrieved_chunks : [];
  const preferred = citationIds.size
    ? [...selected, ...retrieved].filter((chunk) => citationIds.has(chunk.id))
    : selected.length ? selected : retrieved;
  const unique = [];
  const seen = new Set();
  for (const chunk of preferred) {
    if (!chunk?.id || seen.has(chunk.id)) continue;
    seen.add(chunk.id);
    unique.push(chunk);
  }
  return unique.map((chunk, index) => ({
    ...chunk,
    citation_id: index + 1,
    display_title: displayTitle(chunk.filename),
    raw_filename: chunk.filename,
    used_in_answer: citationIds.size ? citationIds.has(chunk.id) : Boolean(selected.find((item) => item.id === chunk.id)),
  }));
}

export function usedChunkIdsFromEvidence(evidenceUnits) {
  return new Set(evidenceUnits.filter((chunk) => chunk.used_in_answer).map((chunk) => chunk.id));
}

export function formatScorePercent(value, { zeroAsUnavailable = false } = {}) {
  if (typeof value !== "number" || Number.isNaN(value)) return "N/A";
  if (zeroAsUnavailable && value <= 0) return "N/A";
  const normalized = value > 1 ? Math.min(100, value) : Math.max(0, Math.min(100, value * 100));
  return `${Math.round(normalized)}%`;
}

export function cleanPreview(text = "", maxLength = 420) {
  const cleaned = text
    .replace(/\s+-\s+/g, " ")
    .replace(/([a-z])-\s+([a-z])/gi, "$1$2")
    .replace(/\s+/g, " ")
    .trim();
  if (cleaned.length <= maxLength) return cleaned;
  const slice = cleaned.slice(0, maxLength);
  const lastStop = Math.max(slice.lastIndexOf("."), slice.lastIndexOf(";"), slice.lastIndexOf(","));
  return `${slice.slice(0, lastStop > 180 ? lastStop + 1 : maxLength).trim()}...`;
}

export function compactRepeatedCitations(text = "") {
  return text
    .split(/\n{2,}/)
    .map(compactBlockCitations)
    .join("\n\n");
}

function compactBlockCitations(block) {
  const lines = block.split("\n");
  const compacted = [...lines];
  let groupStart = null;
  let groupCitation = null;

  const flush = (endIndex) => {
    if (groupStart === null || endIndex - groupStart < 2) return;
    for (let index = groupStart; index < endIndex - 1; index += 1) {
      compacted[index] = removeTrailingCitation(compacted[index]);
    }
  };

  lines.forEach((line, index) => {
    const citation = trailingCitation(line);
    if (isListItem(line) && citation && citation === groupCitation) {
      return;
    }
    flush(index);
    groupStart = isListItem(line) && citation ? index : null;
    groupCitation = groupStart === null ? null : citation;
  });
  flush(lines.length);
  return compacted.join("\n");
}

function isListItem(line) {
  return /^\s*(?:[-*]|\d+[.)])\s+/.test(line);
}

function trailingCitation(line) {
  return line.match(/\[([0-9,\s]+)\]\s*[.)]*\s*$/)?.[1].replace(/\s+/g, "");
}

function removeTrailingCitation(line) {
  return line.replace(/\s*\[[0-9,\s]+\](\s*[.)]*)\s*$/, "$1").trimEnd();
}

export function evidenceStrength(result, evidenceUnits, faithfulnessScore = null) {
  const used = evidenceUnits.filter((chunk) => chunk.used_in_answer);
  const documents = new Set(used.map((chunk) => chunk.document_id));
  const coverage = citationCoverageFromAnswer(result?.answer ?? "", evidenceUnits);
  const status = citationStatus(coverage);
  const faithfulness = typeof faithfulnessScore === "number" ? faithfulnessScore : null;
  const sourceUsage = used.length > 0 ? 1 : 0;
  const supportScore = Math.min(
    1,
    (used.length / 3) * 0.3
      + (documents.size / 2) * 0.24
      + coverage * 0.24
      + sourceUsage * 0.12
      + (faithfulness ?? 0.85) * 0.1
  );
  const label = supportScore >= 0.85 ? "Strong" : supportScore >= 0.55 ? "Moderate" : "Limited";
  return {
    label,
    usedChunkCount: used.length,
    documentCount: documents.size,
    sourcesUsed: documents.size,
    citationCoverage: coverage,
    citationStatus: status,
  };
}

export function citationCoverageFromAnswer(answer, evidenceUnits = []) {
  const claims = evidenceClaims(answer);
  if (!claims.length) return evidenceUnits.some((chunk) => chunk.used_in_answer) ? 1 : 0;
  const citedClaims = claims.filter((claim) => /\[\d+(?:,\s*\d+)*\]/.test(claim)).length;
  return citedClaims / claims.length;
}

export function citationStatus(coverage) {
  if (coverage >= 0.9) return "Fully cited";
  if (coverage >= 0.7) return "Mostly cited";
  if (coverage >= 0.4) return "Partially cited";
  return "Needs citation review";
}

function evidenceClaims(answer = "") {
  return answer
    .split(/\n+|(?<=[.!?])\s+/)
    .map((item) => item.replace(/^[-*]\s*/, "").trim())
    .filter(Boolean)
    .filter(isEvidenceRequiringClaim);
}

function isEvidenceRequiringClaim(sentence) {
  const normalized = sentence.toLowerCase().replace(/\[\d+(?:,\s*\d+)*\]/g, "").trim();
  if (normalized.length < 28) return false;
  if (/^(in summary|summary:|comparison table:|developer interpretation:|the system uses the following approach|the indexed papers show different applications)\b/.test(normalized)) {
    return false;
  }
  return /\b(model|method|technique|architecture|dataset|accuracy|precision|recall|result|detect|classif|recogn|compare|uses?|used|yolov8|efficientnet|cnn|bm25|semantic|retrieval|chunk|paper|plate|pcb|thyroid|score|\d+(?:\.\d+)?%?)\b/.test(normalized);
}
