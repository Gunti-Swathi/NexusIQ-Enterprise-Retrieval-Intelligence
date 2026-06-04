import { ArrowRight, BrainCircuit, GitBranch, ShieldCheck, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

const features = [
  { icon: BrainCircuit, title: "Grounded Generation", text: "Answers are constrained to indexed evidence with compact source citations." },
  { icon: GitBranch, title: "Hybrid Retrieval", text: "Semantic search and BM25 fusion surface the most relevant enterprise context." },
  { icon: ShieldCheck, title: "Evaluation Loop", text: "Faithfulness, relevance, precision, and recall checks keep answers accountable." },
];

export function LandingPage() {
  return (
    <main className="landing">
      <section className="landing-hero">
        <div className="hero-copy">
          <span className="eyebrow"><Sparkles size={16} /> NexusIQ</span>
          <h1>Enterprise Document Intelligence Platform</h1>
          <p>Ask questions across documents, retrieve grounded evidence, validate citations, and monitor answer quality through an observable RAG pipeline.</p>
          <div className="hero-actions">
            <Link className="primary-link" to="/upload">Upload Documents <ArrowRight size={17} /></Link>
          </div>
        </div>
      </section>

      <section className="landing-band">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <article className="feature-card" key={feature.title}>
              <Icon size={22} />
              <h2>{feature.title}</h2>
              <p>{feature.text}</p>
            </article>
          );
        })}
      </section>

      <footer className="landing-footer">NexusIQ · Enterprise Retrieval Intelligence</footer>
    </main>
  );
}
