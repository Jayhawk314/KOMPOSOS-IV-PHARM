# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
KOMPOSOS-III Data Sources Module
=================================

Bulk data ingestion from various sources for building categorical structures.

This module handles loading data from:
1. OpenAlex JSONL exports (citation graphs, papers, concepts)
2. PDF documents (research papers, notes)
3. Wikidata JSON exports (structured knowledge)
4. Custom CSV/JSON files (user data)
5. BibTeX bibliography files

The key insight: KOMPOSOS-III works with PRE-DOWNLOADED corpora, not live APIs.
Users bulk download their corpus once, then the system processes it.

Input formats:
- OpenAlex: JSONL files from their bulk data export
- PDFs: Individual files or directories
- Wikidata: Entity JSON files
- CSV: Objects/morphisms in tabular format
- BibTeX: Bibliography entries as objects

Output:
- StoredObjects and StoredMorphisms for the categorical store
- Temporal metadata for evolution tracking
- Provenance information for traceability
"""

from __future__ import annotations
import json
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import hashlib

from .store import StoredObject, StoredMorphism, KomposOSStore


# =============================================================================
# Data Classes for Parsed Content
# =============================================================================

@dataclass
class ParsedWork:
    """
    A parsed academic work (paper, article, etc.).

    Represents a single item from OpenAlex or PDF extraction.
    """
    id: str
    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    authors: List[str] = field(default_factory=list)
    concepts: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)  # IDs of cited works
    references: List[str] = field(default_factory=list)  # IDs of works citing this
    metadata: Dict[str, Any] = field(default_factory=dict)
    provenance: str = "unknown"

    def to_object(self) -> StoredObject:
        """Convert to StoredObject."""
        created_at = None
        if self.year:
            created_at = datetime(self.year, 1, 1)

        return StoredObject(
            name=self.id,
            type_name="Work",
            metadata={
                "title": self.title,
                "abstract": self.abstract,
                "year": self.year,
                "authors": self.authors,
                "concepts": self.concepts,
                **self.metadata
            },
            created_at=created_at,
            provenance=self.provenance
        )


@dataclass
class ParsedConcept:
    """A parsed concept (from OpenAlex, Wikidata, etc.)."""
    id: str
    name: str
    description: Optional[str] = None
    level: int = 0  # Hierarchy level (0 = most general)
    parent_ids: List[str] = field(default_factory=list)
    related_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    provenance: str = "unknown"

    def to_object(self) -> StoredObject:
        """Convert to StoredObject."""
        return StoredObject(
            name=self.id,
            type_name="Concept",
            metadata={
                "display_name": self.name,
                "description": self.description,
                "level": self.level,
                "parent_ids": self.parent_ids,
                "related_ids": self.related_ids,
                **self.metadata
            },
            provenance=self.provenance
        )


@dataclass
class ParsedEntity:
    """A parsed entity from Wikidata or similar."""
    id: str
    label: str
    description: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    claims: Dict[str, List[str]] = field(default_factory=dict)
    sitelinks: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    provenance: str = "wikidata"

    def to_object(self) -> StoredObject:
        """Convert to StoredObject."""
        return StoredObject(
            name=self.id,
            type_name="Entity",
            metadata={
                "label": self.label,
                "description": self.description,
                "aliases": self.aliases,
                "claims": self.claims,
                **self.metadata
            },
            provenance=self.provenance
        )


# =============================================================================
# OpenAlex Loader
# =============================================================================

class OpenAlexLoader:
    """
    Load data from OpenAlex JSONL exports.

    OpenAlex provides bulk downloads of academic works, authors, concepts,
    institutions, etc. This loader processes their JSONL format.

    Expected directory structure:
        openalex/
        ├── works/
        │   ├── part_000.jsonl
        │   ├── part_001.jsonl
        │   └── ...
        ├── concepts/
        │   └── ...
        └── authors/
            └── ...

    Usage:
        loader = OpenAlexLoader("path/to/openalex")
        for work in loader.iter_works(limit=1000):
            store.add_object(work.to_object())
    """

    def __init__(self, base_path: Union[str, Path]):
        """
        Initialize the loader.

        Args:
            base_path: Path to OpenAlex data directory
        """
        self.base_path = Path(base_path)

    def iter_works(
        self,
        limit: Optional[int] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None
    ) -> Generator[ParsedWork, None, None]:
        """
        Iterate over works in the corpus.

        Args:
            limit: Maximum number of works to yield
            year_min: Minimum publication year
            year_max: Maximum publication year

        Yields:
            ParsedWork instances
        """
        works_dir = self.base_path / "works"
        if not works_dir.exists():
            print(f"[OpenAlexLoader] Works directory not found: {works_dir}")
            return

        count = 0
        for jsonl_file in sorted(works_dir.glob("*.jsonl")):
            for work in self._parse_works_file(jsonl_file):
                # Apply filters
                if year_min and work.year and work.year < year_min:
                    continue
                if year_max and work.year and work.year > year_max:
                    continue

                yield work
                count += 1

                if limit and count >= limit:
                    return

    def _parse_works_file(self, filepath: Path) -> Generator[ParsedWork, None, None]:
        """Parse a single JSONL works file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        yield self._parse_work(data)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[OpenAlexLoader] Error reading {filepath}: {e}")

    def _parse_work(self, data: Dict[str, Any]) -> ParsedWork:
        """Parse a single work entry."""
        # Extract basic info
        work_id = data.get("id", "").replace("https://openalex.org/", "")

        title = data.get("title") or data.get("display_name") or work_id

        abstract = None
        if "abstract_inverted_index" in data and data["abstract_inverted_index"]:
            abstract = self._reconstruct_abstract(data["abstract_inverted_index"])

        year = data.get("publication_year")

        # Extract authors
        authors = []
        for authorship in data.get("authorships", []):
            author = authorship.get("author", {})
            name = author.get("display_name")
            if name:
                authors.append(name)

        # Extract concepts
        concepts = []
        for concept in data.get("concepts", []):
            name = concept.get("display_name")
            if name:
                concepts.append(name)

        # Extract citations (referenced works)
        citations = []
        for ref in data.get("referenced_works", []):
            ref_id = ref.replace("https://openalex.org/", "") if isinstance(ref, str) else str(ref)
            citations.append(ref_id)

        return ParsedWork(
            id=work_id,
            title=title,
            abstract=abstract,
            year=year,
            authors=authors,
            concepts=concepts,
            citations=citations,
            metadata={
                "doi": data.get("doi"),
                "type": data.get("type"),
                "cited_by_count": data.get("cited_by_count"),
                "venue": data.get("primary_location", {}).get("source", {}).get("display_name")
            },
            provenance="openalex"
        )

    @staticmethod
    def _reconstruct_abstract(inverted_index: Dict[str, List[int]]) -> str:
        """Reconstruct abstract from inverted index format."""
        if not inverted_index:
            return ""

        # Build position -> word mapping
        positions = []
        for word, pos_list in inverted_index.items():
            for pos in pos_list:
                positions.append((pos, word))

        # Sort by position and join
        positions.sort(key=lambda x: x[0])
        return " ".join(word for _, word in positions)

    def iter_concepts(
        self,
        limit: Optional[int] = None,
        min_level: int = 0,
        max_level: int = 5
    ) -> Generator[ParsedConcept, None, None]:
        """
        Iterate over concepts in the corpus.

        Args:
            limit: Maximum number of concepts to yield
            min_level: Minimum hierarchy level
            max_level: Maximum hierarchy level

        Yields:
            ParsedConcept instances
        """
        concepts_dir = self.base_path / "concepts"
        if not concepts_dir.exists():
            print(f"[OpenAlexLoader] Concepts directory not found: {concepts_dir}")
            return

        count = 0
        for jsonl_file in sorted(concepts_dir.glob("*.jsonl")):
            for concept in self._parse_concepts_file(jsonl_file):
                if concept.level < min_level or concept.level > max_level:
                    continue

                yield concept
                count += 1

                if limit and count >= limit:
                    return

    def _parse_concepts_file(self, filepath: Path) -> Generator[ParsedConcept, None, None]:
        """Parse a single JSONL concepts file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        yield self._parse_concept(data)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[OpenAlexLoader] Error reading {filepath}: {e}")

    def _parse_concept(self, data: Dict[str, Any]) -> ParsedConcept:
        """Parse a single concept entry."""
        concept_id = data.get("id", "").replace("https://openalex.org/", "")
        name = data.get("display_name", concept_id)
        description = data.get("description")
        level = data.get("level", 0)

        # Extract ancestors (parent concepts)
        parent_ids = []
        for ancestor in data.get("ancestors", []):
            aid = ancestor.get("id", "").replace("https://openalex.org/", "")
            if aid:
                parent_ids.append(aid)

        # Extract related concepts
        related_ids = []
        for related in data.get("related_concepts", []):
            rid = related.get("id", "").replace("https://openalex.org/", "")
            if rid:
                related_ids.append(rid)

        return ParsedConcept(
            id=concept_id,
            name=name,
            description=description,
            level=level,
            parent_ids=parent_ids,
            related_ids=related_ids,
            metadata={
                "works_count": data.get("works_count"),
                "cited_by_count": data.get("cited_by_count"),
                "wikidata": data.get("wikidata")
            },
            provenance="openalex"
        )

    def create_morphisms(
        self,
        store: KomposOSStore,
        include_citations: bool = True,
        include_concept_relations: bool = True
    ) -> int:
        """
        Create morphisms from parsed relationships.

        Args:
            store: The store to add morphisms to
            include_citations: Include citation morphisms
            include_concept_relations: Include concept hierarchy morphisms

        Returns:
            Number of morphisms created
        """
        count = 0

        if include_citations:
            # Create citation morphisms from stored works
            for work_obj in store.get_objects_by_type("Work"):
                citations = work_obj.metadata.get("citations", [])
                if not citations:
                    # Check for concepts
                    concepts = work_obj.metadata.get("concepts", [])
                    for concept_name in concepts:
                        # Find concept object
                        concept_id = concept_name.lower().replace(" ", "_")
                        concept_obj = store.get_object(concept_id)
                        if concept_obj:
                            mor = StoredMorphism(
                                name="about",
                                source_name=work_obj.name,
                                target_name=concept_id,
                                metadata={"type": "concept_tag"},
                                provenance="openalex"
                            )
                            store.add_morphism(mor)
                            count += 1
                else:
                    for cited_id in citations:
                        # Only create if target exists
                        if store.get_object(cited_id):
                            year = work_obj.metadata.get("year")
                            mor = StoredMorphism(
                                name="cites",
                                source_name=work_obj.name,
                                target_name=cited_id,
                                metadata={"year": year},
                                created_at=datetime(year, 1, 1) if year else None,
                                provenance="openalex"
                            )
                            store.add_morphism(mor)
                            count += 1

        if include_concept_relations:
            # Create concept hierarchy morphisms
            for concept_obj in store.get_objects_by_type("Concept"):
                parent_ids = concept_obj.metadata.get("parent_ids", [])
                for parent_id in parent_ids:
                    if store.get_object(parent_id):
                        mor = StoredMorphism(
                            name="subfield_of",
                            source_name=concept_obj.name,
                            target_name=parent_id,
                            metadata={"type": "hierarchy"},
                            provenance="openalex"
                        )
                        store.add_morphism(mor)
                        count += 1

                related_ids = concept_obj.metadata.get("related_ids", [])
                for related_id in related_ids:
                    if store.get_object(related_id):
                        mor = StoredMorphism(
                            name="related_to",
                            source_name=concept_obj.name,
                            target_name=related_id,
                            metadata={"type": "semantic_relation"},
                            provenance="openalex"
                        )
                        store.add_morphism(mor)
                        count += 1

        return count


# =============================================================================
# PDF Loader
# =============================================================================

class PDFLoader:
    """
    Load data from PDF documents.

    Extracts text and metadata from PDFs for building categorical structures.
    Requires PyMuPDF (fitz) or pdfplumber.

    Usage:
        loader = PDFLoader()
        work = loader.parse_pdf("paper.pdf")
        store.add_object(work.to_object())
    """

    def __init__(self):
        """Initialize the PDF loader."""
        self._backend = None
        self._init_backend()

    def _init_backend(self):
        """Initialize PDF parsing backend."""
        try:
            import fitz  # PyMuPDF
            self._backend = "pymupdf"
            return
        except ImportError:
            pass

        try:
            import pdfplumber
            self._backend = "pdfplumber"
            return
        except ImportError:
            pass

        print("[PDFLoader] WARNING: No PDF backend available")
        print("  Install with: pip install pymupdf  or  pip install pdfplumber")

    @property
    def is_available(self) -> bool:
        """Check if PDF parsing is available."""
        return self._backend is not None

    def parse_pdf(self, filepath: Union[str, Path]) -> Optional[ParsedWork]:
        """
        Parse a single PDF file.

        Args:
            filepath: Path to PDF file

        Returns:
            ParsedWork instance, or None if parsing fails
        """
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"[PDFLoader] File not found: {filepath}")
            return None

        if self._backend == "pymupdf":
            return self._parse_pymupdf(filepath)
        elif self._backend == "pdfplumber":
            return self._parse_pdfplumber(filepath)
        else:
            return None

    def _parse_pymupdf(self, filepath: Path) -> Optional[ParsedWork]:
        """Parse PDF using PyMuPDF."""
        try:
            import fitz

            doc = fitz.open(str(filepath))

            # Extract metadata
            metadata = doc.metadata or {}
            title = metadata.get("title") or filepath.stem
            author = metadata.get("author", "")
            authors = [a.strip() for a in author.split(",")] if author else []

            # Extract text (first few pages for abstract)
            full_text = ""
            for page_num in range(min(3, len(doc))):
                page = doc[page_num]
                full_text += page.get_text()

            # Try to extract abstract
            abstract = self._extract_abstract(full_text)

            # Generate ID from filename
            work_id = self._generate_id(filepath.name)

            doc.close()

            return ParsedWork(
                id=work_id,
                title=title,
                abstract=abstract,
                authors=authors,
                metadata={
                    "filepath": str(filepath),
                    "pages": len(doc),
                    "creation_date": metadata.get("creationDate")
                },
                provenance=f"pdf:{filepath.name}"
            )

        except Exception as e:
            print(f"[PDFLoader] Error parsing {filepath}: {e}")
            return None

    def _parse_pdfplumber(self, filepath: Path) -> Optional[ParsedWork]:
        """Parse PDF using pdfplumber."""
        try:
            import pdfplumber

            with pdfplumber.open(str(filepath)) as pdf:
                # Extract metadata
                metadata = pdf.metadata or {}
                title = metadata.get("Title") or filepath.stem
                author = metadata.get("Author", "")
                authors = [a.strip() for a in author.split(",")] if author else []

                # Extract text (first few pages for abstract)
                full_text = ""
                for page in pdf.pages[:3]:
                    text = page.extract_text()
                    if text:
                        full_text += text

                # Try to extract abstract
                abstract = self._extract_abstract(full_text)

                # Generate ID from filename
                work_id = self._generate_id(filepath.name)

                return ParsedWork(
                    id=work_id,
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    metadata={
                        "filepath": str(filepath),
                        "pages": len(pdf.pages),
                        "creation_date": metadata.get("CreationDate")
                    },
                    provenance=f"pdf:{filepath.name}"
                )

        except Exception as e:
            print(f"[PDFLoader] Error parsing {filepath}: {e}")
            return None

    @staticmethod
    def _extract_abstract(text: str) -> Optional[str]:
        """Try to extract abstract from text."""
        # Look for "Abstract" section
        patterns = [
            r"(?i)abstract[:\s]*\n(.+?)(?=\n\s*\n|\n[A-Z][a-z]+:|\n\d+\.|\nIntroduction)",
            r"(?i)abstract[:\s]+(.{100,1000}?)(?=\.\s+[A-Z]|\n\n)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                # Clean up
                abstract = re.sub(r'\s+', ' ', abstract)
                if len(abstract) > 50:  # Minimum sensible length
                    return abstract

        return None

    @staticmethod
    def _generate_id(filename: str) -> str:
        """Generate a unique ID from filename."""
        # Remove extension and hash
        base = Path(filename).stem
        hash_suffix = hashlib.md5(filename.encode()).hexdigest()[:8]
        return f"pdf_{base}_{hash_suffix}"

    def iter_directory(
        self,
        directory: Union[str, Path],
        recursive: bool = True
    ) -> Generator[ParsedWork, None, None]:
        """
        Iterate over all PDFs in a directory.

        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories

        Yields:
            ParsedWork instances
        """
        directory = Path(directory)
        if not directory.exists():
            print(f"[PDFLoader] Directory not found: {directory}")
            return

        pattern = "**/*.pdf" if recursive else "*.pdf"
        for pdf_path in directory.glob(pattern):
            work = self.parse_pdf(pdf_path)
            if work:
                yield work


# =============================================================================
# Wikidata Loader
# =============================================================================

class WikidataLoader:
    """
    Load data from Wikidata JSON exports.

    Wikidata provides structured knowledge about entities (people, places,
    concepts, etc.) with rich relationships (claims).

    Usage:
        loader = WikidataLoader()
        for entity in loader.iter_entities("wikidata-dump.json"):
            store.add_object(entity.to_object())
    """

    # Common property IDs we care about
    RELEVANT_PROPERTIES = {
        "P31": "instance_of",
        "P279": "subclass_of",
        "P361": "part_of",
        "P527": "has_part",
        "P737": "influenced_by",
        "P800": "notable_work",
        "P101": "field_of_work",
        "P1066": "student_of",
        "P185": "doctoral_student",
        "P569": "date_of_birth",
        "P570": "date_of_death",
        "P19": "place_of_birth",
        "P108": "employer",
        "P112": "founded_by",
        "P135": "movement",
        "P1344": "participant_in",
    }

    def iter_entities(
        self,
        filepath: Union[str, Path],
        entity_types: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Generator[ParsedEntity, None, None]:
        """
        Iterate over entities in a Wikidata JSON dump.

        Args:
            filepath: Path to JSON/JSONL file
            entity_types: Filter by instance_of (P31) values
            limit: Maximum number of entities to yield

        Yields:
            ParsedEntity instances
        """
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"[WikidataLoader] File not found: {filepath}")
            return

        count = 0
        with open(filepath, 'r', encoding='utf-8') as f:
            # Handle both JSON array and JSONL formats
            first_char = f.read(1)
            f.seek(0)

            if first_char == '[':
                # JSON array format
                data = json.load(f)
                for item in data:
                    entity = self._parse_entity(item)
                    if entity and self._matches_filter(entity, entity_types):
                        yield entity
                        count += 1
                        if limit and count >= limit:
                            return
            else:
                # JSONL format
                for line in f:
                    if not line.strip() or line.strip() in '[],':
                        continue
                    try:
                        item = json.loads(line.rstrip(',\n'))
                        entity = self._parse_entity(item)
                        if entity and self._matches_filter(entity, entity_types):
                            yield entity
                            count += 1
                            if limit and count >= limit:
                                return
                    except json.JSONDecodeError:
                        continue

    def _parse_entity(self, data: Dict[str, Any]) -> Optional[ParsedEntity]:
        """Parse a single Wikidata entity."""
        try:
            entity_id = data.get("id", "")
            if not entity_id:
                return None

            # Get label (preferring English)
            labels = data.get("labels", {})
            label = labels.get("en", {}).get("value") or entity_id

            # Get description
            descriptions = data.get("descriptions", {})
            description = descriptions.get("en", {}).get("value")

            # Get aliases
            all_aliases = data.get("aliases", {})
            aliases = [a.get("value") for a in all_aliases.get("en", [])]

            # Parse claims (relationships)
            claims = {}
            for prop_id, claim_list in data.get("claims", {}).items():
                prop_name = self.RELEVANT_PROPERTIES.get(prop_id, prop_id)
                values = []
                for claim in claim_list:
                    mainsnak = claim.get("mainsnak", {})
                    datavalue = mainsnak.get("datavalue", {})
                    if datavalue.get("type") == "wikibase-entityid":
                        value_id = datavalue.get("value", {}).get("id")
                        if value_id:
                            values.append(value_id)
                    elif datavalue.get("type") == "time":
                        time_str = datavalue.get("value", {}).get("time")
                        if time_str:
                            values.append(time_str)
                    elif datavalue.get("type") == "string":
                        values.append(datavalue.get("value", ""))

                if values:
                    claims[prop_name] = values

            # Get sitelinks
            sitelinks = {}
            for site, link_data in data.get("sitelinks", {}).items():
                sitelinks[site] = link_data.get("title", "")

            return ParsedEntity(
                id=entity_id,
                label=label,
                description=description,
                aliases=aliases,
                claims=claims,
                sitelinks=sitelinks,
                provenance="wikidata"
            )

        except Exception as e:
            return None

    def _matches_filter(
        self,
        entity: ParsedEntity,
        entity_types: Optional[List[str]]
    ) -> bool:
        """Check if entity matches type filter."""
        if not entity_types:
            return True

        instance_of = entity.claims.get("instance_of", [])
        return any(t in instance_of for t in entity_types)

    def create_morphisms(self, store: KomposOSStore) -> int:
        """
        Create morphisms from Wikidata claims.

        Args:
            store: The store to add morphisms to

        Returns:
            Number of morphisms created
        """
        count = 0

        for entity_obj in store.get_objects_by_type("Entity"):
            claims = entity_obj.metadata.get("claims", {})

            for prop_name, target_ids in claims.items():
                if prop_name in ["date_of_birth", "date_of_death"]:
                    continue  # Skip date properties

                for target_id in target_ids:
                    # Only create if target exists
                    if store.get_object(target_id):
                        mor = StoredMorphism(
                            name=prop_name,
                            source_name=entity_obj.name,
                            target_name=target_id,
                            metadata={"source": "wikidata"},
                            provenance="wikidata"
                        )
                        store.add_morphism(mor)
                        count += 1

        return count


# =============================================================================
# CSV/JSON Loader (Custom Data)
# =============================================================================

class CustomDataLoader:
    """
    Load custom data from CSV or JSON files.

    Supports user-defined objects and morphisms in simple tabular formats.

    CSV Objects format:
        name,type,metadata_json
        "Newton","Physicist","{""era"": ""classical""}"

    CSV Morphisms format:
        name,source,target,metadata_json
        "influenced","Newton","Hamilton","{""year"": 1833}"

    JSON format:
        {
            "objects": [...],
            "morphisms": [...]
        }
    """

    def load_objects_csv(
        self,
        filepath: Union[str, Path],
        type_name: str = "Object"
    ) -> Generator[StoredObject, None, None]:
        """
        Load objects from a CSV file.

        Args:
            filepath: Path to CSV file
            type_name: Default type name if not specified in CSV

        Yields:
            StoredObject instances
        """
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"[CustomDataLoader] File not found: {filepath}")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("name", "").strip()
                if not name:
                    continue

                obj_type = row.get("type", type_name).strip()

                # Parse metadata
                metadata = {}
                metadata_str = row.get("metadata") or row.get("metadata_json")
                if metadata_str:
                    try:
                        metadata = json.loads(metadata_str)
                    except json.JSONDecodeError:
                        pass

                # Add any other columns as metadata
                for key, value in row.items():
                    if key not in ["name", "type", "metadata", "metadata_json"]:
                        metadata[key] = value

                yield StoredObject(
                    name=name,
                    type_name=obj_type,
                    metadata=metadata,
                    provenance=f"csv:{filepath.name}"
                )

    def load_morphisms_csv(
        self,
        filepath: Union[str, Path]
    ) -> Generator[StoredMorphism, None, None]:
        """
        Load morphisms from a CSV file.

        Args:
            filepath: Path to CSV file

        Yields:
            StoredMorphism instances
        """
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"[CustomDataLoader] File not found: {filepath}")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("name", "").strip()
                source = row.get("source", "").strip()
                target = row.get("target", "").strip()

                if not (name and source and target):
                    continue

                # Parse metadata
                metadata = {}
                metadata_str = row.get("metadata") or row.get("metadata_json")
                if metadata_str:
                    try:
                        metadata = json.loads(metadata_str)
                    except json.JSONDecodeError:
                        pass

                # Parse confidence
                confidence = 1.0
                if "confidence" in row:
                    try:
                        confidence = float(row["confidence"])
                    except ValueError:
                        pass

                yield StoredMorphism(
                    name=name,
                    source_name=source,
                    target_name=target,
                    metadata=metadata,
                    confidence=confidence,
                    provenance=f"csv:{filepath.name}"
                )

    def load_json(
        self,
        filepath: Union[str, Path]
    ) -> Tuple[List[StoredObject], List[StoredMorphism]]:
        """
        Load objects and morphisms from a JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            Tuple of (objects_list, morphisms_list)
        """
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"[CustomDataLoader] File not found: {filepath}")
            return [], []

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        objects = []
        for obj_data in data.get("objects", []):
            obj = StoredObject(
                name=obj_data.get("name", ""),
                type_name=obj_data.get("type", "Object"),
                metadata=obj_data.get("metadata", {}),
                provenance=f"json:{filepath.name}"
            )
            if obj.name:
                objects.append(obj)

        morphisms = []
        for mor_data in data.get("morphisms", []):
            mor = StoredMorphism(
                name=mor_data.get("name", ""),
                source_name=mor_data.get("source", ""),
                target_name=mor_data.get("target", ""),
                metadata=mor_data.get("metadata", {}),
                confidence=mor_data.get("confidence", 1.0),
                provenance=f"json:{filepath.name}"
            )
            if mor.name and mor.source_name and mor.target_name:
                morphisms.append(mor)

        return objects, morphisms


# =============================================================================
# BibTeX Loader
# =============================================================================

class BibTeXLoader:
    """
    Load data from BibTeX bibliography files.

    Extracts citations as works and creates citation morphisms.
    """

    def iter_entries(
        self,
        filepath: Union[str, Path]
    ) -> Generator[ParsedWork, None, None]:
        """
        Iterate over BibTeX entries.

        Args:
            filepath: Path to .bib file

        Yields:
            ParsedWork instances
        """
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"[BibTeXLoader] File not found: {filepath}")
            return

        try:
            # Try using bibtexparser if available
            import bibtexparser
            with open(filepath, 'r', encoding='utf-8') as f:
                bib_database = bibtexparser.load(f)

            for entry in bib_database.entries:
                yield self._parse_entry(entry)

        except ImportError:
            # Fallback to simple regex parsing
            for entry in self._parse_bibtex_simple(filepath):
                yield entry

    def _parse_entry(self, entry: Dict[str, str]) -> ParsedWork:
        """Parse a bibtexparser entry."""
        entry_id = entry.get("ID", "")
        title = entry.get("title", entry_id).strip("{}")
        abstract = entry.get("abstract", "").strip("{}")

        # Parse year
        year = None
        if "year" in entry:
            try:
                year = int(entry["year"])
            except ValueError:
                pass

        # Parse authors
        author_str = entry.get("author", "")
        authors = [a.strip() for a in author_str.replace(" and ", ",").split(",") if a.strip()]

        return ParsedWork(
            id=f"bib_{entry_id}",
            title=title,
            abstract=abstract if abstract else None,
            year=year,
            authors=authors,
            metadata={
                "entry_type": entry.get("ENTRYTYPE"),
                "journal": entry.get("journal"),
                "booktitle": entry.get("booktitle"),
                "doi": entry.get("doi"),
            },
            provenance="bibtex"
        )

    def _parse_bibtex_simple(self, filepath: Path) -> Generator[ParsedWork, None, None]:
        """Simple regex-based BibTeX parsing."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Match entries like @article{key, ... }
        entry_pattern = r'@(\w+)\{([^,]+),([^@]*)\}'

        for match in re.finditer(entry_pattern, content, re.DOTALL):
            entry_type = match.group(1)
            entry_key = match.group(2).strip()
            fields_str = match.group(3)

            # Parse fields
            fields = {}
            field_pattern = r'(\w+)\s*=\s*[{"](.*?)[}"]'
            for field_match in re.finditer(field_pattern, fields_str, re.DOTALL):
                field_name = field_match.group(1).lower()
                field_value = field_match.group(2).strip()
                fields[field_name] = field_value

            title = fields.get("title", entry_key)
            abstract = fields.get("abstract")

            year = None
            if "year" in fields:
                try:
                    year = int(fields["year"])
                except ValueError:
                    pass

            author_str = fields.get("author", "")
            authors = [a.strip() for a in author_str.replace(" and ", ",").split(",") if a.strip()]

            yield ParsedWork(
                id=f"bib_{entry_key}",
                title=title,
                abstract=abstract,
                year=year,
                authors=authors,
                metadata={
                    "entry_type": entry_type,
                    "journal": fields.get("journal"),
                    "doi": fields.get("doi"),
                },
                provenance="bibtex"
            )


