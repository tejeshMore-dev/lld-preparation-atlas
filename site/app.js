import { PHASES, TOPICS } from "./data.js";
import {
  buildBackup,
  calculateSummary,
  loadProgress,
  nextIncompleteTopic,
  parseBackup,
  saveProgress,
  setTopicCompleted,
} from "./progress.js";

const REPOSITORY_BLOB_URL =
  "https://github.com/tejeshMore-dev/lld-preparation-atlas/blob/main";
const topicIds = TOPICS.map((topic) => topic.id);

const elements = {
  completed: document.querySelector("#completed-count"),
  remaining: document.querySelector("#remaining-count"),
  percent: document.querySelector("#progress-percent"),
  ring: document.querySelector("#progress-ring"),
  track: document.querySelector(".progress-track"),
  message: document.querySelector("#progress-message"),
  continueLink: document.querySelector("#continue-link"),
  continueTitle: document.querySelector("#continue-title"),
  list: document.querySelector("#topic-list"),
  empty: document.querySelector("#empty-state"),
  search: document.querySelector("#topic-search"),
  filters: [...document.querySelectorAll("[data-filter]")],
  exportButton: document.querySelector("#export-progress"),
  importButton: document.querySelector("#import-progress"),
  importFile: document.querySelector("#import-file"),
  resetButton: document.querySelector("#reset-progress"),
  toast: document.querySelector("#toast"),
};

let progress = loadProgress(window.localStorage, topicIds);
let activeFilter = "all";
let query = "";
let toastTimer;

function formatCompletionDate(value) {
  if (!value) return "Completed";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Completed";
  return `Completed ${new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date)}`;
}

function announce(message) {
  window.clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.add("visible");
  toastTimer = window.setTimeout(() => {
    elements.toast.classList.remove("visible");
  }, 2800);
}

function persist(message) {
  try {
    saveProgress(window.localStorage, progress);
    if (message) announce(message);
  } catch {
    announce("Progress could not be saved in this browser.");
  }
}

function matchesView(topic) {
  const completed = Boolean(progress[topic.id]?.completed);
  if (activeFilter === "complete" && !completed) return false;
  if (activeFilter === "remaining" && completed) return false;
  if (!query) return true;
  const searchable = [
    topic.title,
    topic.summary,
    topic.difficulty,
    topic.prerequisite,
    `topic ${topic.id}`,
  ]
    .join(" ")
    .toLowerCase();
  return searchable.includes(query);
}

function topicCard(topic) {
  const record = progress[topic.id];
  const completed = Boolean(record?.completed);
  const checked = completed ? "checked" : "";
  const stateClass = completed ? " completed" : "";
  const status = completed ? formatCompletionDate(record.completedAt) : "Not completed";
  const href = `${REPOSITORY_BLOB_URL}/${topic.path}`;

  return `
    <article class="topic-card${stateClass}" id="topic-${topic.id}">
      <label class="topic-check" title="Mark Topic ${topic.id} complete">
        <input
          type="checkbox"
          data-topic-id="${topic.id}"
          ${checked}
          aria-label="Mark Topic ${topic.id}: ${topic.title} complete"
        />
        <span aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="m5 12.5 4.2 4.2L19 7" /></svg>
        </span>
      </label>
      <div class="topic-number" aria-hidden="true">${String(topic.id).padStart(2, "0")}</div>
      <div class="topic-content">
        <div class="topic-meta">
          <span>${topic.difficulty}</span>
          <span>${topic.prerequisite}</span>
        </div>
        <h4>${topic.title}</h4>
        <p>${topic.summary}</p>
        <div class="topic-footer">
          <span class="topic-status">${status}</span>
          <a href="${href}">Open chapter <span aria-hidden="true">↗</span></a>
        </div>
      </div>
    </article>`;
}

