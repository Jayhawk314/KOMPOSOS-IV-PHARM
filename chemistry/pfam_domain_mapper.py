# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Pfam Domain Mapper
==================

Maps protein sequences to Pfam domain annotations via the InterPro REST API.
Provides a verification layer for ESM-2 contact predictions by cross-referencing
predicted binding regions against established, peer-reviewed domain annotations.

Integration Points:
- Contact prediction: boost/penalize confidence based on domain agreement
- Oracle inference: shared domain composition as evidence for functional relationships
- Validation: domain-contact agreement checking
- Knowledge graph: domain annotations as verified axioms

Data Source:
- InterPro REST API (https://www.ebi.ac.uk/interpro/api/)
- Local cache to avoid redundant API calls
- Built-in fallback signatures for common domains (offline capability)

References:
- Pfam: https://www.ebi.ac.uk/interpro/entry/pfam/
- InterPro: https://www.ebi.ac.uk/interpro/
- Mistry et al. (2021) Nucleic Acids Research 49(D1):D419-D427
"""

import gzip
import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


@dataclass
class PfamDomain:
    """A Pfam domain annotation on a protein sequence."""
    accession: str          # e.g., "PF00069"
    name: str               # e.g., "Pkinase"
    description: str        # e.g., "Protein kinase domain"
    start: int              # 0-indexed start position in sequence
    end: int                # 0-indexed end position (exclusive)
    evalue: float = 0.0     # E-value from search (lower = more significant)
    domain_type: str = "domain"  # "domain", "family", "repeat", "motif"
    active_site_residues: List[int] = field(default_factory=list)  # Known active site positions

    @property
    def length(self) -> int:
        return self.end - self.start

    def contains_position(self, pos: int) -> bool:
        """Check if a residue position falls within this domain."""
        return self.start <= pos < self.end

    def overlaps_with(self, other: 'PfamDomain') -> bool:
        """Check if two domains overlap in sequence space."""
        return self.start < other.end and other.start < self.end


@dataclass
class TemplateMatch:
    """A PDB template structure matched via Pfam domain identification."""
    pdb_id: str                     # e.g., "1ATP"
    chain: str                      # e.g., "E"
    domain: PfamDomain              # The Pfam domain that identified this template
    coordinates: np.ndarray         # (N, 3) Cα coordinates from PDB
    template_sequence_length: int   # Length of the template structure
    coverage: float                 # Fraction of query sequence covered by template


# Built-in mapping from Pfam accessions to representative PDB structures.
# These are well-characterized, high-resolution structures for common domains.
_PFAM_PDB_MAP = {
    "PF00069": {"pdb": "1ATP", "chain": "E", "desc": "Protein kinase (cAMP-dependent)"},
    "PF07714": {"pdb": "1IRK", "chain": "A", "desc": "Tyrosine kinase (insulin receptor)"},
    "PF00076": {"pdb": "1FXL", "chain": "A", "desc": "RNA recognition motif"},
    "PF00096": {"pdb": "1ZAA", "chain": "A", "desc": "Zinc finger C2H2"},
    "PF00271": {"pdb": "1HEI", "chain": "A", "desc": "Helicase C-terminal"},
    "PF00046": {"pdb": "1AHD", "chain": "A", "desc": "Homeobox"},
    "PF00400": {"pdb": "1ERJ", "chain": "A", "desc": "WD40 repeat"},
    "PF00105": {"pdb": "1HCQ", "chain": "A", "desc": "Zinc finger C4 (nuclear receptor)"},
    "PF00001": {"pdb": "1F88", "chain": "A", "desc": "7TM GPCR rhodopsin"},
    "PF00071": {"pdb": "5P21", "chain": "A", "desc": "Ras family GTPase"},
    "PF00089": {"pdb": "1A0H", "chain": "A", "desc": "Trypsin serine protease"},
    "PF00497": {"pdb": "1STP", "chain": "A", "desc": "Bacterial SBP"},
}


# Built-in fallback domain signatures for common protein families.
# These allow offline operation and testing without API access.
# Signatures are simplified regex-like motifs matched against sequences.
_FALLBACK_SIGNATURES = {
    "PF00069": {
        "name": "Pkinase",
        "description": "Protein kinase domain",
        "domain_type": "domain",
        "motifs": ["HRD", "DFG", "APE"],  # Conserved kinase motifs
        "min_length": 200,
    },
    "PF00076": {
        "name": "RRM_1",
        "description": "RNA recognition motif",
        "domain_type": "domain",
        "motifs": ["RNP1", "LFVGN"],
        "min_length": 70,
    },
    "PF00096": {
        "name": "zf-C2H2",
        "description": "Zinc finger, C2H2 type",
        "domain_type": "domain",
        "motifs": ["CXXC", "HXXXH"],
        "min_length": 23,
    },
    "PF00271": {
        "name": "Helicase_C",
        "description": "Helicase conserved C-terminal domain",
        "domain_type": "domain",
        "motifs": ["DEXH", "SAT"],
        "min_length": 100,
    },
    "PF07714": {
        "name": "Pkinase_Tyr",
        "description": "Protein tyrosine kinase",
        "domain_type": "domain",
        "motifs": ["HRD", "DFG", "YXXP"],
        "min_length": 200,
    },
    "PF00046": {
        "name": "Homeobox",
        "description": "Homeobox domain",
        "domain_type": "domain",
        "motifs": ["WFQNRR"],
        "min_length": 57,
    },
    "PF00400": {
        "name": "WD40",
        "description": "WD domain, G-beta repeat",
        "domain_type": "repeat",
        "motifs": ["GH", "WD"],
        "min_length": 40,
    },
    "PF00105": {
        "name": "zf-C4",
        "description": "Zinc finger, C4 type (nuclear receptor)",
        "domain_type": "domain",
        "motifs": ["CXXXXC", "CXXC"],
        "min_length": 50,
    },
}

# Known active site motifs for specific domain types
_ACTIVE_SITE_MOTIFS = {
    "PF00069": ["HRD", "DFG"],      # Kinase catalytic residues
    "PF07714": ["HRD", "DFG"],      # Tyrosine kinase catalytic residues
    "PF00096": ["CXXC", "HXXXH"],   # Zinc-coordinating residues
    "PF00105": ["CXXXXC", "CXXC"],  # Zinc-coordinating residues
}


class PfamDomainMapper:
    """
    Maps protein sequences to Pfam domain annotations.

    Uses the InterPro REST API with local caching for performance.
    Falls back to built-in motif signatures when the API is unavailable.

    Usage:
        mapper = PfamDomainMapper()
        domains = mapper.lookup_domains("MKTAYIAKQRQISFVK...")
        active_sites = mapper.get_active_site_residues("MKTAYIAKQRQISFVK...")
    """

    # InterPro API endpoint for sequence search
    _API_BASE = "https://www.ebi.ac.uk/interpro/api"
    _SEARCH_URL = "https://www.ebi.ac.uk/Tools/services/rest/iprscan5"
    _TIMEOUT = 30  # seconds
    _MAX_RETRIES = 2
    _RETRY_DELAY = 2  # seconds

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the Pfam domain mapper.

        Args:
            cache_dir: Directory for caching API results.
                       Defaults to data/cache/pfam/ relative to project root.
        """
        if cache_dir is None:
            project_root = Path(__file__).parent.parent
            self.cache_dir = project_root / "data" / "cache" / "pfam"
        else:
            self.cache_dir = Path(cache_dir)

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for current session (avoids repeated disk reads)
        self._session_cache: Dict[str, List[PfamDomain]] = {}

    def lookup_domains(self, sequence: str) -> List[PfamDomain]:
        """
        Look up Pfam domains for a protein sequence.

        Tries in order:
        1. Session memory cache
        2. Local disk cache
        3. InterPro REST API
        4. Built-in fallback signatures

        Args:
            sequence: Amino acid sequence (one-letter codes)

        Returns:
            List of PfamDomain annotations, sorted by start position.
            Returns empty list if no domains found or all lookups fail.
        """
        sequence = sequence.upper().strip()
        if not sequence:
            return []

        cache_key = self._get_cache_key(sequence)

        # 1. Session cache
        if cache_key in self._session_cache:
            return self._session_cache[cache_key]

        # 2. Disk cache
        cached = self._load_from_cache(cache_key)
        if cached is not None:
            self._session_cache[cache_key] = cached
            return cached

        # 3. API lookup
        domains = self._query_interpro_api(sequence)

        # 4. Fallback to built-in signatures if API returned nothing
        if not domains:
            domains = self._match_fallback_signatures(sequence)

        # Sort by start position
        domains.sort(key=lambda d: d.start)

        # Cache result
        self._save_to_cache(cache_key, domains)
        self._session_cache[cache_key] = domains

        return domains

    def get_active_site_residues(self, sequence: str) -> Set[int]:
        """
        Get residue positions that are part of known active sites.

        Args:
            sequence: Amino acid sequence

        Returns:
            Set of 0-indexed residue positions in active sites
        """
        domains = self.lookup_domains(sequence)
        active_residues: Set[int] = set()

        for domain in domains:
            # Include explicitly annotated active site residues
            active_residues.update(domain.active_site_residues)

            # Also match active site motifs within domain boundaries
            if domain.accession in _ACTIVE_SITE_MOTIFS:
                for motif in _ACTIVE_SITE_MOTIFS[domain.accession]:
                    positions = self._find_motif_positions(
                        sequence, motif, domain.start, domain.end
                    )
                    active_residues.update(positions)

        return active_residues

    def get_domain_at_position(self, sequence: str, position: int) -> Optional[PfamDomain]:
        """
        Get the Pfam domain containing a specific residue position.

        Args:
            sequence: Amino acid sequence
            position: 0-indexed residue position

        Returns:
            PfamDomain if position falls within an annotated domain, else None.
            If multiple domains overlap, returns the one with lowest E-value.
        """
        domains = self.lookup_domains(sequence)
        matching = [d for d in domains if d.contains_position(position)]

        if not matching:
            return None

        # Return best (lowest E-value) match
        return min(matching, key=lambda d: d.evalue)

    def get_domain_map(self, sequence: str) -> Dict[int, Optional[PfamDomain]]:
        """
        Build a per-residue domain map for the full sequence.

        Args:
            sequence: Amino acid sequence

        Returns:
            Dict mapping each position to its PfamDomain (or None if unannotated)
        """
        domains = self.lookup_domains(sequence)
        domain_map: Dict[int, Optional[PfamDomain]] = {}

        for pos in range(len(sequence)):
            matching = [d for d in domains if d.contains_position(pos)]
            if matching:
                domain_map[pos] = min(matching, key=lambda d: d.evalue)
            else:
                domain_map[pos] = None

        return domain_map

    def domain_overlap(self, seq1: str, seq2: str) -> float:
        """
        Compute Pfam domain composition overlap (Jaccard similarity).

        Args:
            seq1: First protein sequence
            seq2: Second protein sequence

        Returns:
            Jaccard similarity of domain accession sets (0.0 to 1.0).
            Returns 0.0 if either protein has no annotated domains.
        """
        domains1 = self.lookup_domains(seq1)
        domains2 = self.lookup_domains(seq2)

        if not domains1 or not domains2:
            return 0.0

        accessions1 = {d.accession for d in domains1}
        accessions2 = {d.accession for d in domains2}

        intersection = len(accessions1 & accessions2)
        union = len(accessions1 | accessions2)

        return intersection / union if union > 0 else 0.0

    def residues_in_same_domain(self, sequence: str, pos_i: int, pos_j: int) -> Optional[PfamDomain]:
        """
        Check if two residue positions fall within the same Pfam domain.

        Args:
            sequence: Amino acid sequence
            pos_i: First residue position (0-indexed)
            pos_j: Second residue position (0-indexed)

        Returns:
            The shared PfamDomain if both positions are in the same domain, else None
        """
        domains = self.lookup_domains(sequence)

        for domain in domains:
            if domain.contains_position(pos_i) and domain.contains_position(pos_j):
                return domain

        return None

    # -------------------------------------------------------------------------
    # Internal methods
    # -------------------------------------------------------------------------

    def _get_cache_key(self, sequence: str) -> str:
        """Generate cache key from sequence MD5 hash."""
        return hashlib.md5(sequence.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> Optional[List[PfamDomain]]:
        """Load cached domain annotations from disk."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            domains = []
            for entry in data:
                domains.append(PfamDomain(
                    accession=entry['accession'],
                    name=entry['name'],
                    description=entry['description'],
                    start=entry['start'],
                    end=entry['end'],
                    evalue=entry.get('evalue', 0.0),
                    domain_type=entry.get('domain_type', 'domain'),
                    active_site_residues=entry.get('active_site_residues', []),
                ))
            return domains
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def _save_to_cache(self, cache_key: str, domains: List[PfamDomain]):
        """Save domain annotations to disk cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            data = []
            for d in domains:
                data.append({
                    'accession': d.accession,
                    'name': d.name,
                    'description': d.description,
                    'start': d.start,
                    'end': d.end,
                    'evalue': d.evalue,
                    'domain_type': d.domain_type,
                    'active_site_residues': d.active_site_residues,
                })
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass  # Cache write failure is non-fatal

    def _query_interpro_api(self, sequence: str) -> List[PfamDomain]:
        """
        Query InterPro REST API for Pfam domain annotations.

        Uses the InterProScan job submission endpoint. This is a synchronous
        lookup that submits the sequence and polls for results.

        Returns empty list on any failure (network, timeout, parse error).
        """
        if not HAS_REQUESTS:
            return []

        try:
            # Use the InterPro protein sequence search endpoint
            url = f"{self._API_BASE}/entry/pfam/protein/sequence/"

            for attempt in range(self._MAX_RETRIES):
                try:
                    response = requests.post(
                        url,
                        json={"sequence": sequence},
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        },
                        timeout=self._TIMEOUT,
                    )

                    if response.status_code == 200:
                        return self._parse_interpro_response(response.json(), sequence)
                    elif response.status_code == 408 or response.status_code >= 500:
                        # Timeout or server error - retry
                        if attempt < self._MAX_RETRIES - 1:
                            time.sleep(self._RETRY_DELAY)
                            continue
                    # Client error or unexpected status - don't retry
                    return []

                except requests.exceptions.Timeout:
                    if attempt < self._MAX_RETRIES - 1:
                        time.sleep(self._RETRY_DELAY)
                        continue
                    return []
                except requests.exceptions.ConnectionError:
                    return []  # No network - fall through to fallback

        except Exception:
            return []  # Any unexpected error - fall through to fallback

        return []

    def _parse_interpro_response(self, data: dict, sequence: str) -> List[PfamDomain]:
        """Parse InterPro API JSON response into PfamDomain objects."""
        domains = []

        try:
            # InterPro API response structure varies by endpoint
            # Handle both direct results and nested result formats
            results = data if isinstance(data, list) else data.get('results', [])

            for entry in results:
                metadata = entry.get('metadata', entry)
                accession = metadata.get('accession', '')
                name = metadata.get('name', '')
                description = metadata.get('description', name)
                entry_type = metadata.get('type', 'domain').lower()

                # Extract protein locations
                proteins = entry.get('proteins', [])
                for protein in proteins:
                    locations = protein.get('entry_protein_locations', [])
                    for location in locations:
                        fragments = location.get('fragments', [])
                        for fragment in fragments:
                            start = fragment.get('start', 1) - 1  # Convert to 0-indexed
                            end = fragment.get('end', len(sequence))

                            domains.append(PfamDomain(
                                accession=accession,
                                name=name,
                                description=description if isinstance(description, str) else name,
                                start=max(0, start),
                                end=min(end, len(sequence)),
                                evalue=fragment.get('evalue', location.get('score', 0.0)),
                                domain_type=entry_type,
                            ))
        except (KeyError, TypeError, IndexError):
            pass  # Malformed response - return whatever we have

        return domains

    def _match_fallback_signatures(self, sequence: str) -> List[PfamDomain]:
        """
        Match sequence against built-in domain signatures.

        This provides basic domain annotation when the API is unavailable.
        It is intentionally conservative - only matches well-characterized motifs.
        """
        domains = []
        seq_len = len(sequence)

        for accession, sig in _FALLBACK_SIGNATURES.items():
            if seq_len < sig["min_length"]:
                continue

            # Check if sequence contains the conserved motifs
            motif_positions = []
            for motif in sig["motifs"]:
                positions = self._find_motif_positions(sequence, motif, 0, seq_len)
                if positions:
                    motif_positions.extend(positions)

            if not motif_positions:
                continue

            # Estimate domain boundaries from motif positions
            # Domain extends ~20 residues before first motif and ~20 after last
            min_pos = max(0, min(motif_positions) - 20)
            max_pos = min(seq_len, max(motif_positions) + 20)

            # Only report if the estimated domain region is reasonable
            estimated_length = max_pos - min_pos
            if estimated_length < sig["min_length"] * 0.5:
                continue

            # Find active site residues
            active_sites = []
            if accession in _ACTIVE_SITE_MOTIFS:
                for motif in _ACTIVE_SITE_MOTIFS[accession]:
                    active_sites.extend(
                        self._find_motif_positions(sequence, motif, min_pos, max_pos)
                    )

            domains.append(PfamDomain(
                accession=accession,
                name=sig["name"],
                description=sig["description"],
                start=min_pos,
                end=max_pos,
                evalue=1.0,  # High E-value since this is a heuristic match
                domain_type=sig["domain_type"],
                active_site_residues=sorted(set(active_sites)),
            ))

        return domains

    # -------------------------------------------------------------------------
    # PDB template retrieval
    # -------------------------------------------------------------------------

    def get_representative_pdb(self, accession: str) -> Optional[Dict[str, str]]:
        """
        Get representative PDB structure for a Pfam domain.

        Args:
            accession: Pfam accession (e.g., "PF00069")

        Returns:
            Dict with "pdb" and "chain" keys, or None if unknown
        """
        return _PFAM_PDB_MAP.get(accession)

    def retrieve_template_structure(self, sequence: str) -> Optional[TemplateMatch]:
        """
        Retrieve a PDB template structure for a protein sequence.

        Pipeline: sequence → Pfam domains → PDB ID → download → parse Cα coords

        For proteins with recognized Pfam domains, this provides a known fold
        to initialize structure reconstruction instead of random coordinates.

        Args:
            sequence: Amino acid sequence

        Returns:
            TemplateMatch with PDB coordinates, or None if no template available
        """
        domains = self.lookup_domains(sequence)
        if not domains:
            return None

        # Try each domain (sorted by E-value, best first)
        for domain in sorted(domains, key=lambda d: d.evalue):
            pdb_info = self.get_representative_pdb(domain.accession)
            if pdb_info is None:
                continue

            pdb_id = pdb_info["pdb"]
            chain = pdb_info["chain"]

            # Download and parse PDB
            coords = self._get_pdb_ca_coords(pdb_id, chain)
            if coords is None or len(coords) == 0:
                continue

            # Compute coverage: what fraction of query sequence does
            # the template cover?
            coverage = min(len(coords), domain.length) / len(sequence)

            # If template is much shorter or longer, scale to match
            # the domain region of the query
            template_coords = self._fit_template_to_sequence(
                coords, len(sequence), domain.start, domain.end
            )

            return TemplateMatch(
                pdb_id=pdb_id,
                chain=chain,
                domain=domain,
                coordinates=template_coords,
                template_sequence_length=len(coords),
                coverage=coverage,
            )

        return None

    def retrieve_all_domain_templates(self, sequence: str) -> List[Tuple[PfamDomain, np.ndarray]]:
        """
        Retrieve template coordinates for ALL matching Pfam domains.

        Unlike retrieve_template_structure() which returns only the best match,
        this returns coordinates for every domain that has a known PDB template.

        Args:
            sequence: Amino acid sequence

        Returns:
            List of (PfamDomain, coordinates) tuples.
            Coordinates are (domain_length, 3) CA coords trimmed to domain boundaries.
        """
        domains = self.lookup_domains(sequence)
        results = []

        for domain in sorted(domains, key=lambda d: d.start):
            pdb_info = self.get_representative_pdb(domain.accession)
            if pdb_info is None:
                continue

            coords = self._get_pdb_ca_coords(pdb_info["pdb"], pdb_info["chain"])
            if coords is None or len(coords) == 0:
                continue

            domain_coords = self._fit_template_to_domain(coords, domain)
            results.append((domain, domain_coords))

        return results

    def _fit_template_to_domain(
        self, template_coords: np.ndarray, domain: PfamDomain
    ) -> np.ndarray:
        """
        Trim/pad template coordinates to exactly match domain length.

        If the template is longer than the domain, take the central portion.
        If shorter, center the template and pad with extended chain.

        Args:
            template_coords: (M, 3) CA coords from PDB template
            domain: The PfamDomain to fit

        Returns:
            (domain_length, 3) CA coordinates
        """
        domain_len = domain.end - domain.start
        template_len = len(template_coords)

        if template_len >= domain_len:
            # Template is longer -- take central portion
            offset = (template_len - domain_len) // 2
            return template_coords[offset:offset + domain_len].copy()
        else:
            # Template is shorter -- center it and pad
            result = np.zeros((domain_len, 3))
            offset = (domain_len - template_len) // 2
            result[offset:offset + template_len] = template_coords

            # Extend N-terminal side
            if offset > 0:
                anchor = template_coords[0]
                for i in range(offset - 1, -1, -1):
                    dist_back = offset - i
                    angle = dist_back * 0.3
                    result[i] = anchor + np.array([
                        -3.8 * dist_back,
                        np.sin(angle) * 1.5,
                        np.cos(angle) * 1.5,
                    ])

            # Extend C-terminal side
            c_start = offset + template_len
            if c_start < domain_len:
                anchor = template_coords[-1]
                for i in range(c_start, domain_len):
                    dist_fwd = i - c_start + 1
                    angle = dist_fwd * 0.3
                    result[i] = anchor + np.array([
                        3.8 * dist_fwd,
                        np.sin(angle) * 1.5,
                        np.cos(angle) * 1.5,
                    ])

            return result

    def _get_pdb_ca_coords(
        self, pdb_id: str, chain: str = "A"
    ) -> Optional[np.ndarray]:
        """
        Download a PDB file and extract Cα coordinates for a chain.

        Uses RCSB REST API with local caching.

        Args:
            pdb_id: PDB identifier (e.g., "1ATP")
            chain: Chain identifier (e.g., "E")

        Returns:
            (N, 3) numpy array of Cα coordinates, or None on failure
        """
        # Check cache
        template_cache = self.cache_dir.parent / "pdb_templates"
        template_cache.mkdir(parents=True, exist_ok=True)
        cache_file = template_cache / f"{pdb_id.lower()}_{chain}.npy"

        if cache_file.exists():
            try:
                return np.load(cache_file)
            except (ValueError, IOError):
                pass

        # Download from RCSB
        pdb_text = self._download_pdb(pdb_id)
        if pdb_text is None:
            return None

        # Parse Cα coordinates for the specified chain
        coords = self._parse_pdb_ca(pdb_text, chain)
        if coords is not None and len(coords) > 0:
            # Cache for next time
            try:
                np.save(cache_file, coords)
            except OSError:
                pass

        return coords

    def _download_pdb(self, pdb_id: str) -> Optional[str]:
        """Download PDB file from RCSB."""
        # Check raw PDB cache
        template_cache = self.cache_dir.parent / "pdb_templates"
        raw_cache = template_cache / f"{pdb_id.lower()}.pdb"

        if raw_cache.exists():
            try:
                with open(raw_cache, 'r') as f:
                    return f.read()
            except (IOError, UnicodeDecodeError):
                pass

        url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb.gz"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                compressed = response.read()
            pdb_bytes = gzip.decompress(compressed)
            pdb_text = pdb_bytes.decode('utf-8', errors='replace')

            # Cache raw PDB
            try:
                template_cache.mkdir(parents=True, exist_ok=True)
                with open(raw_cache, 'w') as f:
                    f.write(pdb_text)
            except OSError:
                pass

            return pdb_text
        except Exception:
            return None

    def _parse_pdb_ca(self, pdb_text: str, chain: str = "A") -> Optional[np.ndarray]:
        """Extract Cα coordinates from PDB text for a specific chain."""
        coords = []
        for line in pdb_text.split('\n'):
            if not line.startswith('ATOM'):
                continue
            if ' CA ' not in line:
                continue
            # Chain is column 21 (0-indexed)
            if len(line) > 21 and line[21] != chain:
                continue

            try:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                coords.append([x, y, z])
            except (ValueError, IndexError):
                continue

        if not coords:
            return None

        result = np.array(coords)
        # Center on origin
        result -= result.mean(axis=0)
        return result

    def _fit_template_to_sequence(
        self,
        template_coords: np.ndarray,
        query_length: int,
        domain_start: int,
        domain_end: int
    ) -> np.ndarray:
        """
        Fit template coordinates to the query sequence length.

        Places the template structure at the domain region and generates
        extended-chain coordinates for flanking regions.

        Args:
            template_coords: (M, 3) Cα coords from PDB template
            query_length: Length of query sequence
            domain_start: Where the domain starts in query (0-indexed)
            domain_end: Where the domain ends in query (exclusive)

        Returns:
            (query_length, 3) Cα coordinates covering the full sequence
        """
        full_coords = np.zeros((query_length, 3))
        domain_length = domain_end - domain_start
        template_length = len(template_coords)

        # Place template at domain region
        if template_length >= domain_length:
            # Template is longer or equal — take the central portion
            offset = (template_length - domain_length) // 2
            full_coords[domain_start:domain_end] = template_coords[offset:offset + domain_length]
        else:
            # Template is shorter — center it within domain region
            offset = (domain_length - template_length) // 2
            full_coords[domain_start + offset:domain_start + offset + template_length] = template_coords

        # Generate extended-chain coordinates for N-terminal flank
        if domain_start > 0:
            anchor = full_coords[domain_start]
            for i in range(domain_start - 1, -1, -1):
                # Extend backward with ~3.8 Å spacing along a direction
                direction = np.array([-3.8, 0.0, 0.0])
                # Add slight curvature to avoid linearity
                angle = (domain_start - i) * 0.3
                direction[1] = np.sin(angle) * 1.5
                direction[2] = np.cos(angle) * 1.5
                full_coords[i] = full_coords[i + 1] + direction

        # Generate extended-chain coordinates for C-terminal flank
        if domain_end < query_length:
            for i in range(domain_end, query_length):
                direction = np.array([3.8, 0.0, 0.0])
                angle = (i - domain_end) * 0.3
                direction[1] = np.sin(angle) * 1.5
                direction[2] = np.cos(angle) * 1.5
                full_coords[i] = full_coords[i - 1] + direction

        # Center the full structure
        full_coords -= full_coords.mean(axis=0)
        return full_coords

    def _find_motif_positions(
        self, sequence: str, motif: str, start: int, end: int
    ) -> List[int]:
        """
        Find positions of a motif pattern within a sequence region.

        Supports simple patterns where 'X' matches any amino acid.

        Args:
            sequence: Full protein sequence
            motif: Motif pattern (e.g., "HRD", "CXXC")
            start: Search region start (0-indexed)
            end: Search region end (exclusive)

        Returns:
            List of matching positions (each position in the motif)
        """
        positions = []
        region = sequence[start:end]
        motif_len = len(motif)

        for i in range(len(region) - motif_len + 1):
            match = True
            for j, pattern_char in enumerate(motif):
                if pattern_char != 'X' and region[i + j] != pattern_char:
                    match = False
                    break
            if match:
                # Return all positions in the matched motif
                for j in range(motif_len):
                    positions.append(start + i + j)

        return positions
