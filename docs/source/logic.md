# Internal Logic

Understanding how **BibTeX Validator** processes your entries.

## Validation Process

1.  **Parsing**: The input BibTeX file is parsed using `bibtexparser`.
2.  **DOI Normalization**: DOIs are stripped of prefixes (e.g., `doi:`) to ensure consistent querying.
3.  **API Querying**:
    - **Crossref**: Queried using the DOI.
    - **arXiv**: Queried if an arXiv ID is found or inferred from the DOI.
    - **OpenAlex**: Used as a comprehensive backup.
    - **Semantic Scholar / DBLP**: Used for computer science papers, searched by title/author.
    - **PubMed**: Used for medical papers if PMID is present.
4.  **Comparison**: The script compares the fetched metadata with your local entry.
    - **Identical**: Values match.
    - **Update**: API has a value where yours is missing.
    - **Conflict**: API has a different value than yours.

## Parallelization

To speed up processing, especially for large files, the validator uses `concurrent.futures`.

- **ThreadPoolExecutor**: Utilized to fetch data for multiple entries concurrently.
- **Rate Limiting**: A `delay` parameter ensures we don't hit API rate limits (default: 1.0s).

## Data Sources

The tool integrates with several major academic databases:

- **Crossref**: The primary source for DOI metadata.
- **arXiv**: Definitive source for preprints.
- **Google Scholar**: (via `scholarly`) Used for citation counts and finding missing DOIs.
- **DBLP**: High-quality metadata for CS conferences.
- **Semantic Scholar**: AI-driven scientific literature search.
- **Zenodo / DataCite**: For general repositories and datasets.
