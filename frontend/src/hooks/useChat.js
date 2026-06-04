import { useState } from "react";
import { api } from "../services/api";

export function useChat() {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function ask(question, topK, useMultiQuery) {
    setBusy(true);
    setError(null);
    try {
      const response = await api.ask(question, topK, useMultiQuery);
      setResult(response);
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Question failed.");
      throw err;
    } finally {
      setBusy(false);
    }
  }

  return { ask, busy, result, error };
}
