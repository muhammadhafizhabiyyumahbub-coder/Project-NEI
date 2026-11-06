"""Dependency-free PDF export for auditable preview reports."""
from __future__ import annotations
import json
from typing import Iterable


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _lines(report: dict) -> Iterable[str]:
    yield "NEI Hull Engineering Preview"
    yield f"Task ID: {report.get('task_id', '')}"
    yield f"Status: {report.get('status', 'NOT_FOR_APPROVAL')}"
    yield f"Report SHA-256: {report.get('report_sha256', '')}"
    yield ""
    yield "LIMITATIONS"
    for item in report.get("limitations", []):
        yield f"- {item}"
    yield ""
    yield "CALCULATIONS"
    for key, value in report.get("calculations", {}).items():
        yield f"{key}: {json.dumps(value, sort_keys=True)}"
    yield ""
    yield "CLASSIFICATION BASELINE"
    baseline = report.get("classification_baseline") or {}
    yield f"status: {baseline.get('status', 'UNVERIFIED')}"
    yield f"compliance_claimed: {baseline.get('compliance_claimed', False)}"


def build_pdf(report: dict) -> bytes:
    """Build one-page text PDF. Report remains explicitly non-approval."""
    text = ["BT", "/F1 9 Tf", "50 760 Td"]
    for index, line in enumerate(_lines(report)):
        if index:
            text.append("0 -13 Td")
        text.append(f"({_pdf_escape(line[:150])}) Tj")
    text.append("ET")
    stream = "\n".join(text).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(pdf)
