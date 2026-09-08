from __future__ import annotations

import csv
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")


class ComplaintRecord(BaseModel):
    customer_name: str = Field(..., min_length=1)
    email: str = Field(...)
    phone_number: str = Field(default="")
    complaint_category: str = Field(..., min_length=1)
    issue_description: str = Field(..., min_length=1)
    resolution_provided: str = Field(default="")
    complaint: bool = Field(default=True)
    escalation_required: bool = Field(default=False)
    supporting_document_available: bool = Field(default=True)
    overall_case_status: str = Field(default="Open")
    source_file: str | None = None
    customer_email: str | None = None
    case_summary: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if value and "@" not in value:
            raise ValueError("Email must include an @ symbol.")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        cleaned = re.sub(r"\s+", "", value or "")
        return cleaned or ""

    @field_validator("customer_name", "complaint_category", "issue_description")
    @classmethod
    def strip_values(cls, value: str) -> str:
        return value.strip()


def build_complaint_record(raw: Dict[str, Any], source_file: str | None = None) -> ComplaintRecord:
    payload = {
        "customer_name": raw.get("customer_name") or "Customer",
        "email": raw.get("email") or "unknown@example.com",
        "phone_number": raw.get("phone_number") or "",
        "complaint_category": raw.get("complaint_category") or "General Complaint",
        "issue_description": raw.get("issue_description") or raw.get("complaint") or "Issue not specified.",
        "resolution_provided": raw.get("resolution_provided") or "Case is under review.",
        "complaint": bool(raw.get("complaint", True)),
        "escalation_required": bool(raw.get("escalation_required", False)),
        "supporting_document_available": bool(raw.get("supporting_document_available", True)),
        "overall_case_status": raw.get("overall_case_status") or "Open",
        "source_file": source_file,
    }
    return ComplaintRecord(**payload)


def normalize_yes_no(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"yes", "y", "true", "1", "required", "available"}


def find_field(text: str, labels: List[str]) -> str:
    known_labels = [
        "Customer Name",
        "Customer",
        "Client Name",
        "Email",
        "Email Address",
        "Customer Email",
        "Phone Number",
        "Phone",
        "Contact Number",
        "Mobile",
        "Complaint Category",
        "Category",
        "Issue Type",
        "Product/Service",
        "Issue Description",
        "Problem Description",
        "Complaint",
        "Issue Details",
        "Details",
        "Resolution Provided",
        "Resolution",
        "Action Taken",
        "Status Update",
        "Complaint Status",
        "Escalation Required",
        "Escalation",
        "Supporting Document Available",
        "Supporting Document",
        "Evidence",
        "Overall Case Status",
        "Case Status",
        "Current Status",
    ]
    next_labels = "|".join(re.escape(label) for label in known_labels)

    for label in labels:
        pattern = rf"{re.escape(label)}\s*[:\-]\s*(.*?)(?=\n\s*(?:{next_labels})\s*[:\-]|$)"
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            if value:
                return value

    for label in labels:
        pattern = rf"{re.escape(label)}\s*[:\-]\s*(.+)"
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return ""


def clean_value(value: str) -> str:
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value).strip()
    value = value.strip(" -;")
    return value


def extract_complaint_fields(document_text: str) -> Dict[str, Any]:
    text = document_text or ""

    raw_customer_name = find_field(text, ["Customer Name", "Customer", "Client Name"])
    raw_email = find_field(text, ["Email", "Email Address", "Customer Email"])
    raw_phone = find_field(text, ["Phone Number", "Phone", "Contact Number", "Mobile"])
    raw_category = find_field(text, ["Complaint Category", "Category", "Issue Type", "Product/Service"])
    raw_issue = find_field(text, ["Issue Description", "Problem Description", "Complaint", "Issue Details", "Details"])
    raw_resolution = find_field(text, ["Resolution Provided", "Resolution", "Action Taken", "Status Update"])
    raw_complaint = find_field(text, ["Complaint", "Complaint Status"])
    raw_escalation = find_field(text, ["Escalation Required", "Escalation"])
    raw_support_doc = find_field(text, ["Supporting Document Available", "Supporting Document", "Evidence"])
    raw_status = find_field(text, ["Overall Case Status", "Case Status", "Current Status"])

    result = {
        "customer_name": clean_value(raw_customer_name),
        "email": clean_value(raw_email),
        "phone_number": clean_value(raw_phone),
        "complaint_category": clean_value(raw_category),
        "issue_description": clean_value(raw_issue) or clean_value(raw_complaint),
        "resolution_provided": clean_value(raw_resolution),
        "complaint": normalize_yes_no(raw_complaint or "Yes"),
        "escalation_required": normalize_yes_no(raw_escalation),
        "supporting_document_available": normalize_yes_no(raw_support_doc or "Yes"),
        "overall_case_status": clean_value(raw_status) or "Open",
    }

    # Fallback for common email patterns
    if not result["email"]:
        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}", text)
        if email_match:
            result["email"] = email_match.group(0)

    # Fallback for phone patterns
    if not result["phone_number"]:
        phone_pattern = r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})"
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            result["phone_number"] = phone_match.group(0)

    return result


