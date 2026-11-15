// Fauve desktop page. Renders the state Python returns (webui.Api) and sends
// clicks and typed text back. Rules (checked by T22):
// - text goes on the page through textContent / createTextNode only, never as HTML;
// - no links, images, frames or scripts are ever created; no network calls;
// - the page never decides anything: every action is a call into Python,
//   and SEND ONCE also needs a native macOS dialog that this script can't click.
"use strict";

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text;
  return n;
};

let api = null;
let view = { case: 0, busy: false, card: null };
let lastId = 0;
let pollTimer = null;
let history = [];          // the user's own sent lines, for the up arrow
let historyAt = -1;

// ---------- markdown, built from DOM nodes ----------
const INLINE = /(`[^`\n]+`)|(\*\*[^*\n]+\*\*)|(__[^_\n]+__)|(\*[^*\s][^*\n]*\*)/g;

function inline(parent, s) {
  let last = 0, m;
  INLINE.lastIndex = 0;
  while ((m = INLINE.exec(s))) {
    if (m.index > last) parent.appendChild(document.createTextNode(s.slice(last, m.index)));
    const t = m[0];
    if (t[0] === "`") parent.appendChild(el("code", "", t.slice(1, -1)));
    else if (t.startsWith("**") || t.startsWith("__")) parent.appendChild(el("strong", "", t.slice(2, -2)));
    else parent.appendChild(el("em", "", t.slice(1, -1)));
    last = INLINE.lastIndex;
  }
  if (last < s.length) parent.appendChild(document.createTextNode(s.slice(last)));
}

function codeBlock(code, lang) {
  const wrap = el("div", "codeblock");
  if (lang) wrap.appendChild(el("span", "lang", lang.slice(0, 20)));
  const pre = el("pre");
  pre.appendChild(el("code", "", code));
  wrap.appendChild(pre);
  const copy = el("button", "copy", "Copy");
  copy.type = "button";
  copy.addEventListener("click", () => copyText(code, copy, pre));
  wrap.appendChild(copy);
  return wrap;
}

