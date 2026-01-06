# Reference Validator

A powerful tool to validate and enrich BibTeX entries using metadata from **Crossref**, **arXiv**, and **Google Scholar**. It helps ensure your bibliography is accurate, complete, and up-to-date.

## Features

- **🔍 DOI Validation**: Automatically verifies DOIs against the Crossref API.
- **📄 arXiv Integration**: Detects arXiv preprints and fetches updated metadata or official publication DOIs.
- **✨ Smart Enrichment**: Fills in missing fields using metadata from multiple reliable academic sources:
  - <span style="display: inline-block; background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">Crossref</span> - For official DOI metadata.
  - <span style="display: inline-block; background-color: #fee2e2; color: #991b1b; border: 1px solid #fecaca; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">arXiv</span> - For preprint information and updates.
  - <span style="display: inline-block; background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">Google Scholar</span> - For citation and missing metadata (via `scholarly`).
  - <span style="display: inline-block; background-color: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">DBLP</span> - For computer science bibliography.
  - <span style="display: inline-block; background-color: #e0e7ff; color: #3730a3; border: 1px solid #c7d2fe; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">Semantic Scholar</span> - For AI-powered research paper data.
  - <span style="display: inline-block; background-color: #e0f2fe; color: #075985; border: 1px solid #bae6fd; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">PubMed</span> - For biomedical literature.
  - <span style="display: inline-block; background-color: #f3f4f6; color: #1f2937; border: 1px solid #e5e7eb; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">Zenodo</span> - For general repositories and datasets.
  - <span style="display: inline-block; background-color: #f3f4f6; color: #1f2937; border: 1px solid #e5e7eb; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">DataCite</span> - For data DOI registry.
  - <span style="display: inline-block; background-color: #f3f4f6; color: #1f2937; border: 1px solid #e5e7eb; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">OpenAlex</span> - For comprehensive academic metadata.
- **⚖️ Dual Validation**: Compares your local BibTeX data with partial API data to highlight conflicts.
- **🖥️ Interactive GUI**: A modern web-based interface to review, accept, or reject changes visually with color-coded badges and intuitive controls.
- **📊 Report Generation**: Produces detailed validation reports.

## Usage Scenarios

