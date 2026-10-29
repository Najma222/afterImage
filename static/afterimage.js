const $ = id => document.getElementById(id);
const MAX_FRAGMENTS = 15;
let pending = false;
let lastResult = "";
let fragmentSequence = 0;

function setModelStatus(label, mode) {
  $("model-status").textContent = label;
  $("model-dot").className = "status-dot " + (mode || "");
}

function fragmentList() {
  return $("fragments").value.split(/\n|;/).map(item => item.trim()).filter(Boolean);
}

function updateCounts() {
  const text = $("fragments").value;
  $("char-count").textContent = text.length + " / 2200";
  $("fragment-count").textContent = fragmentList().length + " / 15";
}

function setMessage(text) {
  $("form-message").textContent = text;
}

function showScreen(id) {
  ["boot-screen", "reconstruct-screen"].forEach(screen => $(screen).classList.toggle("hidden", screen !== id));
}

function resetForm() {
  $("fragments").value = "";
  $("form-message").textContent = "";
  $("fragment-count").textContent = "0 / 15";
  $("char-count").textContent = "0 / 2200";
  $("reconstruct-button").disabled = false;
  document.querySelector('input[name="tone"][value="nostalgic"]').checked = true;
  $("result-screen").classList.remove("hidden");
  $("empty-state").classList.remove("hidden");
  $("memory-output").classList.add("hidden");
  $("memory-output").textContent = "";
  $("result-message").textContent = "Shaped from your fragments, not a verified factual memory.";
  showScreen("reconstruct-screen");
  $("fragments").focus();
}

async function checkHealth() {
  try {
    const data = await (await fetch("/api/health")).json();
    const engineName = $("engine-name");
    if (engineName) engineName.textContent = data.model ? "LOCAL " + data.model.toUpperCase() : "LOCAL GEMMA";
    if (data.ollama_reachable && data.model_available) setModelStatus("GEMMA READY", "ready");
    else setModelStatus("GEMMA UNAVAILABLE", "offline");
  } catch {
    setModelStatus("GEMMA UNAVAILABLE", "offline");
  }
}

async function reconstruct(event) {
  event.preventDefault();
  if (pending) return;
  const fragments = fragmentList();
  const tone = document.querySelector('input[name="tone"]:checked')?.value;
  if (!fragments.length) { setMessage("Add at least one fragment first."); $("fragments").focus(); return; }
  if (fragments.length > MAX_FRAGMENTS) { setMessage("Use 15 fragments or fewer."); return; }
  pending = true;
  $("reconstruct-button").disabled = true;
  $("loading-state").classList.remove("hidden");
  $("form-message").textContent = "";
  const loadingCopy = ["Reading the afterimage…", "Sorting damaged signals…", "Stitching the quiet parts…"];
  let tick = 0;
  const loadingTimer = setInterval(() => { $("loading-copy").textContent = loadingCopy[tick++ % loadingCopy.length]; }, 900);
  try {
    const response = await fetch("/api/reconstruct", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ fragments, tone }) });
    const data = await response.json();
    if (!response.ok || data.ok !== true) throw new Error(data.error || "Gemma could not reconstruct this memory.");
    lastResult = data.memory;
    $("memory-output").textContent = data.memory;
    $("empty-state").classList.add("hidden");
    $("memory-output").classList.remove("hidden");
    fragmentSequence += 1;
    $("result-code").textContent = "FRAGMENT_" + String(fragmentSequence).padStart(3, "0");
    $("result-tone").textContent = "MOOD: " + data.tone.toUpperCase();
    $("result-source").textContent = (data.model || "GEMMA").toUpperCase() + " / LOCAL MODEL";
    $("result-fragments").textContent = fragments.length + " FRAGMENTS USED";
    $("result-screen").classList.remove("hidden");
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    $("result-screen").scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
  } catch (error) {
    setMessage(error.message || "Gemma is unavailable. Check Ollama and try again.");
  } finally {
    clearInterval(loadingTimer);
    $("loading-state").classList.add("hidden");
    $("reconstruct-button").disabled = false;
    pending = false;
  }
}

document.querySelectorAll(".example-chip").forEach(chip => chip.addEventListener("click", () => {
  const current = $("fragments").value.trim();
  if (fragmentList().length >= MAX_FRAGMENTS) return;
  $("fragments").value = current ? current + "\n" + chip.textContent : chip.textContent;
  updateCounts();
}));
$("fragments").addEventListener("input", updateCounts);
$("enter-button").addEventListener("click", () => { showScreen("reconstruct-screen"); $("fragments").focus(); });
$("memory-form").addEventListener("submit", reconstruct);
$("again-button").addEventListener("click", resetForm);
$("copy-button").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(lastResult); $("result-message").textContent = "Memory copied to the clipboard."; }
  catch { $("result-message").textContent = "Copy was blocked by the browser. Select the text manually."; }
});
$("download-button").addEventListener("click", () => {
  const blob = new Blob([lastResult], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "afterimage-memory.txt"; link.click(); URL.revokeObjectURL(link.href);
});
$("about-button").addEventListener("click", () => $("about-dialog").showModal());
$("about-close").addEventListener("click", () => $("about-dialog").close());
showScreen("boot-screen");
checkHealth();
