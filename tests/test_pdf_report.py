from nei.engineering.pdf_report import build_pdf


def test_pdf_report_has_valid_header_and_audit_fields():
    pdf = build_pdf({
        "task_id": "task-1",
        "status": "NOT_FOR_APPROVAL",
        "report_sha256": "abc123",
        "calculations": {"volume": 12.5},
        "limitations": ["preview only"],
        "classification_baseline": {"status": "UNVERIFIED", "compliance_claimed": False},
    })
    assert pdf.startswith(b"%PDF-1.4")
    assert b"xref" in pdf
    assert b"NOT_FOR_APPROVAL" in pdf
    assert b"UNVERIFIED" in pdf
