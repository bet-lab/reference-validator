# Interactive GUI Guide

The **BibTeX Validator** features a modern, web-based Graphical User Interface (GUI) that allows you to intuitively review, compare, and accept changes to your BibTeX entries. This guide provides a comprehensive overview of all GUI features, controls, and workflows.

## Launching the GUI

To start the GUI, run:

```bash
uv run bibtex-validator references.bib --gui
```

This launches a local web server (default port: 8010) and automatically opens your default browser. The GUI provides an interactive interface for reviewing validation results and selectively applying changes.

## GUI Structure Overview

The interface is organized into three main sections:

```{mermaid}
flowchart TD
    A[GUI Interface] --> B[Validation Summary]
    A --> C[Navigation Toolbar]
    A --> D[Comparison Table]
    
    B --> B1[Attention Pie Chart]
    B --> B2[Statistics Icons]
    B --> B3[Accept All Entries Button]
    
    C --> C1[Previous/Next Buttons]
    C --> C2[Entry Selector Dropdown]
    C --> C3[Entry Stats Display]
    
    D --> D1[Field Column]
    D --> D2[BibTeX Value Column]
    D --> D3[API Value Column]
    D --> D4[Source Badge Column]
    D --> D5[Status Badge Column]
    D --> D6[Actions Column]
    D --> D7[Footer Actions]
```

## 1. Validation Summary

The Validation Summary appears at the top of the dashboard and provides a global overview of your bibliography's validation status.

### Attention Pie Chart

A circular progress indicator (pie chart) shows the percentage of entries requiring attention. The chart uses a conic gradient where:
- **Red portion**: Percentage of entries with issues (updates, conflicts, or differences)
- **Gray portion**: Percentage of entries that are fully validated

The chart is accompanied by a counter displaying: `{entries_with_issues}/{total_entries} ({percentage}%)`

**Visual Representation:**

```{card} Attention Pie Chart Example
:class: sd-shadow-sm

<div style="display: flex; align-items: center; gap: 1rem; padding: 1rem;">
    <div class="pie-chart" style="--pie-percentage: 30%; flex-shrink: 0;"></div>
    <div>
        <strong>Need Attention</strong><br>
        <span style="font-size: 1.25rem; font-weight: 600;">15/50 (30%)</span>
    </div>
</div>
```

The pie chart uses CSS `conic-gradient` to visualize the percentage of entries requiring attention. The red portion represents entries with issues, while the gray portion represents fully validated entries.

### Statistics Icons

Four icon-based statistics provide quick insights:

#### Reviews (Blue) - `edit-3` Icon
```{bdg-primary}`Review
:class: badge-status-review
```

- **Color**: Blue background with dark blue text
- **Meaning**: Fields where the API found new data to update incomplete or missing fields
- **Action Required**: Review and decide whether to accept the suggested values
- **Example**: A missing `journal` field that can be filled from Crossref

#### Conflicts (Orange) - `alert-triangle` Icon
```{bdg-primary}`Conflict
:class: badge-status-conflict
```

- **Color**: Orange background with dark orange text
- **Meaning**: Critical mismatches between your local BibTeX data and API data
- **Action Required**: Manual review required - these are significant differences (e.g., Year 2023 vs 2024, different author names)
- **Example**: Your BibTeX has `year = {2023}` but Crossref reports `2024`

#### Differences (Yellow) - `git-compare` Icon
```{bdg-primary}`Different
:class: badge-status-different
```

- **Color**: Yellow background with dark yellow text
- **Meaning**: Minor styling or formatting differences that don't affect content
- **Action Required**: Optional review - usually safe to accept
- **Example**: `"Journal Name"` vs `Journal Name` (quotes difference), or `Smith, John` vs `Smith, J.` (abbreviation)

#### Identical (Green) - `check-circle` Icon
```{bdg-primary}`Identical
:class: badge-status-identical
```

- **Color**: Green background with dark green text
- **Meaning**: Fields that perfectly match the authoritative source
- **Action Required**: None - these fields are already correct
- **Example**: Title, author, and year all match exactly

