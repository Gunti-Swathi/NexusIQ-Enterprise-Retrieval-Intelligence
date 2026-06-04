import { evidenceStrength } from "../utils/ragDisplay";

export function EvidenceStrength({ result, evidenceUnits }) {
  if (!result) return null;
  const strength = evidenceStrength(result, evidenceUnits);
  return (
    <aside className="evidence-strength">
      <span>Evidence Strength</span>
      <strong>{strength.label}</strong>
      <p>
        Supported by {strength.usedChunkCount} chunk{strength.usedChunkCount === 1 ? "" : "s"} across{" "}
        {strength.documentCount} document{strength.documentCount === 1 ? "" : "s"}.
      </p>
      <small>Sources used: {strength.sourcesUsed}</small>
      <small>Citation status: {strength.citationStatus}</small>
      <em>Evidence strength summarizes source support and citation status. Retrieval scores are used for ranking and debugging, not direct answer confidence.</em>
    </aside>
  );
}
