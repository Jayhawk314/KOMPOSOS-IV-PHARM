# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
KOMPOSOS-III Configuration
===========================

Configuration management for the data layer.

This module provides:
- Default paths for database and cache files
- Corpus directory structure specification
- Configuration file loading/saving
- Environment variable support

Configuration precedence (highest to lowest):
1. Environment variables (KOMPOSOS3_*)
2. Local config file (.komposos3.json)
3. User config file (~/.komposos3/config.json)
4. Default values
"""

from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict


# =============================================================================
# Default Paths
# =============================================================================

# Project data directory (in project folder, not hidden user folder)
DEFAULT_USER_DIR = Path(__file__).parent

# Database file
DEFAULT_DB_PATH = DEFAULT_USER_DIR / "store.db"

# Embeddings cache
DEFAULT_EMBEDDINGS_CACHE = DEFAULT_USER_DIR / "embeddings_cache"

# Default corpus directory
DEFAULT_CORPUS_DIR = Path.cwd() / "corpus"


# =============================================================================
# Corpus Directory Structure
# =============================================================================

CORPUS_STRUCTURE = """
Recommended corpus directory structure:

corpus/
├── openalex/                    # OpenAlex bulk data exports
│   ├── works/                   # Academic works (papers, articles)
│   │   ├── part_000.jsonl
│   │   ├── part_001.jsonl
│   │   └── ...
│   └── concepts/                # Concept hierarchy
│       └── concepts.jsonl
│
├── pdfs/                        # PDF documents
│   ├── papers/                  # Research papers
│   ├── notes/                   # Personal notes
│   └── books/                   # Book chapters
│
├── wikidata/                    # Wikidata entity exports
│   ├── philosophers.json        # e.g., philosophers subset
│   ├── scientists.json
│   └── concepts.json
│
├── custom/                      # Custom user data
│   ├── objects.csv              # Objects in CSV format
│   ├── morphisms.csv            # Morphisms in CSV format
│   └── data.json                # Combined JSON format
│
├── bibtex/                      # Bibliography files
│   ├── references.bib
│   └── library.bib
│
└── README.md                    # Documentation for your corpus
"""

# Expected subdirectories
CORPUS_SUBDIRS = [
    "openalex/works",
    "openalex/concepts",
    "pdfs/papers",
    "pdfs/notes",
    "wikidata",
    "custom",
    "bibtex",
]


# =============================================================================
# Configuration Data Class
# =============================================================================

@dataclass
class KomposOSConfig:
    """
    Configuration for KOMPOSOS-III.

    Attributes:
        db_path: Path to SQLite database file
        corpus_dir: Path to corpus directory
        embeddings_model: Sentence Transformer model name
        embeddings_cache_dir: Path to embeddings cache
        embeddings_device: Device to run embeddings on
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        parallel_workers: Number of parallel workers for processing
    """
    # Database
    db_path: Path = field(default_factory=lambda: DEFAULT_DB_PATH)

    # Corpus
    corpus_dir: Path = field(default_factory=lambda: DEFAULT_CORPUS_DIR)

    # Embeddings
    embeddings_model: str = "all-mpnet-base-v2"
    embeddings_cache_dir: Path = field(default_factory=lambda: DEFAULT_EMBEDDINGS_CACHE)
    embeddings_device: Optional[str] = None  # 'cpu', 'cuda', etc.

    # Processing
    log_level: str = "INFO"
    parallel_workers: int = 4

    # OpenAlex specific
    openalex_year_min: Optional[int] = None
    openalex_year_max: Optional[int] = None
    openalex_max_works: Optional[int] = None

    def __post_init__(self):
        """Convert string paths to Path objects."""
        if isinstance(self.db_path, str):
            self.db_path = Path(self.db_path)
        if isinstance(self.corpus_dir, str):
            self.corpus_dir = Path(self.corpus_dir)
        if isinstance(self.embeddings_cache_dir, str):
            self.embeddings_cache_dir = Path(self.embeddings_cache_dir)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (with paths as strings)."""
        d = asdict(self)
        d["db_path"] = str(self.db_path)
        d["corpus_dir"] = str(self.corpus_dir)
        d["embeddings_cache_dir"] = str(self.embeddings_cache_dir)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'KomposOSConfig':
        """Create from dictionary."""
        return cls(**d)

    def save(self, filepath: Optional[Path] = None):
        """Save configuration to file."""
        if filepath is None:
            filepath = DEFAULT_USER_DIR / "config.json"

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: Optional[Path] = None) -> 'KomposOSConfig':
        """Load configuration from file."""
        if filepath is None:
            filepath = DEFAULT_USER_DIR / "config.json"

        if not filepath.exists():
            return cls()  # Return defaults

        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


# =============================================================================
# Environment Variable Support
# =============================================================================

def load_from_env(config: Optional[KomposOSConfig] = None) -> KomposOSConfig:
    """
    Load configuration from environment variables.

    Environment variables (all optional):
        KOMPOSOS3_DB_PATH: Database file path
        KOMPOSOS3_CORPUS_DIR: Corpus directory path
        KOMPOSOS3_EMBEDDINGS_MODEL: Sentence Transformer model name
        KOMPOSOS3_EMBEDDINGS_DEVICE: Device for embeddings
        KOMPOSOS3_LOG_LEVEL: Logging level
        KOMPOSOS3_PARALLEL_WORKERS: Number of parallel workers

    Args:
        config: Base configuration to override (uses defaults if None)

    Returns:
        Configuration with environment overrides applied
    """
    if config is None:
        config = KomposOSConfig()

    env_map = {
        "KOMPOSOS3_DB_PATH": ("db_path", Path),
        "KOMPOSOS3_CORPUS_DIR": ("corpus_dir", Path),
        "KOMPOSOS3_EMBEDDINGS_MODEL": ("embeddings_model", str),
        "KOMPOSOS3_EMBEDDINGS_DEVICE": ("embeddings_device", str),
        "KOMPOSOS3_LOG_LEVEL": ("log_level", str),
        "KOMPOSOS3_PARALLEL_WORKERS": ("parallel_workers", int),
        "KOMPOSOS3_OPENALEX_YEAR_MIN": ("openalex_year_min", int),
        "KOMPOSOS3_OPENALEX_YEAR_MAX": ("openalex_year_max", int),
    }

    for env_var, (attr_name, type_fn) in env_map.items():
        value = os.getenv(env_var)
        if value is not None:
            try:
                setattr(config, attr_name, type_fn(value))
            except (ValueError, TypeError):
                pass

    return config


