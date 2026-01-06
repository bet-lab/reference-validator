# Internal Logic

Detailed explanation of how **BibTeX Validator** processes, validates, and enriches your bibliography.

## Validation Pipeline

The core validation logic follows a multi-stage pipeline designed for accuracy and performance.

### Process Flow

```{mermaid}
flowchart LR
    Start([Input BibTeX]) --> Parser{Parse}
    Parser --> |Entries| Validator[Validation Engine]

    subgraph Parallel[Parallel Processing]
        direction TB
        Validator --> Check{Check IDs}
        Check --> |Has DOI| Crossref[Fetch Crossref]
        Check --> |Has arXiv| Arxiv[Fetch arXiv]
        Check --> |Missing| Scholar[Search Backup\nScholar/DBLP]

        Crossref --> Normalize[Normalize Data]
        Arxiv --> Normalize
        Scholar --> Normalize
    end

    Normalize --> Compare{Comparison}
    Compare --> |Match| StatusOk[Identical]
    Compare --> |Mismatch| StatusDiff[Conflict]
    Compare --> |New Data| StatusNew[Review]

    StatusOk --> Result([Final Result])
    StatusDiff --> Result
    StatusNew --> Result

    classDef distinct fill:#f9f,stroke:#333,stroke-width:2px;
    class Start,Result distinct;
```

### 1. Parsing & Identification

The validator first parses the `.bib` file using `bibtexparser`. It then identifies the best strategy for each entry:

- **DOI-based**: Preferred method. Queries Crossref directly.
- **arXiv-based**: Used for preprints. Queries arXiv API.
- **Search-based**: Fallback. Uses Title/Author to search Google Scholar or DBLP.

### 2. Parallel Execution

To ensure high performance even with large bibliographies, the validator processes entries in parallel.

- **Concurrency**: Uses `ThreadPoolExecutor` to handle multiple network requests simultaneously.
- **Rate Limiting**: Implements smart delays to respect API rate limits (e.g., Crossref, arXiv).

### 3. Smart Comparison

The system doesn't just check for equality; it understands bibliographic data:

- **Normalization**: Standardizes author names, page numbers, and dates before comparing.
- **Fuzzy Matching**: Detects minor stylistic differences (like "Journal of..." vs "J. of...") to avoid false alarms.

## Data Source Priority

When multiple sources provide data for the same field, the validator applies a strict priority system to ensure the highest quality metadata.

| Priority | Source               | Best For                          |
| :------- | :------------------- | :-------------------------------- |
| **1**    | **Crossref**         | Official DOIs, Publisher Metadata |
| **2**    | **Zenodo**           | Datasets, Software, GitHub Links  |
| **3**    | **arXiv**            | Preprints, Latest Revisions       |
| **4**    | **DBLP**             | Computer Science Conferences      |
| **5**    | **DataCite**         | General Datasets                  |
| **6**    | **PubMed**           | Biomedical Literature             |
| **7**    | **Semantic Scholar** | AI-driven discovery, Missing DOIs |
| **8**    | **OpenAlex**         | General Backup                    |

## Scoring & Status Logic

Each field in an entry is assigned a validation status based on the comparison:

- :gui-status-identical:`Identical`: Perfect match (after normalization).
- :gui-status-different:`Different`: Content matches but format differs slightly (>70% similarity).
- :gui-status-conflict:`Conflict`: Significant content mismatch (e.g., completely different year).
- :gui-status-review:`Review`: Using data from API to fill a missing local field.
