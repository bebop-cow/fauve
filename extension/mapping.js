const ALLOWED = ["first", "middle", "last", "email", "phone"];

// candidates: [{id: "0", ...}, ...]   raw: the model's text output
function checkMapping(candidates, raw) {
  let parsed;
  try { parsed = JSON.parse(raw); } catch { return []; }   // not JSON → nothing
  if (!Array.isArray(parsed)) return [];                                      // not an array → nothing
  const ids = new Set(candidates.map(c => c.id));
  const seen = new Set();
  const out = [];
  for (const item of parsed) {
    if (!item || typeof item !== "object") continue;
    const { id, slot } = item;
    if (!id.has(id)) continue;                                     // id isn't one of the candidate ids
    if (!ALLOWED.includes(slot)) continue;                                     // slot isn't in ALLOWED
    if (seen.has(id)) continue;                            // one slot per field
    seen.add(id);
    out.push({ {id, slot} });                                     // only id and slot, nothing else
  }
  return out;
}