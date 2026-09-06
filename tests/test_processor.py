from __future__ import annotations

from pathlib import Path

from complaint_processor import ComplaintRecord, extract_complaint_fields, generate_case_summary, generate_customer_email, process_batch, process_document_workflow


def test_extract_complaint_fields_parses_expected_keys() -> None:
    text = """
    Customer Name: Priya Sharma
    Email: priya.sharma@example.com
    Phone Number: 555-012-3456
    Complaint Category: Billing
    Issue Description: I was charged twice for my monthly subscription after cancellation.
    Resolution Provided: Refunded the duplicate charge and canceled the account.
    Complaint: Yes
    Escalation Required: No
    Supporting Document Available: Yes
    Overall Case Status: Resolved
    """

    record = extract_complaint_fields(text)

    assert record["customer_name"] == "Priya Sharma"
    assert record["email"] == "priya.sharma@example.com"
    assert record["phone_number"] == "555-012-3456"
    assert record["complaint_category"] == "Billing"
    assert record["issue_description"] == "I was charged twice for my monthly subscription after cancellation."
    assert record["resolution_provided"] == "Refunded the duplicate charge and canceled the account."
    assert record["complaint"] is True
    assert record["escalation_required"] is False
    assert record["supporting_document_available"] is True
    assert record["overall_case_status"] == "Resolved"


def test_complaint_record_validation_and_generated_outputs() -> None:
    record = ComplaintRecord(
        customer_name="Arjun Mehta",
        email="arjun.mehta@example.com",
        phone_number="333-444-5566",
        complaint_category="Product Quality",
        issue_description="Smartwatch stopped charging after three days.",
        resolution_provided="Replaced the unit and provided warranty update.",
        complaint=True,
        escalation_required=False,
        supporting_document_available=True,
        overall_case_status="In Progress",
    )

    email = generate_customer_email(record.model_dump())
    summary = generate_case_summary(record.model_dump())

    assert "Dear Arjun Mehta" in email
    assert "Smartwatch stopped charging after three days." in email
    assert "Case Overview" in summary
    assert "In Progress" in summary


def test_process_batch_creates_expected_outputs(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    output_dir = tmp_path / "output"
    data_dir.mkdir()

    complaint_path = data_dir / "complaint_001.txt"
    complaint_path.write_text(
        "Customer Name: Priya Sharma\n"
        "Email: priya.sharma@example.com\n"
        "Phone Number: 555-012-3456\n"
        "Complaint Category: Billing\n"
        "Issue Description: Duplicate charge after cancellation.\n"
        "Resolution Provided: Sent refund and closed account.\n"
        "Complaint: Yes\n"
        "Escalation Required: No\n"
        "Supporting Document Available: Yes\n"
        "Overall Case Status: Resolved\n",
        encoding="utf-8",
    )

    result = process_batch(data_folder=str(data_dir), output_folder=str(output_dir))

    assert result["processed_files"] == 1
    assert (output_dir / "structured_data" / "complaint_001.json").exists()
    assert (output_dir / "customer_emails" / "complaint_001.txt").exists()
    assert (output_dir / "case_summaries" / "complaint_001.txt").exists()
    assert (output_dir / "final_report.csv").exists()


def test_process_document_workflow_returns_structured_record(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    file_path = data_dir / "complaint_002.txt"
    file_path.write_text(
        "Customer Name: Leela Kumar\n"
        "Email: leela.kumar@example.com\n"
        "Phone Number: 777-888-9999\n"
        "Complaint Category: Delivery Delay\n"
        "Issue Description: Shipment was delayed by six days.\n"
        "Resolution Provided: Issued credit to the customer.\n"
        "Complaint: Yes\n"
        "Escalation Required: Yes\n"
        "Supporting Document Available: Yes\n"
        "Overall Case Status: Escalated\n",
        encoding="utf-8",
    )

    record = process_document_workflow(file_path, tmp_path / "output")

    assert record.customer_name == "Leela Kumar"
    assert record.email == "leela.kumar@example.com"
    assert record.complaint_category == "Delivery Delay"
    assert record.escalation_required is True
    assert record.customer_email.startswith("Dear Leela Kumar")
    assert "Escalated" in record.case_summary