### Accept All Entries Button

A global action button that allows batch-approval of all non-conflicting changes across all entries.

**Features:**
- **Two-step confirmation**: Click once to activate confirmation mode, click again within 3 seconds to confirm
- **Visual feedback**: Button changes to red/destructive style during confirmation
- **Scope**: Accepts all `fields_updated` and `fields_different` for all entries
- **Safety**: Conflicts are included in "Accept All" - use with caution

**Workflow:**
1. First click: Button text changes to "Click again to confirm" (red background)
2. Second click (within 3 seconds): Processes all changes
3. After 3 seconds: Button reverts to normal state if not confirmed

**Visual States:**

```{grid} 1 2
:gutter: 2

```{card} Normal State
:class: sd-shadow-sm

```{bdg-primary}`Accept All Entries
:class: badge-status-review
```
```

```{card} Confirm State
:class: sd-shadow-sm

```{bdg-primary}`Click again to confirm
:class: badge-destructive
```
```

```{card} Processing State
:class: sd-shadow-sm

```{bdg-primary}`Processing...
:class: badge-muted
```
```

```{card} Success State
:class: sd-shadow-sm

```{bdg-primary}`All Accepted
:class: badge-status-accepted
```
```
```

## 2. Navigation Toolbar

The navigation toolbar, located below the summary, provides controls for moving through your bibliography entries.

### Entry Selector Dropdown

A searchable dropdown menu listing all BibTeX entries by their citation keys.

**Features:**
- **Badge Indicators**: Entries with issues show badges next to their keys:
  - `+N`: Number of fields with suggested updates
  - `!N`: Number of fields with conflicts
- **Auto-selection**: First entry is automatically selected when entries load
- **Keyboard Accessible**: Can be navigated with arrow keys

**Example Display:**

```{dropdown} Entry Selector Example
Select an entry...

smith2023 (+2, !1)
:   Entry with 2 updates and 1 conflict

jones2024
:   Entry with no issues

brown2022 (+1)
:   Entry with 1 update
```

The dropdown shows badge indicators next to entries that need attention:
- `+N`: Number of fields with suggested updates
- `!N`: Number of fields with conflicts

### Previous/Next Buttons

Sequential navigation controls for moving through entries one at a time.

- **Previous** (`◀`): Moves to the previous entry
- **Next** (`▶`): Moves to the next entry
- **Auto-disable**: Buttons are disabled at the first/last entry
- **Keyboard Alternative**: Arrow keys provide the same functionality

### Entry Stats Display

An inline summary showing the current entry's validation status:

```
📝 2 reviews | ⚠ 1 conflicts | 🔄 0 differences | ✓ 5 identical
```

The stats update dynamically as you navigate between entries and reflect:
- Number of fields in each category (updates, conflicts, differences, identical)
- Color-coded icons matching the global summary

## 3. Keyboard Shortcuts

The GUI supports comprehensive keyboard navigation for efficient workflow. All shortcuts are disabled when input fields (INPUT, TEXTAREA, SELECT) have focus to prevent conflicts.

### Navigation Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| `←` (Left Arrow) | Previous Entry | Navigate to the previous entry in the list |
| `↑` (Up Arrow) | Previous Entry | Same as Left Arrow - navigate backward |
| `→` (Right Arrow) | Next Entry | Navigate to the next entry in the list |
| `↓` (Down Arrow) | Next Entry | Same as Right Arrow - navigate forward |
| `Home` | First Entry | Jump to the first entry in the bibliography |
| `End` | Last Entry | Jump to the last entry in the bibliography |
| `PageUp` | Jump Back 10 | Move backward by 10 entries (or to first if less than 10 remain) |
| `PageDown` | Jump Forward 10 | Move forward by 10 entries (or to last if less than 10 remain) |
| `Esc` | Clear Selection | Deselect current entry and show empty state |

### Keyboard Navigation Logic