This project is managed with [uv](https://github.com/astral-sh/uv). Ensure you have **uv** installed on your system.

### Scenario 1: Integration into a LaTeX Writing Environment

If you are writing a paper and simply want to use this tool to validate your `references.bib` file without modifying the tool's code:

#### Option A: Install as a Standalone Tool (Recommended)

This installs the tool in an isolated environment, making `bibtex-validator` available globally or for your specific project without polluting dependencies.

```bash
# Install directly from the repository
uv tool install git+https://github.com/bet-lab/reference-validator.git
```

**Run validation:**

```bash
bibtex-validator references.bib --gui
```

#### Option B: Add to Your Project Dependencies

If you are already managing your paper's environment (e.g., for processing scripts) using `uv` or a `pyproject.toml`:

```bash
# Add to your existing project
uv add git+https://github.com/bet-lab/reference-validator.git
```

**Run validation:**

```bash
uv run bibtex-validator references.bib
```

---

### Scenario 2: Development & Contribution

If you want to modify the source code, fix bugs, or add new features:

1. **Clone the repository**:

   ```bash
   git clone https://github.com/bet-lab/reference-validator.git
   cd reference-validator
   ```

2. **Sync dependencies**:
   Run `uv sync` to create a virtual environment and install all dependencies (including dev dependencies).

   ```bash
   uv sync
   ```

3. **Run from source**:
   You can run the script using `uv run`.
   ```bash
   uv run bibtex-validator references_test.bib --gui
   ```

## Detailed Usage

### Command Line Interface (CLI)

**Basic Validation (Dry Run)**
Checks the file and prints a report without making changes.

```bash
# If installed via Scenario 1 (Option A)
bibtex-validator references.bib

# If installed via Scenario 1 (Option B) or Scenario 2
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

### Interactive GUI 🖥️

Launch the modern web-based review interface to manually inspect and approve changes.

```bash
uv run bibtex-validator references.bib --gui
```

Once running, the web interface will automatically launch in your default browser (default: `http://127.0.0.1:8010`).

#### Key Features

<div style="background-color: #f8f9fa; border-left: 4px solid #3b82f6; padding: 1rem; margin: 1rem 0; border-radius: 4px;">

**📊 Validation Summary Dashboard**

- Attention pie chart showing percentage of entries needing review
- Real-time statistics: <span style="display: inline-block; background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">Reviews</span> <span style="display: inline-block; background-color: #ffedd5; color: #9a3412; border: 1px solid #fed7aa; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">Conflicts</span> <span style="display: inline-block; background-color: #fef9c3; color: #854d0e; border: 1px solid #fde047; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">Differences</span> <span style="display: inline-block; background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">Identical</span>
- Global Action: <span style="display: inline-block; background-color: #0f172a; color: #f8fafc; border: 1px solid #0f172a; border-radius: 6px; padding: 4px 12px; font-size: 0.85em; font-weight: 500; margin: 2px; box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);">✅ Accept All Entries</span>

</div>

<div style="background-color: #f8f9fa; border-left: 4px solid #10b981; padding: 1rem; margin: 1rem 0; border-radius: 4px;">

**🔍 Field-by-Field Comparison**

- Side-by-side comparison of BibTeX vs API values
- Color-coded status badges for each field:
  - <span style="display: inline-block; background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">Review</span> - New data available
  - <span style="display: inline-block; background-color: #ffedd5; color: #9a3412; border: 1px solid #fed7aa; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">Conflict</span> - Significant mismatch
  - <span style="display: inline-block; background-color: #fef9c3; color: #854d0e; border: 1px solid #fde047; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">Different</span> - Minor formatting difference
  - <span style="display: inline-block; background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; border-radius: 12px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; margin: 2px;">Identical</span> - Verified match
- Source selection dropdown for fields with multiple data sources

</div>

<div style="background-color: #f8f9fa; border-left: 4px solid #f59e0b; padding: 1rem; margin: 1rem 0; border-radius: 4px;">

**⌨️ Keyboard Navigation**

- Arrow keys (`←` `→`) to navigate between entries
- `Home`/`End` to jump to first/last entry
- `PageUp`/`PageDown` to jump by 10 entries
- `Esc` to clear selection

</div>

<div style="background-color: #f8f9fa; border-left: 4px solid #8b5cf6; padding: 1rem; margin: 1rem 0; border-radius: 4px;">

**🎯 Flexible Actions**

- Accept/Reject individual fields
- Bulk actions: <span style="display: inline-block; background-color: #ffffff; color: #7f1d1d; border: 1px solid #ef4444; border-radius: 6px; padding: 2px 8px; font-size: 0.8em; font-weight: 500;">Reject All</span> / <span style="display: inline-block; background-color: #0f172a; color: #f8fafc; border: 1px solid #0f172a; border-radius: 6px; padding: 2px 8px; font-size: 0.8em; font-weight: 500;">Accept All</span> per entry
- Global batch approval for all entries
- Real-time save with visual feedback

</div>

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
  --gui                 Launch web-based GUI interface 🖥️
  --workers WORKERS     Number of threads for parallel validation (default: 10)
  --port PORT           Port for GUI web server (default: 8010)
```

#### Keyboard Shortcuts (GUI Mode)

| Key        | Action          | Description                 |
| ---------- | --------------- | --------------------------- |
| `←` `↑`    | Previous Entry  | Navigate to previous entry  |
| `→` `↓`    | Next Entry      | Navigate to next entry      |
| `Home`     | First Entry     | Jump to first entry         |
| `End`      | Last Entry      | Jump to last entry          |
| `PageUp`   | Jump Back 10    | Move backward by 10 entries |
| `PageDown` | Jump Forward 10 | Move forward by 10 entries  |
| `Esc`      | Clear Selection | Deselect current entry      |

## Dependencies

- **📚 Core Libraries**

  - `bibtexparser` (>=1.4.0): For reading and writing BibTeX files.
  - `requests` (>=2.31.0): For making API calls to academic databases.

- **🔍 Data Sources**

  - `scholarly` (>=1.7.0): For accessing Google Scholar data (optional).

- **🖥️ GUI Components**
  - `fastapi` (>=0.104.0): Modern web framework for the GUI.
  - `uvicorn[standard]` (>=0.24.0): ASGI server for running the web interface.

These are automatically installed when using `uv run` or `uv sync`.

## Data Sources

The validator integrates with multiple academic databases and metadata providers:

<div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 1rem 0;">

<span style="display: inline-block; background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; border-radius: 12px; padding: 4px 12px; font-size: 0.9em; font-weight: 600;">Crossref</span>
<span style="display: inline-block; background-color: #fee2e2; color: #991b1b; border: 1px solid #fecaca; border-radius: 12px; padding: 4px 12px; font-size: 0.9em; font-weight: 600;">arXiv</span>
<span style="display: inline-block; background-color: #e0e7ff; color: #3730a3; border: 1px solid #c7d2fe; border-radius: 12px; padding: 4px 12px; font-size: 0.9em; font-weight: 600;">Semantic Scholar</span>
<span style="display: inline-block; background-color: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; border-radius: 12px; padding: 4px 12px; font-size: 0.9em; font-weight: 600;">DBLP</span>
<span style="display: inline-block; background-color: #e0f2fe; color: #075985; border: 1px solid #bae6fd; border-radius: 12px; padding: 4px 12px; font-size: 0.9em; font-weight: 600;">PubMed</span>
<span style="display: inline-block; background-color: #f3f4f6; color: #1f2937; border: 1px solid #e5e7eb; border-radius: 12px; padding: 4px 12px; font-size: 0.9em; font-weight: 600;">Zenodo</span>
<span style="display: inline-block; background-color: #f3f4f6; color: #1f2937; border: 1px solid #e5e7eb; border-radius: 12px; padding: 4px 12px; font-size: 0.9em; font-weight: 600;">DataCite</span>
<span style="display: inline-block; background-color: #f3f4f6; color: #1f2937; border: 1px solid #e5e7eb; border-radius: 12px; padding: 4px 12px; font-size: 0.9em; font-weight: 600;">OpenAlex</span>

</div>
