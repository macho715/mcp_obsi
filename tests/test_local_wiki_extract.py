import json

from openpyxl import Workbook

from scripts.local_wiki_extract import extract_document


def test_extract_text_file(tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("alpha\nbeta", encoding="utf-8")
    assert "alpha" in extract_document(path)["text"]


def test_extract_json_file(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps({"alpha": 1}), encoding="utf-8")
    assert '"alpha": 1' in extract_document(path)["text"]


def test_extract_xlsx_file(tmp_path):
    path = tmp_path / "book.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "SheetA"
    ws.append(["Name", "Qty"])
    ws.append(["Cable", 3])
    wb.save(path)
    result = extract_document(path)
    assert result["status"] == "ok"
    assert "SheetA" in result["text"]


def test_extract_legacy_doc_is_limited(tmp_path):
    path = tmp_path / "legacy.doc"
    path.write_bytes(b"fake")
    assert extract_document(path)["status"] == "limited"