- **Input Field Detection**: Shortcuts are automatically disabled when:
  - An `<input>` field has focus
  - A `<textarea>` has focus
  - A `<select>` dropdown is open
  - Any content-editable element is active

- **Boundary Handling**: Navigation respects list boundaries:
  - Previous/Next buttons disable at first/last entry
  - Home/End work only when entries exist
  - PageUp/PageDown clamp to valid range

### Usage Tips

- Use arrow keys for quick sequential review
- Use `PageUp`/`PageDown` for large bibliographies
- Use `Home`/`End` to jump to extremes
- Press `Esc` to clear selection and see the overview

## 4. Source Badge System

Source badges indicate which online database provided the metadata for each field. Each source has a distinct color scheme for easy identification.

### Source Types and Colors

#### Crossref (Blue)
```{bdg-primary}`CROSSREF
:class: badge-source-crossref
```

- **Primary Use**: DOI metadata - the main authoritative source for published papers
- **Coverage**: Journals, conferences, books with DOIs
- **Priority**: Highest (1st in priority order)
- **Reliability**: Very high - official DOI registry

#### arXiv (Red)
```{bdg-primary}`ARXIV
:class: badge-source-arxiv
```

- **Primary Use**: Preprint papers and arXiv-hosted publications
- **Coverage**: Preprints, e-prints, arXiv papers
- **Priority**: High (3rd in priority order)
- **Reliability**: High - official arXiv metadata
- **Special Features**: Automatically adds `eprint` and `eprinttype` fields

#### Semantic Scholar (Indigo)
```{bdg-primary}`SEMANTIC SCHOLAR
:class: badge-source-semantic-scholar
```

- **Primary Use**: AI-powered academic search and metadata
- **Coverage**: Broad academic literature
- **Priority**: Lower (7th in priority order)
- **Reliability**: Good - AI-enhanced but may have errors
- **Best For**: Finding missing DOIs or metadata for obscure papers

#### DBLP (Purple)
```{bdg-primary}`DBLP
:class: badge-source-dblp
```

- **Primary Use**: Computer science bibliography
- **Coverage**: CS conferences, journals, and proceedings
- **Priority**: Medium (4th in priority order)
- **Reliability**: Very high for CS publications
- **Best For**: Computer science papers, especially conference proceedings

#### PubMed (Sky Blue)
```{bdg-primary}`PUBMED
:class: badge-source-pubmed
```

- **Primary Use**: Biomedical and life sciences literature
- **Coverage**: Medical journals, biomedical research
- **Priority**: Medium (6th in priority order)
- **Reliability**: Very high for medical publications
- **Best For**: Papers with PMID identifiers

#### Zenodo (Gray)
```{bdg-primary}`ZENODO
:class: badge-source-zenodo
```

- **Primary Use**: General repository for research outputs
- **Coverage**: Datasets, software, reports, presentations
- **Priority**: High (2nd in priority order, after Crossref)
- **Reliability**: High - official repository
- **Special Features**: Often includes GitHub repository links

#### DataCite (Gray)
```{bdg-primary}`DATACITE
:class: badge-source-datacite
```

- **Primary Use**: Data DOI registry
- **Coverage**: Research datasets, data publications
- **Priority**: Medium (5th in priority order)
- **Reliability**: High - official data DOI registry
- **Best For**: Datasets and data publications

#### OpenAlex (Gray)
```{bdg-primary}`OPENALEX
:class: badge-source-openalex
```

- **Primary Use**: Comprehensive academic metadata
- **Coverage**: Very broad - aggregates multiple sources
- **Priority**: Lowest (8th in priority order)
- **Reliability**: Good - comprehensive but may be less precise
- **Best For**: Fallback when other sources fail

### Source Priority Order

When multiple sources provide data for the same field, the validator uses this priority order:

1. **Crossref** (highest priority)
2. **Zenodo**
3. **arXiv**
4. **DBLP**
5. **DataCite**
6. **PubMed**
7. **Semantic Scholar**
8. **OpenAlex** (lowest priority)

### Source Selection Dropdown