def get_config() -> KomposOSConfig:
    """
    Get the current configuration.

    Loads from (in order of precedence):
    1. Environment variables
    2. Local .komposos3.json
    3. User config (~/.komposos3/config.json)
    4. Defaults

    Returns:
        KomposOSConfig instance
    """
    # Start with defaults
    config = KomposOSConfig()

    # Load user config if exists
    user_config_path = DEFAULT_USER_DIR / "config.json"
    if user_config_path.exists():
        config = KomposOSConfig.load(user_config_path)

    # Load local config if exists
    local_config_path = Path.cwd() / ".komposos3.json"
    if local_config_path.exists():
        config = KomposOSConfig.load(local_config_path)

    # Apply environment overrides
    config = load_from_env(config)

    return config


# =============================================================================
# Corpus Setup
# =============================================================================

def init_corpus(corpus_dir: Optional[Path] = None) -> Path:
    """
    Initialize a corpus directory with the recommended structure.

    Args:
        corpus_dir: Directory to initialize (uses DEFAULT_CORPUS_DIR if None)

    Returns:
        Path to the initialized corpus directory
    """
    if corpus_dir is None:
        corpus_dir = DEFAULT_CORPUS_DIR

    corpus_dir = Path(corpus_dir)

    # Create subdirectories
    for subdir in CORPUS_SUBDIRS:
        (corpus_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Create README
    readme_path = corpus_dir / "README.md"
    if not readme_path.exists():
        with open(readme_path, 'w') as f:
            f.write("# KOMPOSOS-III Corpus\n\n")
            f.write("This directory contains data for KOMPOSOS-III.\n\n")
            f.write("## Structure\n")
            f.write(CORPUS_STRUCTURE)
            f.write("\n## Data Formats\n\n")
            f.write("### OpenAlex\n")
            f.write("Download from: https://openalex.org/data-dump\n\n")
            f.write("### Custom CSV Objects\n")
            f.write("```\nname,type,metadata_json\n")
            f.write('"Newton","Physicist","{""era"": ""classical""}"\n')
            f.write("```\n\n")
            f.write("### Custom CSV Morphisms\n")
            f.write("```\nname,source,target,metadata_json,confidence\n")
            f.write('"influenced","Newton","Hamilton","{""year"": 1833}",0.95\n')
            f.write("```\n")

    # Create sample custom files
    objects_sample_path = corpus_dir / "custom" / "objects_sample.csv"
    if not objects_sample_path.exists():
        with open(objects_sample_path, 'w') as f:
            f.write("name,type,era,birth_year\n")
            f.write("Newton,Physicist,classical,1643\n")
            f.write("Hamilton,Physicist,classical,1805\n")
            f.write("Schrödinger,Physicist,quantum,1887\n")

    morphisms_sample_path = corpus_dir / "custom" / "morphisms_sample.csv"
    if not morphisms_sample_path.exists():
        with open(morphisms_sample_path, 'w') as f:
            f.write("name,source,target,year,confidence\n")
            f.write("influenced,Newton,Hamilton,1833,0.95\n")
            f.write("wave_mechanics,Hamilton,Schrödinger,1926,1.0\n")

    print(f"[init_corpus] Initialized corpus at: {corpus_dir}")
    print(f"[init_corpus] Created directories:")
    for subdir in CORPUS_SUBDIRS:
        print(f"    {subdir}/")

    return corpus_dir


def verify_corpus(corpus_dir: Optional[Path] = None) -> Dict[str, bool]:
    """
    Verify a corpus directory structure.

    Args:
        corpus_dir: Directory to verify

    Returns:
        Dict of path -> exists for each expected path
    """
    if corpus_dir is None:
        corpus_dir = DEFAULT_CORPUS_DIR

    corpus_dir = Path(corpus_dir)
    results = {}

    for subdir in CORPUS_SUBDIRS:
        path = corpus_dir / subdir
        results[subdir] = path.exists()

    return results


# =============================================================================
# Demo
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("KOMPOSOS-III Configuration Demo")
    print("=" * 70)

    # Show defaults
    print("\n[1] Default configuration:")
    config = KomposOSConfig()
    for key, value in config.to_dict().items():
        print(f"    {key}: {value}")

    # Show environment
    print("\n[2] Environment variables:")
    for var in ["KOMPOSOS3_DB_PATH", "KOMPOSOS3_CORPUS_DIR", "KOMPOSOS3_EMBEDDINGS_MODEL"]:
        value = os.getenv(var)
        print(f"    {var}: {value or '(not set)'}")

    # Show corpus structure
    print("\n[3] Recommended corpus structure:")
    print(CORPUS_STRUCTURE)

    # Initialize corpus
    print("\n[4] Would you like to initialize a corpus? (demo only)")
    print("    Run: from data.config import init_corpus; init_corpus()")

    print("\n" + "=" * 70)
    print("Demo complete!")