def generate_customer_email(record: Dict[str, Any]) -> str:
    customer_name = record.get("customer_name") or "Customer"
    category = record.get("complaint_category") or "your complaint"
    issue = record.get("issue_description") or "We have received your concern."
    resolution = record.get("resolution_provided") or "We are reviewing your case."
    status = record.get("overall_case_status") or "In Progress"

    email = (
        f"Dear {customer_name},\n\n"
        f"Thank you for contacting us regarding your {category.lower()} complaint.\n\n"
        f"We understand the issue raised: {issue}\n\n"
        f"Our team has reviewed the matter and the current resolution is as follows: {resolution}\n\n"
        f"The current case status is: {status}.\n\n"
        "Thank you for your patience and cooperation. We appreciate the opportunity to support you.\n\n"
        "Sincerely,\n"
        "Customer Support Team"
    )

    return email


def generate_case_summary(record: Dict[str, Any]) -> str:
    customer_name = record.get("customer_name") or "Unnamed customer"
    category = record.get("complaint_category") or "General complaint"
    issue = record.get("issue_description") or "No issue description was provided."
    action = record.get("resolution_provided") or "Case is under review."
    status = record.get("overall_case_status") or "Open"
    escalation = "Yes" if record.get("escalation_required") else "No"

    summary = (
        f"Case Overview: {customer_name} filed a {category.lower()} complaint.\n"
        f"Key Issue: {issue}\n"
        f"Action Taken: {action}\n"
        f"Current Status: {status}\n"
        f"Escalation Required: {escalation}\n"
        "Recommended Next Action: Continue case monitoring and confirm the customer has received the resolution update."
    )
    return summary


def process_document_workflow(file_path: Path, output_dir: Path) -> ComplaintRecord:
    record = analyze_document(file_path)
    record_model = build_complaint_record(record, source_file=file_path.name)
    record_model.customer_email = generate_customer_email(record)
    record_model.case_summary = generate_case_summary(record)

    structured_dir = output_dir / "structured_data"
    email_dir = output_dir / "customer_emails"
    summary_dir = output_dir / "case_summaries"

    structured_dir.mkdir(parents=True, exist_ok=True)
    email_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)

    save_json(structured_dir / f"{file_path.stem}.json", record_model.model_dump())
    save_text(email_dir / f"{file_path.stem}.txt", record_model.customer_email or "")
    save_text(summary_dir / f"{file_path.stem}.txt", record_model.case_summary or "")
    return record_model


