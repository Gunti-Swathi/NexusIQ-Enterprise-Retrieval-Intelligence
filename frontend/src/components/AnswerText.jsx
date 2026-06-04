export function AnswerText({ text }) {
  if (!text) return null;
  const parts = text.split(/(\*\*[^*]+\*\*|\[\d+\])/g);
  return (
    <p>
      {parts.map((part, index) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={index}>{part.slice(2, -2)}</strong>;
        }
        if (/^\[\d+\]$/.test(part)) {
          return <span className="inline-citation" key={index}>{part}</span>;
        }
        return <span key={index}>{part}</span>;
      })}
    </p>
  );
}