For fields with multiple available sources, a dropdown menu allows you to choose which source's value to use.

**Features:**
- **Visual Indicator**: Badge shows a chevron-down icon when multiple sources are available
- **Click to Expand**: Clicking the badge opens a dropdown menu
- **Source List**: Shows all sources that have data for this field
- **Current Selection**: Checkmark indicates the currently selected source
- **Auto-Update**: Changing the source immediately updates the displayed API value

**Visual Example:**

```{card} Source Selection Dropdown
:class: sd-shadow-sm

```{bdg-primary}`CROSSREF
:class: badge-source-crossref
```
: Click to expand

When expanded, shows available sources:

```{grid} 1
:gutter: 1

```{bdg-primary}`CROSSREF ✓
:class: badge-source-crossref
```
: Currently selected

```{bdg-primary}`ARXIV
:class: badge-source-arxiv
```

```{bdg-primary}`SEMANTIC SCHOLAR
:class: badge-source-semantic-scholar
```

```{bdg-primary}`DBLP
:class: badge-source-dblp
```
```
```

**When Available:**
- Multiple sources found data for the same field
- Field is not in "identical" or "bibtex-only" status
- At least 2 sources have different values

## 5. Status Badge System

Status badges indicate the relationship between your BibTeX value and the API value for each field.

### Status Types

#### Review (Blue)
```{bdg-primary}`Review
:class: badge-status-review
```

- **Label**: "Review"
- **Meaning**: New data is available from the API for a field that is missing or empty in your BibTeX
- **Action**: Review the suggested value and accept if appropriate
- **Visual**: BibTeX value shows as strikethrough red `(empty)`, API value in green
- **Example**: Your entry has no `journal` field, but Crossref provides it

#### Conflict (Orange)
```{bdg-primary}`Conflict
:class: badge-status-conflict
```

- **Label**: "Conflict"
- **Meaning**: Significant mismatch between your BibTeX value and API value
- **Action**: **Manual review required** - these are important differences
- **Visual**: Both values displayed side-by-side for comparison
- **Examples**:
  - Year mismatch: `2023` vs `2024`
  - Different author names: `Smith, John` vs `Smith, Jane`
  - Journal name differences: `J. ACM` vs `Journal of the ACM`

#### Different (Yellow)
```{bdg-primary}`Different
:class: badge-status-different
```

- **Label**: "Different"
- **Meaning**: Minor formatting or stylistic differences (similarity > 70%)
- **Action**: Usually safe to accept - these are cosmetic differences
- **Visual**: Both values displayed for comparison
- **Examples**:
  - Quote differences: `"Title"` vs `Title`
  - Abbreviation: `Smith, John` vs `Smith, J.`
  - Case differences: `Journal Name` vs `journal name`

#### Identical (Green)
```{bdg-primary}`Identical
:class: badge-status-identical
```

- **Label**: "Identical"
- **Meaning**: Your BibTeX value perfectly matches the API value (after normalization)
- **Action**: **No action needed** - field is already correct
- **Visual**: Single value displayed (same in both columns)
- **Note**: These fields are verified and correct

#### Accepted (Emerald)
```{bdg-primary}`Accepted
:class: badge-status-accepted
```

- **Label**: "Accepted"
- **Meaning**: You have accepted the API value for this field
- **Action**: None - change has been applied
- **Visual**: Shows briefly after accepting, then field reloads
- **Transient**: Status appears for ~2 seconds after acceptance

#### Rejected (Red)
```{bdg-primary}`Rejected
:class: badge-status-rejected
```

- **Label**: "Rejected"
- **Meaning**: You have explicitly rejected the API suggestion
- **Action**: None - your original value is preserved
- **Visual**: Shows briefly after rejecting, then field reloads
- **Transient**: Status appears for ~2 seconds after rejection

#### Local Only (Gray)
```{bdg-primary}`Local Only
:class: badge-status-local-only
```

