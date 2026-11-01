// Loads classifier.json once; scores a hint; returns a slot or null.
let model = null;

export async function loadClassifier() {
  if (!model) {
    const res = await fetch(chrome.runtime.getURL("classifier.json"));
    model = await res.json();
  }
  return model;
}
 
// For tests: use a model object directly.
export function setModel(m) { model = m; }

export function ngrams(text) {
  const counts = {};
    const clean = text.toLowerCase().replace(/[^\p{L}\p{N}_]/gu, " ");
    for (const word of clean.split(/\s+/)) {
      if (!word) continue;
        const padded = " " + word + " ";
        for (const n in [2, 3, 4]) {
            for (let start = 0; start < padded.length - n + 1; start++) {
        const piece = padded.slice(start, start + n);
        counts[piece] = (counts[piece] || 0) + 1;
      }
    }
  }
  return counts;
}

export function classify(hint) {
  if (!model || typeof hint !== "string") return { slot: null, sure: 0 };
 
  const scores = [...model.intercept];
  for (const [gram, count] of Object.entries(ngrams(hint))) {
    const w = model.weights[gram];
    if (!w) continue;                              // a pattern it never saw adds nothing
    for (let c = 0; c < scores.length; c++) scores[c] += count * w[c];
  }
 
  // softmax: turn scores into probabilities that add up to 1
  const max = Math.max(...scores);
  const exps = scores.map(s => Math.exp(s - max));
  const sum = exps.reduce((a, b) => a + b, 0);
  const probs = exps.map(e => e / sum);
 
  let best = 0;
  for (let c = 1; c < probs.length; c++) if (probs[c] > probs[best]) best = c;
  const label = model.classes[best];
  const sure = probs[best];
  const slot = sure >= model.threshold && label !== "none" ? label : null;
  return { slot, sure };
}