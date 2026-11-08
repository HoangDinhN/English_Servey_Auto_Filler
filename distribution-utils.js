(() => {
  "use strict";

  function rankedPositiveIndexes(percentages) {
    return percentages
      .map((value, index) => ({ index, value: Math.max(0, Number(value) || 0) }))
      .filter((item) => item.value > 0)
      .sort((a, b) => b.value - a.value || a.index - b.index)
      .map((item) => item.index);
  }

  function allocateCounts(rawPercentages, rawTotalRuns) {
    const percentages = rawPercentages.map((value) => Math.max(0, Number(value) || 0));
    const totalRuns = Math.max(1, Math.floor(Number(rawTotalRuns) || 1));
    const counts = Array(percentages.length).fill(0);
    const positive = rankedPositiveIndexes(percentages);
    if (!positive.length) return counts;

    if (totalRuns === 1) {
      counts[positive[0]] = 1;
      return counts;
    }

    if (totalRuns === 2) {
      counts[positive[0]] += 1;
      counts[positive[1] ?? positive[0]] += 1;
      return counts;
    }

    const sum = percentages.reduce((total, value) => total + value, 0);
    const quotas = percentages.map((value) => (value / sum) * totalRuns);
    quotas.forEach((quota, index) => {
      counts[index] = Math.floor(quota);
    });

    let remaining = totalRuns - counts.reduce((total, value) => total + value, 0);
    const remainderOrder = quotas
      .map((quota, index) => ({
        index,
        remainder: quota - Math.floor(quota),
        percentage: percentages[index]
      }))
      .sort(
        (a, b) =>
          b.remainder - a.remainder ||
          b.percentage - a.percentage ||
          a.index - b.index
      );

    for (let cursor = 0; remaining > 0; cursor += 1, remaining -= 1) {
      counts[remainderOrder[cursor % remainderOrder.length].index] += 1;
    }
    return counts;
  }

  function hashSeed(value) {
    let hash = 2166136261;
    for (const character of String(value)) {
      hash ^= character.codePointAt(0);
      hash = Math.imul(hash, 16777619);
    }
    return hash >>> 0;
  }

  function buildSchedule(percentages, totalRuns, seed = "") {
    const counts = allocateCounts(percentages, totalRuns);
    const schedule = [];
    counts.forEach((count, optionIndex) => {
      for (let index = 0; index < count; index += 1) schedule.push(optionIndex);
    });

    let state = hashSeed(seed) || 1;
    for (let index = schedule.length - 1; index > 0; index -= 1) {
      state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
      const target = state % (index + 1);
      [schedule[index], schedule[target]] = [schedule[target], schedule[index]];
    }
    return schedule;
  }

  function normalizedLabel(value) {
    return String(value || "")
      .normalize("NFC")
      .toLocaleLowerCase("vi")
      .normalize("NFD")
      .replace(/\p{M}+/gu, "")
      .replace(/[^\p{L}\p{N}]+/gu, " ")
      .trim();
  }

  function findBestLabelIndex(rawCandidateLabels, rawTargetLabel) {
    const target = normalizedLabel(rawTargetLabel);
    if (!target) return -1;

    const candidates = rawCandidateLabels.map((labels) =>
      (Array.isArray(labels) ? labels : [labels])
        .map(normalizedLabel)
        .filter(Boolean)
    );

    const exactIndex = candidates.findIndex((labels) => labels.includes(target));
    if (exactIndex >= 0) return exactIndex;

    const wholePhrase = ` ${target} `;
    const targetWordCount = target.split(" ").length;
    let bestIndex = -1;
    let smallestExtraWordCount = Number.POSITIVE_INFINITY;

    candidates.forEach((labels, index) => {
      for (const label of labels) {
        if (!` ${label} `.includes(wholePhrase)) continue;
        const extraWordCount = label.split(" ").length - targetWordCount;
        if (extraWordCount < smallestExtraWordCount) {
          bestIndex = index;
          smallestExtraWordCount = extraWordCount;
        }
      }
    });
    return bestIndex;
  }

  globalThis.RandomFormDistribution = Object.freeze({
    allocateCounts,
    buildSchedule,
    findBestLabelIndex
  });
})();
