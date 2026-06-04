import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api";

export function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.documents();
      setDocuments(result.documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load documents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { documents, loading, error, refresh };
}
