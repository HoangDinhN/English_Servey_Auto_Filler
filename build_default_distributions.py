import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "form-questions.json"
OUTPUT = ROOT / "desired-distributions.js"


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


def equal_percentages(option_count):
    base, remainder = divmod(100, option_count)
    return [base + (1 if index < remainder else 0) for index in range(option_count)]


def main():
    with SOURCE.open("r", encoding="utf-8") as stream:
        data = json.load(stream)

    distributions = []
    for number, question in enumerate(percentage_questions(data), start=1):
        percentages = equal_percentages(len(question["options"]))
        distributions.append(
            {
                "number": number,
                "id": question["id"],
                "question": question["question"],
                "options": [
                    {"label": label, "percent": percentage}
                    for label, percentage in zip(
                        question["options"], percentages, strict=True
                    )
                ],
            }
        )

    payload = json.dumps(distributions, ensure_ascii=False, indent=2)
    OUTPUT.write_text(
        "// Equal-percentage defaults. Import a completed Word file to override them.\n"
        f"globalThis.RANDOM_FORM_DESIRED_DISTRIBUTIONS = Object.freeze({payload});\n",
        encoding="utf-8",
    )
    print(f"Generated {OUTPUT.name}: {len(distributions)} percentage questions.")


if __name__ == "__main__":
    main()
