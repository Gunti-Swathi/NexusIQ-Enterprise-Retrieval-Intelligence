export function ContradictionAlert({ contradictions }) {
  if (!contradictions?.length) return null;
  return (
    <section className="contradiction-alert">
      <h2>Potential Contradictions</h2>
      {contradictions.map((item) => (
        <article key={`${item.left_chunk_id}-${item.right_chunk_id}`}>
          <strong>{item.left_file} conflicts with {item.right_file}</strong>
          <p>{item.reason}</p>
        </article>
      ))}
    </section>
  );
}
