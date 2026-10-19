
const CA_SUBJECT = "CCPA request to delete and opt out – {name}";
const CA_BODY = `To {broker}:

Under the California Consumer Privacy Act, I request that you:
1. Delete all personal information you hold about me (Civ. Code §1798.105).
2. Stop selling or sharing my personal information (§1798.120).
3. Limit use of any sensitive personal information (§1798.121).

Name: {name}
Email: {email}
Phone: {phone}
City/State: {city_state}

Please confirm in writing within 45 days, as §1798.130 requires. I'll verify my identity through your standard process, but please don't ask for more information than necessary.

Thank you,
{name}`;

const GEN_SUBJECT = "Request to delete and opt out – {name}";
const GEN_BODY = `To {broker}:

I request that you delete all personal information you hold about me and stop selling or sharing it, under any state privacy law that applies to you.

Name: {name}
Email: {email}
Phone: {phone}
City/State: {city_state}

Please confirm in writing when this is done.

Thank you,
{name}`;

const brokers = await (await fetch("brokers.json", { cache: "no-store" })).json();

const nameBox = document.getElementById("name");
const emailBox = document.getElementById("email");
const phoneBox = document.getElementById("phone");
const placeBox = document.getElementById("place");
const caBox = document.getElementById("ca");          // checkbox
const makeBtn = document.getElementById("make");
const list = document.getElementById("list");

const sent = {};                                   // broker name → "YYYY-MM-DD", in memory only
const today = () => new Date().toLocaleDateString("en-CA");

const dlBtn = document.getElementById("dl");
const loadInput = document.getElementById("load");
const statusList = document.getElementById("status");

// Replace each {slot} in a template with the user's value.
function fill(template, broker) {
  return template
    .replaceAll("{name}", nameBox.value)
    .replaceAll("{email}", emailBox.value)
    .replaceAll("{phone}", phoneBox.value)
    .replaceAll("{city_state}", placeBox.value)
    .replaceAll("{broker}", broker.name);
}

// Only allow real web links; the registry has entries without https://.
function safeUrl(u) {
  if (!u.startsWith("http")) u = "https://" + u;
  return u.startsWith("https://") || u.startsWith("http://") ? u : null;                 // true only if u starts with "https://" or "http://"
}

makeBtn.addEventListener("click", () => {
  list.textContent = "";                 // clear old buttons
  const subject = caBox.checked ? CA_SUBJECT : GEN_SUBJECT;
  const body = caBox.checked ? CA_BODY : GEN_BODY;

  if (!nameBox.value.trim() || !emailBox.value.trim()) { list.textContent = "Enter at least your name and email."; return; }

  for (const b of brokers) {
    const row = document.createElement("li");
    const link = document.createElement("a");
    link.textContent = b.name;
    row.append(link);
    link.addEventListener("click", () => { sent[b.name] = today(); });
    if (b.type === "email") {
      link.href = "mailto:" + b.email
        + "?subject=" + encodeURIComponent(fill(subject, b))               // the filled subject, encoded
        + "&body=" + encodeURIComponent(fill(body, b));                 // the filled body, encoded
        const copy = document.createElement("button");
        row.append(copy);
  	copy.textContent = "Copy";
  	copy.onclick = () => navigator.clipboard.writeText("To: " + b.email + "\nSubject: " + fill(subject, b) + "\n\n" + fill(body, b)).then(() => { copy.textContent = "Copied"; sent[b.name] = today(); });
    } else {
      const u = safeUrl(b.rights_url);
      if (!u) continue;                   // skip anything that isn't a web link
      link.href = u;
      link.target ="_blank";
      link.rel = "noopener";
  	}
  
  	list.append(row);
  }
});

dlBtn.onclick = () => {
  const blob = new Blob([JSON.stringify(sent)], { type: "application/json" });   // `sent` as JSON text
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "houdini-tracker.json";
  a.click();
  URL.revokeObjectURL(a.href);
};

// Load: read the file back and flag overdue brokers.
loadInput.onchange = async () => {
  try {
    const data = JSON.parse(await loadInput.files[0].text());
    statusList.textContent = "";
    for (const [name, date] of Object.entries(data)) {
      if (!brokers.some(x => x.name === name)) continue;        // only known brokers
      if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) continue;          // only real dates
      const days = (Date.now() - new Date(date)) / 86400000;
      const line = document.createElement("li");
      line.textContent = name + ": sent " + date + " – " + (days > 45 ? "overdue, send a follow-up" : "waiting (" + Math.floor(days) + " days)");
      statusList.append(line);
    }
  } catch {
    statusList.textContent = "Couldn't read that file.";
  }
};