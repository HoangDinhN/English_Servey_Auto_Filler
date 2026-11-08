import assert from "node:assert/strict";

await import("../distribution-utils.js");
await import("../desired-distributions.js");

const { allocateCounts, buildSchedule, findBestLabelIndex } =
  globalThis.RandomFormDistribution;

assert.deepEqual(allocateCounts([35, 35, 30], 1), [1, 0, 0]);
assert.deepEqual(allocateCounts([35, 35, 30], 2), [1, 1, 0]);
assert.deepEqual(allocateCounts([90, 10], 2), [1, 1]);
assert.deepEqual(allocateCounts([100], 2), [2]);
assert.deepEqual(allocateCounts([55, 45], 20), [11, 9]);
assert.deepEqual(allocateCounts([25, 35, 25, 15], 20), [5, 7, 5, 3]);

const schedule = buildSchedule([20, 30, 50], 10, "stable-seed");
assert.equal(schedule.length, 10);
assert.deepEqual(
  schedule.reduce((counts, optionIndex) => {
    counts[optionIndex] += 1;
    return counts;
  }, [0, 0, 0]),
  [2, 3, 5]
);
assert.deepEqual(schedule, buildSchedule([20, 30, 50], 10, "stable-seed"));

const likertLabels = [
  ["Strongly disagree"],
  ["Disagree"],
  ["Neither agree nor disagree"],
  ["Agree"],
  ["Strongly agree"]
];
assert.equal(findBestLabelIndex(likertLabels, "Strongly disagree"), 0);
assert.equal(findBestLabelIndex(likertLabels, "Disagree"), 1);
assert.equal(findBestLabelIndex(likertLabels, "Neither agree nor disagree"), 2);
assert.equal(findBestLabelIndex(likertLabels, "Agree"), 3);
assert.equal(findBestLabelIndex(likertLabels, "Strongly agree"), 4);
assert.equal(
  findBestLabelIndex(
    likertLabels.map(([label]) => [`WTC2 row, ${label}`]),
    "Agree"
  ),
  3
);
assert.equal(findBestLabelIndex(likertLabels, "Missing option"), -1);

const wtc2 = globalThis.RANDOM_FORM_DESIRED_DISTRIBUTIONS[9];
const gridCandidateLabels = likertLabels.map(([label]) => [
  `WTC2. I am willing to ask a question, ${label}`
]);
const mappedWtc2Counts = buildSchedule(
  wtc2.options.map((option) => option.percent),
  20,
  "grid-regression"
).reduce((counts, desiredOptionIndex) => {
  const actualOptionIndex = findBestLabelIndex(
    gridCandidateLabels,
    wtc2.options[desiredOptionIndex].label
  );
  counts[actualOptionIndex] += 1;
  return counts;
}, [0, 0, 0, 0, 0]);
assert.deepEqual(mappedWtc2Counts, [0, 2, 1, 12, 5]);

assert.equal(globalThis.RANDOM_FORM_DESIRED_DISTRIBUTIONS.length, 20);
assert.deepEqual(
  globalThis.RANDOM_FORM_DESIRED_DISTRIBUTIONS[0].options.map((option) => option.percent),
  [90, 10]
);
assert.deepEqual(
  globalThis.RANDOM_FORM_DESIRED_DISTRIBUTIONS[1].options.map((option) => option.percent),
  [25, 20, 25, 20, 10, 0]
);
assert.deepEqual(
  globalThis.RANDOM_FORM_DESIRED_DISTRIBUTIONS[19].options.map((option) => option.percent),
  [0, 0, 0, 45, 55]
);
for (const distribution of globalThis.RANDOM_FORM_DESIRED_DISTRIBUTIONS) {
  const total = distribution.options.reduce((sum, option) => sum + option.percent, 0);
  assert.equal(total, 100, `Question ${distribution.number} must total 100%`);
}

console.log("desired answer distribution allocation: OK");
