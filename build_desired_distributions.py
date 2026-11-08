import json
import re
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parent
DOCX_PATH = ROOT / "ENIGLISH_Survey_Questions_and_Percentages.docx"
QUESTIONS_PATH = ROOT / "form-questions.json"
OUTPUT_PATH = ROOT / "desired-distributions.js"

WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
QUESTION_PATTERN = re.compile(
    r"^\d+\.\s+(.+?)(?:\s+(?:Required|Optional))?$", re.IGNORECASE
)
PERCENTAGE_PATTERN = re.compile(r"(-?\d+(?:[.,]\d+)?)[_\s]*%")


def document_paragraph_texts(path):
    with ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))

    for paragraph in root.iter(f"{WORD_NS}p"):
        parts = []
        for node in paragraph.iter():
            if node.tag == f"{WORD_NS}t":
                parts.append(node.text or "")
            elif node.tag == f"{WORD_NS}tab":
                parts.append("\t")
        text = "".join(parts).strip()
        if text:
            yield re.sub(r"[ \r\n]+", " ", text)


def extract_percentages(path):
    values = {}
    current_question = None

    for text in document_paragraph_texts(path):
        question_match = QUESTION_PATTERN.match(text)
        if question_match:
            current_question = question_match.group(1).strip()
            values[current_question] = []
            continue

        if current_question is None:
            continue
        percentage_match = PERCENTAGE_PATTERN.search(text.rsplit("\t", 1)[-1])
        if not percentage_match:
            continue

        percentage = float(percentage_match.group(1).replace(",", "."))
        if percentage < 0 or percentage > 100:
            raise ValueError(
                f"Percentage must be between 0 and 100 for: {current_question}"
            )
        values[current_question].append(percentage)

    return values


def percentage_questions(data):
    for section in data["sections"]:
        groups = section.get("subsections") or [section]
        for group in groups:
            shared_options = group.get("sharedOptions")
            for question in group.get("questions", []):
                options = question.get("options") or shared_options
                if not options or question.get("autoFill") is False:
                    continue
                yield {**question, "options": options}


def normalized_number(value):
    return int(value) if value.is_integer() else value


def build_distributions(questions, percentages):
    result = []
    for number, question in enumerate(questions, start=1):
        question_percentages = percentages.get(question["question"])
        if question_percentages is None:
            raise ValueError(
                f"No percentages found in Word for question {number}: "
                f"{question['question']}"
            )
        if len(question_percentages) != len(question["options"]):
            raise ValueError(
                f"Question {number} has {len(question_percentages)} percentages; "
                f"expected {len(question['options'])}: {question['question']}"
            )

        total = sum(question_percentages)
        if abs(total - 100) > 0.01:
            raise ValueError(
                f"Question {number} totals {total:g}%; expected 100%: "
                f"{question['question']}"
            )

        result.append(
            {
                "number": number,
                "id": question["id"],
                "question": question["question"],
                "options": [
                    {
                        "label": label,
                        "percent": normalized_number(percentage),
                    }
                    for label, percentage in zip(
                        question["options"], question_percentages, strict=True
                    )
                ],
            }
        )
    return result


def main():
    with QUESTIONS_PATH.open("r", encoding="utf-8") as stream:
        questions_data = json.load(stream)

    questions = list(percentage_questions(questions_data))
    percentages = extract_percentages(DOCX_PATH)
    distributions = build_distributions(questions, percentages)
    payload = json.dumps(distributions, ensure_ascii=False, indent=2)
    OUTPUT_PATH.write_text(
        f"// Generated from {DOCX_PATH.name}.\n"
        f"globalThis.RANDOM_FORM_DESIRED_DISTRIBUTIONS = Object.freeze({payload});\n",
        encoding="utf-8",
    )
    print(
        f"Generated {OUTPUT_PATH.name}: {len(distributions)} questions and "
        f"{sum(len(item['options']) for item in distributions)} percentages."
    )
    for distribution in distributions:
        percentages_text = ", ".join(
            f"{option['label']}={option['percent']:g}%"
            for option in distribution["options"]
        )
        print(f"{distribution['number']:02d}. {percentages_text}")


if __name__ == "__main__":
    main()