- **Label**: "Local Only"
- **Meaning**: Field exists in your BibTeX but no API source provides data for it
- **Action**: None - keep your local value
- **Visual**: BibTeX value shown, API value shows as `-` (dash)
- **Examples**: Custom fields, notes, or fields not in standard metadata

### Status Badge Visual Reference

```{grid} 3
:gutter: 2

```{bdg-primary}`Review
:class: badge-status-review
```

```{bdg-primary}`Conflict
:class: badge-status-conflict
```

```{bdg-primary}`Different
:class: badge-status-different
```

```{bdg-primary}`Identical
:class: badge-status-identical
```

```{bdg-primary}`Accepted
:class: badge-status-accepted
```

```{bdg-primary}`Rejected
:class: badge-status-rejected
```

```{bdg-primary}`Local Only
:class: badge-status-local-only
```
```

## 6. Comparison Table

The comparison table is the core of the GUI, providing a detailed field-by-field comparison for the selected entry.

### Table Structure

The table has six columns:

1. **Field**: BibTeX field name (e.g., `title`, `author`, `year`, `journal`)
2. **BibTeX Value**: Current value in your local `.bib` file
3. **API Value**: Suggested value from online sources
4. **Source**: Data source badge (with dropdown if multiple sources available)
5. **Status**: Status badge indicating the comparison result
6. **Actions**: Accept/Reject buttons or status message

### Row Display Logic

Rows are displayed in priority order:
1. **Updates** (Review status) - New data available
2. **Conflicts** - Significant mismatches
3. **Differences** - Minor differences
4. **Identical** - Verified matches
5. **Local Only** - Fields not in API

### Visual Formatting by Status

#### Update Rows

```{list-table} Update Row Example
:header-rows: 1
:class: longtable

* - Field
  - BibTeX Value
  - API Value
  - Status
* - title
  - ~~(empty)~~
  - **New Title from API**
  - ```{bdg-primary}`Review
:class: badge-status-review
```
```

#### Conflict/Different Rows

```{list-table} Conflict Row Example
:header-rows: 1
:class: longtable

* - Field
  - BibTeX Value
  - API Value
  - Status
* - year
  - 2023
  - 2024
  - ```{bdg-primary}`Conflict
:class: badge-status-conflict
```
```

#### Identical Rows

```{list-table} Identical Row Example
:header-rows: 1
:class: longtable

* - Field
  - BibTeX Value
  - API Value
  - Status
* - title
  - Matching Title
  - Matching Title
  - ```{bdg-primary}`Identical
:class: badge-status-identical
```
```

#### Local Only Rows

```{list-table} Local Only Row Example
:header-rows: 1
:class: longtable

* - Field
  - BibTeX Value
  - API Value
  - Status
* - note
  - Custom note text
  - *-*
  - ```{bdg-primary}`Local Only
:class: badge-status-local-only
```
```

### Footer Actions

At the bottom of the table, bulk action buttons appear when there are actionable items (updates, conflicts, or differences):

- **Reject All**: Discard all suggestions for the current entry
  - Restores all fields to their original BibTeX values
  - Removes fields that were added (if they were originally missing)
  
- **Accept All**: Apply all suggested changes for the current entry
  - Accepts all updates, conflicts, and differences
  - Uses the selected source for each field (or default priority if none selected)
  - Immediately saves to the BibTeX file

**Visual Layout:**

```{card} Footer Actions
:class: sd-shadow-sm

Apply to all fields in this entry:

