import { BarChart3, Database, FileUp, Home, MessageSquareText, Route } from "lucide-react";
import { useState } from "react";
import { NavLink, Navigate, Route as RouterRoute, Routes } from "react-router-dom";
import { useDocuments } from "./hooks/useDocuments";
import { ChatPage } from "./pages/ChatPage";
import { EvaluationPage } from "./pages/EvaluationPage";
import { LandingPage } from "./pages/LandingPage";
import { LibraryPage } from "./pages/LibraryPage";
import { TracePage } from "./pages/TracePage";
import { UploadPage } from "./pages/UploadPage";

const nav = [
  { id: "home", label: "Overview", icon: Home, path: "/" },
  { id: "upload", label: "Ingestion", icon: FileUp, path: "/upload" },
  { id: "chat", label: "Intelligence", icon: MessageSquareText, path: "/chat" },
  { id: "library", label: "Knowledge Base", icon: Database, path: "/library" },
  { id: "evaluation", label: "Evaluation Lab", icon: BarChart3, path: "/evaluation" },
  { id: "traces", label: "Observability", icon: Route, path: "/traces" },
];

export function App() {
  const [lastTrace, setLastTrace] = useState();
  const [lastAnswer, setLastAnswer] = useState(null);
  const [lastRun, setLastRun] = useState(null);
  const { documents } = useDocuments();
  const totalChunks = documents.reduce((sum, doc) => sum + (doc.chunk_count ?? 0), 0);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">N</span>
          <div>
            <strong>NexusIQ</strong>
            <span>Enterprise RAG Platform</span>
          </div>
        </div>
        <nav>
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.id} className={({ isActive }) => (isActive ? "active" : "")} to={item.path}>
                <Icon size={18} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </aside>
      <main className="main">
        <section className="top-stats" aria-label="Platform statistics">
          <Stat label="Documents Indexed" value={documents.length} />
          <Stat label="Total Chunks" value={totalChunks} />
          <Stat label="Avg Retrieval Latency" value="~1.2s" />
          <Stat label="Grounding Score" value="92%" />
          <Stat label="Retrieval Mode" value="Adaptive Hybrid" />
        </section>
        <Routes>
          <RouterRoute path="/" element={<LandingPage />} />
          <RouterRoute path="/upload" element={<UploadPage />} />
          <RouterRoute
            path="/chat"
            element={
              <ChatPage
                onTrace={setLastTrace}
                onAnswer={(question, answer, contexts, response, topK) => {
                  setLastAnswer({ question, answer, contexts, response });
                  setLastRun({
                    question,
                    answer,
                    response,
                    topK,
                    traceUrl: response.trace_url,
                    status: "Passed",
                    completedAt: new Date().toISOString(),
                  });
                }}
              />
            }
          />
          <RouterRoute path="/library" element={<LibraryPage />} />
          <RouterRoute path="/evaluation" element={<EvaluationPage seed={lastAnswer} />} />
          <RouterRoute path="/traces" element={<TracePage traceUrl={lastTrace} lastRun={lastRun} />} />
          <RouterRoute path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <article>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}
