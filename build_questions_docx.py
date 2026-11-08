import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "form-questions.json"
OUTPUT = ROOT / "ENIGLISH_Survey_Questions_and_Percentages.docx"

FONT = "Aptos"
BLACK = "000000"
MUTED = "666666"
LIGHT_BLUE = "DCE6F1"
PALE_BLUE = "F3F7FB"
BORDER = "D9D9D9"


def set_run_font(run, size=None, bold=None, italic=None, color=BLACK):
    run.font.name = FONT
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), FONT)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), FONT)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def configure_styles(document):
    normal = document.styles["Normal"]
    normal.font.name = FONT
    normal._element.rPr.rFonts.set(qn("w:ascii"), FONT)
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(BLACK)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08

    title = document.styles["Title"]
    title.font.name = FONT
    title._element.rPr.rFonts.set(qn("w:ascii"), FONT)
    title._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
    title.font.size = Pt(21)
    title.font.bold = True
    title.font.color.rgb = RGBColor.from_string(BLACK)


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = tc_pr.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        tc_pr.append(shading)
    shading.set(qn("w:fill"), fill)


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = borders.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:color"), BORDER)


def prevent_row_split(row):
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("Page ")
    set_run_font(run, size=9, color=MUTED)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, end])


def add_heading(document, text, level=1):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(7)
    paragraph.paragraph_format.keep_with_next = True
    p_pr = paragraph._p.get_or_add_pPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), LIGHT_BLUE if level == 1 else PALE_BLUE)
    p_pr.append(shading)
    indent = OxmlElement("w:ind")
    indent.set(qn("w:left"), "110")
    indent.set(qn("w:right"), "110")
    p_pr.append(indent)
    run = paragraph.add_run(text)
    set_run_font(run, size=13.5 if level == 1 else 11.5, bold=True)


def add_question_title(document, number, question, required):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(7)
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(f"{number}. {question}")
    set_run_font(run, size=10.8, bold=True)
    status = paragraph.add_run("  Required" if required else "  Optional")
    set_run_font(status, size=8.5, italic=True, color=MUTED)


def add_options(document, options):
    paragraphs = []
    for option in options:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.24)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.tab_stops.add_tab_stop(
            Inches(6.48), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.SPACES
        )
        marker = paragraph.add_run("○  ")
        marker.font.name = "Segoe UI Symbol"
        marker.font.size = Pt(10.5)
        text = paragraph.add_run(option)
        set_run_font(text, size=10.5)
        blank = paragraph.add_run("\t________ %")
        set_run_font(blank, size=10.5, bold=True)
        paragraphs.append(paragraph)
    for paragraph in paragraphs[:-1]:
        paragraph.paragraph_format.keep_with_next = True


def add_percentage_scale(document, options):
    table = document.add_table(rows=1, cols=len(options))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    prevent_row_split(table.rows[0])
    for index, option in enumerate(options):
        cell = table.rows[0].cells[index]
        cell.width = Inches(6.6 / len(options))
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_shading(cell, PALE_BLUE)
        label = cell.paragraphs[0]
        label.alignment = WD_ALIGN_PARAGRAPH.CENTER
        label.paragraph_format.space_after = Pt(3)
        label_run = label.add_run(option)
        set_run_font(label_run, size=8.5, bold=True)
        percentage = cell.add_paragraph()
        percentage.alignment = WD_ALIGN_PARAGRAPH.CENTER
        percentage.paragraph_format.space_after = Pt(0)
        percentage_run = percentage.add_run("________ %")
        set_run_font(percentage_run, size=10, bold=True)


def add_text_exclusion(document):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.24)
    paragraph.paragraph_format.space_after = Pt(3)
    run = paragraph.add_run("Text response - excluded from automatic filling.")
    set_run_font(run, size=10, italic=True, color=MUTED)


def build_document(data):
    document = Document()
    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.72)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.82)
    section.right_margin = Inches(0.82)
    configure_styles(document)

    title = document.add_paragraph(style="Title")
    title.add_run("ENIGLISH Survey Questions and Answer Percentages")

    subtitle = document.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(8)
    subtitle_run = subtitle.add_run(data["formTitle"])
    set_run_font(subtitle_run, size=11.5, italic=True)

    intro = document.add_paragraph()
    intro.paragraph_format.space_after = Pt(5)
    intro_run = intro.add_run(
        f"This document contains {data['percentageQuestionCount']} percentage-based questions "
        "and one optional text question. Enter a percentage beside every answer choice; "
        "the percentages for each choice question must total 100%. The optional text "
        "question is listed for reference and will not be filled automatically."
    )
    set_run_font(intro_run, size=10.5)

    source = document.add_paragraph()
    source.paragraph_format.space_after = Pt(11)
    source_label = source.add_run("Source: ")
    set_run_font(source_label, size=9, bold=True, color=MUTED)
    source_value = source.add_run(data["source"])
    set_run_font(source_value, size=9, color=MUTED)

    number = 1
    for section_data in data["sections"]:
        add_heading(document, section_data["title"], level=1)
        if section_data.get("description"):
            description = document.add_paragraph(section_data["description"])
            description.paragraph_format.space_after = Pt(7)

        groups = section_data.get("subsections") or [section_data]
        for group in groups:
            if group is not section_data:
                add_heading(document, group["title"], level=2)
            shared_options = group.get("sharedOptions")
            for question in group.get("questions", []):
                add_question_title(
                    document, number, question["question"], question["required"]
                )
                if question.get("type") == "paragraph_text":
                    add_text_exclusion(document)
                elif shared_options:
                    add_percentage_scale(document, shared_options)
                else:
                    add_options(document, question["options"])
                number += 1

    add_page_number(section.footer.paragraphs[0])
    document.core_properties.title = "ENIGLISH Survey Questions and Answer Percentages"
    document.core_properties.subject = "Answer percentage configuration"
    document.core_properties.author = ""
    document.save(OUTPUT)


if __name__ == "__main__":
    with SOURCE.open("r", encoding="utf-8") as stream:
        form_data = json.load(stream)
    build_document(form_data)
    print(OUTPUT.name)
