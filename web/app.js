const py = await loadPyodide();

for (const name of ["sanitize.py", "pipeline.py", "scan.py"]) {
  const code = await (await fetch("../src/" + name)).text();
  py.FS.writeFile(name, code);
}

const prepare = py.runPython(`
from pipeline import prepare
prepare
`);

const find = py.runPython(`
from scan import find_sensitive
find_sensitive
`);

document.getElementById("go").onclick = () => {
  const emails = document.getElementById("in").value.split("\n---\n");
  const [modelInput, banners] = prepare(py.toPy(emails)).toJs();

  const extra = [];
  modelInput.forEach((chunk, i) => {
    const kinds = find(chunk).toJs();
    if (kinds.length > 0) {
      extra.push("EMAIL " + (i + 1) + " of " + modelInput.length + ": sensitive data: " + kinds.join(", "));
    }
  });
  const all = [...banners, ...extra];

  document.getElementById("model").innerText = modelInput.join("\n\n");
  document.getElementById("banner").innerText =
    all.length ? "WARNING: " + all.join(" | ") : "nothing removed :)";
};