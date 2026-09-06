# AI Customer Complaint & Case Processing System

This project automatically processes customer complaint documents in `.txt`, `.pdf`, and `.docx` formats, extracts key complaint details, and generates:

- structured JSON records
- customer response emails
- internal case summaries
- a consolidated CSV report

## Features

- Reads complaint files from the `data/` folder
- Supports text, PDF, and Word document input
- Extracts structured details such as customer name, email, phone number, category, issue, resolution, status, and escalation flag
- Uses Gemini when an API key is available
- Falls back to local rule-based extraction when the API key is unavailable
- Saves generated outputs in the `output/` folder

## Project Structure

- `main.py` – entry point for running the full workflow
- `complaint_processor.py` – complaint parsing, extraction, and output generation logic
- `config.json` – optional Gemini API configuration
- `data/` – input complaint files
- `output/` – generated results
- `tests/` – project tests
- `requirements.txt` – Python dependencies

## Setup

1. Open a terminal in the project folder.
2. Create and activate a virtual environment (optional but recommended).
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Add your Gemini API key to environment variables or `config.json` if you want AI-based extraction:

   ```bash
   set GEMINI_API_KEY=your_key_here
   ```

## Run the Project

```bash
python main.py
```

Optional custom input/output folders:

```bash
python main.py --data-dir ./data --output-dir ./output
```

## Output Files

After processing, the project creates:

- `output/structured_data/` – structured JSON result for each complaint
- `output/customer_emails/` – customer-facing emails
- `output/case_summaries/` – internal summaries
- `output/final_report.csv` – combined CSV report

## Sample Data

The project includes sample complaint input files in the `data/` folder:

- `complain1.txt`
- `complain2.docx`
- `complain3.pdf`

## Notes

- If no Gemini API key is configured, the system still works using local extraction logic.
- This project is designed for complaint intake workflows and case processing automation.

## Repository Status

The project is intended to be committed and pushed to a GitHub repository after Git is available in the environment.