def get_gemini_api_key() -> str | None:
    env_path = Path(__file__).resolve().parent / ".env"
    try:
        from dotenv import load_dotenv

        env_text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
        if any("=" in line for line in env_text.splitlines()):
            load_dotenv(env_path)
    except ImportError:
        pass

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key.strip()

    # Accept a single raw key for compatibility with the existing .env file.
    if env_path.exists():
        try:
            env_lines = [line.strip() for line in env_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if len(env_lines) == 1 and "=" not in env_lines[0] and not env_lines[0].startswith("#"):
                raw_key = env_lines[0].strip("\"'").strip()
                if ":" in raw_key:
                    raw_key = raw_key.split(":", 1)[1].strip().strip("\"'").strip()
                return raw_key
        except OSError:
            pass

    config_path = Path(__file__).resolve().parent / "config.json"
    if config_path.exists():
        try:
            with config_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
            gemini_config = config.get("gemini", {})
            key = (
                config.get("GEMINI_API_KEY")
                or config.get("GOOGLE_API_KEY")
                or gemini_config.get("api_key")
                or gemini_config.get("GEMINI_API_KEY")
            )
            if key:
                return str(key).strip()
        except Exception:
            pass

    return None


def extract_text_from_pdf(file_path: Path) -> str:
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz  # compatibility fallback
        except ImportError:
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise RuntimeError("PDF support requires PyMuPDF or pypdf") from exc

            reader = PdfReader(str(file_path))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            return "\n".join(pages)

        doc = fitz.open(str(file_path))
        text_blocks: List[str] = []
        for page in doc:
            text_blocks.append(page.get_text("text"))
        doc.close()
        return "\n".join(text_blocks)

    doc = pymupdf.open(str(file_path))
    text_blocks: List[str] = []
    for page in doc:
        text_blocks.append(page.get_text("text"))
    doc.close()
    return "\n".join(text_blocks)


def extract_text_from_docx(file_path: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("DOCX support requires python-docx") from exc

    doc = Document(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\\n".join(paragraphs)


def extract_text_from_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)

    if suffix == ".docx":
        return extract_text_from_docx(file_path)

    raise ValueError(f"Unsupported file type: {suffix}")


def call_gemini_for_extraction(document_text: str) -> Dict[str, Any] | None:
    api_key = get_gemini_api_key()
    if not api_key:
        logging.info("No Gemini API key found. Using local extraction fallback.")
        return None

    try:
        import importlib
        genai = importlib.import_module("google.generativeai")
    except Exception as exc:
        logging.warning("Gemini SDK not installed: %s", exc)
        return None

    try:
        genai.configure(api_key=api_key)
        model_name = "gemini-3.6-flash"
        config_path = Path(__file__).resolve().parent / "config.json"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
            model_name = config.get("gemini", {}).get("model") or model_name

        model = genai.GenerativeModel(model_name)
        prompt = """Extract structured complaint data in valid JSON format with keys:
        customer_name, email, phone_number, complaint_category, issue_description,
        resolution_provided, complaint, escalation_required, supporting_document_available,
        overall_case_status.
        Return ONLY valid JSON.
        Data:
        """ + document_text[:12000]

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text.startswith("```"):
            response_text = response_text.strip("`")
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()

        return json.loads(response_text)
    except Exception as exc:
        logging.warning("Gemini extraction failed: %s", exc)
        return None


def analyze_document(file_path: Path) -> Dict[str, Any]:
    text = extract_text_from_file(file_path)
    extracted = extract_complaint_fields(text)

    ai_data = call_gemini_for_extraction(text)
    if ai_data:
        for key, value in ai_data.items():
            if value not in (None, "", []):
                extracted[key] = value

    extracted["source_file"] = file_path.name
    extracted["customer_email"] = generate_customer_email(extracted)
    extracted["case_summary"] = generate_case_summary(extracted)
    return extracted


def validate_record(record: Dict[str, Any], source_file: str | None = None) -> ComplaintRecord:
    complaint_record = build_complaint_record(record, source_file=source_file)
    complaint_record.customer_email = generate_customer_email(record)
    complaint_record.case_summary = generate_case_summary(record)
    return complaint_record


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def process_batch(data_folder: str = "./data", output_folder: str = "./output") -> Dict[str, Any]:
    data_dir = Path(data_folder)
    output_dir = Path(output_folder)

    if not data_dir.exists():
        raise FileNotFoundError(f"Data folder not found: {data_dir}")

    supported = {".txt", ".pdf", ".docx"}
    files = [p for p in data_dir.iterdir() if p.is_file() and p.suffix.lower() in supported]

    structured_dir = output_dir / "structured_data"
    email_dir = output_dir / "customer_emails"
    summary_dir = output_dir / "case_summaries"

    results: List[Dict[str, Any]] = []

    for file_path in sorted(files):
        try:
            logging.info("Processing %s", file_path.name)
            record = analyze_document(file_path)
            validated = validate_record(record, source_file=file_path.name)
            results.append(validated.model_dump())

            save_json(structured_dir / f"{file_path.stem}.json", validated.model_dump())
            save_text(email_dir / f"{file_path.stem}.txt", validated.customer_email or "")
            save_text(summary_dir / f"{file_path.stem}.txt", validated.case_summary or "")
        except Exception as exc:
            logging.error("Failed to process %s: %s", file_path.name, exc)

    csv_path = output_dir / "final_report.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_file",
                "customer_name",
                "email",
                "phone_number",
                "complaint_category",
                "issue_description",
                "resolution_provided",
                "complaint",
                "escalation_required",
                "supporting_document_available",
                "overall_case_status",
            ],
        )
        writer.writeheader()
        for row in results:
            writer.writerow({
                "source_file": row.get("source_file", ""),
                "customer_name": row.get("customer_name", ""),
                "email": row.get("email", ""),
                "phone_number": row.get("phone_number", ""),
                "complaint_category": row.get("complaint_category", ""),
                "issue_description": row.get("issue_description", ""),
                "resolution_provided": row.get("resolution_provided", ""),
                "complaint": row.get("complaint", False),
                "escalation_required": row.get("escalation_required", False),
                "supporting_document_available": row.get("supporting_document_available", False),
                "overall_case_status": row.get("overall_case_status", "Open"),
            })

    return {
        "processed_files": len(results),
        "output_folder": str(output_dir),
        "report_path": str(csv_path),
    }