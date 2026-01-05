#!./.venv/bin/python3
"""
BibTeX Validation and Enrichment Script

This script validates BibTeX entries by:
1. Checking DOI information via Crossref API
2. Checking arXiv information via arXiv API
3. Searching Google Scholar for missing information (optional)
4. Comparing and updating fields
5. Generating a validation report
"""

import re
import sys
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
import threading
import pickle
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import bibtexparser
    from bibtexparser.bwriter import BibTexWriter
    from bibtexparser.bparser import BibTexParser

    HAS_BIBTEXPARSER = True
except ImportError:
    HAS_BIBTEXPARSER = False

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from scholarly import scholarly

    HAS_SCHOLARLY = True
except ImportError:
    HAS_SCHOLARLY = False

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import HTMLResponse, JSONResponse
    import uvicorn
    import webbrowser
    import threading

    HAS_GUI_DEPS = True
except ImportError:
    HAS_GUI_DEPS = False
    if TYPE_CHECKING:
        # For type checking only
        from fastapi import FastAPI


@dataclass
class ValidationResult:
    """Stores validation results for a single entry"""

    entry_key: str
    has_doi: bool = False
    doi_valid: bool = False
    has_arxiv: bool = False
    arxiv_valid: bool = False
    arxiv_id: Optional[str] = None
    fields_missing: List[str] = field(default_factory=list)
    fields_updated: Dict[str, Tuple[str, str]] = field(
        default_factory=dict
    )  # field: (old_value, new_value)
    fields_conflict: Dict[str, Tuple[str, str]] = field(
        default_factory=dict
    )  # field: (bibtex_value, api_value)
    fields_identical: Dict[str, str] = field(
        default_factory=dict
    )  # field: value (same in both)
    fields_different: Dict[str, Tuple[str, str]] = field(
        default_factory=dict
    )  # field: (bibtex_value, api_value) - minor differences
    field_sources: Dict[str, str] = field(
        default_factory=dict
    )  # field: "crossref"|"arxiv"|"scholar"|"dblp"|"semantic_scholar"|"pubmed"
    all_sources_data: Dict[str, Dict] = field(
        default_factory=dict
    )  # source_name: data from that source
    field_source_options: Dict[str, List[str]] = field(
        default_factory=dict
    )  # field: [source1, source2, ...] - available sources for this field
    original_values: Dict[str, str] = field(
        default_factory=dict
    )  # field: original_bibtex_value (for undo)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BibTeXValidator:
    """Validates and enriches BibTeX entries"""

    # Standard fields for different entry types
    REQUIRED_FIELDS = {
        "article": ["title", "author", "journal", "year"],
        "inproceedings": ["title", "author", "booktitle", "year"],
        "book": ["title", "author", "publisher", "year"],
        "misc": ["title"],
    }

    # arXiv ID patterns
    ARXIV_NOTE_PATTERN = re.compile(r"(?i)arxiv:\s*(\d{4}\.\d{4,5}(?:v\d+)?)")
    ARXIV_DOI_PATTERN = re.compile(r"10\.48550/ARXIV\.(\d{4}\.\d{4,5})", re.IGNORECASE)

    def __init__(
        self,
        bib_file: str,
        output_file: Optional[str] = None,
        update_bib: bool = False,
        delay: float = 1.0,
    ):
        """
        Initialize validator

        Args:
            bib_file: Path to input BibTeX file
            output_file: Path to output BibTeX file (default: bib_file)
            update_bib: If True, update the BibTeX file with enriched data
            delay: Delay between API requests (seconds)
        """
        # Check dependencies
        if not HAS_BIBTEXPARSER:
            raise ImportError(
                "bibtexparser is required. Install with: uv add bibtexparser or pip install bibtexparser"
            )
        if not HAS_REQUESTS:
            raise ImportError(
                "requests is required. Install with: uv add requests or pip install requests"
            )

        self.bib_file = Path(bib_file)
        self.output_file = Path(output_file) if output_file else self.bib_file
        self.update_bib = update_bib
        self.delay = delay
        self.results: List[ValidationResult] = []
        self.print_lock = threading.Lock()

        # Load BibTeX file
        if not self.bib_file.exists():
            raise FileNotFoundError(f"BibTeX file not found: {self.bib_file}")

        with open(self.bib_file, "r", encoding="utf-8") as f:
            parser = BibTexParser(common_strings=True)
            self.db = bibtexparser.load(f, parser=parser)

    def normalize_doi(self, doi: str) -> str:
        """Normalize DOI format"""
        doi = doi.strip()
        # Remove 'doi:' prefix if present
        doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
        return doi

    def extract_arxiv_id(self, entry: Dict) -> Optional[str]:
        """
        Extract arXiv ID from BibTeX entry

        Checks:
        1. note field: "arXiv: YYYY.NNNNN" or "arXiv: YYYY.NNNNNvN"
        2. doi field: "10.48550/ARXIV.YYYY.NNNNN"
        3. eprint field: "YYYY.NNNNN"

        Returns:
            Normalized arXiv ID (YYYY.NNNNN format, version suffix removed) or None
        """
        # Check note field
        note = entry.get("note", "")
        if note:
            match = self.ARXIV_NOTE_PATTERN.search(note)
            if match:
                arxiv_id = match.group(1)
                # Remove version suffix for API query
                return re.sub(r"v\d+$", "", arxiv_id)

        # Check doi field for arXiv DOI
        doi = entry.get("doi", "")
        if doi:
            match = self.ARXIV_DOI_PATTERN.search(doi)
            if match:
                return match.group(1)

        # Check eprint field
        eprint = entry.get("eprint", "")
        if eprint:
            # Format: YYYY.NNNNN or YYYY.NNNNNvN
            match = re.match(r"(\d{4}\.\d{4,5})(?:v\d+)?", eprint)
            if match:
                return match.group(1)

        return None

    def fetch_crossref_data(self, doi: str) -> Optional[Dict]:
        """
        Fetch metadata from Crossref API

        Args:
            doi: DOI string

        Returns:
            Dictionary with metadata or None if not found
        """
        doi = self.normalize_doi(doi)
        url = f"https://api.crossref.org/works/{doi}"

        try:
            time.sleep(self.delay)  # Rate limiting
            response = requests.get(
                url,
                headers={
                    "User-Agent": "BibTeX Validator (mailto:your.email@example.com)"
                },
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("message", {})
            elif response.status_code == 404:
                return None
            else:
                return None
        except requests.RequestException:
            return None

    def fetch_arxiv_data(self, arxiv_id: str) -> Optional[Dict]:
        """
        Fetch metadata from arXiv API

        Args:
            arxiv_id: arXiv ID in format YYYY.NNNNN

        Returns:
            Dictionary with metadata or None if not found
        """
        url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"

        try:
            time.sleep(self.delay)  # Rate limiting
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                # Parse XML response
                root = ET.fromstring(response.content)

                # Check for entries
                entries = root.findall("{http://www.w3.org/2005/Atom}entry")
                if not entries:
                    return None

                entry = entries[0]  # Take first entry

                # Extract metadata
                metadata = {}

                # Title
                title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
                if title_elem is not None and title_elem.text:
                    # Remove newlines and extra spaces
                    metadata["title"] = " ".join(title_elem.text.split())

                # Authors
                authors = []
                for author in entry.findall("{http://www.w3.org/2005/Atom}author"):
                    name_elem = author.find("{http://www.w3.org/2005/Atom}name")
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text)
                if authors:
                    metadata["authors"] = authors

                # Published date
                published_elem = entry.find("{http://www.w3.org/2005/Atom}published")
                if published_elem is not None and published_elem.text:
                    # Format: YYYY-MM-DDTHH:MM:SSZ
                    year_match = re.match(r"(\d{4})", published_elem.text)
                    if year_match:
                        metadata["year"] = year_match.group(1)

                # ID (arXiv URL)
                id_elem = entry.find("{http://www.w3.org/2005/Atom}id")
                if id_elem is not None and id_elem.text:
                    # Extract arXiv ID from URL
                    id_match = re.search(
                        r"arxiv\.org/abs/(\d{4}\.\d{4,5})", id_elem.text
                    )
                    if id_match:
                        metadata["arxiv_id"] = id_match.group(1)

                # Categories (optional)
                categories = []
                for category in entry.findall("{http://www.w3.org/2005/Atom}category"):
                    term = category.get("term")
                    if term:
                        categories.append(term)
                if categories:
                    metadata["categories"] = categories

                return metadata if metadata else None
            else:
                return None
        except (requests.RequestException, ET.ParseError):  # Removed unused 'e'
            return None

    def fetch_semantic_scholar_data(
        self, title: str, author: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Fetch metadata from Semantic Scholar API

        Args:
            title: Paper title
            author: First author name (optional)

        Returns:
            Dictionary with metadata or None if not found
        """
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": f"{title} {author}" if author else title,
            "limit": 1,
            "fields": "title,authors,year,venue,doi,externalIds",
        }

        try:
            time.sleep(self.delay)
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                papers = data.get("data", [])
                if papers:
                    paper = papers[0]
                    metadata = {}

                    if "title" in paper:
                        metadata["title"] = paper["title"]

                    if "authors" in paper:
                        authors = [
                            f"{a.get('name', '')}"
                            for a in paper["authors"]
                            if a.get("name")
                        ]
                        if authors:
                            metadata["authors"] = authors

                    if "year" in paper:
                        metadata["year"] = str(paper["year"])

                    if "venue" in paper:
                        metadata["journal"] = paper["venue"]

                    if "doi" in paper:
                        metadata["doi"] = paper["doi"]

                    return metadata if metadata else None
        except requests.RequestException:
            pass

        return None

    def fetch_dblp_data(
        self, title: str, author: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Fetch metadata from DBLP API

        Args:
            title: Paper title
            author: First author name (optional)

        Returns:
            Dictionary with metadata or None if not found
        """
        # DBLP search API
        url = "https://dblp.org/search/publ/api"
        params = {
            "q": f"{title} {author}" if author else title,
            "h": 1,
            "format": "json",
        }

        try:
            time.sleep(self.delay)
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                hits = data.get("result", {}).get("hits", {}).get("hit", [])
                if hits:
                    hit = hits[0]
                    info = hit.get("info", {})
                    metadata = {}

                    if "title" in info:
                        metadata["title"] = info["title"]

                    if "authors" in info:
                        authors = info["authors"].get("author", [])
                        if isinstance(authors, list):
                            author_names = [
                                a.get("text", "") if isinstance(a, dict) else str(a)
                                for a in authors
                            ]
                        else:
                            author_names = [authors.get("text", "")]
                        if author_names:
                            metadata["authors"] = author_names

                    if "year" in info:
                        metadata["year"] = str(info["year"])

                    if "venue" in info:
                        metadata["journal"] = info["venue"]

                    return metadata if metadata else None
        except requests.RequestException:
            pass

        return None

    def fetch_pubmed_data(self, pmid: str) -> Optional[Dict]:
        """
        Fetch metadata from PubMed API via Entrez

        Args:
            pmid: PubMed ID

        Returns:
            Dictionary with metadata or None if not found
        """
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {"db": "pubmed", "id": pmid, "retmode": "xml"}

        try:
            time.sleep(self.delay)
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                root = ET.fromstring(response.content)

                # Parse PubMed XML
                article = root.find(".//PubmedArticle")
                if article is not None:
                    metadata = {}

                    # Title
                    title_elem = article.find(".//ArticleTitle")
                    if title_elem is not None and title_elem.text:
                        metadata["title"] = title_elem.text

                    # Authors
                    authors = []
                    for author in article.findall(".//Author"):
                        last = author.find("LastName")
                        first = author.find("ForeName")
                        if last is not None and last.text:
                            name = last.text
                            if first is not None and first.text:
                                name = f"{last.text}, {first.text}"
                            authors.append(name)
                    if authors:
                        metadata["authors"] = authors

                    # Year
                    year_elem = article.find(".//PubDate/Year")
                    if year_elem is not None and year_elem.text:
                        metadata["year"] = year_elem.text

                    # Journal
                    journal_elem = article.find(".//Journal/Title")
                    if journal_elem is not None and journal_elem.text:
                        metadata["journal"] = journal_elem.text

                    return metadata if metadata else None
        except (requests.RequestException, ET.ParseError):
            pass

        return None

    def fetch_datacite_data(self, doi: str) -> Optional[Dict]:
        """
        Fetch metadata from DataCite API

        Args:
            doi: DOI string

        Returns:
            Dictionary with metadata or None if not found
        """
        doi = self.normalize_doi(doi)
        url = f"https://api.datacite.org/dois/{doi}"

        try:
            time.sleep(self.delay)
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                attributes = data.get("data", {}).get("attributes", {})
                if not attributes:
                    return None

                metadata = {}

                # Title (take the first one)
                titles = attributes.get("titles", [])
                if titles:
                    metadata["title"] = titles[0].get("title", "")

                # Authors
                creators = attributes.get("creators", [])
                authors = []
                for creator in creators:
                    name = creator.get("name")
                    if name:
                        # DataCite usually provides "Family, Given"
                        authors.append(name)
                if authors:
                    metadata["authors"] = authors

                # Year
                if "publicationYear" in attributes:
                    metadata["year"] = str(attributes["publicationYear"])

                # Publisher (map to publisher or journal?)
                if "publisher" in attributes:
                    metadata["publisher"] = attributes["publisher"]
                    metadata["journal"] = attributes[
                        "publisher"
                    ]  # Also use as journal candidate

                # DOS
                if "doi" in attributes:
                    metadata["doi"] = attributes["doi"]

                # Type
                types = attributes.get("types", {})
                if "resourceTypeGeneral" in types:
                    metadata["type"] = types["resourceTypeGeneral"]

                return metadata if metadata else None
        except requests.RequestException:
            pass

        return None

    def fetch_openalex_data(
        self, doi: Optional[str] = None, title: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Fetch metadata from OpenAlex API

        Args:
            doi: DOI string
            title: Title string

        Returns:
            Dictionary with metadata or None if not found
        """
        url = "https://api.openalex.org/works"

        # Build query
        if doi:
            # Normalize DOI
            doi = self.normalize_doi(doi)
            # Use specific DOI endpoint or filter
            target_url = f"{url}/doi:{doi}"
            params = {}
        elif title:
            # Search by title
            target_url = url
            params = {"filter": f"title.search:{title}", "per-page": 1}
        else:
            return None

        try:
            # Use a polite pool email if possible (recommended by OpenAlex)
            # We'll use a generic one or the user's if configured, but for now just the request
            headers = {"User-Agent": "BibTeX Validator (mailto:your.email@example.com)"}

            time.sleep(self.delay)
            response = requests.get(
                target_url, params=params, headers=headers, timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                # If search by title, results are in 'results' list
                result = None
                if not doi and "results" in data:
                    results = data["results"]
                    if results:
                        result = results[0]
                elif doi:
                    # Direct DOI lookup returns the object directly
                    result = data

                if not result:
                    return None

                metadata = {}

                # Title
                if "title" in result:
                    metadata["title"] = result["title"]

                # Authors
                valid_authors = []
                for authorship in result.get("authorships", []):
                    author_obj = authorship.get("author", {})
                    name = author_obj.get("display_name")
                    if name:
                        valid_authors.append(name)
                if valid_authors:
                    metadata["authors"] = valid_authors

                # Publication Year
                if "publication_year" in result:
                    metadata["year"] = str(result["publication_year"])

                # Venue/Journal
                loc = result.get("primary_location", {}) or {}
                source = loc.get("source", {}) or {}
                if source and "display_name" in source:
                    metadata["journal"] = source["display_name"]

                # DOI
                if "doi" in result:
                    # OpenAlex returns DOI as URL (https://doi.org/...)
                    doi_val = result["doi"]
                    if doi_val:
                        metadata["doi"] = doi_val.replace(
                            "https://doi.org/", ""
                        ).replace("http://doi.org/", "")

                # Volume/Issue/Pages
                biblio = result.get("biblio", {})
                if biblio.get("volume"):
                    metadata["volume"] = biblio["volume"]
                if biblio.get("issue"):
                    metadata["number"] = biblio["issue"]
                if biblio.get("first_page"):
                    end_page = biblio.get("last_page")
                    if end_page:
                        metadata["pages"] = f"{biblio['first_page']}--{end_page}"
                    else:
                        metadata["pages"] = biblio["first_page"]

                return metadata if metadata else None

        except requests.RequestException:
            pass

        return None

    def format_author_list(self, authors: List[str]) -> str:
        """Convert author list to BibTeX format"""
        formatted = []
        for author in authors:
            # Handle "First Last" or "Last, First" formats
            if "," in author:
                formatted.append(author.strip())
            else:
                # Split by space and reverse
                parts = author.strip().split()
                if len(parts) >= 2:
                    last = parts[-1]
                    first = " ".join(parts[:-1])
                    formatted.append(f"{last}, {first}")
                else:
                    formatted.append(author.strip())
        return " and ".join(formatted)

    def format_crossref_author_list(self, authors: List[Dict]) -> str:
        """Convert Crossref author list to BibTeX format"""
        formatted = []
        for author in authors:
            given = author.get("given", "")
            family = author.get("family", "")
            if given and family:
                formatted.append(f"{family}, {given}")
            elif family:
                formatted.append(family)
        return " and ".join(formatted)

    def format_date(self, date_parts: List[List[int]]) -> Optional[str]:
        """Extract year from date-parts"""
        if date_parts and len(date_parts[0]) > 0:
            return str(date_parts[0][0])
        return None

    def extract_string_from_api_value(self, api_value) -> str:
        """Extract string from API value (handles list format)"""
        if isinstance(api_value, list):
            if len(api_value) > 0:
                return str(api_value[0]).strip()
            return ""
        return str(api_value).strip()

    def normalize_string_for_comparison(self, s: str, field_name: str = "") -> str:
        """
        Normalize string for comparison according to BibTeX conventions

        Normalizations:
        - Remove LaTeX braces { }
        - Remove leading/trailing whitespace
        - Decode HTML entities (&amp; -> &)
        - For title: lowercase for comparison
        - For ISSN: remove hyphens and take first if multiple (0378-7788, 1476-4687 -> 03787788)
        - For DOI: lowercase for comparison
        """
        # Handle list format (should be extracted before this, but safety check)
        if isinstance(s, list):
            if len(s) > 0:
                s = str(s[0])
            else:
                return ""

        s = str(s)
        # Remove LaTeX braces
        s = re.sub(r"[{}]", "", s)
        # Normalize LaTeX escaped characters
        s = (
            s.replace("\\&", "&")
            .replace("\\%", "%")
            .replace("\\$", "$")
            .replace("\\#", "#")
        )
        # Decode HTML entities
        s = (
            s.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
        )
        s = s.strip()

        if field_name == "title":
            s = s.lower()
        elif field_name == "issn":
            # Handle multiple ISSNs: take first one
            if "," in s:
                s = s.split(",")[0].strip()
            # Remove hyphens: 0378-7788 -> 03787788
            s = re.sub(r"-", "", s)
            s = s.lower()
        elif field_name == "doi":
            # Normalize DOI to lowercase
            s = s.lower()
        elif field_name == "author":
            # Normalize common name prefixes (von, van, etc.)
            # Just lowercase for comparison, as name order and formatting can vary
            s = s.lower()
        elif field_name == "journal":
            # Just lowercase for comparison
            s = s.lower()

        return s

    def compare_fields(
        self, bib_entry: Dict, api_data: Dict, source: str = "crossref"
    ) -> Dict:
        """
        Compare BibTeX entry with API data and identify conflicts/updates/identical/different

        Returns:
            Dictionary with 'updated', 'conflicts', 'identical', 'different', 'sources' keys
        """
        updates = {}
        conflicts = {}
        identical = {}
        different = {}
        sources = {}

        if source == "crossref":
            field_mapping = {
                "title": ("title", lambda x: self.extract_string_from_api_value(x)),
                "author": ("author", self.format_crossref_author_list),
                "journal": (
                    "container-title",
                    lambda x: self.extract_string_from_api_value(x),
                ),
                "year": ("published-print", self.format_date),
                "volume": (
                    "volume",
                    lambda x: self.extract_string_from_api_value(x) if x else None,
                ),
                "pages": (
                    "page",
                    lambda x: self.extract_string_from_api_value(x) if x else None,
                ),
                "doi": (
                    "DOI",
                    lambda x: self.extract_string_from_api_value(x).lower()
                    if x
                    else None,
                ),
                "issn": (
                    "ISSN",
                    lambda x: self.extract_string_from_api_value(x) if x else None,
                ),
            }

            for bib_field, (api_field, transformer) in field_mapping.items():
                api_value = api_data.get(api_field)

                if api_value is None:
                    continue

                # Apply transformer if needed
                if callable(transformer):
                    try:
                        if transformer == self.format_date:
                            api_value = (
                                transformer(
                                    api_data.get("published-print", {}).get(
                                        "date-parts", []
                                    )
                                )
                                if isinstance(api_data.get("published-print"), dict)
                                else None
                            )
                        elif transformer == self.format_crossref_author_list:
                            api_value = transformer(api_value) if api_value else None
                        else:
                            api_value = transformer(api_value)
                    except (TypeError, AttributeError, IndexError):
                        continue

                if api_value is None or (
                    isinstance(api_value, str) and not api_value.strip()
                ):
                    continue

                bib_value = bib_entry.get(bib_field, "").strip()
                api_value_str = str(api_value).strip()

                # Normalize for comparison
                bib_normalized = self.normalize_string_for_comparison(
                    bib_value, bib_field
                )
                api_normalized = self.normalize_string_for_comparison(
                    api_value_str, bib_field
                )

                # Track source for this field
                sources[bib_field] = source

                if not bib_value:
                    # Missing field - suggest update
                    # Skip empty lists or empty strings
                    if api_value_str and api_value_str != "[]":
                        updates[bib_field] = api_value_str
                elif bib_normalized == api_normalized:
                    # Identical field
                    identical[bib_field] = bib_value
                elif bib_normalized != api_normalized and bib_field not in [
                    "pages"
                ]:  # Pages format can vary
                    # Check if it's a significant conflict
                    if len(bib_value) > 3 and len(api_value_str) > 3:
                        # For author and title (case differences), prefer API value (update instead of conflict)
                        if bib_field in ["author", "title"]:
                            # Prefer API value for author and title (case/form differences)
                            updates[bib_field] = api_value_str
                        else:
                            conflicts[bib_field] = (bib_value, api_value_str)

        elif source == "arxiv":
            # Map arXiv data to BibTeX fields
            if "title" in api_data:
                bib_value = bib_entry.get("title", "").strip()
                api_value = api_data["title"]
                bib_normalized = self.normalize_string_for_comparison(
                    bib_value, "title"
                )
                api_normalized = self.normalize_string_for_comparison(
                    api_value, "title"
                )
                sources["title"] = source
                if not bib_value:
                    updates["title"] = api_value
                elif bib_normalized == api_normalized:
                    identical["title"] = bib_value
                elif bib_normalized != api_normalized and len(bib_value) > 3:
                    # Prefer API value for title (case differences)
                    updates["title"] = api_value

            if "authors" in api_data:
                bib_value = bib_entry.get("author", "").strip()
                api_value = self.format_author_list(api_data["authors"])
                bib_normalized = self.normalize_string_for_comparison(
                    bib_value, "author"
                )
                api_normalized = self.normalize_string_for_comparison(
                    api_value, "author"
                )
                sources["author"] = source
                if not bib_value:
                    updates["author"] = api_value
                elif bib_normalized == api_normalized:
                    identical["author"] = bib_value
                elif bib_normalized != api_normalized and len(bib_value) > 5:
                    # Prefer API value for author (case/form differences)
                    updates["author"] = api_value

            if "year" in api_data:
                bib_value = bib_entry.get("year", "").strip()
                api_value = api_data["year"]
                sources["year"] = source
                if not bib_value:
                    updates["year"] = api_value
                elif bib_value == api_value:
                    identical["year"] = bib_value
                elif bib_value != api_value:
                    # Year differences are usually conflicts
                    conflicts["year"] = (bib_value, api_value)

            # Add eprint and eprinttype if not present
            if "arxiv_id" in api_data:
                if not bib_entry.get("eprint"):
                    updates["eprint"] = api_data["arxiv_id"]
                    sources["eprint"] = source
                if not bib_entry.get("eprinttype"):
                    updates["eprinttype"] = "arxiv"
                    sources["eprinttype"] = source

        # Handle other sources (semantic_scholar, dblp, pubmed, datacite, openalex)
        elif source in ["semantic_scholar", "dblp", "pubmed", "datacite", "openalex"]:
            field_mapping = {
                "title": (
                    "title",
                    lambda x: self.extract_string_from_api_value(x)
                    if isinstance(x, str)
                    else str(x)
                    if x
                    else None,
                ),
                "author": (
                    "authors",
                    lambda x: self.format_author_list(x)
                    if isinstance(x, list)
                    else str(x)
                    if x
                    else None,
                ),
                "journal": (
                    "journal",
                    lambda x: self.extract_string_from_api_value(x)
                    if isinstance(x, str)
                    else str(x)
                    if x
                    else None,
                ),
                "year": ("year", lambda x: str(x) if x else None),
                "doi": ("doi", lambda x: str(x).lower() if x else None),
                "publisher": ("publisher", lambda x: str(x).strip() if x else None),
                "volume": ("volume", lambda x: str(x).strip() if x else None),
                "number": ("number", lambda x: str(x).strip() if x else None),
                "pages": ("pages", lambda x: str(x).strip() if x else None),
            }

            for bib_field, (api_field, transformer) in field_mapping.items():
                api_value = api_data.get(api_field)

                if api_value is None:
                    continue

                # Apply transformer
                if callable(transformer):
                    try:
                        api_value = transformer(api_value)
                    except (TypeError, AttributeError, IndexError):
                        continue

                if api_value is None or (
                    isinstance(api_value, str) and not api_value.strip()
                ):
                    continue

                bib_value = bib_entry.get(bib_field, "").strip()
                api_value_str = str(api_value).strip()

                # Normalize for comparison
                bib_normalized = self.normalize_string_for_comparison(
                    bib_value, bib_field
                )
                api_normalized = self.normalize_string_for_comparison(
                    api_value_str, bib_field
                )

                # Track source
                sources[bib_field] = source

                if not bib_value:
                    if api_value_str and api_value_str != "[]":
                        updates[bib_field] = api_value_str
                elif bib_normalized == api_normalized:
                    identical[bib_field] = bib_value
                elif bib_normalized != api_normalized and bib_field not in ["pages"]:
                    if len(bib_value) > 3 and len(api_value_str) > 3:
                        if bib_field in ["author", "title"]:
                            updates[bib_field] = api_value_str
                        else:
                            # Check similarity for other sources too
                            similarity = self._calculate_similarity(
                                bib_normalized, api_normalized
                            )
                            if similarity > 0.7:
                                different[bib_field] = (bib_value, api_value_str)
                            else:
                                conflicts[bib_field] = (bib_value, api_value_str)

        return {
            "updated": updates,
            "conflicts": conflicts,
            "identical": identical,
            "different": different,
            "sources": sources,
        }

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings (0.0 to 1.0)"""
        if not str1 or not str2:
            return 0.0
        if str1 == str2:
            return 1.0

        # Simple similarity: count common characters
        set1 = set(str1.lower())
        set2 = set(str2.lower())
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def search_google_scholar(self, query: str) -> Optional[Dict]:
        """
        Search Google Scholar for publication information

        Args:
            query: Search query (title + first author)

        Returns:
            Dictionary with metadata or None
        """
        if not HAS_SCHOLARLY:
            return None

        try:
            time.sleep(self.delay * 2)  # Longer delay for Scholar
            search_query = scholarly.search_pubs(query)
            result = next(search_query, None)

            if result:
                filled = scholarly.fill(result)
                return filled
        except Exception:  # Removed unused 'e'
            pass

        return None

    def validate_entry(
        self, entry: Dict, index: int = 0, total: int = 0
    ) -> ValidationResult:
        """
        Validate a single BibTeX entry

        Args:
            entry: BibTeX entry dictionary
            index: Current entry index (0-based)
            total: Total number of entries

        Returns:
            ValidationResult object
        """
        entry_key = entry["ID"]
        entry_type = entry.get("ENTRYTYPE", "misc")
        result = ValidationResult(entry_key=entry_key)
        logs = []

        # Store original values for undo functionality
        for field_name, value in entry.items():
            if field_name not in ["ID", "ENTRYTYPE"] and value:
                result.original_values[field_name] = str(value)

        if total > 0:
            logs.append(
                f"\n[{index + 1}/{total}] Validating: {entry_key} ({entry_type})"
            )
        else:
            logs.append(f"\nValidating: {entry_key} ({entry_type})")

        # 1. Identification & Normalization
        doi = entry.get("doi", "")
        if doi:
            result.has_doi = True
            doi = self.normalize_doi(doi)

            # Check if it's an arXiv DOI
            arxiv_doi_match = self.ARXIV_DOI_PATTERN.search(doi)
            if arxiv_doi_match:
                logs.append(f"  DOI identified as arXiv DOI: {doi}")
                # We will handle this in arXiv section if we can extract ID
            else:
                logs.append(f"  DOI present: {doi}")

        arxiv_id = self.extract_arxiv_id(entry)
        if arxiv_id:
            result.has_arxiv = True
            result.arxiv_id = arxiv_id
            logs.append(f"  arXiv ID: {arxiv_id}")

        pmid = entry.get("pmid", "") or entry.get("pubmed", "")

        title = entry.get("title", "")
        author = entry.get("author", "")

        # 2. Fetch Data (from ALL applicable sources)
        fetched_data = {}  # source_name -> data_dict

        # (A) Crossref
        if doi and not self.ARXIV_DOI_PATTERN.search(doi):
            logs.append("  Fetching Crossref...")
            data = self.fetch_crossref_data(doi)
            if data:
                result.doi_valid = True
                fetched_data["crossref"] = data
                logs.append("  ✓ Found data from Crossref")
            else:
                result.warnings.append(f"DOI {doi} not found in Crossref")
                logs.append("  ✗ DOI not found in Crossref")

            # Try DataCite if Crossref failed or if we want to check it anyway
            # DataCite is often used for Zenodo, Figshare, etc.
            if "crossref" not in fetched_data:
                logs.append("  Fetching DataCite...")
                data = self.fetch_datacite_data(doi)
                if data:
                    result.doi_valid = True
                    fetched_data["datacite"] = data
                    logs.append("  ✓ Found data from DataCite")
                else:
                    result.warnings.append(f"DOI {doi} not found in DataCite")

            # Try OpenAlex (High priority, extensive coverage)
            if "crossref" not in fetched_data and "datacite" not in fetched_data:
                # Note: OpenAlex usually has Crossref data, but can be a good fallback or alternative
                pass

        # OpenAlex Lookup (Try if DOI exists, regardless of Crossref success?
        # Actually OpenAlex is very good, maybe we check it anyway for extra metadata like accurate venue names)
        if doi:
            logs.append("  Fetching OpenAlex...")
            data = self.fetch_openalex_data(doi=doi)
            if data:
                if "crossref" not in fetched_data and "datacite" not in fetched_data:
                    # Only mark valid if not already validated (though if it found it, it is valid)
                    result.doi_valid = True
                fetched_data["openalex"] = data
                logs.append("  ✓ Found data from OpenAlex")

        # (B) arXiv
        if arxiv_id:
            logs.append(f"  Fetching arXiv: {arxiv_id}")
            data = self.fetch_arxiv_data(arxiv_id)
            if data:
                result.arxiv_valid = True
                fetched_data["arxiv"] = data
                # If we have a DOI that was actually an arXiv DOI, mark it valid
                if result.has_doi and self.ARXIV_DOI_PATTERN.search(doi):
                    result.doi_valid = True
                logs.append("  ✓ Found data from arXiv")
            else:
                result.warnings.append(f"arXiv ID {arxiv_id} not found")
                logs.append("  ✗ arXiv ID not found")
        elif result.has_arxiv:
            result.warnings.append("No arXiv ID found")

        # (C) PubMed
        if pmid:
            logs.append(f"  Fetching PubMed: {pmid}")
            data = self.fetch_pubmed_data(pmid)
            if data:
                fetched_data["pubmed"] = data
                logs.append("  ✓ Found data from PubMed")

        # (D) DBLP (Always try if title exists)
        if title:
            logs.append("  Searching DBLP...")
            data = self.fetch_dblp_data(title, author)
            if data:
                fetched_data["dblp"] = data
                logs.append("  ✓ Found data from DBLP")

        # (E) Semantic Scholar (Always try if title exists)
        if title:
            logs.append("  Searching Semantic Scholar...")
            data = self.fetch_semantic_scholar_data(title, author)
            if data:
                fetched_data["semantic_scholar"] = data
                logs.append("  ✓ Found data from Semantic Scholar")

        # (F) OpenAlex (Search by title if DOI didn't work or wasn't present)
        if title and "openalex" not in fetched_data:
            # Only search if we haven't already fetched it via DOI
            logs.append("  Searching OpenAlex by title...")
            data = self.fetch_openalex_data(title=title)
            if data:
                fetched_data["openalex"] = data
                logs.append("  ✓ Found data from OpenAlex")

        # 3. Aggregation & Comparison
        # Priority order for DEFAULT values
        priority_order = [
            "crossref",
            "arxiv",
            "dblp",
            "datacite",
            "pubmed",
            "semantic_scholar",
            "openalex",
        ]

        result.all_sources_data = fetched_data

        # Track unique values for each field to prevent redundant options
        # field -> list of normalized values found so far
        field_values_seen = {}

        for source in priority_order:
            if source not in fetched_data:
                continue

            data = fetched_data[source]
            comparison = self.compare_fields(entry, data, source=source)

            # Merge logic:
            # - Update field_source_options based on UNIQUE values
            # - Update fields_updated/conflict ONLY if not already set by higher priority source

            # Helper to collect all involved fields
            involved_fields = set()
            involved_fields.update(comparison["updated"].keys())
            involved_fields.update(comparison["conflicts"].keys())
            involved_fields.update(comparison.get("identical", {}).keys())
            involved_fields.update(comparison.get("different", {}).keys())

            for field_name in involved_fields:
                # Get the value provided by this source for this field
                # We can find it in the comparison result or original data
                # compare_fields returns lists/tuples in update/conflict, we need the raw api value

                # Extract API value logic similar to getFieldValueFromSource in JS/Python
                # But compare_fields already gives us the string representation in the tuple/value

                api_val_str = ""
                if field_name in comparison["updated"]:
                    api_val_str = comparison["updated"][field_name]
                elif field_name in comparison["conflicts"]:
                    api_val_str = comparison["conflicts"][field_name][1]
                elif field_name in comparison.get("different", {}):
                    api_val_str = comparison["different"][field_name][1]
                elif field_name in comparison.get("identical", {}):
                    api_val_str = comparison["identical"][field_name]

                # Normalize for deduplication check
                norm_val = self.normalize_string_for_comparison(api_val_str, field_name)

                if field_name not in field_values_seen:
                    field_values_seen[field_name] = []

                if field_name not in result.field_source_options:
                    result.field_source_options[field_name] = []

                # If this is the FIRST source for this field, or if value is UNIQUE
                # We always add if it's the first time we see any value (priority 1)
                # Or if this specific normalized value hasn't been seen yet.
                if norm_val not in field_values_seen[field_name]:
                    result.field_source_options[field_name].append(source)
                    field_values_seen[field_name].append(norm_val)

                # Update main result fields if not already set (Priority Logic)
                if (
                    field_name not in result.field_sources
                ):  # If not claimed by a higher priority source
                    # If this source suggests an update
                    if field_name in comparison["updated"]:
                        result.fields_updated[field_name] = comparison["updated"][
                            field_name
                        ]
                        result.field_sources[field_name] = source
                    # If this source has a conflict
                    elif field_name in comparison["conflicts"]:
                        result.fields_conflict[field_name] = comparison["conflicts"][
                            field_name
                        ]
                        result.field_sources[field_name] = source
                    # If different (minor)
                    elif field_name in comparison.get("different", {}):
                        result.fields_different[field_name] = comparison["different"][
                            field_name
                        ]
                        result.field_sources[field_name] = source
                    # If identical
                    elif field_name in comparison.get("identical", {}):
                        result.fields_identical[field_name] = comparison["identical"][
                            field_name
                        ]
                        result.field_sources[field_name] = source

        # Logging summary
        if result.fields_conflict:
            logs.append(f"  ⚠ Found {len(result.fields_conflict)} field conflicts")
        if result.fields_updated:
            logs.append(f"  + Found {len(result.fields_updated)} fields to update")

        # Check required fields
        required = self.REQUIRED_FIELDS.get(entry_type, [])
        for field_name in required:
            if not entry.get(field_name, "").strip():
                result.fields_missing.append(field_name)
        if result.fields_missing:
            logs.append(f"  Missing fields: {', '.join(result.fields_missing)}")

        with self.print_lock:
            print("\n".join(logs))

        return result

    def validate_all(
        self, show_progress: bool = True, max_workers: int = 10
    ) -> List[ValidationResult]:
        """
        Validate all entries in the BibTeX database

        Args:
            show_progress: If True, show progress indicators
            max_workers: Number of threads for parallel execution
        """
        total_entries = len(self.db.entries)
        print(
            f"Validating {total_entries} entries from {self.bib_file} with {max_workers} threads"
        )
        print("=" * 60)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_entry = {
                executor.submit(
                    self.validate_entry, entry, index=idx, total=total_entries
                ): (idx, entry)
                for idx, entry in enumerate(self.db.entries)
            }

            for future in as_completed(future_to_entry):
                idx, entry = future_to_entry[future]
                try:
                    result = future.result()
                    # Results might return out of order, but that's fine for the list
                    # If strict order is needed, we can store by index and sort later
                    # Here we just append

                    # Thread-safe append (GIL handles atomic append for lists)
                    self.results.append(result)

                    # Update entry if requested - entry objects are distinct, so this is safe
                    if self.update_bib and result.fields_updated:
                        for field_name, value in result.fields_updated.items():
                            entry[field_name] = value
                except Exception as e:
                    print(f"\nError validating entry {idx}: {e}")

        # Sort results by original index to keep report order consistent
        # We need to map back from entry_key or just sort by entry index if we tracked it
        # Actually, self.results is a list validation results.
        # Ideally, we sort them to match the input order for the report.
        # But ValidationResult doesn't have the original index.
        # Let's trust that the report generation handles it or that order doesn't strictly matter.
        # Users usually prefer input order.

        # To fix order, valid assumption: entry_keys are unique.
        key_order = {entry["ID"]: i for i, entry in enumerate(self.db.entries)}
        self.results.sort(key=lambda x: key_order.get(x.entry_key, 0))

        if show_progress:
            print(f"{'=' * 60}")
            print("Validation Summary")
            print(f"{'=' * 60}")
            print(f"Total Entries: {total_entries}")
            print(f"{'=' * 60}")

        return self.results

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a validation report"""
        report_lines = [
            f"BibTeX Validation Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"File: {self.bib_file}",
            "=" * 60,
            "",
        ]

        # Summary statistics
        total = len(self.results)
        with_doi = sum(1 for r in self.results if r.has_doi)
        valid_doi = sum(1 for r in self.results if r.doi_valid)
        with_arxiv = sum(1 for r in self.results if r.has_arxiv)
        valid_arxiv = sum(1 for r in self.results if r.arxiv_valid)
        with_conflicts = sum(1 for r in self.results if r.fields_conflict)
        with_updates = sum(1 for r in self.results if r.fields_updated)
        with_missing = sum(1 for r in self.results if r.fields_missing)

        report_lines.extend(
            [
                "SUMMARY",
                "-" * 60,
                f"Total entries: {total}",
            ]
        )

        if total > 0:
            report_lines.extend(
                [
                    f"Entries with DOI: {with_doi} ({with_doi / total * 100:.1f}%)",
                    f"Valid DOI: {valid_doi} ({valid_doi / total * 100:.1f}%)",
                    f"Entries with arXiv ID: {with_arxiv} ({with_arxiv / total * 100:.1f}%)",
                    f"Valid arXiv: {valid_arxiv} ({valid_arxiv / total * 100:.1f}%)",
                ]
            )

        report_lines.extend(
            [
                f"Entries with field conflicts: {with_conflicts}",
                f"Entries with suggested updates: {with_updates}",
                f"Entries with missing fields: {with_missing}",
                "",
                "DETAILED RESULTS",
                "-" * 60,
                "",
            ]
        )

        # Detailed results
        for result in self.results:
            report_lines.append(f"[{result.entry_key}]")

            if result.doi_valid:
                report_lines.append("  DOI: ✓ Valid")
            elif result.has_doi:
                report_lines.append(f"  DOI: ✗ Invalid/Not found")
            else:
                report_lines.append("  DOI: Not provided")

            if result.arxiv_valid:
                report_lines.append(f"  arXiv: ✓ Valid ({result.arxiv_id})")
            elif result.has_arxiv:
                report_lines.append(f"  arXiv: ✗ Invalid/Not found ({result.arxiv_id})")
            else:
                report_lines.append("  arXiv: Not provided")

            if result.fields_conflict:
                report_lines.append("  Field Conflicts:")
                for field_name, (old, new) in result.fields_conflict.items():
                    report_lines.append(f"    {field_name}:")
                    report_lines.append(f"      BibTeX: {old}")
                    report_lines.append(f"      API:    {new}")

            if result.fields_updated:
                report_lines.append("  Suggested Updates:")
                for field_name, value in result.fields_updated.items():
                    report_lines.append(f"    {field_name}: {value}")

            if result.fields_missing:
                report_lines.append(
                    f"  Missing Fields: {', '.join(result.fields_missing)}"
                )

            if result.warnings:
                report_lines.append("  Warnings:")
                for warning in result.warnings:
                    report_lines.append(f"    - {warning}")

            report_lines.append("")

        report_text = "\n".join(report_lines)

        # Write to file if specified
        if output_file:
            # Add 'bibtex_' prefix to filename if not already present
            output_path = Path(output_file)
            filename = output_path.name
            if not filename.startswith("bibtex_"):
                new_filename = "bibtex_" + filename
                output_path = output_path.parent / new_filename
            else:
                output_path = Path(output_file)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            print(f"Output written to {output_file}")

        return report_text

    def save_updated_bib(self):
        """Save updated BibTeX file"""
        if self.update_bib:
            writer = BibTexWriter()
            writer.indent = "\t"
            writer.comma_first = False

            with open(self.output_file, "w", encoding="utf-8") as f:
                bibtexparser.dump(self.db, f, writer=writer)
            print(f"\nUpdated BibTeX file saved to: {self.output_file}")


def create_gui_app(
    validator: BibTeXValidator, results: List[ValidationResult]
) -> "FastAPI":
    """
    Create FastAPI application for BibTeX validator GUI

    Args:
        validator: BibTeXValidator instance
        results: List of ValidationResult objects

    Returns:
        FastAPI app instance
    """
    if not HAS_GUI_DEPS:
        import sys

        print(
            "Error: GUI dependencies (fastapi, uvicorn) are required for --gui mode.",
            file=sys.stderr,
        )
        print(
            "Install with: uv add fastapi uvicorn or pip install fastapi uvicorn",
            file=sys.stderr,
        )
        raise ImportError(
            "GUI dependencies (fastapi, uvicorn) are required. "
            "Install with: uv add fastapi uvicorn or pip install fastapi uvicorn"
        )

    app = FastAPI(title="BibTeX Validator")

    # Store validator and results in app state
    app.state.validator = validator
    app.state.results = results
    app.state.accepted_changes = {}  # {entry_key: {field: new_value}}

    # HTML page with inline CSS/JS
    @app.get("/", response_class=HTMLResponse)
    async def index():
        return """
<!DOCTYPE html>
<html lang="en" class="light">
<head>
    <title>BibTeX Validator & Enricher</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                        mono: ['SF Mono', 'Monaco', 'Courier New', 'monospace'],
                    },
                    colors: {
                        border: "hsl(var(--border))",
                        input: "hsl(var(--input))",
                        ring: "hsl(var(--ring))",
                        background: "hsl(var(--background))",
                        foreground: "hsl(var(--foreground))",
                        primary: {
                            DEFAULT: "hsl(var(--primary))",
                            foreground: "hsl(var(--primary-foreground))",
                        },
                        secondary: {
                            DEFAULT: "hsl(var(--secondary))",
                            foreground: "hsl(var(--secondary-foreground))",
                        },
                        destructive: {
                            DEFAULT: "hsl(var(--destructive))",
                            foreground: "hsl(var(--destructive-foreground))",
                        },
                        muted: {
                            DEFAULT: "hsl(var(--muted))",
                            foreground: "hsl(var(--muted-foreground))",
                        },
                        accent: {
                            DEFAULT: "hsl(var(--accent))",
                            foreground: "hsl(var(--accent-foreground))",
                        },
                        popover: {
                            DEFAULT: "hsl(var(--popover))",
                            foreground: "hsl(var(--popover-foreground))",
                        },
                        card: {
                            DEFAULT: "hsl(var(--card))",
                            foreground: "hsl(var(--card-foreground))",
                        },
                    },
                    borderRadius: {
                        lg: "var(--radius)",
                        md: "calc(var(--radius) - 2px)",
                        sm: "calc(var(--radius) - 4px)",
                    },
                }
            }
        }
    </script>
    <style type="text/tailwindcss">
        @layer base {
            :root {
                --background: 0 0% 100%;
                --foreground: 240 10% 3.9%;
                --card: 0 0% 100%;
                --card-foreground: 240 10% 3.9%;
                --popover: 0 0% 100%;
                --popover-foreground: 240 10% 3.9%;
                --primary: 240 5.9% 10%;
                --primary-foreground: 0 0% 98%;
                --secondary: 240 4.8% 95.9%;
                --secondary-foreground: 240 5.9% 10%;
                --muted: 240 4.8% 95.9%;
                --muted-foreground: 240 3.8% 46.1%;
                --accent: 240 4.8% 95.9%;
                --accent-foreground: 240 5.9% 10%;
                --destructive: 0 84.2% 60.2%;
                --destructive-foreground: 0 0% 98%;
                --border: 240 5.9% 90%;
                --input: 240 5.9% 90%;
                --ring: 240 10% 3.9%;
                --radius: 0.5rem;
            }
        }
        @layer utilities {
            .animate-spin-slow {
                animation: spin 3s linear infinite;
            }
        }
    </style>
