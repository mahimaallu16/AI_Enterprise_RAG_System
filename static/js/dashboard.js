/**
 * dashboard.js
 * ------------
 * Renders statistics cards, the document library (both the "recent" list
 * on the dashboard view and the full list on the documents view), the
 * document-filter dropdown in chat, and the usage/cost view. Listens for
 * "documents:changed" and "usage:changed" events fired by other modules.
 */

const DashboardModule = (() => {
  function extIcon(ext) {
    return (ext || "").toUpperCase().slice(0, 4) || "DOC";
  }

  function statusPill(doc) {
    const map = {
      processed: '<span class="pill pill-success">Processed</span>',
      processing: '<span class="pill pill-warning">Processing</span>',
      failed: '<span class="pill pill-danger">Failed</span>',
      pending: '<span class="pill pill-muted">Pending</span>',
    };
    return map[doc.status] || map.pending;
  }

  function renderDocRow(doc, { withDelete } = { withDelete: true }) {
    const row = document.createElement("div");
    row.className = "doc-row";
    row.innerHTML = `
      <div class="doc-icon">${extIcon(doc.extension)}</div>
      <div class="doc-meta">
        <div class="doc-name">${doc.original_name}</div>
        <div class="doc-sub">${doc.total_pages} pages · ${doc.total_chunks} chunks ${statusPill(doc).replace(/<[^>]+>/g, m => m).length ? '' : ''}</div>
      </div>
      ${statusPill(doc)}
      ${withDelete ? `<div class="doc-actions"><button class="icon-btn danger" data-doc-id="${doc.doc_id}" title="Delete">🗑️</button></div>` : ""}
    `;
    if (withDelete) {
      row.querySelector(".icon-btn.danger").addEventListener("click", async (e) => {
        const docId = e.currentTarget.getAttribute("data-doc-id");
        if (!confirm(`Delete "${doc.original_name}"? This removes its embeddings too.`)) return;
        try {
          await Api.deleteDocument(docId);
          Toast.success("Document deleted.");
          document.dispatchEvent(new CustomEvent("documents:changed"));
        } catch (err) {
          Toast.error(err.message || "Could not delete document.");
        }
      });
    }
    return row;
  }

  async function refreshDocuments() {
    try {
      const res = await Api.listDocuments();
      const docs = res.data || [];

      const recentList = document.getElementById("recentDocList");
      const fullList = document.getElementById("fullDocList");
      const filterSelect = document.getElementById("documentFilter");

      [recentList, fullList].forEach((el) => el && (el.innerHTML = ""));

      if (!docs.length) {
        if (recentList) recentList.innerHTML = '<div class="empty-state">No documents uploaded yet.</div>';
        if (fullList) fullList.innerHTML = '<div class="empty-state">No documents uploaded yet.</div>';
      } else {
        docs.slice(0, 5).forEach((doc) => recentList && recentList.appendChild(renderDocRow(doc, { withDelete: false })));
        docs.forEach((doc) => fullList && fullList.appendChild(renderDocRow(doc, { withDelete: true })));
      }

      if (filterSelect) {
        const currentValue = filterSelect.value;
        filterSelect.innerHTML = '<option value="">All documents</option>';
        docs
          .filter((d) => d.status === "processed")
          .forEach((d) => {
            const opt = document.createElement("option");
            opt.value = d.original_name;
            opt.textContent = d.original_name;
            filterSelect.appendChild(opt);
          });
        filterSelect.value = currentValue;
      }
    } catch (err) {
      Toast.error(err.message || "Could not load documents.");
    }
  }

  async function refreshStats() {
    try {
      const res = await Api.getStats();
      const s = res.data;
      const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
      };
      set("statDocuments", s.total_documents ?? 0);
      set("statPages", s.total_pages ?? 0);
      set("statChunks", s.total_chunks ?? 0);
      set("statProcessing", s.processing ?? 0);
    } catch (err) {
      // Non-fatal; stats card just stays at previous values.
    }
  }

  async function refreshUsage() {
    try {
      const res = await Api.getUsage();
      const u = res.data;
      const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
      };
      set("usageRequests", u.total_requests ?? 0);
      set("usageInputTokens", u.total_input_tokens ?? 0);
      set("usageOutputTokens", u.total_output_tokens ?? 0);
      set("usageCost", `$${(u.estimated_cost_usd ?? 0).toFixed(4)}`);
    } catch (err) {
      // Non-fatal.
    }
  }

  async function refreshHealth() {
    const pill = document.getElementById("healthPill");
    if (!pill) return;
    try {
      const res = await Api.getHealth();
      if (res.data.warnings && res.data.warnings.length) {
        pill.textContent = "⚠️ Needs API key";
        pill.className = "pill pill-warning";
      } else {
        pill.textContent = "● Online";
        pill.className = "pill pill-success";
      }
    } catch (err) {
      pill.textContent = "● Offline";
      pill.className = "pill pill-danger";
    }
  }

  function refreshAll() {
    refreshDocuments();
    refreshStats();
    refreshUsage();
    refreshHealth();
  }

  function bindRefreshEmbeddings() {
    const btn = document.getElementById("refreshEmbeddingsBtn");
    if (!btn) return;
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      const original = btn.textContent;
      btn.innerHTML = '<span class="spinner dark"></span> Rebuilding...';
      try {
        const res = await Api.refreshEmbeddings();
        const { rebuilt, failed } = res.data;
        Toast.success(`Rebuilt embeddings for ${rebuilt.length} document(s).`);
        if (failed.length) Toast.warning(`${failed.length} document(s) failed to rebuild.`);
        refreshAll();
      } catch (err) {
        Toast.error(err.message || "Refresh failed.");
      } finally {
        btn.disabled = false;
        btn.textContent = original;
      }
    });
  }

  function init() {
    refreshAll();
    bindRefreshEmbeddings();
    document.addEventListener("documents:changed", refreshAll);
    document.addEventListener("usage:changed", refreshUsage);
    setInterval(refreshHealth, 30000);
  }

  return { init, refreshAll };
})();

document.addEventListener("DOMContentLoaded", DashboardModule.init);
