const py = await loadPyodide();


for (const name of ["sanitize.py", "scan.py", "pipeline.py"]) {
  const code = await (await fetch("../src/" + name, {cache: "no-store"})).text();
  py.FS.writeFile(name, code);
}

const prepare = py.runPython(`
from pipeline import prepare
prepare
`);

document.getElementById("go").onclick = () => {
  const emails = document.getElementById("in").value.split("\n---\n");
  const [modelInput, banners] = prepare(py.toPy(emails)).toJs();

  document.getElementById("model").innerText = modelInput.join("\n\n");
  document.getElementById("banner").innerText =
    banners.length ? "WARNING: " + banners.join(" | ") : "nothing removed :)";
};