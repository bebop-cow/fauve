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

document.getElementById("fill").onclick = async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const host = tab.url ? new URL(tab.url).hostname : "";
  const recipe = Object.values(recipes).find(r => r.host === host);        // the recipe whose host equals this page's host
  if (!recipe) { msg.textContent = "Houdini doesn't support this page."; return; }

  const name = splitName(document.getElementById("name").value);
  if (!name.first) { msg.textContent = "Enter your name first."; return; }
  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: fillPage,
    args: [recipe.fields, { ...name, email: document.getElementById("email").value }]
  });
  msg.textContent = "Filled " + result + " field(s). Check them, then continue yourself:\n• " + recipe.manual.join("\n• ");
};