import assert from "node:assert/strict";

await import("../desired-distributions.js");
await import("../word-import.js");

const defaults = globalThis.RANDOM_FORM_DESIRED_DISTRIBUTIONS;
const { buildDistributionsFromParagraphTexts } = globalThis.RandomFormWordImport;

function paragraphTexts(overrides = new Map()) {
  return defaults.flatMap((distribution) => {
    const percentages =
      overrides.get(distribution.question) ||
      distribution.options.map((option) => option.percent);
    return [
      `${distribution.number}. ${distribution.question}  Required`,
      ...distribution.options.map(
        (option, index) => `○  ${option.label}\t${percentages[index]} %`
      )
    ];
  });
}

const targetQuestion =
  "Q01. Are you 18 years of age or older?";
const secondQuestionPercentages = defaults[1].options.map(
  (option) => option.percent
);
const imported = buildDistributionsFromParagraphTexts(
  paragraphTexts(new Map([[targetQuestion, [80, 20]]])),
  defaults
);
assert.deepEqual(
  imported[0].options.map((option) => option.percent),
  [80, 20]
);
assert.deepEqual(
  imported[1].options.map((option) => option.percent),
  secondQuestionPercentages
);

const underscoredParagraphs = paragraphTexts().map((text) =>
  text.replace(/\t(\d+(?:\.\d+)?) %$/, "\t____$1____ %")
);
assert.equal(
  buildDistributionsFromParagraphTexts(underscoredParagraphs, defaults).length,
  20
);

assert.throws(
  () =>
    buildDistributionsFromParagraphTexts(
      paragraphTexts(new Map([[targetQuestion, [70, 20]]])),
      defaults
    ),
  /cần bằng 100%/
);

assert.throws(
  () => buildDistributionsFromParagraphTexts(paragraphTexts().slice(1), defaults),
  /Không tìm thấy câu hỏi/
);

console.log("Word percentage import validation: OK");
