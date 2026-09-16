const form = document.getElementById("matcher-form");
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("resume");
const dropzoneText = document.getElementById("dropzone-text");
const errorMsg = document.getElementById("error-msg");
const submitBtn = document.getElementById("submit-btn");
const resultSection = document.getElementById("result");

dropzone.addEventListener("click", () => fileInput.click());
dropzone.setAttribute("tabindex", "0");
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fileInput.click();
  }
});

["dragenter", "dragover"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  })
);

["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  })
);

dropzone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (file) {
    fileInput.files = e.dataTransfer.files;
    updateDropzoneLabel(file);
  }
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) updateDropzoneLabel(file);
});

function updateDropzoneLabel(file) {
  dropzone.classList.add("has-file");
  dropzoneText.textContent = `${file.name} (${(file.size / 1024).toFixed(0)} KB)`;
}

function showError(message) {
  errorMsg.textContent = message;
  errorMsg.hidden = false;
}

function clearError() {
  errorMsg.hidden = true;
  errorMsg.textContent = "";
}

function scoreColor(score) {
  if (score >= 65) return "#3ecf8e";
  if (score >= 45) return "#f2b84b";
  return "#f2665a";
}

function renderChips(container, items, missing) {
  container.innerHTML = "";
  if (items.length === 0) {
    const note = document.createElement("span");
    note.className = "empty-note";
    note.textContent = missing ? "No missing keywords — great coverage!" : "No matches found.";
    container.appendChild(note);
    return;
  }
  items.forEach((kw) => {
    const chip = document.createElement("span");
    chip.className = missing ? "chip missing" : "chip";
    chip.textContent = kw;
    container.appendChild(chip);
  });
}

function renderResult(data) {
  const color = scoreColor(data.overall_score);

  document.getElementById("score-value").textContent = data.overall_score;
  document.getElementById("score-ring").style.background =
    `conic-gradient(${color} ${data.overall_score * 3.6}deg, var(--border) 0deg)`;

  document.getElementById("verdict").textContent = data.verdict;

  document.getElementById("similarity-bar").style.width = `${data.similarity_score}%`;
  document.getElementById("similarity-value").textContent = `${data.similarity_score}%`;

  document.getElementById("keyword-bar").style.width = `${data.keyword_score}%`;
  document.getElementById("keyword-value").textContent = `${data.keyword_score}%`;

  document.getElementById("matched-count").textContent = `(${data.matched_keywords.length})`;
  document.getElementById("missing-count").textContent = `(${data.missing_keywords.length})`;

  renderChips(document.getElementById("matched-chips"), data.matched_keywords, false);
  renderChips(document.getElementById("missing-chips"), data.missing_keywords, true);

  resultSection.hidden = false;
  resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError();

  if (!fileInput.files[0]) {
    showError("Please upload a resume file (PDF or DOCX).");
    return;
  }

  const jd = document.getElementById("job_description").value.trim();
  if (!jd) {
    showError("Please paste a job description.");
    return;
  }

  const formData = new FormData();
  formData.append("resume", fileInput.files[0]);
  formData.append("job_description", jd);

  submitBtn.disabled = true;
  submitBtn.textContent = "Analyzing...";

  try {
    const res = await fetch("/analyze", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      showError(data.error || "Something went wrong. Please try again.");
      resultSection.hidden = true;
      return;
    }

    renderResult(data);
  } catch (err) {
    showError("Network error. Please try again.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Analyze Match";
  }
});