```{bdg-primary}`Reject All
:class: badge-destructive
```
```{bdg-primary}`Accept All
:class: badge-status-review
```
```

## 7. Action Buttons

### Field-Level Actions

#### Accept Button
- **Function**: Applies the API value to your BibTeX entry
- **Process**:
  1. Sends request to backend with field name and selected source
  2. Backend updates the entry in memory
  3. Saves to BibTeX file
  4. Reloads entry data
  5. Updates global statistics
- **Visual Feedback**:
  - Button shows "Saving..." with spinner during save
  - Changes to "Saved" with checkmark for 2 seconds
  - Then returns to normal state
- **Source Handling**: Uses the selected source (from dropdown) if available, otherwise uses default priority

#### Reject Button
- **Function**: Keeps your original BibTeX value, rejecting the API suggestion
- **Process**:
  1. Sends request to backend with field name
  2. Backend restores original value from `original_values` or `fields_conflict[0]`
  3. Saves to BibTeX file
  4. Reloads entry data
  5. Updates global statistics
- **Visual Feedback**: Same as Accept button
- **Restoration Logic**:
  - For conflicts: Uses first element of conflict tuple (BibTeX value)
  - For updates: Restores from `original_values` or deletes field if it was missing
  - For differences: Uses first element of difference tuple

### Entry-Level Actions

#### Accept All (Footer)
- **Function**: Accepts all suggested changes for the current entry
- **Scope**: All fields with status "Review", "Conflict", or "Different"
- **Process**:
  1. Collects all actionable field names
  2. Sends batch request with all fields and selected sources
  3. Backend applies all changes
  4. Saves to file
  5. Reloads entry
  6. Updates statistics
- **Safety**: Only processes fields that haven't been accepted/rejected yet

#### Reject All (Footer)
- **Function**: Rejects all suggestions for the current entry
- **Scope**: All fields with status "Review", "Conflict", or "Different"
- **Process**:
  1. Collects all actionable field names
  2. Sends batch request to reject all
  3. Backend restores all original values
  4. Saves to file
  5. Reloads entry
  6. Updates statistics

### Global Actions

#### Accept All Entries
- **Function**: Batch-approves all non-conflicting changes across all entries
- **Scope**: All entries in the bibliography
- **Confirmation**: Two-step process (click twice within 3 seconds)
- **Process**:
  1. Iterates through all entries
  2. Collects all `fields_updated`, `fields_different`, and `fields_conflict`
  3. Applies all changes using default priority sources
  4. Saves to file
  5. Updates all entry statistics
  6. Reloads entries list
- **Safety Note**: This includes conflicts - use with caution for large bibliographies

## 8. API and Data Sources

The BibTeX Validator integrates with multiple academic databases and metadata providers. Understanding each source helps you make informed decisions when reviewing suggestions.

### Data Source Overview

```{mermaid}
graph TD
    A[BibTeX Entry] --> B{Has DOI?}
    B -->|Yes| C[Crossref API]
    B -->|No| D{Has arXiv ID?}
    D -->|Yes| E[arXiv API]
    D -->|No| F{Has Title?}
    F -->|Yes| G[Search APIs]
    
    C --> H{Zenodo DOI?}
    H -->|Yes| I[Zenodo API]
    H -->|No| J[DataCite API]
    
    G --> K[DBLP Search]
    G --> L[Semantic Scholar]
    G --> M[OpenAlex Search]
    
    D -->|Yes| N[Extract DOI from arXiv]
    N --> C
    
    O[Has PMID?] --> P[PubMed API]
    
    Q[Recursive Enrichment] --> R{Found New DOI?}
    R -->|Yes| C
    R -->|No| S{Found New arXiv ID?}
    S -->|Yes| E
```

### Source Details

#### Crossref
- **API Endpoint**: `https://api.crossref.org/works/{doi}`
- **Primary Use**: DOI metadata for published papers
- **Data Quality**: Very high - official DOI registry
- **Coverage**: Journals, conferences, books, reports
- **Rate Limiting**: Polite user-agent recommended
- **Best For**: Published papers with DOIs
- **Fields Provided**: title, author, journal, year, volume, pages, DOI, ISSN, entrytype

#### arXiv
- **API Endpoint**: `http://export.arxiv.org/api/query?id_list={arxiv_id}`
- **Primary Use**: Preprint papers
- **Data Quality**: High - official arXiv metadata
- **Coverage**: Preprints, e-prints
- **Rate Limiting**: 1 request per second recommended
- **Best For**: Preprint papers, arXiv-hosted publications
- **Fields Provided**: title, authors, year, arxiv_id, categories
- **Special**: Automatically adds `eprint` and `eprinttype="arxiv"` fields

