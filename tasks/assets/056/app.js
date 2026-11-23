"use strict";

const form = document.getElementById("ask-form");
const question = document.getElementById("question");
const button = document.getElementById("ask-button");
const result = document.getElementById("result");
const answer = document.getElementById("answer");
const warning = document.getElementById("warning");
const sourcesTitle = document.getElementById("sources-title");
const sources = document.getElementById("sources");
const errorBox = document.getElementById("error");

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function linkCitations(text, list) {
  const byNumber = new Map(list.map((s) => [s.number, s]));
  return escapeHtml(text).replace(/\[(\d+)\]/g, (match, n) => {
    const s = byNumber.get(Number(n));
    if (!s) return match;
    const title = escapeHtml(`${s.source}, p. ${s.page}`);
    return `<a href="${s.url}" target="_blank" title="${title}">${match}</a>`;
  });
}

function showDone(data) {
  if (!data.no_answer) answer.innerHTML = linkCitations(data.text, data.sources);
  sources.innerHTML = "";
  for (const s of data.sources) {
    const li = document.createElement("li");
    li.value = s.number;
    const a = document.createElement("a");
    a.href = s.url;
    a.target = "_blank";
    a.textContent = `${s.source}, p. ${s.page}`;
    li.appendChild(a);
    sources.appendChild(li);
  }
  sourcesTitle.hidden = data.sources.length === 0;
  if (data.invalid_citations.length > 0) {
    const nums = data.invalid_citations.map((n) => `[${n}]`).join(", ");
    warning.textContent = `Citas sin fuente descartadas: ${nums}`;
    warning.hidden = false;
  }
}

function showError(message) {
  errorBox.textContent = `Error: ${message}`;
  errorBox.hidden = false;
}

function handleEvent(event, data) {
  if (event === "token") answer.textContent += data.text;
  else if (event === "done") showDone(data);
  else if (event === "error") showError(data.message);
}

function parseBlock(block) {
  let event = "message";
  let data = "";
  for (const line of block.split("\n")) {
    if (line.startsWith("event: ")) event = line.slice(7);
    else if (line.startsWith("data: ")) data += line.slice(6);
  }
  return data ? [event, JSON.parse(data)] : null;
}

async function ask(text) {
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: text }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replaceAll("\r\n", "\n");
    let index = buffer.indexOf("\n\n");
    while (index !== -1) {
      const parsed = parseBlock(buffer.slice(0, index));
      buffer = buffer.slice(index + 2);
      if (parsed) handleEvent(parsed[0], parsed[1]);
      index = buffer.indexOf("\n\n");
    }
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = question.value.trim();
  if (!text) return;
  answer.textContent = "";
  sources.innerHTML = "";
  sourcesTitle.hidden = true;
  warning.hidden = true;
  errorBox.hidden = true;
  result.hidden = false;
  button.disabled = true;
  button.textContent = "Pensando…";
  try {
    await ask(text);
  } catch (err) {
    showError(err.message);
  } finally {
    button.disabled = false;
    button.textContent = "Preguntar";
  }
});

question.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});
