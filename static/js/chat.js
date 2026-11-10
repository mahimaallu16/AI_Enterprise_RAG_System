/**
 * chat.js
 * -------
 * Chat window logic: sending questions, rendering the assistant's answer
 * with citations and retrieved chunks, clear/export controls, and a
 * persistent session id (per browser tab) so conversation memory works.
 */

const ChatModule = (() => {
  const SESSION_KEY = "enterprise_rag_session_id";

  function getSessionId() {
    let id = sessionStorage.getItem(SESSION_KEY);
    if (!id) {
      id = "sess_" + Math.random().toString(36).slice(2, 12);
      sessionStorage.setItem(SESSION_KEY, id);
    }
    return id;
  }

  function scrollToBottom(container) {
    container.scrollTop = container.scrollHeight;
  }

  function renderMessage(container, role, content, citations = []) {
    const emptyState = document.getElementById("chatEmptyState");
    if (emptyState) emptyState.remove();

    const row = document.createElement("div");
    row.className = `msg-row ${role}`;

    const avatar = document.createElement("div");
    avatar.className = `msg-avatar ${role}`;
    avatar.textContent = role === "user" ? "You" : "AI";

    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    bubble.innerText = content;

    if (citations && citations.length) {
      const box = document.createElement("div");
      box.className = "citations-box";
      citations.forEach((c, i) => {
        const chip = document.createElement("div");
        chip.className = "citation-chip";
        const pageStr = c.page_number ? `, page ${c.page_number}` : "";
        chip.innerHTML = `<span class="num">[${i + 1}]</span><span>${c.document_name}${pageStr} — chunk ${c.chunk_id}</span>`;
        box.appendChild(chip);
      });
      bubble.appendChild(box);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    container.appendChild(row);
    scrollToBottom(container);
    return row;
  }

  function renderTyping(container) {
    const row = document.createElement("div");
    row.className = "msg-row assistant";
    row.id = "typingRow";
    row.innerHTML = `
      <div class="msg-avatar assistant">AI</div>
      <div class="msg-bubble typing-dots"><span></span><span></span><span></span></div>
    `;
    container.appendChild(row);
    scrollToBottom(container);
  }

  function removeTyping() {
    const row = document.getElementById("typingRow");
    if (row) row.remove();
  }

  async function sendMessage(question) {
    const container = document.getElementById("chatMessages");
    const filterSelect = document.getElementById("documentFilter");
    const documentFilter = filterSelect ? filterSelect.value : "";

    renderMessage(container, "user", question);
    renderTyping(container);

    const sendBtn = document.getElementById("sendBtn");
    if (sendBtn) sendBtn.disabled = true;

    try {
      const res = await Api.askQuestion(question, getSessionId(), documentFilter);
      removeTyping();
      const { answer, citations, retrieved_chunks } = res.data;
      const row = renderMessage(container, "assistant", answer, citations);

      if (retrieved_chunks && retrieved_chunks.length) {
        const chunksBox = document.createElement("div");
        chunksBox.className = "retrieved-chunks";
        chunksBox.innerHTML = `<div style="font-size:11px; font-weight:700; text-transform:uppercase; color:var(--color-text-muted); margin-bottom:6px;">Retrieved chunks</div>`;
        retrieved_chunks.forEach((c) => {
          const card = document.createElement("div");
          card.className = "chunk-card";
          const pageStr = c.page_number ? ` · page ${c.page_number}` : "";
          card.innerHTML = `<strong>${c.document_name}</strong>${pageStr} · similarity ${c.similarity}<br>${c.text}`;
          chunksBox.appendChild(card);
        });
        row.querySelector(".msg-bubble").appendChild(chunksBox);
      }
      scrollToBottom(container);
      document.dispatchEvent(new CustomEvent("usage:changed"));
    } catch (err) {
      removeTyping();
      renderMessage(container, "assistant", `⚠️ ${err.message}`);
      Toast.error(err.message || "Something went wrong.");
    } finally {
      if (sendBtn) sendBtn.disabled = false;
    }
  }

  function init() {
    const input = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendBtn");
    const clearBtn = document.getElementById("clearChatBtn");
    const exportBtn = document.getElementById("exportChatBtn");

    if (sendBtn && input) {
      const submit = () => {
        const value = input.value.trim();
        if (!value) return;
        input.value = "";
        sendMessage(value);
      };
      sendBtn.addEventListener("click", submit);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          submit();
        }
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", async () => {
        try {
          await Api.clearChat(getSessionId());
          const container = document.getElementById("chatMessages");
          container.innerHTML = '<div class="empty-state" id="chatEmptyState">Ask a question about your uploaded documents to get started.</div>';
          Toast.success("Chat history cleared.");
        } catch (err) {
          Toast.error(err.message || "Could not clear chat.");
        }
      });
    }

    if (exportBtn) {
      exportBtn.addEventListener("click", async () => {
        try {
          const res = await Api.exportChat(getSessionId());
          const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `chat-export-${Date.now()}.json`;
          a.click();
          URL.revokeObjectURL(url);
          Toast.success("Chat exported.");
        } catch (err) {
          Toast.error(err.message || "Could not export chat.");
        }
      });
    }
  }

  return { init, getSessionId, sendMessage };
})();

document.addEventListener("DOMContentLoaded", ChatModule.init);