#### Zenodo
- **API Endpoint**: `https://zenodo.org/api/records/{record_id}`
- **Primary Use**: General research repository
- **Data Quality**: High - official repository
- **Coverage**: Datasets, software, reports, presentations
- **Best For**: Research outputs in Zenodo
- **Fields Provided**: title, authors, year, publisher, DOI, URL (often GitHub links)
- **Special**: Extracts GitHub repository URLs from related identifiers

#### DataCite
- **API Endpoint**: `https://api.datacite.org/dois/{doi}`
- **Primary Use**: Data DOI registry
- **Data Quality**: High - official data DOI registry
- **Coverage**: Research datasets, data publications
- **Best For**: Datasets and data publications
- **Fields Provided**: title, creators, year, publisher, DOI, type, URL

#### DBLP
- **API Endpoint**: `https://dblp.org/search/publ/api`
- **Primary Use**: Computer science bibliography
- **Data Quality**: Very high for CS publications
- **Coverage**: CS conferences, journals, proceedings
- **Search Method**: Title + author search
- **Best For**: Computer science papers, especially conference proceedings
- **Fields Provided**: title, authors, year, venue (journal/conference)

#### Semantic Scholar
- **API Endpoint**: `https://api.semanticscholar.org/graph/v1/paper/search`
- **Primary Use**: AI-powered academic search
- **Data Quality**: Good - AI-enhanced but may have errors
- **Coverage**: Broad academic literature
- **Search Method**: Title + author search
- **Best For**: Finding missing DOIs or metadata for obscure papers
- **Fields Provided**: title, authors, year, venue, DOI, externalIds

#### PubMed
- **API Endpoint**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi`
- **Primary Use**: Biomedical and life sciences literature
- **Data Quality**: Very high for medical publications
- **Coverage**: Medical journals, biomedical research
- **Requires**: PMID (PubMed ID) in BibTeX entry
- **Best For**: Papers with PMID identifiers
- **Fields Provided**: title, authors, year, journal

#### OpenAlex
- **API Endpoint**: `https://api.openalex.org/works`
- **Primary Use**: Comprehensive academic metadata
- **Data Quality**: Good - comprehensive but may be less precise
- **Coverage**: Very broad - aggregates multiple sources
- **Search Method**: DOI lookup or title search
- **Best For**: Fallback when other sources fail, or for comprehensive metadata
- **Fields Provided**: title, authors, publication_year, venue, DOI, volume, issue, pages
- **Special**: Provides detailed bibliographic information (volume, issue, pages)

### Priority Order and Conflict Resolution

When multiple sources provide data for the same field, the validator uses this priority order:

1. **Crossref** (highest priority - most authoritative for DOIs)
2. **Zenodo** (high priority - official repository)
3. **arXiv** (high priority - official preprint source)
4. **DBLP** (medium priority - excellent for CS)
5. **DataCite** (medium priority - official data registry)
6. **PubMed** (medium priority - excellent for medical)
7. **Semantic Scholar** (lower priority - AI-enhanced)
8. **OpenAlex** (lowest priority - comprehensive fallback)

**Rationale**: Official registries (Crossref, Zenodo, DataCite) have highest priority, followed by domain-specific authoritative sources (arXiv, DBLP, PubMed), then general search engines (Semantic Scholar, OpenAlex).

### Recursive Enrichment

The validator implements a "recursive enrichment" feature that discovers missing identifiers:

**Process:**
1. If an entry has no DOI, search secondary sources (DBLP, Semantic Scholar, OpenAlex, PubMed)
2. If a DOI is found in secondary sources, fetch from Crossref/Zenodo/DataCite
3. If an entry has no arXiv ID, check if secondary sources mention one
4. If an arXiv ID is found, fetch from arXiv API

**Example Flow:**
```
Entry (no DOI, has title)
  → Search DBLP → Found DOI: 10.1234/example
  → Fetch Crossref → Got full metadata
  → Check Crossref → Found arXiv ID: 1234.5678
  → Fetch arXiv → Got preprint metadata
```

