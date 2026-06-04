import { Check } from "lucide-react";
import { useEffect, useState } from "react";

const steps = [
  "Analyzing Query",
  "Running Hybrid Retrieval",
  "Reranking Chunks",
  "Compressing Context",
  "Generating Grounded Answer",
  "Evaluating Faithfulness",
];

export function WorkflowStatus({ active, complete = false, error = false, visible = active }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!visible) {
      setIndex(0);
      return undefined;
    }
    if (complete) {
      setIndex(steps.length);
      return undefined;
    }
    if (error) {
      return undefined;
    }

    const timers = steps.slice(0, -1).map((_, stepIndex) =>
      window.setTimeout(() => {
        setIndex((value) => Math.max(value, stepIndex + 1));
      }, (stepIndex + 1) * 900)
    );
    return () => timers.forEach((timer) => window.clearTimeout(timer));
  }, [active, complete, error, visible]);

  if (!visible) return null;

  return (
    <section className="workflow-status">
      {steps.map((step, stepIndex) => {
        const completed = complete || stepIndex < index;
        const current = active && !complete && stepIndex === index;
        const state = completed ? "completed" : current ? "current" : "pending";
        return (
          <div className={`flow-step ${state}`} key={step}>
            <span>{completed ? <Check size={12} /> : stepIndex + 1}</span>
            <strong>{step}</strong>
            <small>{completed ? "Completed" : current ? "In progress" : "Pending"}</small>
          </div>
        );
      })}
    </section>
  );
}