const FENCE = /^\s*```/;
const BULLET = /^\s*[-*•]\s+/;
const NUMBER = /^\s*\d+[.)]\s+/;
const HEADING = /^(#{1,6})\s+(.*)$/;
const QUOTE = /^\s*>\s?/;
const HEADINGS = ["h3", "h3", "h4", "h5", "h6", "h6"];   // # .. ######
const special = (l) => FENCE.test(l) || BULLET.test(l) || NUMBER.test(l) || HEADING.test(l) || QUOTE.test(l);

function markdown(text) {
  const out = document.createDocumentFragment();
  const lines = text.split("\n");
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (FENCE.test(line)) {
      const lang = line.replace(FENCE, "").trim();
      const buf = [];
      i++;
      while (i < lines.length && !FENCE.test(lines[i])) buf.push(lines[i++]);
      i++;
      out.appendChild(codeBlock(buf.join("\n"), lang));
      continue;
    }
    const h = HEADING.exec(line);
    if (h) {
      const n = el(HEADINGS[h[1].length - 1]);
      inline(n, h[2]);
      out.appendChild(n);
      i++;
      continue;
    }
    if (BULLET.test(line) || NUMBER.test(line)) {
      const ordered = !BULLET.test(line);
      const re = ordered ? NUMBER : BULLET;
      const list = el(ordered ? "ol" : "ul");
      while (i < lines.length && re.test(lines[i])) {
        const li = el("li");
        inline(li, lines[i++].replace(re, ""));
        list.appendChild(li);
      }
      out.appendChild(list);
      continue;
    }
    if (QUOTE.test(line)) {
      const q = el("blockquote");
      const buf = [];
      while (i < lines.length && QUOTE.test(lines[i])) buf.push(lines[i++].replace(QUOTE, ""));
      inline(q, buf.join("\n"));
      out.appendChild(q);
      continue;
    }
    if (!line.trim()) { i++; continue; }
    const buf = [];
    while (i < lines.length && lines[i].trim() && !special(lines[i])) buf.push(lines[i++]);
    const p = el("p");
    inline(p, buf.join("\n"));
    out.appendChild(p);
  }
  return out;
}

function copyText(text, button, pre) {
  const done = () => { button.textContent = "Copied"; setTimeout(() => (button.textContent = "Copy"), 1200); };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(done, () => selectAndCopy(pre, done));
  } else {
    selectAndCopy(pre, done);
  }
}

function selectAndCopy(node, done) {
  const range = document.createRange();
  range.selectNodeContents(node);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  try { if (document.execCommand("copy")) done(); } catch (e) { /* the text stays selected */ }
}

// ---------- rendering ----------
// Notices are written by code, never the model: a bordered block with a bold head, no avatar.
function noticeNode(head, text) {
  const box = el("div", "notice");
  box.appendChild(el("p", "notice-head", head));
  box.appendChild(el("p", "", text));
  return box;
}

function messageNode(m) {
  if (m.kind === "notice") return noticeNode("FAUVE NOTICE", m.text);
  const row = el("div", "row " + m.kind);
  const bubble = el("div", "bubble " + m.kind);
  if (m.kind === "user") {
    bubble.textContent = m.text;
  } else {
    row.appendChild(el("span", "avatar"));
    if (m.kind === "cloud") {
      bubble.appendChild(el("p", "cloud-head", "ANSWERED IN THE CLOUD"));
      bubble.appendChild(el("p", "meta", m.model + " · " + view.cloud_host + " · reviewed before showing"));
    }
    const body = el("div", "md");
    body.appendChild(markdown(m.text));
    bubble.appendChild(body);
  }
  row.appendChild(bubble);
  return row;
}

function nearBottom() {
  const log = $("log");
  return log.scrollHeight - log.scrollTop - log.clientHeight < 120;
}

function toBottom() {
  const log = $("log");
  log.scrollTop = log.scrollHeight;
}

function render(s) {
  if (!s) return;
  const stick = nearBottom();
  view.cloud_host = s.cloud_host;
  if (s.case !== view.case) {
    $("messages").replaceChildren();
    lastId = 0;
  }
  for (const m of s.messages) {
    if (m.id <= lastId) continue;
    $("messages").appendChild(messageNode(m));
    lastId = m.id;
  }

  const first = document.body.classList.contains("boot");
  document.body.className = s.mode + " " + s.phase + (first ? " boot" : "");   // phase: idle | work | ask (the Red Studio)
  if (first) { void document.body.offsetWidth; document.body.classList.remove("boot"); }   // no fade on launch
  $("mode").textContent = s.mode === "day" ? "NIGHT" : "DAY";
  $("model").textContent = s.model.split("/").pop() + " · on this Mac";
  $("prompt").placeholder = s.phase === "idle" ? "Give Fauve a case…" : "Reply to Fauve…";
  $("web").textContent = s.web ? "WEB ACCESS: ON" : "WEB ACCESS: OFF";
  $("web").classList.toggle("on", s.web);
  $("cloud").textContent = s.cloud ? "CLOUD: ASK EACH TIME" : "CLOUD: OFF";
  $("cloud").classList.toggle("on", s.cloud);
  $("leaves").textContent = s.nothing_leaves ? "Nothing leaves this Mac" : "Something can leave this Mac: see above";
  $("leaves").classList.toggle("out", !s.nothing_leaves);
  $("kicker").textContent = s.status.kicker;
  $("head").textContent = s.status.head;
  $("facts").replaceChildren(...s.status.facts.map(([name, value]) => {
    const row = el("div", "fact");
    row.appendChild(el("span", "", name));
    row.appendChild(el("span", "", value));
    return row;
  }));
  $("taint").hidden = !s.tainted;
  $("pill").textContent = s.card ? "◐ WAITING ON YOU" : s.busy ? "● THINKING…" : "● ON THE CASE";
  $("pill").classList.toggle("busy", s.busy && !s.card);
  $("pill").classList.toggle("waiting", !!s.card);
  $("send").disabled = s.busy;
  $("new").disabled = s.busy;
  renderCases(s);

  // streaming reply: reviewed text only (webui.live_preview)
  $("live").hidden = !s.live;
  if (s.live) {
    $("live-meta").textContent = s.live.chars
      ? s.live.chars + " characters · shown after review, a sentence at a time"
      : "Thinking…";
    $("live-wrap").hidden = !s.live.text;
    $("live-body").replaceChildren(markdown(s.live.text));
  }

  $("suggest").hidden = !s.suggest;
  renderCard(s.card, s.busy);

  const cardOpened = s.card && (!view.card || view.card.id !== s.card.id);
  view = s;
  if (cardOpened) $("card-row").scrollIntoView({ block: "nearest" });
  else if (stick) toBottom();
  schedulePoll();
}

// Saved cases: titles are masked text from Python, shown with textContent.
function renderCases(s) {
  $("save").hidden = !s.can_save;
  $("save").disabled = s.busy;
  $("save").textContent = s.saved_id ? "SAVED · SAVE AGAIN" : "SAVE";
  $("no-cases").hidden = s.cases.length > 0;
  $("cases").replaceChildren(...s.cases.map((c) => {
    const row = el("div", "case" + (c.id === s.saved_id ? " active" : ""));
    const open = el("button", "case-open", c.title);
    open.type = "button";
    open.title = c.title;
    open.disabled = s.busy;
    open.addEventListener("click", () => call("open_case", c.id));
    const del = el("button", "case-del", "×");
    del.type = "button";
    del.title = "Delete from this Mac";
    del.addEventListener("click", () => call("delete_case", c.id));
    row.appendChild(open);
    row.appendChild(del);
    return row;
  }));
}

function renderCard(card, busy) {
  $("card-row").hidden = !card;
  if (!card) return;
  const ask = $("card-ask");
  ask.replaceChildren(
    document.createTextNode("Fauve needs to reach "),
    el("strong", "", card.host),
    document.createTextNode(" to ask " + card.model + ". Nothing has been sent yet."));
  $("card-to").textContent = "to: " + card.host + " · model: " + card.model + " · one request, nothing else is sent";
  $("card-masked").hidden = !card.masked.length;
  $("card-masked").textContent = "Masked before sending: " + card.masked.join(", ");
  const warn = $("card-warnings");
  warn.replaceChildren(...card.warnings.map((w) => noticeNode("WARNING", w)));
  $("include").checked = card.include_chat;
  $("card-preview").textContent = card.preview;
  $("send-once").disabled = busy;
}

function schedulePoll() {
  clearTimeout(pollTimer);
  if (view.busy) pollTimer = setTimeout(() => call("state"), 80);
}

async function call(name, ...args) {
  if (!api) return;
  try {
    render(await api[name](...args, lastId));
  } catch (e) {
    console.error(name, e);
  }
}

// ---------- the prompt box ----------
const COMMANDS = [
  { cmd: "/web", arg: "<url>", what: "read a page", needs: "web" },
  { cmd: "/ask-claude", arg: "<question>", what: "ask the cloud", needs: "cloud" },
];

function updateHints() {
  const v = $("prompt").value;
  const box = $("hints");
  if (!v.startsWith("/") || v.includes(" ")) { box.hidden = true; return; }
  const found = COMMANDS.filter((c) => c.cmd.startsWith(v));
  box.replaceChildren(...found.map((c) => {
    const ready = view[c.needs];
    const h = el("span", "hint" + (ready ? "" : " off"));
    h.appendChild(el("b", "", c.cmd));
    h.appendChild(document.createTextNode(" " + c.arg + " · " + c.what + (ready ? "" : " (turn on " + c.needs.toUpperCase() + " first)")));
    return h;
  }));
  box.hidden = !found.length;
}

function grow() {
  const t = $("prompt");
  t.style.height = "auto";
  t.style.height = Math.min(t.scrollHeight, 200) + "px";
}

function submit() {
  const t = $("prompt");
  const text = t.value.trim();
  if (!text || view.busy) return;
  history.push(text);
  historyAt = -1;
  t.value = "";
  grow();
  updateHints();
  call("send", text);
}

function wire() {
  const t = $("prompt");
  t.addEventListener("input", () => { grow(); updateHints(); });
  t.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); submit(); return; }
    if (e.key === "ArrowUp" && !t.value && history.length) {
      e.preventDefault();
      historyAt = historyAt < 0 ? history.length - 1 : Math.max(0, historyAt - 1);
      t.value = history[historyAt];
      grow();
    }
    if (e.key === "Tab" && t.value.startsWith("/") && !t.value.includes(" ")) {
      const c = COMMANDS.find((c) => c.cmd.startsWith(t.value));
      if (c) { e.preventDefault(); t.value = c.cmd + " "; updateHints(); }
    }
  });
  $("send").addEventListener("click", submit);
  $("new").addEventListener("click", () => call("new_case"));
  $("save").addEventListener("click", () => call("save_case"));
  $("web").addEventListener("click", () => call("toggle_web"));
  $("cloud").addEventListener("click", () => call("toggle_cloud"));
  $("mode").addEventListener("click", () => call("toggle_mode"));
  $("suggest").addEventListener("click", () => call("ask_suggested"));
  $("include").addEventListener("change", (e) => call("set_include", e.target.checked === true));
  $("cancel").addEventListener("click", () => call("cancel_card"));
  $("privacy").addEventListener("click", () => call("open_privacy"));
  $("send-once").addEventListener("click", () => { if (view.card) call("send_once", view.card.id); });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && view.card) { e.preventDefault(); call("cancel_card"); }
    if (e.key.toLowerCase() === "k" && e.metaKey) { e.preventDefault(); call("new_case"); }
    if (e.key.toLowerCase() === "s" && e.metaKey) { e.preventDefault(); call("save_case"); }
  });
  // dropping a file would make the web view navigate to it
  for (const ev of ["dragover", "drop"]) document.addEventListener(ev, (e) => e.preventDefault());
  t.focus();
}

wire();
window.addEventListener("pywebviewready", () => {
  api = window.pywebview.api;
  call("state");
});
