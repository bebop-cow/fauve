const ids = ["name", "email", "phone", "place"];
const msg = document.getElementById("msg");

// On open: put saved details back in the boxes.
const { details } = await chrome.storage.session.get("details");
if (details) {
  for (const id of ids) document.getElementById(id).value = details[id] ?? "";
}

// Save: collect the four boxes into one object and store it (memory only).
document.getElementById("save").onclick = async () => {
  const d = {};
  for (const id of ids) d[id] = document.getElementById(id).value;
  await chrome.storage.session.set({ details: d });
  msg.textContent = "Saved until you close the browser.";
};

const recipes = await (await fetch(chrome.runtime.getURL("recipes.json"))).json();

// "Ann Bee Cee" -> { first: "Ann", middle: "Bee", last: "Cee" }
function splitName(full) {
  const parts = full.trim().split(/\s+/);
  return {
    first: parts[0],
    last: parts.length > 1 ? parts[parts.length - 1] : "",
    middle: parts.slice(1, -1).join(" ")
  };
}

// Runs INSIDE a page that has a recipe. Fills only; never clicks or submits.
function fillPage(fields, values) {
  let filled = 0;
  const setValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
  for (const [selector, slot] of Object.entries(fields)) {
    const el = document.querySelector(selector);
    if (!el || el.disabled || el.readOnly) continue;   // missing or locked field: skip it
    const v = values[slot];
    if (!v) continue;                                 // nothing to put here: leave the field alone
    setValue.call(el, v);
    el.dispatchEvent(new Event("input", { bubbles: true }));
    filled++;
  }
  return filled;
}

// Runs INSIDE a page with no recipe. Guesses each field from its clues.
// Fills only; never clicks or submits. When unsure, leaves the field alone.
function autoFill(values) {
  function labelText(el) {
    return [...(el.labels || [])].map(l => l.textContent).join(" ");
  }

  function guessSlot(el) {
    const clues = [el.autocomplete, el.type, el.name, el.id, el.placeholder,
                   el.getAttribute("aria-label"), labelText(el)].join(" ").toLowerCase();
    if (clues.includes("email") || el.type === "email") return "email";
    if (clues.includes("phone") || el.type === "tel") return "phone";
    if (clues.includes("middle")) return "middle";
    if (clues.includes("given-name") || clues.includes("first")) return "first";
    if (clues.includes("family-name") || clues.includes("last") || clues.includes("surname")) return "last";
    return null;
  }

  function looksLikeSearch(el) {
    const form = el.closest("form, [role=search]");
    if (!form) return false;
    if (form.getAttribute("role") === "search") return true;                                  // the form's role attribute is "search"
    if ((form.getAttribute("action") || "").toLowerCase().includes("search")) return true;                                  // the form's action contains "search"
    const buttons = form.querySelectorAll("button, input[type=submit]");
    return [...buttons].some(b => (b.textContent + " " + b.value).toLowerCase().includes("search"));                    // the button's text or value, lowercased, includes "search"
  }

  const setValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
  const SKIP = ["hidden", "password", "search", "checkbox", "radio", "submit", "button", "file"];
  let filled = 0;
  for (const el of document.querySelectorAll("input")) {
    if (SKIP.includes(el.type) || el.disabled || el.readOnly) continue;
    if (looksLikeSearch(el)) continue;
    if (el.offsetParent === null) continue;   // invisible: could be a bot trap
    if (el.value) continue;                   // never overwrite what's there
    const slot = guessSlot(el);
    const v = slot && values[slot];
    if (!v) continue;
    setValue.call(el, v);
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.style.outline = "2px solid #ddb13c";   // highlight so the user can check it
    filled++;
  }
  return filled;
}

let pendingHost = "";   // an unknown site the user was warned about once

document.getElementById("fill").onclick = async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const host = tab.url ? new URL(tab.url).hostname : "";

  const name = splitName(document.getElementById("name").value);
  if (!name.first) { msg.textContent = "Enter your name first."; return; }
  const values = {
    ...name,
    email: document.getElementById("email").value,
    phone: document.getElementById("phone").value
  };

  const recipe = Object.values(recipes).find(r => r.host === host);

  if (!recipe) {
    const path = new URL(tab.url).pathname.toLowerCase();
    if (!/opt.?out|remov|suppress|privacy|delete|do-not-sell|request/.test(path)) {
      msg.textContent = "This doesn't look like an opt-out page, so Houdini won't auto-fill here.";
      return;
    }
    if (pendingHost !== host) {               // first click on this site: warn only
      pendingHost = host;
      msg.textContent = host + " isn't a known data broker. Check the address, then click Fill again to fill it anyway.";
      return;
    }
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id }, func: autoFill, args: [values]
    });
    msg.textContent = "Filled " + result + " field(s) (outlined in gold). Check every one before you submit.";
    return;
  }

  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id }, func: fillPage, args: [recipe.fields, values]
  });
  msg.textContent = "Filled " + result + " field(s). Check them, then continue yourself:\n• " + recipe.manual.join("\n• ");
};