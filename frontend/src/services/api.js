import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request(path, init) {
  try {
    const response = await axios({
      url: `${API_BASE}${path}`,
      method: init?.method ?? "GET",
      data: init?.body,
      headers: init?.headers,
    });
    return response.data;
  } catch (error) {
    const detail = error.response?.data?.detail ?? error.message;
    throw new Error(detail ?? "Request failed");
  }
}

export const api = {
  health: () => request("/health"),
  documents: () => request("/documents"),
  deleteDocument: (id) => request(`/documents/${id}`, { method: "DELETE" }),
  upload: (files) => {
    const body = new FormData();
    files.forEach((file) => body.append("files", file, file.name));
    return request("/upload", { method: "POST", body });
  },
  ask: (question, topK = 8, useMultiQuery = true) =>
    request("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: topK, use_multi_query: useMultiQuery }),
    }),
  evaluate: (question, answer, contexts, groundTruth) =>
    request("/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, answer, contexts, ground_truth: groundTruth || null }),
    }),
};
