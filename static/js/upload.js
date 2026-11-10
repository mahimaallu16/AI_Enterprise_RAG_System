/**
 * upload.js
 * ---------
 * Handles drag-and-drop / click-to-browse uploads, renders a per-file
 * progress queue, and calls Api.uploadFiles(). Refreshes the dashboard
 * stats and document lists on success via a custom "documents:changed"
 * event that dashboard.js listens for.
 */

const UploadModule = (() => {
  function attachDropzone(dropzoneEl, queueEl) {
    if (!dropzoneEl) return;

    const input = document.createElement("input");
    input.type = "file";
    input.multiple = true;
    input.accept = ".pdf,.txt,.md,.markdown,.docx";
    input.style.display = "none";
    dropzoneEl.appendChild(input);

    dropzoneEl.addEventListener("click", () => input.click());

    input.addEventListener("change", () => {
      if (input.files.length) handleFiles(input.files, queueEl);
      input.value = "";
    });

    ["dragenter", "dragover"].forEach((evt) =>
      dropzoneEl.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzoneEl.classList.add("dragover");
      })
    );
    ["dragleave", "drop"].forEach((evt) =>
      dropzoneEl.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzoneEl.classList.remove("dragover");
      })
    );
    dropzoneEl.addEventListener("drop", (e) => {
      const files = e.dataTransfer.files;
      if (files.length) handleFiles(files, queueEl);
    });
  }

  function renderQueueItem(queueEl, filename) {
    if (!queueEl) return null;
    const row = document.createElement("div");
    row.className = "upload-item";
    row.innerHTML = `
      <span class="upload-status-icon">⏳</span>
      <span style="flex-shrink:0; max-width:160px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${filename}</span>
      <div class="upload-progress-track"><div class="upload-progress-fill"></div></div>
      <span class="upload-result-text" style="font-size:12px; color: var(--color-text-muted);">Processing…</span>
    `;
    queueEl.prepend(row);
    const fill = row.querySelector(".upload-progress-fill");
    fill.style.width = "70%";
    return row;
  }

  async function handleFiles(fileList, queueEl) {
    const rows = Array.from(fileList).map((f) => renderQueueItem(queueEl, f.name));

    try {
      const res = await Api.uploadFiles(fileList);
      const results = res.data || [];

      results.forEach((result, i) => {
        const row = rows[i];
        if (!row) return;
        const fill = row.querySelector(".upload-progress-fill");
        const icon = row.querySelector(".upload-status-icon");
        const text = row.querySelector(".upload-result-text");
        fill.style.width = "100%";

        if (result.success) {
          icon.textContent = "✅";
          const doc = result.document;
          text.textContent = `${doc.total_pages} pages · ${doc.total_chunks} chunks`;
          Toast.success(`"${doc.original_name}" processed successfully.`);
        } else {
          icon.textContent = "❌";
          text.textContent = result.error || "Failed";
          Toast.error(`"${result.filename}": ${result.error}`);
        }
      });

      document.dispatchEvent(new CustomEvent("documents:changed"));
    } catch (err) {
      rows.forEach((row) => {
        if (!row) return;
        row.querySelector(".upload-status-icon").textContent = "❌";
        row.querySelector(".upload-result-text").textContent = "Upload failed";
      });
      Toast.error(err.message || "Upload failed.");
    }
  }

  function init() {
    attachDropzone(document.getElementById("uploadDropzone"), document.getElementById("uploadQueue"));
    attachDropzone(document.getElementById("dashDropzone"), document.getElementById("uploadQueue"));
  }

  return { init };
})();

document.addEventListener("DOMContentLoaded", UploadModule.init);
