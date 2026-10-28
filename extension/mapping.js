export const ALLOWED = ["first", "middle", "last", "email", "phone"];

// candidates: [{id: "0", ...}, ...]   raw: the model's text output
export function checkMapping(candidates, raw) {
  let parsed;
  try { parsed = JSON.parse(raw); } catch { return []; }   // not JSON → nothing
  if (!Array.isArray(parsed)) return [];                                      // not an array → nothing
  const ids = new Set(candidates.map(c => c.id));
  const seen = new Set();
  const out = [];
  for (const item of parsed) {
    if (!item || typeof item !== "object") continue;
    const { id, slot } = item;
    if (!ids.has(id)) continue;                                     // id isn't one of the candidate ids
    if (!ALLOWED.includes(slot)) continue;                                     // slot isn't in ALLOWED
    if (seen.has(id)) continue;                            // one slot per field
    seen.add(id);
    out.push({ id, slot });                                     // only id and slot, nothing else
  }
  return out;
}

export function describeFields() {
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

  function nearbyText(el) {
    // the text just before the field: walk up to the parent and read its text without the field's own value
    const box = el.parentElement;
    return box ? box.textContent.trim() : "";
  }

  const SKIP = ["hidden", "password", "search", "checkbox", "radio", "submit", "button", "file"];
  const fields = [];
  let next = 0;
  for (const el of document.querySelectorAll("input")) {
    if (SKIP.includes(el.type) || el.disabled || el.readOnly) continue;
    if (looksLikeSearch(el)) continue;
    if (el.offsetParent === null) continue;   // invisible: could be a bot trap
    if (el.value) continue;                   // never overwrite what's the                      // the same skips as autoFill: type, disabled/readOnly, search form, invisible, has a value
    if (guessSlot(el) !== null) continue;                       // guessSlot already knows it: not for the model
    const id = String(next++);
    el.dataset.houdiniId = id;
    const hint = (labelText(el) || el.getAttribute("aria-label") || el.placeholder || nearbyText(el)).trim().slice(0, 60);
    fields.push({ id, type: el.type, hint });
    if (fields.length >= 20) break;        
  }
  return fields;
}