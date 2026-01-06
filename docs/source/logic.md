# Internal Logic

Understanding how **BibTeX Validator** processes your entries.

## Validation Process

The validation pipeline follows a parallel execution model to ensure speed and efficiency.

```{mermaid}
graph TD
    A[Start: Input BibTeX] --> B{Parse Entries}
    B --> C[Validate Entry]

    subgraph Parallel Execution
        C --> D{Check Identifiers}
        D -->|Has DOI| E[Fetch Crossref]
        D -->|Has arXiv ID| F[Fetch arXiv]
        D -->|Missing IDs| G[Search Google Scholar / DBLP]

        E --> H[Normalize Data]
        F --> H
        G --> H
    end

    H --> I{Compare with Local}
    I -->|Match| J[Status: Identical]
    I -->|Mismatch| K[Status: Conflict/Different]
    I -->|New Data| L[Status: Review (Update)]

    J --> M[End: Result]
    K --> M
    L --> M
```

### Steps Explained

1.  **Parsing**: The input BibTeX file is parsed using `bibtexparser`.
2.  **DOI Normalization**: DOIs are stripped of prefixes (e.g., `doi:`) to ensure consistent querying.
3.  **API Querying**:
    - **Crossref**: Primary source for DOI-based metadata.
    - **arXiv**: Used if an arXiv ID is found or inferred.
    - **Backup Searches**: OpenAlex, DBLP, and Semantic Scholar are queried for additional coverage or if primary IDs are missing.
4.  **Comparison**: The script compares the fetched metadata with your local entry to determine the status (Identical, Conflict, etc.).

## Speed Optimization

To speed up processing, especially for large files, the validator uses `concurrent.futures`.

- **ThreadPoolExecutor**: Utilized to fetch data for multiple entries concurrently.
- **Rate Limiting**: A `delay` parameter ensures we don't hit API rate limits (default: 1.0s between requests for the same provider).
