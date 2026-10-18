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

  for (const b of brokers) {
    const row = document.createElement("li");
    const link = document.createElement("a");
    link.textContent = b.name;
    row.append(link);
    if (b.type === "email") {
      link.href = "mailto:" + b.email
        + "?subject=" + encodeURIComponent(fill(subject, b))               // the filled subject, encoded
        + "&body=" + encodeURIComponent(fill(body, b));                 // the filled body, encoded
        const copy = document.createElement("button");
        row.append(copy);
  	copy.textContent = "Copy";
  	copy.onclick = () => navigator.clipboard.writeText("To: " + b.email + "\nSubject: " + fill(subject, b) + "\n\n" + fill(body, b)).then(() => { copy.textContent = "Copied"; });
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