function renderTopics() {
  let visibleCount = 0;
  const sections = PHASES.map((phase) => {
    const topics = TOPICS.filter(
      (topic) => topic.phase === phase.id && matchesView(topic),
    );
    if (!topics.length) return "";
    visibleCount += topics.length;
    const phaseAll = TOPICS.filter((topic) => topic.phase === phase.id);
    const phaseCompleted = phaseAll.filter(
      (topic) => progress[topic.id]?.completed,
    ).length;
    return `
      <section class="phase-section" aria-labelledby="phase-${phase.id}-title">
        <header class="phase-header">
          <div class="phase-index">Phase ${phase.id}</div>
          <div>
            <h3 id="phase-${phase.id}-title">${phase.title}</h3>
            <p>${phase.subtitle}</p>
          </div>
          <span class="phase-count">${phaseCompleted}/${phaseAll.length}</span>
        </header>
        <div class="phase-topics">${topics.map(topicCard).join("")}</div>
      </section>`;
  }).join("");

  elements.list.innerHTML = sections;
  elements.empty.hidden = visibleCount !== 0;
}

function updateDashboard() {
  const summary = calculateSummary(TOPICS, progress);
  const next = nextIncompleteTopic(TOPICS, progress);
  elements.completed.textContent = String(summary.completed);
  elements.remaining.textContent = String(summary.remaining);
  elements.percent.textContent = `${summary.percent}%`;
  elements.ring.style.setProperty("--progress", `${summary.percent * 3.6}deg`);
  elements.ring.setAttribute("aria-label", `${summary.percent} percent complete`);
  elements.track.value = summary.completed;
  elements.track.textContent = `${summary.completed} of ${summary.total} topics complete`;

  if (summary.completed === 0) {
    elements.message.textContent = "Your first chapter is ready.";
  } else if (summary.completed === summary.total) {
    elements.message.textContent = "Curriculum completed.";
  } else {
    elements.message.textContent = `${summary.percent}% of the study path complete.`;
  }

  if (next) {
    elements.continueLink.href = `#topic-${next.id}`;
    elements.continueTitle.textContent = `Topic ${next.id} · ${next.title}`;
    elements.continueLink.classList.remove("all-complete");
  } else {
    elements.continueLink.href =
      `${REPOSITORY_BLOB_URL}/docs/practice/readiness-checklist.md`;
    elements.continueTitle.textContent = "Open the final readiness checklist";
    elements.continueLink.classList.add("all-complete");
  }
}

function render() {
  updateDashboard();
  renderTopics();
}

elements.list.addEventListener("change", (event) => {
  const checkbox = event.target.closest("[data-topic-id]");
  if (!checkbox) return;
  const topicId = Number(checkbox.dataset.topicId);
  progress = setTopicCompleted(progress, topicId, checkbox.checked);
  persist(checkbox.checked ? `Topic ${topicId} completed.` : `Topic ${topicId} reopened.`);
  render();
  document.querySelector(`[data-topic-id="${topicId}"]`)?.focus({ preventScroll: true });
});

elements.search.addEventListener("input", (event) => {
  query = event.target.value.trim().toLowerCase();
  renderTopics();
});

for (const button of elements.filters) {
  button.addEventListener("click", () => {
    activeFilter = button.dataset.filter;
    for (const candidate of elements.filters) {
      const selected = candidate === button;
      candidate.classList.toggle("active", selected);
      candidate.setAttribute("aria-pressed", String(selected));
    }
    renderTopics();
  });
}

elements.exportButton.addEventListener("click", () => {
  const backup = buildBackup(progress);
  const blob = new Blob([JSON.stringify(backup, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `lld-progress-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  announce("Progress backup exported.");
});

elements.importButton.addEventListener("click", () => elements.importFile.click());

elements.importFile.addEventListener("change", async () => {
  const [file] = elements.importFile.files;
  elements.importFile.value = "";
  if (!file) return;
  try {
    progress = parseBackup(JSON.parse(await file.text()), topicIds);
    persist("Progress backup imported.");
    render();
  } catch (error) {
    announce(error instanceof Error ? error.message : "Backup import failed.");
  }
});

elements.resetButton.addEventListener("click", () => {
  if (!window.confirm("Reset all topic progress stored in this browser?")) return;
  progress = {};
  persist("All local progress reset.");
  render();
});

window.addEventListener("storage", (event) => {
  if (event.key !== null && !event.key.includes("lld-preparation-bible")) return;
  progress = loadProgress(window.localStorage, topicIds);
  render();
  announce("Progress updated from another tab.");
});

for (const button of elements.filters) {
  button.setAttribute("aria-pressed", String(button.classList.contains("active")));
}

render();