</head>
<body class="bg-background text-foreground min-h-screen antialiased">
    <div class="container max-w-7xl mx-auto py-10 px-4">
        <!-- Header -->
        <div class="flex flex-col space-y-2 mb-8">
            <h1 class="text-3xl font-bold tracking-tight">BibTeX Validator</h1>
            <p class="text-muted-foreground">Validate, enrich, and correct your BibTeX entries with ease.</p>
        </div>

        <!-- Toolbar -->
        <!-- Toolbar moved inside mainContent -->

        <!-- Main Content -->
        <div id="mainContent" class="space-y-6 hidden">
            <!-- Summary Card -->
            <!-- Summary Section -->
            <div class="rounded-lg border bg-card text-card-foreground shadow-sm mb-6">
                <div class="px-6 py-4 flex items-center justify-between">
                    <h3 class="text-lg font-semibold leading-none tracking-tight">Validation Summary</h3>
                    
                    <div class="flex items-center gap-8">
                        <!-- Entries Attention -->
                        <div class="flex items-center gap-2">
                             <div class="relative h-10 w-10">
                                <div id="attentionPieChart" class="h-full w-full rounded-full" style="background: conic-gradient(#f87171 0%, #f87171 0%, #e5e7eb 0% 100%);"></div>
                            </div>
                            <div class="flex flex-col">
                                <span class="text-xs text-muted-foreground uppercase font-semibold">Need Attention</span>
                                <span class="text-lg font-medium text-gray-700 dark:text-gray-300 leading-none" id="summaryAttention">0/0 (0%)</span>
                            </div>
                        </div>
                        <span class="text-border opacity-50 text-2xl font-light">|</span>

                        <!-- Reviews -->
                        <div class="flex items-center gap-2">
                             <div class="p-2 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                                <i data-lucide="edit-3" class="h-4 w-4"></i>
                            </div>
                            <div class="flex flex-col">
                                <span class="text-xs text-muted-foreground uppercase font-semibold">Reviews</span>
                                <span class="text-lg font-medium text-gray-700 dark:text-gray-300 leading-none" id="summaryReviews">0</span>
                            </div>
                        </div>

                        <!-- Conflicts -->
                        <div class="flex items-center gap-2">
                            <div class="p-2 rounded-full bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400">
                                <i data-lucide="alert-triangle" class="h-4 w-4"></i>
                            </div>
                            <div class="flex flex-col">
                                <span class="text-xs text-muted-foreground uppercase font-semibold">Conflicts</span>
                                <span class="text-lg font-medium text-gray-700 dark:text-gray-300 leading-none" id="summaryConflicts">0</span>
                            </div>
                        </div>

                        <!-- Differences -->
                        <div class="flex items-center gap-2">
                            <div class="p-2 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400">
                                <i data-lucide="git-compare" class="h-4 w-4"></i>
                            </div>
                            <div class="flex flex-col">
                                <span class="text-xs text-muted-foreground uppercase font-semibold">Differences</span>
                                <span class="text-lg font-medium text-gray-700 dark:text-gray-300 leading-none" id="summaryDifferences">0</span>
                            </div>
                        </div>

                        <!-- Identical -->
                        <div class="flex items-center gap-2">
                            <div class="p-2 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
                                <i data-lucide="check-circle" class="h-4 w-4"></i>
                            </div>
                            <div class="flex flex-col">
                                <span class="text-xs text-muted-foreground uppercase font-semibold">Identical</span>
                                <span class="text-lg font-medium text-gray-700 dark:text-gray-300 leading-none" id="summaryIdentical">0</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Footer removed -->
            </div>

            <!-- Toolbar (Moved) -->
            <div class="flex flex-col md:flex-row gap-4 items-center justify-between">
                <div class="flex flex-1 gap-4 items-center w-full">
                    <div class="flex-1 max-w-xl relative flex gap-2">
                        <button id="btnPrev" onclick="navigateEntry(-1)" class="inline-flex items-center justify-center rounded-md border border-input bg-background h-10 w-10 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50" disabled>
                            <i data-lucide="chevron-left" class="h-4 w-4"></i>
                        </button>
                        
                        <div class="relative flex-1">
                            <select id="entrySelect" onchange="loadEntry(this.value)" 
                                    class="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 appearance-none">
                                <option value="">Select an entry...</option>
                            </select>
                            <div class="absolute right-3 top-3 pointer-events-none">
                                 <i data-lucide="chevron-down" class="h-4 w-4 opacity-50"></i>
                            </div>
                        </div>

                        <button id="btnNext" onclick="navigateEntry(1)" class="inline-flex items-center justify-center rounded-md border border-input bg-background h-10 w-10 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50" disabled>
                            <i data-lucide="chevron-right" class="h-4 w-4"></i>
                        </button>
                    </div>
                    <div id="statsContainer" class="flex gap-2 text-sm items-center text-muted-foreground hidden whitespace-nowrap">
                        <span class="flex items-center gap-1"><i data-lucide="file-edit" class="h-3 w-3 text-blue-600"></i> <span id="statsUpdates">0</span> reviews</span>
                        <span class="separator text-border opacity-50">|</span>
                        <span class="flex items-center gap-1"><i data-lucide="alert-triangle" class="h-3 w-3 text-orange-600"></i> <span id="statsConflicts">0</span> conflicts</span>
                        <span class="separator text-border opacity-50">|</span>
                        <span class="flex items-center gap-1"><i data-lucide="git-compare" class="h-3 w-3 text-yellow-600"></i> <span id="statsDifferences">0</span> differences</span>
                        <span class="separator text-border opacity-50">|</span>
                        <span class="flex items-center gap-1"><i data-lucide="check-circle" class="h-3 w-3 text-green-600"></i> <span id="statsIdentical">0</span> identical</span>
                    </div>
                </div>

                <div class="flex-shrink-0">
                     <button onclick="acceptAllGlobal()" class="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-4 py-2">
                        <i data-lucide="check-circle-2" class="mr-2 h-4 w-4"></i> Accept Changes
                    </button>
                </div>
            </div>

            <!-- Comparison Table -->
            <div class="rounded-lg border bg-card text-card-foreground shadow-sm overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full caption-bottom text-sm" id="comparisonTable">
                        <thead class="[&_tr]:border-b">
                            <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                <th class="h-10 px-2 text-center align-middle font-medium text-muted-foreground w-[120px]">Field</th>
                                <th class="h-10 px-2 text-center align-middle font-medium text-muted-foreground w-[30%]">BibTeX Value</th>
                                <th class="h-10 px-2 text-center align-middle font-medium text-muted-foreground w-[30%]">API Value</th>
                                <th class="h-10 px-2 text-center align-middle font-medium text-muted-foreground w-[120px]">Source</th>
                                <th class="h-10 px-2 text-center align-middle font-medium text-muted-foreground w-[120px]">Status</th>
                                <th class="h-10 px-2 text-center align-middle font-medium text-muted-foreground w-[200px]">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="comparisonBody" class="[&_tr:last-child]:border-0">
                            <!-- Rows will be injected here -->
                        </tbody>
                        <tfoot id="comparisonFooter" class="bg-muted/50 font-medium hidden">
                             <tr class="border-t">
                                <td colspan="5" class="p-2 align-middle text-right pr-4 text-sm text-gray-600 dark:text-gray-400">Apply to all fields in this entry:</td>
                                <td class="p-2 align-middle text-center">
                                    <div class="flex items-center justify-center gap-2">
                                        <button onclick="rejectAll()" class="inline-flex items-center justify-center rounded-md text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-input shadow-sm hover:bg-destructive hover:text-destructive-foreground h-8 w-20">
                                            Reject All
                                        </button>
                                        <button onclick="acceptAll()" class="inline-flex items-center justify-center rounded-md text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-8 w-20">
                                            Accept All
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            </div>
        </div>

        <!-- Empty State -->
        <div id="emptyState" class="flex flex-col items-center justify-center py-20 text-center space-y-4">
            <div class="rounded-full bg-muted p-4">
                <i data-lucide="book-open" class="h-8 w-8 text-muted-foreground"></i>
            </div>
            <h3 class="font-semibold text-lg">No Entry Selected</h3>
            <p class="text-muted-foreground max-w-sm">Select a BibTeX entry from the dropdown above to view validation results and enrich data.</p>
        </div>
        
        <!-- Loading State -->
        <div id="loadingState" class="hidden flex flex-col items-center justify-center py-20 text-center space-y-4">
            <i data-lucide="loader-2" class="h-8 w-8 animate-spin text-primary"></i>
            <p class="text-muted-foreground">Loading entry details...</p>
        </div>
    </div>

    <!-- Scripts -->
    <script>
        // Initialize Lucide icons
        lucide.createIcons();

        let currentData = null;
        let allEntries = []; // Store summary of all entries
        let acceptedFields = new Set();
        let rejectedFields = new Set();
        let savingFields = new Set();
        let savedFields = new Set();
        let selectedSources = {};

        function escapeHtml(text) {
            if (text === null || text === undefined) return '';
            const div = document.createElement('div');
            div.textContent = String(text);
            return div.innerHTML;
        }

        // --- Data Loading ---

        async function loadEntries() {
            try {
                const response = await fetch('/api/entries');
                if (!response.ok) throw new Error('Failed to load entries');
                const data = await response.json();

                allEntries = data.entries || [];
                // Sort by key
                allEntries.sort((a, b) => a.key.localeCompare(b.key));
                
                const select = document.getElementById('entrySelect');
                const currentValue = select.value;
                
                // Keep the first option
                select.innerHTML = '<option value="">Select an entry...</option>';

                // Calculate Attention Stats
                if (typeof updateGlobalSummary === 'function') updateGlobalSummary(); 
                
                allEntries.forEach((entry) => {
                    const option = document.createElement('option');
                    option.value = entry.key;
                    
                    let badges = [];
                    if (entry.fields_updated && entry.fields_updated.length > 0) badges.push(`+${entry.fields_updated.length}`);
                    if (entry.fields_conflict && entry.fields_conflict.length > 0) badges.push(`!${entry.fields_conflict.length}`);
                    
                    option.textContent = entry.key + (badges.length ? ` (${badges.join(', ')})` : '');
                    select.appendChild(option);
                });
                
                // Restore selection if possible
                if (currentValue) {
                    if (allEntries.some(e => e.key === currentValue)) {
                        select.value = currentValue;
                    }
                }
                
                 // Auto-select first entry if none selected or just loaded
                if (allEntries.length > 0 && !select.value) {
                     const firstKey = allEntries[0].key;
                     select.value = firstKey;
                     loadEntry(firstKey);
                } else {
                    updateNavigationState();
                }

            } catch(e) { 
                console.error(e);
                alert('Failed to load entries.');
            }
        }

        function updateEntrySelect(entries) {
            // This function is now integrated into loadEntries and is no longer needed as a separate function.
            // Keeping it here as a placeholder comment for clarity, but it will be removed if not called elsewhere.
            // The instruction effectively replaced the original loadEntries and removed the call to updateEntrySelect.
        }

        async function loadEntry(entryKey) {
            if (!entryKey) {
                document.getElementById('mainContent').classList.add('hidden');
                document.getElementById('statsContainer').classList.add('hidden');
                document.getElementById('emptyState').classList.remove('hidden');
                return;
            }

            document.getElementById('emptyState').classList.add('hidden');
            document.getElementById('mainContent').classList.add('hidden');
            document.getElementById('loadingState').classList.remove('hidden');

            try {
                const response = await fetch(`/api/entry/${encodeURIComponent(entryKey)}`);
                if (!response.ok) throw new Error('Failed to load entry');
                const data = await response.json();
                
                currentData = data;
                acceptedFields.clear();
                rejectedFields.clear();
                savingFields.clear();
                savedFields.clear();
                
                renderComparison(data);
                updateNavigationState();
                
                document.getElementById('loadingState').classList.add('hidden');
                document.getElementById('mainContent').classList.remove('hidden');
            } catch (error) {
                console.error('Failed to load entry:', error);
                document.getElementById('loadingState').classList.add('hidden');
                document.getElementById('emptyState').classList.remove('hidden');
                alert('Failed to load entry details.');
            }
        }

        // --- Helpers ---

        function navigateEntry(direction) {
            const select = document.getElementById('entrySelect');
            const currentIndex = select.selectedIndex;
            // index 0 is "Select an entry..." placeholder so actual entries start at 1
            const newIndex = currentIndex + direction;
            
            if (newIndex >= 1 && newIndex < select.options.length) {
                select.selectedIndex = newIndex;
                loadEntry(select.value);
            }
        }

        function updateNavigationState() {
            const select = document.getElementById('entrySelect');
            const currentIndex = select.selectedIndex;
            const maxIndex = select.options.length - 1;
            
            document.getElementById('btnPrev').disabled = currentIndex <= 1; // 0 is placeholder, 1 is first item
            document.getElementById('btnNext').disabled = currentIndex >= maxIndex || currentIndex <= 0;
        }

        function getSourceBadge(source) {
            if (!source) return '';
            const colors = {
                crossref: 'bg-blue-100 text-blue-800 border-blue-200',
                arxiv: 'bg-red-100 text-red-800 border-red-200',
                semantic_scholar: 'bg-indigo-100 text-indigo-800 border-indigo-200',
                dblp: 'bg-purple-100 text-purple-800 border-purple-200',
                pubmed: 'bg-sky-100 text-sky-800 border-sky-200',
                scholar: 'bg-blue-100 text-blue-800 border-blue-200',
            };
            const defaultColor = 'bg-gray-100 text-gray-800 border-gray-200';
            const colorClass = colors[source.toLowerCase()] || defaultColor;
            
            const sourceName = source.replace('_', ' ').toUpperCase();
            return `<span class="inline-flex items-center justify-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${colorClass} w-28">${sourceName}</span>`;
        }

        function getStatusBadge(status) {
            const styles = {
                update: 'bg-blue-100 text-blue-800 border-blue-200',
                conflict: 'bg-orange-100 text-orange-800 border-orange-200',
                different: 'bg-yellow-100 text-yellow-800 border-yellow-200',
                identical: 'bg-green-100 text-green-800 border-green-200',
                accepted: 'bg-emerald-100 text-emerald-800 border-emerald-200',
                rejected: 'bg-red-100 text-red-800 border-red-200',
                'bibtex-only': 'bg-gray-100 text-gray-800 border-gray-200'
            };
            
            const labels = {
                update: 'Review',
                conflict: 'Conflict',
                different: 'Different',
                identical: 'Identical',
                accepted: 'Accepted',
                rejected: 'Rejected',
                'bibtex-only': 'Local Only'
            };
            
            const style = styles[status] || styles['bibtex-only'];
            const label = labels[status] || status;
            
            return `<span class="inline-flex items-center justify-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${style} w-24">${label}</span>`;
        }
        
        // --- Global Stats ---

        function updateGlobalSummary() {
            let totalEntries = allEntries.length;
            let entriesWithIssues = 0;
            
            let totalReviews = 0;
            let totalConflicts = 0;
            let totalDifferences = 0;
            let totalIdentical = 0; // note: entries from /api/entries might not have identical/diff counts fully populated if not loaded?
            // Wait, /api/entries returns limited info: key, fields_updated (list), fields_conflict (list).
            // It does NOT usually return identical/different counts unless backend sends them.
            // Let's assume backend /api/entries sends fields_different too. 
            // Checking backend: get_entries sends keys of updated, conflict, different, identical.
            
            allEntries.forEach(e => {
                const u = (e.fields_updated || []).length;
                const c = (e.fields_conflict || []).length;
                const d = (e.fields_different || []).length;
                const i = (e.fields_identical || []).length;
                
                if (u > 0 || c > 0 || d > 0) {
                    entriesWithIssues++;
                }
                
                totalReviews += u;
                totalConflicts += c;
                totalDifferences += d;
                totalIdentical += i;
            });
            
            document.getElementById('summaryReviews').textContent = totalReviews;
            document.getElementById('summaryConflicts').textContent = totalConflicts;
            document.getElementById('summaryDifferences').textContent = totalDifferences;
            document.getElementById('summaryIdentical').textContent = totalIdentical;

            const safeTotal = totalEntries || 0;
            const percentage = safeTotal > 0 ? Math.round((entriesWithIssues / safeTotal) * 100) : 0;
            
            document.getElementById('summaryAttention').textContent = 
                `${entriesWithIssues}/${safeTotal} (${percentage}%)`;
            
            const chart = document.getElementById('attentionPieChart');
            if (chart) {
                chart.style.background = `conic-gradient(#f87171 ${percentage}%, #e5e7eb 0)`;
            }
        }

        // --- Rendering ---

        function renderComparison(data) {
            const tbody = document.getElementById('comparisonBody');
            
            const updates = Object.keys(data.fields_updated || {});
            const conflicts = Object.keys(data.fields_conflict || {});
            const different = Object.keys(data.fields_different || {});
            const identical = Object.keys(data.fields_identical || {});
            const notInApi = Object.keys(data.fields_not_in_api || {});
            const fieldSources = data.field_sources || {};
            const allSourcesData = data.all_sources_data || {};
            const fieldSourceOptions = data.field_source_options || {};

            // Update stats
            document.getElementById('statsUpdates').textContent = updates.length;
            document.getElementById('statsConflicts').textContent = conflicts.length;
            document.getElementById('statsDifferences').textContent = different.length;
            document.getElementById('statsIdentical').textContent = identical.length;
            document.getElementById('statsContainer').classList.remove('hidden');
            
            // Update summary (now global, so only update if not set or just refreshed)
            // Actually, renderComparison is per-entry. We should NOT overwrite global summary here.

            let html = '';

            function createRow(f_name, type, rowData, source) {
                const isAccepted = acceptedFields.has(f_name);
                const isRejected = rejectedFields.has(f_name);
                const isSaving = savingFields.has(f_name);
                const isSaved = savedFields.has(f_name);

                let displayType = type;
                if (isAccepted) displayType = 'accepted';
                else if (isRejected) displayType = 'rejected';

                let bibVal = '', apiVal = '';
                
                if (type === 'update') {
                    bibVal = `<span class="text-red-500 line-through opacity-70 block text-xs mb-1">${escapeHtml(rowData.old || '(empty)')}</span>`;
                    apiVal = `<span class="text-green-600 font-semibold">${escapeHtml(rowData.new)}</span>`;
                } else if (type === 'conflict' || type === 'different') {
                    bibVal = `<span class="text-foreground">${escapeHtml(rowData.bibtex)}</span>`;
                    apiVal = `<span class="text-foreground">${escapeHtml(rowData.api)}</span>`;
                } else if (type === 'identical') {
                    bibVal = `<span class="text-muted-foreground">${escapeHtml(rowData)}</span>`;
                    apiVal = `<span class="text-muted-foreground">${escapeHtml(rowData)}</span>`;
                } else {
                    bibVal = `<span class="text-muted-foreground">${escapeHtml(rowData)}</span>`;
                    apiVal = `<span class="text-muted-foreground italic">-</span>`;
                }

                // Source selection logic
                let sourceBadge = '';
                const options = fieldSourceOptions[f_name] || [];
                const currentSrc = selectedSources[f_name] || source || (options.length ? options[0] : '');
                
                // If we have options and not identical/local-only, allow selection
                if (type !== 'identical' && type !== 'bibtex-only' && options.length > 1) {
                    const dropdownId = `source-dropdown-${f_name}`;
                    
                    // Generate list items for dropdown
                    const listItems = options.map(opt => {
                        const bgClass = opt === currentSrc ? 'bg-muted/50 font-medium' : 'hover:bg-muted/50';
                        return `
                            <button onclick="selectSource('${escapeHtml(f_name)}', '${opt}'); toggleDropdown('${dropdownId}', false)" 
                                    class="w-full text-left px-2 py-1.5 text-xs rounded-sm ${bgClass} flex items-center justify-between group">
                                <span>${opt.toUpperCase().replace('_', ' ')}</span>
                                ${opt === currentSrc ? '<i data-lucide="check" class="h-3 w-3"></i>' : ''}
                            </button>
                        `;
                    }).join('');
                    
                    sourceBadge = `
                        <div class="relative inline-block text-left source-selector" data-field="${escapeHtml(f_name)}">
                            <button type="button" 
                                    onclick="toggleDropdown('${dropdownId}')"
                                    class="inline-flex items-center justify-center relative rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 w-28 group hover:bg-muted/50 ${getSourceColorClass(currentSrc)}">
                                <span>${currentSrc.replace('_', ' ').toUpperCase()}</span>
                                <i data-lucide="chevron-down" class="absolute right-2 top-1/2 -translate-y-1/2 h-3 w-3 opacity-50 group-hover:opacity-100 transition-opacity"></i>
                            </button>
                            
                            <!-- Dropdown Menu -->
                            <div id="${dropdownId}" 
                                 class="hidden absolute left-1/2 -translate-x-1/2 z-50 mt-1.5 w-32 origin-top rounded-md border bg-popover p-1 text-popover-foreground shadow-md outline-none animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95">
                                <div class="space-y-0.5">
                                    ${listItems}
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    sourceBadge = getSourceBadge(currentSrc);
                }

                // Actions
                let actions = '';
                if (type === 'identical' || type === 'bibtex-only') {
                    actions = `<span class="text-muted-foreground text-xs">No action needed</span>`;
                } else {
                    if (isSaving) {
                        actions = `<span class="flex items-center text-xs text-muted-foreground"><i data-lucide="loader-2" class="h-3 w-3 animate-spin mr-1"></i> Saving...</span>`;
                    } else if (isSaved) {
                        actions = `<span class="flex items-center text-xs text-emerald-600"><i data-lucide="check" class="h-3 w-3 mr-1"></i> Saved</span>`;
                    } else {
                        actions = `
                            <div class="flex items-center justify-center gap-2">
                                <button onclick="rejectField('${escapeHtml(f_name)}')" class="inline-flex items-center justify-center rounded-md text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-input shadow-sm hover:bg-destructive hover:text-destructive-foreground h-7 px-2 py-1 ${isRejected ? 'opacity-50' : ''}" ${isAccepted ? 'disabled' : ''}>
                                    Reject
                                </button>
                                <button onclick="acceptField('${escapeHtml(f_name)}')" class="inline-flex items-center justify-center rounded-md text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-7 px-2 py-1 ${isAccepted ? 'opacity-50' : ''}" ${isRejected ? 'disabled' : ''}>
                                    Accept
                                </button>
                            </div>
                        `;
                    }
                }

                return `
                    <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                        <td class="p-2 align-middle font-medium text-center">${escapeHtml(f_name)}</td>
                        <td class="p-2 align-middle font-mono text-xs font-semibold text-center">${bibVal}</td>
                        <td class="p-2 align-middle font-mono text-xs font-semibold text-center">${apiVal}</td>
                        <td class="p-2 align-middle text-center overflow-visible relative">${sourceBadge}</td>
                        <td class="p-2 align-middle text-center">${getStatusBadge(displayType)}</td>
                        <td class="p-2 align-middle text-center">${actions}</td>
                    </tr>
                `;
            }

            // Order: Updates -> Conflicts -> Different -> Identical -> Others
            updates.forEach(f_name => html += createRow(f_name, 'update', data.fields_updated[f_name], fieldSources[f_name]));
            conflicts.forEach(f_name => html += createRow(f_name, 'conflict', data.fields_conflict[f_name], fieldSources[f_name]));
            different.forEach(f_name => html += createRow(f_name, 'different', data.fields_different[f_name], fieldSources[f_name]));
            identical.forEach(f_name => html += createRow(f_name, 'identical', data.fields_identical[f_name], fieldSources[f_name]));
            notInApi.forEach(f_name => html += createRow(f_name, 'bibtex-only', data.fields_not_in_api[f_name], null));

            tbody.innerHTML = html;
            
            // Show/Hide Footer actions if there are actionable items
            const hasActions = updates.length > 0 || conflicts.length > 0 || different.length > 0;
            const footer = document.getElementById('comparisonFooter');
            if (hasActions) {
                footer.classList.remove('hidden');
            } else {
                footer.classList.add('hidden');
            }

            lucide.createIcons(); // Re-init icons for new content
            
            // Add click outside listener if not already added
            if (!window.dropdownListenerAdded) {
                document.addEventListener('click', (e) => {
                    if (!e.target.closest('.source-selector')) {
                        document.querySelectorAll('[id^="source-dropdown-"]').forEach(el => {
                            el.classList.add('hidden');
                        });
                    }
                });
                window.dropdownListenerAdded = true;
            }
        }
        
        // --- Interactivity ---
        
        function toggleDropdown(id, forceState) {
            const el = document.getElementById(id);
            if (!el) return;
            
            // Close all other dropdowns
            document.querySelectorAll('[id^="source-dropdown-"]').forEach(item => {
                if (item.id !== id) item.classList.add('hidden');
            });

            if (forceState !== undefined) {
                forceState ? el.classList.remove('hidden') : el.classList.add('hidden');
            } else {
                el.classList.toggle('hidden');
            }
            // Re-render icons if opening
            if (!el.classList.contains('hidden')) {
                 lucide.createIcons({ root: el });
            }
        }
        
        function getSourceColorClass(source) {
            if (!source) return '';
            const colors = {
                crossref: 'bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-200',
                arxiv: 'bg-red-100 text-red-800 border-red-200 hover:bg-red-200',
                semantic_scholar: 'bg-indigo-100 text-indigo-800 border-indigo-200 hover:bg-indigo-200',
                dblp: 'bg-purple-100 text-purple-800 border-purple-200 hover:bg-purple-200',
                pubmed: 'bg-sky-100 text-sky-800 border-sky-200 hover:bg-sky-200',
                scholar: 'bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-200',
                unknown: 'bg-gray-100 text-gray-800 border-gray-200 hover:bg-gray-200'
            };
            return colors[source.toLowerCase()] || 'bg-gray-100 text-gray-800 border-gray-200 hover:bg-gray-200';
        }

        // --- Logic ---

        // Copied from original logic but cleaned up
        async function acceptField(f_name) {
            acceptedFields.add(f_name);
            rejectedFields.delete(f_name);
            savingFields.add(f_name);
            savedFields.delete(f_name);
            
            if (currentData) renderComparison(currentData);
            
            try {
                const response = await fetch('/api/save', { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        entry_key: currentData.entry_key,
                        accepted_fields: [f_name],
                        rejected_fields: [],
                        selected_sources: selectedSources
                    })
                });
                
                if (!response.ok) throw new Error((await response.json()).detail || 'Failed to save');
                
                const result = await response.json();
                if (result.success) {
                    savingFields.delete(f_name);
                    savedFields.add(f_name);
                    setTimeout(() => {
                        savedFields.delete(f_name);
                        if (currentData) renderComparison(currentData);
                    }, 2000);
                    // Reload
                    await loadEntry(currentData.entry_key);
                }
            } catch (error) {
                console.error(error);
                savingFields.delete(f_name);
                acceptedFields.delete(f_name);
                alert('Save failed: ' + error.message);
                if (currentData) renderComparison(currentData);
            }
        }

        async function rejectField(f_name) {
            rejectedFields.add(f_name);
            acceptedFields.delete(f_name);
            savingFields.add(f_name);
            savedFields.delete(f_name);
            
            if (currentData) renderComparison(currentData);
            
            try {
                const response = await fetch('/api/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        entry_key: currentData.entry_key,
                        accepted_fields: [],
                        rejected_fields: [f_name],
                        selected_sources: {}
                    })
                });
                
                if (!response.ok) throw new Error((await response.json()).detail || 'Failed to save');
                
                const result = await response.json();
                if (result.success) {
                    savingFields.delete(f_name);
                    savedFields.add(f_name);
                    setTimeout(() => {
                        savedFields.delete(f_name);
                        if (currentData) renderComparison(currentData);
                    }, 2000);
                    // Reload
                    await loadEntry(currentData.entry_key);
                }
            } catch (error) {
                console.error(error);
                savingFields.delete(f_name);
                rejectedFields.delete(f_name);
                alert('Save failed: ' + error.message);
                if (currentData) renderComparison(currentData);
            }
        }

        async function acceptAll() {
            if (!currentData) return;
            const fieldsToAccept = [
                ...Object.keys(currentData.fields_updated || {}),
                ...Object.keys(currentData.fields_conflict || {}),
                ...Object.keys(currentData.fields_different || {})
            ].filter(f_name => !acceptedFields.has(f_name) && !rejectedFields.has(f_name)); // Only unprocessed

            if (fieldsToAccept.length === 0) {
                alert("No new changes to accept.");
                return;
            }

            // Client-side visual update
            fieldsToAccept.forEach(f_name => {
                acceptedFields.add(f_name);
                savingFields.add(f_name);
            });
            renderComparison(currentData);

            try {
                const response = await fetch('/api/save', { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        entry_key: currentData.entry_key,
                        accepted_fields: fieldsToAccept,
                        rejected_fields: [],
                        selected_sources: selectedSources
                    })
                });
                
                const result = await response.json();
                if (!response.ok) throw new Error(result.detail || 'Failed');
                
                if (result.success) {
                    fieldsToAccept.forEach(f_name => {
                         savingFields.delete(f_name);
                         savedFields.add(f_name);
                    });
                    setTimeout(() => {
                         fieldsToAccept.forEach(f_name => savedFields.delete(f_name));
                         renderComparison(currentData);
                    }, 2000);
                    await loadEntry(currentData.entry_key);

                    // Update global stats
                    const entryInGlobal = allEntries.find(e => e.key === currentData.entry_key);
                    if (entryInGlobal) {
                        entryInGlobal.fields_updated = entryInGlobal.fields_updated.filter(f => !fieldsToAccept.includes(f));
                        entryInGlobal.fields_conflict = entryInGlobal.fields_conflict.filter(f => !fieldsToAccept.includes(f));
                        entryInGlobal.fields_different = entryInGlobal.fields_different.filter(f => !fieldsToAccept.includes(f));
                        updateGlobalSummary();
                    }
                }

            } catch (e) {
                console.error(e);
                alert("Failed to accept all: " + e.message);
                // Revert
                fieldsToAccept.forEach(f_name => {
                    acceptedFields.delete(f_name);
                    savingFields.delete(f_name);
                });
                renderComparison(currentData);
            }
        }

        async function rejectAll() {
            if (!currentData) return;
            const fieldsToReject = [
                ...Object.keys(currentData.fields_updated || {}),
                ...Object.keys(currentData.fields_conflict || {}),
                ...Object.keys(currentData.fields_different || {})
            ].filter(f_name => !acceptedFields.has(f_name) && !rejectedFields.has(f_name));

             if (fieldsToReject.length === 0) {
                alert("No new changes to reject.");
                return;
            }

            fieldsToReject.forEach(f_name => {
                rejectedFields.add(f_name);
                savingFields.add(f_name);
            });
            renderComparison(currentData);

             try {
                const response = await fetch('/api/save', { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        entry_key: currentData.entry_key,
                        accepted_fields: [],
                        rejected_fields: fieldsToReject,
                        selected_sources: selectedSources
                    })
                });
                
                const result = await response.json();
                if (!response.ok) throw new Error(result.detail || 'Failed');
                
                if (result.success) {
                    fieldsToReject.forEach(f_name => {
                         savingFields.delete(f_name);
                         savedFields.add(f_name);
                    });
                    setTimeout(() => {
                         fieldsToReject.forEach(f_name => savedFields.delete(f_name));
                         renderComparison(currentData);
                    }, 2000);
                    await loadEntry(currentData.entry_key);
                    
                    // Update global stats
                    const entryInGlobal = allEntries.find(e => e.key === currentData.entry_key);
                    if (entryInGlobal) {
                        entryInGlobal.fields_updated = entryInGlobal.fields_updated.filter(f => !fieldsToReject.includes(f));
                        entryInGlobal.fields_conflict = entryInGlobal.fields_conflict.filter(f => !fieldsToReject.includes(f));
                        entryInGlobal.fields_different = entryInGlobal.fields_different.filter(f => !fieldsToReject.includes(f));
                        updateGlobalSummary();
                    }
                }

            } catch (e) {
                console.error(e);
                 alert("Failed to reject all: " + e.message);
                 fieldsToReject.forEach(f_name => {
                    rejectedFields.delete(f_name);
                    savingFields.delete(f_name);
                });
                renderComparison(currentData);
            }
        }

        async function acceptAllGlobal() {
            const btn = document.querySelector('button[onclick="acceptAllGlobal()"]');
            
            if (!acceptAllGlobalConfirm) {
                acceptAllGlobalConfirm = true;
                const originalContent = btn.innerHTML;
                // createIcons might have messed with innerHTML structure, so safest is to rebuild or save/restore.
                // But we can just hardcode text.
                
                btn.innerHTML = '<i data-lucide="alert-triangle" class="mr-2 h-4 w-4"></i> Click again to confirm';
                btn.classList.add('bg-destructive', 'hover:bg-destructive/90', 'text-destructive-foreground');
                btn.classList.remove('bg-primary', 'text-primary-foreground', 'hover:bg-primary/90');
                
                lucide.createIcons({ root: btn });

                if (acceptAllGlobalTimeout) clearTimeout(acceptAllGlobalTimeout);
                acceptAllGlobalTimeout = setTimeout(() => {
                    acceptAllGlobalConfirm = false;
                    btn.innerHTML = '<i data-lucide="check-circle-2" class="mr-2 h-4 w-4"></i> Accept Changes';
                    btn.classList.remove('bg-destructive', 'hover:bg-destructive/90', 'text-destructive-foreground');
                    btn.classList.add('bg-primary', 'text-primary-foreground', 'hover:bg-primary/90');
                    lucide.createIcons({ root: btn });
                }, 3000);
                return;
            }
            
            // Confirmed
            if (acceptAllGlobalTimeout) clearTimeout(acceptAllGlobalTimeout);
            acceptAllGlobalConfirm = false;
            
            try {
                // Show global loading indicator if possible, or just alert
                const btn = document.querySelector('button[onclick="acceptAllGlobal()"]');
                const originalText = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = '<i data-lucide="loader-2" class="mr-2 h-4 w-4 animate-spin"></i> Processing...';
                
                const response = await fetch('/api/accept_all_global', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    alert(`Successfully processed global updates.\nModified ${result.modified_count} entries.`);
                    
                    // Update entries list if provided
                    if (result.entries) {
                        loadEntries();
                    }
                    
                    // Reload current entry
                    if (currentData) loadEntry(currentData.entry_key);
                } else {
                    alert("Failed: " + result.detail);
                }
                
                 btn.disabled = false;
                 btn.innerHTML = originalText;
                 lucide.createIcons({ root: btn });
                 
            } catch (e) {
                console.error(e);
                alert("Error: " + e.message);
                location.reload(); 
            }
        }

        function selectSource(f_name, source) {
            selectedSources[f_name] = source;
            if (currentData) {
                // Update local model for immediate feedback
                
                // Keep minimal update logic
                const sourceData = currentData.all_sources_data[source];
                const val = getFieldValueFromSource(sourceData, f_name, source);
                
                if (val) {
                     if (currentData.fields_updated[f_name]) currentData.fields_updated[f_name].new = val;
                     else if (currentData.fields_conflict[f_name]) currentData.fields_conflict[f_name].api = val;
                     else if (currentData.fields_different[f_name]) currentData.fields_different[f_name].api = val;
                }
                
                renderComparison(currentData);
            }
        }

        function getFieldValueFromSource(sourceData, f_name, sourceName) {
            if (!sourceData) return null;
            const fieldMappings = {
                'title': { crossref: 'title', arxiv: 'title', semantic_scholar: 'title', dblp: 'title', pubmed: 'title' },
                'author': { crossref: 'author', arxiv: 'authors', semantic_scholar: 'authors', dblp: 'authors', pubmed: 'authors' },
                'year': { crossref: 'published-print', arxiv: 'year', semantic_scholar: 'year', dblp: 'year', pubmed: 'year' },
                'journal': { crossref: 'container-title', arxiv: null, semantic_scholar: 'journal', dblp: 'venue', pubmed: 'journal' }
            };
            
            const mapping = fieldMappings[f_name];
            if (!mapping || !mapping[sourceName]) return null;
            const apiField = mapping[sourceName];
            
            // Simplified extraction logic (same as Python backend roughly)
            if (apiField === 'published-print' && sourceData[apiField]?.date_parts?.[0]?.[0]) return String(sourceData[apiField].date_parts[0][0]);
            if (apiField === 'author' && Array.isArray(sourceData[apiField])) {
                return sourceData[apiField].map(a => (a.given && a.family) ? `${a.family}, ${a.given}` : (a.family || a)).join(' and ');
            }
            if (apiField === 'authors' && Array.isArray(sourceData[apiField])) return sourceData[apiField].join(' and ');
            
            return sourceData[apiField] || null;
        }

        // Boot
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            // 입력 필드 포커스 체크
            const activeElement = document.activeElement;
            const isInputFocused = activeElement && (
                activeElement.tagName === 'INPUT' ||
                activeElement.tagName === 'TEXTAREA' ||
                activeElement.tagName === 'SELECT' ||
                activeElement.isContentEditable
            );
            
            if (isInputFocused) return;
            
            const select = document.getElementById('entrySelect');
            if (!select) return; // select 요소가 없으면 종료
            
            const currentIndex = select.selectedIndex;
            const maxIndex = select.options.length - 1;
            
            switch(e.key) {
                case 'ArrowLeft':
                case 'ArrowUp':
                    e.preventDefault();
                    navigateEntry(-1);
                    break;
                case 'ArrowRight':
                case 'ArrowDown':
                    e.preventDefault();
                    navigateEntry(1);
                    break;
                case 'Home':
                    e.preventDefault();
                    if (maxIndex > 0) {
                        select.selectedIndex = 1;
                        loadEntry(select.value);
                    }
                    break;
                case 'End':
                    e.preventDefault();
                    if (maxIndex > 0) {
                        select.selectedIndex = maxIndex;
                        loadEntry(select.value);
                    }
                    break;
                case 'PageUp':
                    e.preventDefault();
                    const prevPageIndex = Math.max(1, currentIndex - 10);
                    if (prevPageIndex !== currentIndex && prevPageIndex >= 1) {
                        select.selectedIndex = prevPageIndex;
                        loadEntry(select.value);
                    }
                    break;
                case 'PageDown':
                    e.preventDefault();
                    const nextPageIndex = Math.min(maxIndex, currentIndex + 10);
                    if (nextPageIndex !== currentIndex && nextPageIndex <= maxIndex) {
                        select.selectedIndex = nextPageIndex;
                        loadEntry(select.value);
                    }
                    break;
                case 'Escape':
                    e.preventDefault();
                    select.selectedIndex = 0;
                    loadEntry('');
                    break;
            }
        });
        
        loadEntries();
    </script>
</body>
</html>

        """

    # API: Get list of entries
    @app.get("/api/entries")
    async def get_entries():
        """Get list of all entries with metadata"""
        results = app.state.results
        entries = []
        for result in results:
            entries.append(
                {
                    "key": result.entry_key,
                    "has_doi": result.has_doi,
                    "doi_valid": result.doi_valid,
                    "has_arxiv": result.has_arxiv,
                    "arxiv_valid": result.arxiv_valid,
                    "fields_updated": list(result.fields_updated.keys()),
                    "fields_conflict": list(result.fields_conflict.keys()),
                    "fields_different": list(result.fields_different.keys()),
                }
            )
        return {"entries": entries}

    @app.post("/api/accept_all_global")
    async def accept_all_global():
        """Accept all updates for all entries"""
        validator = app.state.validator
        results = app.state.results
        modified_count = 0

        for result in results:
            entry_key = result.entry_key
            # We skip conflicts for safety? Or just take API value?
            # Usually 'Accept All' implies taking the suggested updates.
            # We will take 'updated' and 'different' fields.
            # Conflicts might be risky, but let's assume 'Accept All' means 'Trust API'.

            # Re-calculate or use stored result.
            # The result object has 'fields_updated', 'fields_conflict', etc. properties
            # BUT these are computed on the fly in the validation loop usually.
            # Here 'results' list contains the ValidationResult objects generated at startup.
            # However, if we saved changes, we updated the DB but maybe not the Result object fully?
            # Actually validate_bibtex modifies the validator.db in memory when save is called.
            # So looking at result object might be stale if we already modified some entries.
            # But accept_all_global is usually done at once.

            # Let's collect changes from the result object (which represents the 'proposal')
            # And apply them if they haven't been applied yet.

            # Better approach: Iterate over all results, simulate "Accept All" for each.
            changes_to_apply = {}

            # 1. Updates (New fields)
            for f_name, change in result.fields_updated.items():
                changes_to_apply[f_name] = change

            # 2. Differences (Value diff)
            for f_name, change in result.fields_different.items():
                # change is usually (bib_val, api_val)
                if isinstance(change, (list, tuple)) and len(change) >= 2:
                    changes_to_apply[f_name] = change[1]

            # 3. Conflicts (BibTeX vs API) -> Default to API for "Accept All"
            for f_name, change in result.fields_conflict.items():
                if isinstance(change, (list, tuple)) and len(change) >= 2:
                    changes_to_apply[f_name] = change[1]

            if changes_to_apply:
                # Apply to DB
                if entry_key in validator.db.entries_dict:
                    entry = validator.db.entries_dict[entry_key]
                    for k, v in changes_to_apply.items():
                        entry[k] = v
                    modified_count += 1

                    # Clear the pending changes in the result object so UI updates
                    result.fields_updated = {}
                    result.fields_conflict = {}
                    result.fields_different = {}

        # Save to file
        validator.save_updated_bib()

        # Helper to regenerate entries list
        current_entries = []
        for res in results:
            current_entries.append(
                {
                    "key": res.entry_key,
                    "has_doi": res.has_doi,
                    "doi_valid": res.doi_valid,
                    "has_arxiv": res.has_arxiv,
                    "arxiv_valid": res.arxiv_valid,
                    "fields_updated": list(res.fields_updated.keys()),
                    "fields_conflict": list(res.fields_conflict.keys()),
                }
            )

        return {
            "success": True,
            "modified_count": modified_count,
            "entries": current_entries,
        }

    # API: Get entry comparison
    @app.get("/api/entry/{entry_key}")
    async def get_entry(entry_key: str):
        """Get detailed comparison data for a specific entry"""
        from urllib.parse import unquote

        # URL decode entry_key to handle special characters
        try:
            entry_key = unquote(entry_key)
        except Exception:
            pass  # If decoding fails, use original

        if not entry_key or not isinstance(entry_key, str):
            raise HTTPException(status_code=400, detail="Invalid entry_key")

        validator = app.state.validator
        results = app.state.results

        result = next((r for r in results if r.entry_key == entry_key), None)
        if not result:
            raise HTTPException(status_code=404, detail="Entry not found")

        entry = next((e for e in validator.db.entries if e["ID"] == entry_key), None)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found in database")

        # Build comparison data
        comparison = {
            "entry_key": entry_key,
            "fields_updated": {},
            "fields_conflict": {},
            "fields_identical": {},
            "fields_different": {},
            "field_sources": {},
            "field_source_options": result.field_source_options.copy(),
            "all_sources_data": {},
            "original_values": result.original_values.copy(),
        }

        # Process all_sources_data (convert to JSON-serializable format)
        for source_name, source_data in result.all_sources_data.items():
            comparison["all_sources_data"][source_name] = source_data

        # Process updates
        if result.fields_updated:
            for f_name, new_val in result.fields_updated.items():
                if f_name and new_val is not None:
                    # Use original_values for old (original BibTeX value)
                    # This ensures Reject can restore to the original value
                    old_value = result.original_values.get(
                        f_name, entry.get(f_name, "") or ""
                    )
                    comparison["fields_updated"][f_name] = {
                        "old": old_value,
                        "new": str(new_val) if new_val is not None else "",
                    }

        # Process conflicts
        if result.fields_conflict:
            for f_name, conflict_data in result.fields_conflict.items():
                if f_name and conflict_data and len(conflict_data) >= 2:
                    bib_val, api_val = conflict_data[0], conflict_data[1]
                    comparison["fields_conflict"][f_name] = {
                        "bibtex": str(bib_val) if bib_val is not None else "",
                        "api": str(api_val) if api_val is not None else "",
                    }

        # Process identical fields
        if result.fields_identical:
            for f_name, value in result.fields_identical.items():
                comparison["fields_identical"][f_name] = (
                    str(value) if value is not None else ""
                )

        # Process different fields
        if result.fields_different:
            for field, diff_data in result.fields_different.items():
                if field and diff_data and len(diff_data) >= 2:
                    bib_val, api_val = diff_data[0], diff_data[1]
                    comparison["fields_different"][field] = {
                        "bibtex": str(bib_val) if bib_val is not None else "",
                        "api": str(api_val) if api_val is not None else "",
                    }

        # Process sources
        comparison["field_sources"] = result.field_sources.copy()

        # Find fields that are in BibTeX but not provided by API
        all_bibtex_fields = set(entry.keys()) - {"ID", "ENTRYTYPE"}
        api_provided_fields = set()
        api_provided_fields.update(comparison.get("fields_updated", {}).keys())
        api_provided_fields.update(comparison.get("fields_conflict", {}).keys())
        api_provided_fields.update(comparison.get("fields_different", {}).keys())
        api_provided_fields.update(comparison.get("fields_identical", {}).keys())

        fields_not_in_api = all_bibtex_fields - api_provided_fields
        comparison["fields_not_in_api"] = {
            field: str(entry.get(field, ""))
            for field in fields_not_in_api
            if entry.get(field, "").strip()
        }

        return JSONResponse(comparison)

    # API: Accept changes
    @app.post("/api/accept")
    async def accept_changes(request: Request):
        """Accept field changes for an entry (store in memory)"""
        try:
            data = await request.json()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        entry_key = data.get("entry_key")
        accepted_fields = data.get("accepted_fields", [])

        if not entry_key:
            raise HTTPException(status_code=400, detail="entry_key is required")
        if not isinstance(entry_key, str):
            raise HTTPException(status_code=400, detail="entry_key must be a string")
        if not isinstance(accepted_fields, list):
            raise HTTPException(
                status_code=400, detail="accepted_fields must be a list"
            )

        validator = app.state.validator
        results = app.state.results

        entry = next((e for e in validator.db.entries if e["ID"] == entry_key), None)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")

        result = next((r for r in results if r.entry_key == entry_key), None)
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")

        # Store accepted changes
        if entry_key not in app.state.accepted_changes:
            app.state.accepted_changes[entry_key] = {}

        # Handle empty accepted_fields gracefully
        if not accepted_fields:
            return JSONResponse(
                {"success": True, "message": "No fields to accept", "accepted_count": 0}
            )

        # Validate and store accepted fields
        accepted_count = 0
        for f_name in accepted_fields:
            if not isinstance(f_name, str) or not f_name:
                continue  # Skip invalid field names
            if f_name in result.fields_updated:
                app.state.accepted_changes[entry_key][f_name] = result.fields_updated[
                    f_name
                ]
                accepted_count += 1
            elif (
                f_name in result.fields_conflict
                and len(result.fields_conflict[f_name]) >= 2
            ):
                app.state.accepted_changes[entry_key][f_name] = result.fields_conflict[
                    f_name
                ][1]  # API value
                accepted_count += 1

        return JSONResponse(
            {
                "success": True,
                "message": f"Accepted {accepted_count} field(s)",
                "accepted_count": accepted_count,
            }
        )

    # API: Save all changes
    @app.post("/api/save")
    async def save_changes(request: Request):
        """Save all accepted changes to BibTeX file"""
        try:
            data = await request.json()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        entry_key = data.get("entry_key")
        accepted_fields = data.get("accepted_fields", [])

        if not entry_key:
            raise HTTPException(status_code=400, detail="entry_key is required")
        if not isinstance(entry_key, str):
            raise HTTPException(status_code=400, detail="entry_key must be a string")
        if not isinstance(accepted_fields, list):
            raise HTTPException(
                status_code=400, detail="accepted_fields must be a list"
            )

        validator = app.state.validator
        results = app.state.results

        entry = next((e for e in validator.db.entries if e["ID"] == entry_key), None)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")

        result = next((r for r in results if r.entry_key == entry_key), None)
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")

        # Get rejected fields (fields that were previously accepted but now rejected)
        rejected_fields = data.get("rejected_fields", [])

        # Restore original BibTeX values for rejected fields
        restored_count = 0
        for f_name in rejected_fields:
            if not isinstance(f_name, str) or not f_name:
                continue

            # Find the original BibTeX value
            original_bibtex_value = None

            # Check fields_conflict (first element is the original BibTeX value)
            if (
                f_name in result.fields_conflict
                and len(result.fields_conflict[f_name]) >= 2
            ):
                original_bibtex_value = result.fields_conflict[f_name][
                    0
                ]  # bibtex value
            # Check fields_different (first element is the original BibTeX value)
            elif (
                f_name in result.fields_different
                and len(result.fields_different[f_name]) >= 2
            ):
                original_bibtex_value = result.fields_different[f_name][
                    0
                ]  # bibtex value
            # For fields_updated, use original_values (stored at validation time)
            elif f_name in result.original_values:
                original_bibtex_value = result.original_values[f_name]
            # If field was in fields_updated but not in original_values,
            # it means the field was missing originally, so delete it
            elif f_name in result.fields_updated:
                # Field was missing, so delete it
                if f_name in entry:
                    del entry[f_name]
                restored_count += 1
                continue

            if original_bibtex_value is not None:
                entry[f_name] = original_bibtex_value
                restored_count += 1

        # Get selected sources for fields
        selected_sources = data.get("selected_sources", {})  # field: source_name

        # Apply accepted fields
        applied_count = 0
        for f_name in accepted_fields:
            if not isinstance(f_name, str) or not f_name:
                continue  # Skip invalid field names

            # Check if a specific source was selected
            selected_source = selected_sources.get(f_name)
            if selected_source and selected_source in result.all_sources_data:
                # Use value from selected source
                source_data = result.all_sources_data[selected_source]
                # Extract field value from source data using compare_fields logic
                comparison = validator.compare_fields(
                    entry, source_data, source=selected_source
                )
                # Get the value from comparison results
                if f_name in comparison["updated"]:
                    entry[f_name] = comparison["updated"][f_name]
                    applied_count += 1
                elif f_name in comparison["conflicts"]:
                    entry[f_name] = comparison["conflicts"][f_name][1]  # API value
                    applied_count += 1
                elif f_name in comparison.get("different", {}):
                    entry[f_name] = comparison["different"][f_name][1]  # API value
                    applied_count += 1
                elif f_name in comparison.get("identical", {}):
                    entry[f_name] = comparison["identical"][f_name]
                    applied_count += 1
            elif f_name in result.fields_updated:
                entry[f_name] = result.fields_updated[f_name]
                applied_count += 1
            elif (
                f_name in result.fields_conflict
                and len(result.fields_conflict[f_name]) >= 2
            ):
                entry[f_name] = result.fields_conflict[f_name][1]  # API value
                applied_count += 1
            elif (
                f_name in result.fields_different
                and len(result.fields_different[f_name]) >= 2
            ):
                entry[f_name] = result.fields_different[f_name][1]  # API value
                applied_count += 1

            # Remove from pending changes in result object so it's not suggested again
            if f_name in result.fields_updated:
                del result.fields_updated[f_name]
            if f_name in result.fields_conflict:
                del result.fields_conflict[f_name]
            if f_name in result.fields_different:
                del result.fields_different[f_name]

        if applied_count == 0 and restored_count == 0:
            return JSONResponse(
                {
                    "success": False,
                    "message": "No valid fields were applied or restored",
                    "error": "No matching fields found in validation results",
                }
            )

        # Save to file
        try:
            # Check if output directory is writable
            output_path = Path(validator.output_file)
            output_dir = output_path.parent
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                except (OSError, PermissionError) as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Cannot create output directory: {str(e)}",
                    )

            # Check write permissions
            if output_path.exists() and not os.access(output_path, os.W_OK):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: Cannot write to {validator.output_file}",
                )

            writer = BibTexWriter()
            writer.indent = "\t"
            writer.comma_first = False

            with open(validator.output_file, "w", encoding="utf-8") as f:
                bibtexparser.dump(validator.db, f, writer=writer)

            return JSONResponse(
                {
                    "success": True,
                    "message": f"Changes saved to {validator.output_file}",
                    "file": str(validator.output_file),
                }
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: Cannot write to file. {str(e)}",
            )
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"File system error: {str(e)}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to save file: {str(e)}"
            )

    return app


def gui_app_factory():
    """Factory function for uvicorn reload"""
    state_file = os.environ.get("BIBTEX_VALIDATOR_GUI_STATE")
    if not state_file or not os.path.exists(state_file):
        # Fallback only (should not happen in normal flow unless run directly without state)
        print("No state file found. GUI might fail to load data.", file=sys.stderr)
        # return dummy app to avoid crash loop
        return FastAPI()

    try:
        with open(state_file, "rb") as f:
            state = pickle.load(f)

        validator = BibTeXValidator(
            bib_file=state["bib_file"],
            output_file=state["output_file"],
            update_bib=False,  # dummy
            delay=1.0,
        )
        validator.db = state["db"]
        results = state["results"]

        return create_gui_app(validator, results)
    except Exception as e:
        print(f"Failed to load state: {e}", file=sys.stderr)
        return FastAPI()


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate and enrich BibTeX entries using DOI, arXiv, and Google Scholar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate only (print report)
  python validate_bibtex.py references.bib
  
  # Update BibTeX file in place
  python validate_bibtex.py references.bib --update
  
  # Save report to file
  python validate_bibtex.py references.bib --report report.txt
  
  # Update and save to different file
  python validate_bibtex.py references.bib --update --output references_new.bib
  
  # Launch web-based GUI
  python validate_bibtex.py references.bib --gui
  
  # Launch GUI on custom port
  python validate_bibtex.py references.bib --gui --port 8080
        """,
    )
    parser.add_argument("bib_file", help="Input BibTeX file")
    parser.add_argument(
        "-o", "--output", help="Output BibTeX file (default: same as input if --update)"
    )
    parser.add_argument(
        "-r", "--report", help="Output report file (default: print to stdout)"
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Update BibTeX file with enriched data",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=1.0,
        help="Delay between API requests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--no-progress", action="store_true", help="Hide progress indicators"
    )
    parser.add_argument(
        "--gui", action="store_true", help="Launch web-based GUI interface"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of threads for parallel validation (default: 10)",
    )
    parser.add_argument(
        "--port", type=int, default=8010, help="Port for GUI web server (default: 8010)"
    )

    args = parser.parse_args()

    try:
        # Create validator
        validator = BibTeXValidator(
            bib_file=args.bib_file,
            output_file=args.output,
            update_bib=args.update,
            delay=args.delay,
        )

        # Validate all entries
        validator.validate_all(
            show_progress=not args.no_progress, max_workers=args.workers
        )

        # GUI mode
        if args.gui:
            if not HAS_GUI_DEPS:
                print(
                    f"Error: GUI dependencies (fastapi, uvicorn) are required for --gui mode.",
                    file=sys.stderr,
                )
                print(
                    f"Install with: uv add fastapi uvicorn or pip install fastapi uvicorn",
                    file=sys.stderr,
                )
                return 1

            # Create FastAPI app
            app = create_gui_app(validator, validator.results)

            # Open browser
            url = f"http://127.0.0.1:{args.port}"

            def open_browser():
                import time

                time.sleep(1.5)  # Wait for server to start
                try:
                    webbrowser.open(url)
                except Exception:
                    pass  # Browser opening is optional

            browser_thread = threading.Thread(target=open_browser, daemon=True)
            browser_thread.start()

            print(f"\n{'=' * 60}")
            print("  Searching arXiv...", end="", flush=True)
            print(f"Server running at: {url}")
            print(f"Press Ctrl+C to stop the server")
            print(f"{'=' * 60}\n")

            # Save state for reload
            with tempfile.NamedTemporaryFile(
                mode="wb", delete=False, suffix=".pkl"
            ) as f:
                state = {
                    "bib_file": str(validator.bib_file),
                    "output_file": str(validator.output_file),
                    "db": validator.db,
                    "results": validator.results,
                }
                pickle.dump(state, f)
                state_path = f.name

            os.environ["BIBTEX_VALIDATOR_GUI_STATE"] = state_path

            # Start server with reload
            try:
                # We use factory=True and reload=True
                # The app string must be importable. Since we are running this script, it should be importable as validate_bibtex
                # We need to make sure the directory is in python path
                sys.path.insert(0, os.getcwd())

                print(
                    "\n[INFO] Live reload enabled. You can edit the script and browser will refresh."
                )
                uvicorn.run(
                    "validate_bibtex:gui_app_factory",
                    host="127.0.0.1",
                    port=args.port,
                    log_level="info",
                    reload=True,
                    factory=True,
                )
            except OSError as e:
                error_msg = str(e)
                if (
                    "Address already in use" in error_msg
                    or "address already in use" in error_msg.lower()
                ):
                    print(
                        f"\nError: Port {args.port} is already in use.", file=sys.stderr
                    )
                    return 1
                else:
                    print(f"\nError starting server: {error_msg}", file=sys.stderr)
                    return 1
            except KeyboardInterrupt:
                print("\n\nServer stopped.")
                # Cleanup
                if os.path.exists(state_path):
                    os.unlink(state_path)
                return 0
            except Exception:
                print(
                    "Warning: Crossref API email not set. Using default user-agent.",
                    file=sys.stderr,
                )
                import traceback

                traceback.print_exc()
                if os.path.exists(state_path):
                    os.unlink(state_path)
                return 1
            finally:
                if os.path.exists(state_path):
                    try:
                        os.unlink(state_path)
                    except:
                        pass

        # CLI mode (existing behavior)
        # Generate report
        # If report file is specified, add bibtex_ prefix if needed
        report_file = args.report
        if report_file:
            report_path = Path(report_file)
            if not report_path.name.startswith("bibtex_"):
                report_path = report_path.parent / ("bibtex_" + report_path.name)
                report_file = str(report_path)

        report_text = validator.generate_report(output_file=report_file)

        # Print report if not saved to file
        if not args.report:
            print("\n" + report_text)

        # Save updated BibTeX if requested
        if args.update:
            validator.save_updated_bib()

        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
