/**
 * api.js
 * ------
 * Thin wrapper around fetch() for every backend endpoint. All other JS
 * modules go through this file instead of calling fetch() directly, so
 * error handling and JSON parsing stay consistent app-wide.
 */

const Api = (() => {
  async function request(url, options = {}) {
    const res = await fetch(url, options);
    let body;
    try {
      body = await res.json();
    } catch (e) {
      body = { success: false, message: "Invalid server response." };
    }
    if (!res.ok || body.success === false) {
      const err = new Error(body.message || `Request failed (${res.status})`);
      err.data = body;
      throw err;
    }
    return body;
  }

  return {
    uploadFiles(fileList) {
      const formData = new FormData();
      for (const file of fileList) formData.append("files", file);
      return request("/api/upload", { method: "POST", body: formData });
    },

    listDocuments() {
      return request("/api/documents");
    },

    deleteDocument(docId) {
      return request(`/api/documents/${docId}`, { method: "DELETE" });
    },

    refreshEmbeddings() {
      return request("/api/documents/refresh-embeddings", { method: "POST" });
    },

    askQuestion(question, sessionId, documentFilter) {
      return request("/api/chat/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, session_id: sessionId, document_filter: documentFilter || null }),
      });
    },

    clearChat(sessionId) {
      return request("/api/chat/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });
    },

    exportChat(sessionId) {
      return request(`/api/chat/export?session_id=${encodeURIComponent(sessionId)}`);
    },

    getStats() {
      return request("/api/stats");
    },

    getUsage() {
      return request("/api/usage");
    },

    getHealth() {
      return request("/api/health");
    },
  };
})();
