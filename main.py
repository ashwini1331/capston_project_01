from __future__ import annotations

import argparse
from pathlib import Path

from complaint_processor import process_batch


def ensure_sample_data(data_dir: str | Path) -> Path:
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    text_file = data_path / "complain1.txt"
    if not text_file.exists():
        text_file.write_text(
            "Customer Name: Priya Sharma\n"
            "Email: priya.sharma@example.com\n"
            "Phone Number: 555-012-3456\n"
            "Complaint Category: Billing\n"
            "Issue Description: I was charged twice for my monthly subscription after cancellation.\n"
            "Resolution Provided: Refunded the duplicate charge and canceled the account.\n"
            "Complaint: Yes\n"
            "Escalation Required: No\n"
            "Supporting Document Available: Yes\n"
            "Overall Case Status: Resolved\n",
            encoding="utf-8",
        )

    docx_file = data_path / "complain2.docx"
    if not docx_file.exists():
        try:
            from docx import Document

            doc = Document()
            doc.add_paragraph("Customer Name: Arjun Mehta")
            doc.add_paragraph("Email: arjun.mehta@example.com")
            doc.add_paragraph("Phone Number: 333-444-5566")
            doc.add_paragraph("Complaint Category: Product Quality")
            doc.add_paragraph("Issue Description: The new smartwatch stopped charging after three days of use and the battery drained quickly.")
            doc.add_paragraph("Resolution Provided: Replaced the unit and provided a warranty update.")
            doc.add_paragraph("Complaint: Yes")
            doc.add_paragraph("Escalation Required: No")
            doc.add_paragraph("Supporting Document Available: Yes")
            doc.add_paragraph("Overall Case Status: In Progress")
            doc.save(docx_file)
        except Exception:
            docx_file.write_text(
                "Customer Name: Arjun Mehta\n"
                "Email: arjun.mehta@example.com\n"
                "Phone Number: 333-444-5566\n"
                "Complaint Category: Product Quality\n"
                "Issue Description: The new smartwatch stopped charging after three days of use and the battery drained quickly.\n"
                "Resolution Provided: Replaced the unit and provided a warranty update.\n"
                "Complaint: Yes\n"
                "Escalation Required: No\n"
                "Supporting Document Available: Yes\n"
                "Overall Case Status: In Progress\n",
                encoding="utf-8",
            )

    pdf_file = data_path / "complain3.pdf"
    if not pdf_file.exists():
        try:
            pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 500 250] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n4 0 obj\n<< /Length 120 >>\nstream\nBT\n/F1 14 Tf\n50 130 Td\n(Customer Name: Leela Kumar) Tj\n0 -20 Td\n(Email: leela.kumar@example.com) Tj\n0 -20 Td\n(Complaint Category: Delivery Delay) Tj\n0 -20 Td\n(Issue Description: Shipment arrived six days late and missing accessories.) Tj\nET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000062 00000 n \n0000000120 00000 n \n0000000410 00000 n \n0000001125 00000 n \ntrailer\n<< /Root 1 0 R /Size 6 >>\nstartxref\n1228\n%%EOF\n"
            pdf_file.write_bytes(pdf_content)
        except Exception:
            pdf_file.write_text(
                "Customer Name: Leela Kumar\n"
                "Email: leela.kumar@example.com\n"
                "Complaint Category: Delivery Delay\n"
                "Issue Description: Shipment arrived six days late and missing accessories.\n"
                "Resolution Provided: Issued a partial credit and arranged delivery of missing parts.\n"
                "Complaint: Yes\n"
                "Escalation Required: Yes\n"
                "Supporting Document Available: Yes\n"
                "Overall Case Status: Escalated\n",
                encoding="utf-8",
            )

    return text_file


def main(data_dir: str = "./data", output_dir: str = "./output") -> int:
    ensure_sample_data(data_dir)
    result = process_batch(data_folder=data_dir, output_folder=output_dir)
    print(f"Processed {result['processed_files']} files.")
    print(f"Output saved to: {output_dir}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI complaint and case processing system")
    parser.add_argument("--data-dir", default="./data", help="Folder containing complaint documents")
    parser.add_argument("--output-dir", default="./output", help="Folder for generated outputs")
    args = parser.parse_args()
    raise SystemExit(main(data_dir=args.data_dir, output_dir=args.output_dir))