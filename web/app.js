const py = await loadPyodide();
const code = await (await fetch("../src/sanitize.py")).text();
py.FS.writeFile("sanitize.py", code);
const sanitize = py.runPython(`
from sanitize import sanitize
sanitize
`);

document.getElementById("go").onclick = () => {
  const [text, report] = sanitize(document.getElementById("in").value).toJs({dict_converter: (pairs) => new Map(pairs)});
  const out = document.getElementById("out");
  const banner = document.getElementById("banner");

  if (text == null) {
    out.innerText = "email withheld";
    banner.innerText = "WARNING: email withheld: " + report.get("error");
    return;
  }

  out.innerText = text;
  const lines = [];
  report.forEach((count, name) => {
    if (count > 0) lines.push(name + ": " + count);
  });
  banner.innerText = lines.length ? "WARNING: " + lines.join(", ") : "nothing removed :)";
};