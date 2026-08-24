import test from "node:test";
import assert from "node:assert/strict";

import {
  BACKUP_FORMAT,
  STORAGE_KEY,
  buildBackup,
  calculateSummary,
  loadProgress,
  nextIncompleteTopic,
  parseBackup,
  saveProgress,
  setTopicCompleted,
} from "../progress.js";

class MemoryStorage {
  values = new Map();

  getItem(key) {
    return this.values.get(key) ?? null;
  }

  setItem(key, value) {
    this.values.set(key, value);
  }
}

const topics = [{ id: 1 }, { id: 2 }, { id: 3 }];
const ids = topics.map((topic) => topic.id);

test("topic completion is immutable and reversible", () => {
  const now = new Date("2030-01-02T03:04:05.000Z");
  const completed = setTopicCompleted({}, 1, true, now);
  assert.deepEqual(completed, {
    1: { completed: true, completedAt: now.toISOString() },
  });
  assert.deepEqual(setTopicCompleted(completed, 1, false, now), {});
  assert.equal(completed[1].completed, true);
});

test("progress round-trips through local storage", () => {
  const storage = new MemoryStorage();
  const progress = { 2: { completed: true, completedAt: null } };
  saveProgress(storage, progress);
  assert.equal(storage.getItem(STORAGE_KEY), JSON.stringify(progress));
  assert.deepEqual(loadProgress(storage, ids), progress);
});

test("invalid and stale local records are ignored", () => {
  const storage = new MemoryStorage();
  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      1: { completed: false },
      2: { completed: true, completedAt: "2030-01-01T00:00:00.000Z" },
      99: { completed: true },
    }),
  );
  assert.deepEqual(loadProgress(storage, ids), {
    2: { completed: true, completedAt: "2030-01-01T00:00:00.000Z" },
  });
});

test("summary and next topic reflect completed records", () => {
  const progress = {
    1: { completed: true, completedAt: null },
    2: { completed: true, completedAt: null },
  };
  assert.deepEqual(calculateSummary(topics, progress), {
    completed: 2,
    total: 3,
    remaining: 1,
    percent: 67,
  });
  assert.equal(nextIncompleteTopic(topics, progress)?.id, 3);
  assert.equal(nextIncompleteTopic(topics, { ...progress, 3: { completed: true } }), null);
});

test("backup validates its format and normalizes progress", () => {
  const progress = { 1: { completed: true, completedAt: null } };
  const backup = buildBackup(progress, new Date("2030-01-01T00:00:00.000Z"));
  assert.equal(backup.format, BACKUP_FORMAT);
  assert.deepEqual(parseBackup(backup, ids), progress);
  assert.throws(
    () => parseBackup({ ...backup, version: 2 }, ids),
    /not a supported LLD tracker backup/,
  );
});
