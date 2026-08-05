"""Minimal .xlsx writer (stdlib zipfile)，对齐 Java ExcelDownLoadUtil 下载形态。"""

from __future__ import annotations

import re
import zipfile
from io import BytesIO
from xml.sax.saxutils import escape


def _col_letter(idx: int) -> str:
    """0-based column index → A, B, ..., Z, AA, ..."""
    n = idx + 1
    letters: list[str] = []
    while n:
        n, rem = divmod(n - 1, 26)
        letters.append(chr(65 + rem))
    return "".join(reversed(letters))


def _cell_xml(row: int, col: int, value) -> str:
    ref = f"{_col_letter(col)}{row}"
    if value is None:
        text = ""
    else:
        # Decimal / int / float → 数字单元格
        try:
            from decimal import Decimal

            if isinstance(value, Decimal):
                return f'<c r="{ref}"><v>{value}</v></c>'
        except Exception:
            pass
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return f'<c r="{ref}"><v>{value}</v></c>'
        text = str(value)
    # Excel 不允许控制字符
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return f'<c r="{ref}" t="inlineStr"><is><t>{escape(text)}</t></is></c>'


def rows_to_xlsx(
    headers: list[str],
    rows: list[list],
    *,
    sheet_name: str = "Sheet1",
) -> bytes:
    """生成可被 Excel 打开的 .xlsx 字节流。"""
    sheet_safe = re.sub(r"[\\/*?:\[\]]", "_", (sheet_name or "Sheet1")[:31]) or "Sheet1"
    max_row = 1 + len(rows)
    max_col = max(len(headers), 1)
    dim = f"A1:{_col_letter(max_col - 1)}{max_row}"

    sheet_parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        f'<dimension ref="{dim}"/>',
        "<sheetData>",
    ]
    # header
    cells = "".join(_cell_xml(1, i, h) for i, h in enumerate(headers))
    sheet_parts.append(f'<row r="1">{cells}</row>')
    for r_idx, row in enumerate(rows, start=2):
        padded = list(row) + [""] * max(0, len(headers) - len(row))
        cells = "".join(_cell_xml(r_idx, i, padded[i]) for i in range(len(headers)))
        sheet_parts.append(f'<row r="{r_idx}">{cells}</row>')
    sheet_parts.append("</sheetData></worksheet>")
    sheet_xml = "".join(sheet_parts)

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""
    workbook = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="{escape(sheet_safe)}" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>
"""

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buf.getvalue()
