const ids = ["name", "email", "phone", "place"];
const msg = document.getElementById("msg");

// On open: put saved details back in the boxes.
const { details } = await chrome.storage.session.get("details");
if (details) {
  for (const id of ids) document.getElementById(id).value = details[id];   // that id's saved value
}

// Save: collect the four boxes into one object and store it.
document.getElementById("save").onclick = async () => {
  const d = {};
  for (const id of ids) d[id] = document.getElementById(id).value;                                // that box's value
  await chrome.storage.session.set({ details: d });
  msg.textContent = "Saved until you close the browser.";
};

const recipes = await (await fetch(chrome.runtime.getURL("recipes.json"))).json();


function splitName(full) {
  const parts = full.trim().split(/\s+/);
  return {
    first: parts[0],                                    // the first part
    last: parts.length > 1 ? parts[parts.length - 1] : "",             // the final part
    middle: parts.slice(1, -1).join(" ")                                    // the parts in between, joined with " "
  };
}

// Runs INSIDE the broker page. Fills only; never clicks or submits.
function fillPage(fields, values) {
  let filled = 0;
  const v = values[slot];
  if (!v) continue;                 // nothing to put here: leave the field alone
  setValue.call(el, v);
  for (const [selector, slot] of Object.entries(fields)) {
    const el = document.querySelector(selector);
    if (!el || el.disabled || el.readOnly) continue;   // missing or locked field: skip it
    setValue.call(el, values[slot] ?? "");
    el.dispatchEvent(new Event("input", { bubbles: true }));  // tell the page's code the value changed
    filled++;
  }
  return filled;
}
// Runs INSIDE the page when there's no recipe. Guesses each field from its clues.
// Fills only; never clicks or submits. When unsure, leaves the field alone.
function autoFill(values) {
  function labelText(el) {
    return [...(el.labels || [])].map(l => l.textContent).join(" ");
  }

  function guessSlot(el) {
    const clues = [el.autocomplete, el.type, el.name, el.id, el.placeholder,
                   el.getAttribute("aria-label"), labelText(el)].join(" ").toLowerCase();
    if (clues.includes("email")|| el.type === "email") return "email";     // clues contain "email", or the type is "email"
    if (clues.includes("phone")||el.type === "tel") return "phone";     // type is "tel", or clues contain "phone"
    if (clues.includes("middle")) return "middle";    // clues contain "middle"
    if (clues.includes("given-name") || clues.includes("first")) return "first";     // clues contain "given-name" or "first"
    if (clues.includes("family-name") || clues.includes("last") || clues.includes("surname")) return "last";      // clues contain "family-name", "last" or "surname"
    return null;                 // anything else: don't touch it
  }

  const setValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
  const SKIP = ["hidden", "password", "search", "checkbox", "radio", "submit", "button", "file"];
  let filled = 0;
  for (const el of document.querySelectorAll("input")) {
    if (SKIP.includes(el.type) || el.disabled || el.readOnly) continue;
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
const name = splitName(document.getElementById("name").value);
   const values = { ...name, email: document.getElementById("email").value, phone: document.getElementById("phone").value };
  if (!name.first) { msg.textContent = "Enter your name first."; return; }
  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: fillPage,
    args: [recipe.fields, { name, email: document.getElementById("email").value }]
  });
  msg.textContent = "Filled " + result + " field(s). Check them, then continue yourself:\n• " + recipe.manual.join("\n• ");
};


if (!recipe) {
  let pendingHost = ""
  document.getElementById("fill").onclick = async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const host = tab.url ? new URL(tab.url).hostname : "";
  const recipe = Object.values(recipes).find(r => r.host === host);        // the recipe whose host equals this page's host
  if (pendingHost !== host) { 
    pendingHost = host;
    msg.textContent = host + "isn't a known data broker. Check the address, then click Fill again to fill it anyway."; 
    return; 
  } else {
    const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id }, func: autoFill, args: [values]
    msg.textContent = "Filled" + result +"field(s)(outlined in gold). Check every one before you submit.";
    });
    
  }
}


  