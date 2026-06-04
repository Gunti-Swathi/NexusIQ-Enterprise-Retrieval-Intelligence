import { FileStack, Layers3, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useDocuments } from "../hooks/useDocuments";
import { api } from "../services/api";
import { displayTitle, documentCategory } from "../utils/ragDisplay";

export function LibraryPage() {
  const { documents, loading, error, refresh } = useDocuments();
  const [activeCategory, setActiveCategory] = useState("All Documents");
  const categories = buildCategories(documents);
  useEffect(() => {
    if (!categories.includes(activeCategory)) {
      setActiveCategory("All Documents");
    }
  }, [activeCategory, categories]);
  const filteredDocuments = activeCategory === "All Documents"
    ? documents
    : documents.filter((doc) => categoryForDocument(doc.filename, categories) === activeCategory);

  async function remove(id) {
    await api.deleteDocument(id);
    await refresh();
  }

  return (
    <section className="page">
      <div className="page-heading">
        <p>Knowledge Base</p>
        <h1>{documents.length} indexed documents</h1>
        <span>Semantic document clusters, chunk inventory, and indexing status for your retrieval corpus.</span>
      </div>
      {loading && <p className="muted">Loading library...</p>}
      {error && <div className="error">{error}</div>}
      <div className="cluster-strip category-strip">
        {categories.map((cluster, index) => (
          <button className={activeCategory === cluster ? "active" : ""} key={cluster} type="button" onClick={() => setActiveCategory(cluster)}>
            <span>0{index + 1}</span>
            <strong>{cluster}</strong>
          </button>
        ))}
      </div>
      <div className="document-grid">
        {filteredDocuments.map((doc) => (
          <article className="document-card" key={doc.id}>
            <FileStack size={24} />
            <strong title={doc.filename}>{displayTitle(doc.filename)}</strong>
            <div className="document-meta-grid">
              <Meta label="Raw filename" value={doc.filename} />
              <Meta label="File type" value={fileType(doc)} />
              <Meta label="File size" value={formatBytes(doc.size_bytes)} />
              <Meta label="Chunks" value={<><Layers3 size={14} /> {doc.chunk_count}</>} />
              <Meta label="Status" value={<span className="status-badge passed">Indexed</span>} />
              <Meta label="Indexed" value={formatDate(doc.created_at)} />
              <Meta label="Embedding model" value="text-embedding-004" />
            </div>
            <button className="icon-button" onClick={() => void remove(doc.id)} title="Delete document">
              <Trash2 size={16} />
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

function Meta({ label, value }) {
  return (
    <span>
      <small>{label}</small>
      <b>{value}</b>
    </span>
  );
}

function fileType(doc) {
  return doc.content_type?.split("/").pop()?.toUpperCase() || doc.filename.split(".").pop()?.toUpperCase() || "FILE";
}

function formatBytes(bytes = 0) {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.max(1, Math.ceil(bytes / 1024))} KB`;
}

function formatDate(value) {
  if (!value) return "n/a";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }).format(new Date(value));
}

function buildCategories(documents) {
  const names = documents.map((doc) => doc.filename.toLowerCase()).join(" ");
  if (/policy|expense|attendance|leave|incident|playbook|apexflow/.test(names)) {
    return ["All Documents", "Company Policies", "Travel & Expense", "Leave & Attendance", "Incident Response"];
  }
  return ["All Documents", "Computer Vision", "Medical AI", "Object Detection", "Classification"];
}

function categoryForDocument(filename, categories) {
  const value = filename.toLowerCase();
  if (categories.includes("Company Policies")) {
    if (/travel|expense|reimbursement/.test(value)) return "Travel & Expense";
    if (/leave|attendance|pto|absence/.test(value)) return "Leave & Attendance";
    if (/incident|response|playbook|security/.test(value)) return "Incident Response";
    return "Company Policies";
  }
  return documentCategory(filename);
}