This ensures maximum metadata coverage even when identifiers are missing.

## 9. Data Flow and Workflow

Understanding the complete data flow helps you use the GUI effectively.

### Validation to Display Flow

```{mermaid}
sequenceDiagram
    participant User
    participant GUI
    participant Backend
    participant APIs as External APIs
    participant File as BibTeX File
    
    User->>GUI: Launch --gui
    GUI->>Backend: Load BibTeX file
    Backend->>Backend: Parse entries
    Backend->>APIs: Fetch metadata (parallel)
    APIs-->>Backend: Return metadata
    Backend->>Backend: Compare & validate
    Backend->>Backend: Generate ValidationResult
    Backend-->>GUI: Return results
    GUI->>GUI: Display summary & entries
    
    User->>GUI: Select entry
    GUI->>Backend: GET /api/entry/{key}
    Backend-->>GUI: Return comparison data
    GUI->>GUI: Render comparison table
    
    User->>GUI: Accept field
    GUI->>Backend: POST /api/save
    Backend->>Backend: Update entry
    Backend->>File: Save to .bib file
    Backend-->>GUI: Success response
    GUI->>GUI: Reload entry & update stats
```

### Typical Workflow

1. **Launch and Validate**
   - Run `bibtex-validator references.bib --gui`
   - Validator fetches metadata from all available sources
   - Summary displays global statistics

2. **Review Summary**
   - Check attention pie chart for overall status
   - Review statistics (reviews, conflicts, differences, identical)
   - Decide whether to use "Accept All Entries" or review individually

3. **Navigate Entries**
   - Use dropdown, arrow keys, or Previous/Next buttons
   - Focus on entries with badges (`+N`, `!N`)

4. **Review Comparison Table**
   - Check each field's status badge
   - Compare BibTeX vs API values
   - Select source if multiple available (dropdown)

5. **Make Decisions**
   - **Accept**: Click Accept button for individual fields
   - **Reject**: Click Reject button to keep original
   - **Bulk Actions**: Use Accept All / Reject All for entry
   - **Global**: Use Accept All Entries for everything

6. **Verify Changes**
   - Changes are saved immediately upon acceptance
   - Entry reloads to show updated state
   - Statistics update in real-time

## 10. Tips and Best Practices

### Efficient Review Process

1. **Start with Summary**: Use the attention pie chart to gauge overall quality
2. **Focus on Conflicts**: Prioritize entries with conflict badges (`!N`)
3. **Use Keyboard Navigation**: Arrow keys and PageUp/PageDown speed up navigation
4. **Batch When Safe**: Use "Accept All" for entries where you trust the API sources
5. **Verify Critical Fields**: Always manually review conflicts in title, author, and year

### Source Selection Strategy

- **Trust Official Sources**: Crossref and Zenodo are most reliable
- **Domain-Specific**: Use DBLP for CS, PubMed for medical
- **Multiple Sources**: When multiple sources agree, confidence is higher
- **Source Disagreement**: If sources conflict, prefer Crossref for published papers

### Handling Conflicts

- **Year Mismatches**: Often indicate preprint vs published version - verify publication date
- **Author Differences**: Check for name variations, middle initials, or order
- **Journal Names**: Abbreviations vs full names are common - usually safe to accept API version
- **Title Differences**: Usually minor (capitalization, punctuation) - review carefully

### Performance Considerations

- **Large Bibliographies**: Use keyboard shortcuts for faster navigation
- **Network Delays**: API fetching happens during validation, not in GUI
- **Save Frequency**: Each Accept action saves immediately - no batch save needed

## Conclusion

The BibTeX Validator GUI provides a powerful, intuitive interface for reviewing and enriching your bibliography. By understanding the badge systems, keyboard shortcuts, and data sources, you can efficiently validate large bibliographies while maintaining control over every change.

For command-line usage, see the [Usage Guide](usage.md). For details on the validation logic, see the [Internal Logic](logic.md) documentation.