# =============================================================================
# Unified Corpus Loader
# =============================================================================

class CorpusLoader:
    """
    Unified loader for multiple data sources.

    Handles a corpus directory with the following structure:
        corpus/
        ├── openalex/         # OpenAlex JSONL exports
        │   ├── works/
        │   └── concepts/
        ├── pdfs/             # PDF documents
        ├── wikidata/         # Wikidata JSON exports
        ├── custom/           # Custom CSV/JSON files
        │   ├── objects.csv
        │   └── morphisms.csv
        └── bibtex/           # BibTeX files
            └── references.bib

    Usage:
        loader = CorpusLoader("path/to/corpus")
        loader.load_all(store)
    """

    def __init__(self, corpus_path: Union[str, Path]):
        """
        Initialize the corpus loader.

        Args:
            corpus_path: Path to corpus directory
        """
        self.corpus_path = Path(corpus_path)
        self.openalex_loader = OpenAlexLoader(self.corpus_path / "openalex")
        self.pdf_loader = PDFLoader()
        self.wikidata_loader = WikidataLoader()
        self.custom_loader = CustomDataLoader()
        self.bibtex_loader = BibTeXLoader()

    def load_all(
        self,
        store: KomposOSStore,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, int]:
        """
        Load all data sources into the store.

        Args:
            store: Target store
            progress_callback: Optional callback(source, count)

        Returns:
            Dict of source -> count loaded
        """
        stats = {
            "openalex_works": 0,
            "openalex_concepts": 0,
            "pdfs": 0,
            "wikidata": 0,
            "custom_objects": 0,
            "custom_morphisms": 0,
            "bibtex": 0,
            "morphisms": 0,
        }

        # Load OpenAlex works
        openalex_dir = self.corpus_path / "openalex"
        if openalex_dir.exists():
            print("[CorpusLoader] Loading OpenAlex works...")
            for work in self.openalex_loader.iter_works():
                store.add_object(work.to_object())
                stats["openalex_works"] += 1
                if progress_callback:
                    progress_callback("openalex_works", stats["openalex_works"])

            print("[CorpusLoader] Loading OpenAlex concepts...")
            for concept in self.openalex_loader.iter_concepts():
                store.add_object(concept.to_object())
                stats["openalex_concepts"] += 1

        # Load PDFs
        pdfs_dir = self.corpus_path / "pdfs"
        if pdfs_dir.exists() and self.pdf_loader.is_available:
            print("[CorpusLoader] Loading PDFs...")
            for work in self.pdf_loader.iter_directory(pdfs_dir):
                store.add_object(work.to_object())
                stats["pdfs"] += 1

        # Load Wikidata
        wikidata_dir = self.corpus_path / "wikidata"
        if wikidata_dir.exists():
            print("[CorpusLoader] Loading Wikidata...")
            for json_file in wikidata_dir.glob("*.json"):
                for entity in self.wikidata_loader.iter_entities(json_file):
                    store.add_object(entity.to_object())
                    stats["wikidata"] += 1

        # Load custom data
        custom_dir = self.corpus_path / "custom"
        if custom_dir.exists():
            print("[CorpusLoader] Loading custom data...")
            for csv_file in custom_dir.glob("*objects*.csv"):
                for obj in self.custom_loader.load_objects_csv(csv_file):
                    store.add_object(obj)
                    stats["custom_objects"] += 1

            for csv_file in custom_dir.glob("*morphisms*.csv"):
                for mor in self.custom_loader.load_morphisms_csv(csv_file):
                    store.add_morphism(mor)
                    stats["custom_morphisms"] += 1

            for json_file in custom_dir.glob("*.json"):
                objects, morphisms = self.custom_loader.load_json(json_file)
                for obj in objects:
                    store.add_object(obj)
                    stats["custom_objects"] += 1
                for mor in morphisms:
                    store.add_morphism(mor)
                    stats["custom_morphisms"] += 1

        # Load BibTeX
        bibtex_dir = self.corpus_path / "bibtex"
        if bibtex_dir.exists():
            print("[CorpusLoader] Loading BibTeX...")
            for bib_file in bibtex_dir.glob("*.bib"):
                for work in self.bibtex_loader.iter_entries(bib_file):
                    store.add_object(work.to_object())
                    stats["bibtex"] += 1

        # Create morphisms from relationships
        print("[CorpusLoader] Creating morphisms from relationships...")
        if openalex_dir.exists():
            stats["morphisms"] += self.openalex_loader.create_morphisms(store)
        if wikidata_dir.exists():
            stats["morphisms"] += self.wikidata_loader.create_morphisms(store)

        return stats


