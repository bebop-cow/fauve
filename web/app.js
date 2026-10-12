const py = await loadPyodide();
const code = await (await fetch("../src/sanitize.py")).text();
py.FS.writeFile("sanitize.py", code);
const sanitize = py.runPython(`
from sanitize import sanitize
sanitize
`);
document.getElementById("go").onclick = () => {
  const [text, report] = sanitize(document.getElementById("in").value).toJs();
  const out = document.getElementById("out");
  if (text == null) {
    out.innerText = "email withheld";
  } else {
    out.innerText = text;
  }
};