export const STORAGE_KEY = "lld-preparation-bible:topic-progress:v1";
export const BACKUP_FORMAT = "lld-preparation-bible-progress";

export function normalizeProgress(value, validTopicIds) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  const validIds = new Set(validTopicIds);
  const normalized = {};

  for (const [rawId, rawRecord] of Object.entries(value)) {
    const id = Number(rawId);
    if (!validIds.has(id) || !rawRecord || typeof rawRecord !== "object") continue;
    if (rawRecord.completed !== true) continue;
    normalized[id] = {
      completed: true,
      completedAt:
        typeof rawRecord.completedAt === "string" ? rawRecord.completedAt : null,
    };
  }
  return normalized;
}

export function loadProgress(storage, validTopicIds) {
  try {
    const raw = storage.getItem(STORAGE_KEY);
    return normalizeProgress(raw ? JSON.parse(raw) : {}, validTopicIds);
  } catch {
    return {};
  }
}

export function saveProgress(storage, progress) {
  storage.setItem(STORAGE_KEY, JSON.stringify(progress));
}

export function setTopicCompleted(progress, topicId, completed, now = new Date()) {
  const next = { ...progress };
  if (completed) {
    next[topicId] = {
      completed: true,
      completedAt: now.toISOString(),
    };
  } else {
    delete next[topicId];
  }
  return next;
}

export function calculateSummary(topics, progress) {
  const completed = topics.filter((topic) => progress[topic.id]?.completed).length;
  const total = topics.length;
  return {
    completed,
    total,
    remaining: total - completed,
    percent: total === 0 ? 0 : Math.round((completed / total) * 100),
  };
}

export function nextIncompleteTopic(topics, progress) {
  return topics.find((topic) => !progress[topic.id]?.completed) ?? null;
}

export function buildBackup(progress, now = new Date()) {
  return {
    format: BACKUP_FORMAT,
    version: 1,
    exportedAt: now.toISOString(),
    progress,
  };
}

export function parseBackup(value, validTopicIds) {
  if (!value || typeof value !== "object") throw new Error("Invalid backup file.");
  if (value.format !== BACKUP_FORMAT || value.version !== 1) {
    throw new Error("This is not a supported LLD tracker backup.");
  }
  return normalizeProgress(value.progress, validTopicIds);
}