# =============================================================================
# Demo
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("KOMPOSOS-III Data Sources Demo")
    print("=" * 70)

    # Create a sample corpus structure
    from .store import create_memory_store

    store = create_memory_store()

    # Demo custom data loading
    print("\n[1] Demo: Custom data loading")

    custom_loader = CustomDataLoader()

    # Create sample data
    sample_objects = [
        StoredObject("Newton", "Physicist", {"era": "classical", "birth": 1643}),
        StoredObject("Hamilton", "Physicist", {"era": "classical", "birth": 1805}),
        StoredObject("Schrödinger", "Physicist", {"era": "quantum", "birth": 1887}),
    ]
    sample_morphisms = [
        StoredMorphism("influenced", "Newton", "Hamilton", {"year": 1833}),
        StoredMorphism("wave_mechanics", "Hamilton", "Schrödinger", {"year": 1926}),
    ]

    for obj in sample_objects:
        store.add_object(obj)
    for mor in sample_morphisms:
        store.add_morphism(mor)

    print(f"  Added {len(sample_objects)} objects")
    print(f"  Added {len(sample_morphisms)} morphisms")

    # Show statistics
    stats = store.get_statistics()
    print(f"\n[2] Store statistics:")
    for k, v in stats.items():
        print(f"    {k}: {v}")

    # Find paths
    print(f"\n[3] Finding paths from Newton to Schrödinger...")
    paths = store.find_paths("Newton", "Schrödinger")
    for path in paths:
        print(f"    {path.source_name} -> {path.target_name} ({path.length} steps)")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("\nTo load real data, create a corpus directory with:")
    print("  corpus/")
    print("  ├── openalex/works/*.jsonl")
    print("  ├── pdfs/*.pdf")
    print("  ├── wikidata/*.json")
    print("  ├── custom/*.csv")
    print("  └── bibtex/*.bib")
