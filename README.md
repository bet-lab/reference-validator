# Reference Validator

A powerful tool to validate and enrich BibTeX entries using metadata from **Crossref**, **arXiv**, and **Google Scholar**. It helps ensure your bibliography is accurate, complete, and up-to-date.

## Features

- **DOI Validation**: Automatically verifies DOIs against the Crossref API.
- **arXiv Integration**: Detects arXiv preprints and fetches updated metadata or official publication DOIs.
- **Smart Enrichment**: Fills in missing fields (e.g., year, journal, author names) using data from multiple academic sources.
- **Dual Validation**: Compares your local BibTeX data with partial API data to highlight conflicts.
- **Interactive GUI**: A web-based interface to review, accept, or reject changes visually.
- **Report Generation**: Produces detailed validation reports.

## Installation

This project is managed with [uv](https://github.com/astral-sh/uv).

### Prerequisites

- [uv](https://github.com/astral-sh/uv) installed on your system.
- Python 3.8 or higher.

### Setup

1. **Clone the repository**:

   ```bash
   git clone <your-repo-url>
   cd reference-validator
   ```

2. **Sync dependencies**:
   Run `uv sync` to create a virtual environment and install all dependencies defined in `pyproject.toml`.
   ```bash
   uv sync
   ```

## Usage

You can run the validator using `uv run`.

### Command Line Interface (CLI)

**Basic Validation (Dry Run)**
Checks the file and prints a report without making changes.

```bash
uv run bibtex-validator references.bib
```

**Auto-Update BibTeX File**
Validates and applies enriched metadata directly to your file.

```bash
uv run bibtex-validator references.bib --update
```

**Save Update to New File**
Keeps the original file intact and saves the updated version to a new file.

```bash
uv run bibtex-validator references.bib --update --output references_enriched.bib
```

**Save Report to File**

```bash
uv run bibtex-validator references.bib --report validation_report.txt
```

### Interactive GUI

Launch the web-based review interface to manually inspect and approve changes.

```bash
uv run bibtex-validator references.bib --gui
```

Once running, open your browser at [http://127.0.0.1:8010](http://127.0.0.1:8010) (default port).

- **Green Badges**: Validated data from APIs.
- **Red/Yellow Highlights**: Conflicts or missing data.
- **Actions**: Accept or reject changes per field or per entry.

### Options

```text
usage: validate_bibtex.py [-h] [-o OUTPUT] [-r REPORT] [-u] [-d DELAY] [--no-progress] [--gui] [--workers WORKERS] [--port PORT] bib_file

Validate and enrich BibTeX entries using DOI, arXiv, and Google Scholar

positional arguments:
  bib_file              Input BibTeX file

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output BibTeX file (default: same as input if --update)
  -r REPORT, --report REPORT
                        Output report file (default: print to stdout)
  -u, --update          Update BibTeX file with enriched data
  -d DELAY, --delay DELAY
                        Delay between API requests in seconds (default: 1.0)
  --no-progress         Hide progress indicators
  --gui                 Launch web-based GUI interface
  --workers WORKERS     Number of threads for parallel validation (default: 10)
  --port PORT           Port for GUI web server (default: 8010)
```

## Dependencies

- `bibtexparser`: For reading and writing BibTeX files.
- `requests`: For making API calls.
- `scholarly`: For accessing Google Scholar data.
- `fastapi` & `uvicorn`: For the interactive GUI.

These are automatically installed when using `uv run` or `uv sync`.
