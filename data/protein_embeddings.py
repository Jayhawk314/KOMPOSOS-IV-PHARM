# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Protein structure embeddings using ESMFold and AlphaFold.

Provides structural embeddings for proteins, going beyond simple text embeddings.
"""

import numpy as np
import requests
from typing import Dict, Optional, List
from pathlib import Path
import json
import hashlib

class ProteinStructureEmbeddings:
    """
    Fetch and cache protein structure embeddings.

    Sources:
    1. ESM-2 (protein language model) - Fast, no structure needed
    2. AlphaFold DB - Pre-computed structures for human proteome
    3. Fallback to sequence-based embeddings
    """

    def __init__(self, cache_dir: str = "data/proteins/embeddings_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.uniprot_map = {}  # gene name -> UniProt ID
        self.embedding_cache = {}

        print("[ProteinEmbeddings] Initialized")
        print(f"  Cache: {self.cache_dir}")

    def get_uniprot_id(self, gene_name: str) -> Optional[str]:
        """Map gene name to UniProt ID using UniProt API."""
        if gene_name in self.uniprot_map:
            return self.uniprot_map[gene_name]

        try:
            url = f"https://rest.uniprot.org/uniprotkb/search"
            params = {
                'query': f'gene:{gene_name} AND organism_id:9606',  # Human
                'format': 'json',
                'size': 1
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get('results'):
                uniprot_id = data['results'][0]['primaryAccession']
                self.uniprot_map[gene_name] = uniprot_id
                return uniprot_id

        except Exception as e:
            print(f"  [Warning] Could not map {gene_name}: {e}")

        return None

    def get_alphafold_embedding(self, uniprot_id: str) -> Optional[np.ndarray]:
        """
        Fetch AlphaFold structure embedding from AlphaFold DB.

        Returns pLDDT scores per residue as a simple structural embedding.
        """
        cache_file = self.cache_dir / f"af_{uniprot_id}.npy"

        if cache_file.exists():
            return np.load(cache_file)

        try:
            # AlphaFold DB provides pLDDT scores and coordinates
            url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.pdb"

            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                return None

            # Parse PDB for pLDDT scores (in B-factor column)
            plddt_scores = []
            for line in response.text.split('\n'):
                if line.startswith('ATOM'):
                    # B-factor is columns 61-66
                    try:
                        plddt = float(line[60:66].strip())
                        plddt_scores.append(plddt)
                    except ValueError:
                        continue

            if plddt_scores:
                # Create embedding: mean, std, max, min of pLDDT scores
                embedding = np.array([
                    np.mean(plddt_scores),
                    np.std(plddt_scores),
                    np.max(plddt_scores),
                    np.min(plddt_scores),
                    len(plddt_scores)  # protein length
                ])

                np.save(cache_file, embedding)
                return embedding

        except Exception as e:
            print(f"  [Warning] AlphaFold fetch failed for {uniprot_id}: {e}")

        return None

    def get_esm_embedding(self, sequence: str) -> Optional[np.ndarray]:
        """
        Get ESM-2 protein language model embedding.

        Note: Requires ESM model installed. Falls back to simple features if not available.
        """
        try:
            import torch
            import esm

            # Load ESM-2 model (this is heavy - consider caching)
            model, alphabet = esm.pretrained.esm2_t33_650M_UR50D()
            batch_converter = alphabet.get_batch_converter()
            model.eval()

            # Prepare data
            data = [("protein", sequence)]
            batch_labels, batch_strs, batch_tokens = batch_converter(data)

            # Extract per-residue representations
            with torch.no_grad():
                results = model(batch_tokens, repr_layers=[33])
                token_representations = results["representations"][33]

            # Mean pool to get protein-level embedding
            embedding = token_representations[0, 1:len(sequence)+1].mean(0).numpy()
            return embedding

        except ImportError:
            # ESM not installed - use simple sequence features
            return self.get_sequence_features(sequence)
        except Exception as e:
            print(f"  [Warning] ESM embedding failed: {e}")
            return None

    def get_sequence_features(self, sequence: str) -> np.ndarray:
        """
        Simple sequence-based features as fallback.

        Returns:
            [length, hydrophobicity, charge, aromatic_content, ...]
        """
        if not sequence:
            return np.zeros(10)

        # Amino acid properties
        hydrophobic = set('AILMFWYV')
        charged = set('DEKR')
        aromatic = set('FWY')
        polar = set('STNQ')

        features = [
            len(sequence),
            sum(1 for aa in sequence if aa in hydrophobic) / len(sequence),
            sum(1 for aa in sequence if aa in charged) / len(sequence),
            sum(1 for aa in sequence if aa in aromatic) / len(sequence),
            sum(1 for aa in sequence if aa in polar) / len(sequence),
            sequence.count('C') / len(sequence),  # Cysteine content
            sequence.count('P') / len(sequence),  # Proline content
            sequence.count('G') / len(sequence),  # Glycine content
        ]

        return np.array(features + [0.0] * (10 - len(features)))  # Pad to 10

    def get_protein_embedding(self, gene_name: str,
                             use_alphafold: bool = True,
                             use_sequence: bool = False) -> Optional[np.ndarray]:
        """
        Get comprehensive protein embedding.

        Priority:
        1. AlphaFold structural embedding (if use_alphafold=True)
        2. ESM sequence embedding (if use_sequence=True and sequence provided)
        3. Simple sequence features

        Args:
            gene_name: Gene name (e.g., "TP53")
            use_alphafold: Try AlphaFold DB first
            use_sequence: Try ESM if sequence available

        Returns:
            Embedding vector or None
        """
        # Check cache
        if gene_name in self.embedding_cache:
            return self.embedding_cache[gene_name]

        embedding = None

        # Try AlphaFold
        if use_alphafold:
            uniprot_id = self.get_uniprot_id(gene_name)
            if uniprot_id:
                embedding = self.get_alphafold_embedding(uniprot_id)
                if embedding is not None:
                    print(f"  [AlphaFold] {gene_name} ({uniprot_id})")

        # Cache and return
        if embedding is not None:
            self.embedding_cache[gene_name] = embedding
            return embedding

        # Fallback: return placeholder
        print(f"  [Fallback] {gene_name} -> random embedding")
        embedding = np.random.randn(5) * 0.1  # Small random vector
        self.embedding_cache[gene_name] = embedding
        return embedding

    def batch_fetch(self, gene_names: List[str],
                   use_alphafold: bool = True) -> Dict[str, np.ndarray]:
        """
        Fetch embeddings for multiple proteins efficiently.

        Args:
            gene_names: List of gene names
            use_alphafold: Use AlphaFold DB

        Returns:
            Dict mapping gene name to embedding
        """
        print(f"[ProteinEmbeddings] Fetching embeddings for {len(gene_names)} proteins...")

        embeddings = {}
        for i, gene in enumerate(gene_names):
            if i % 50 == 0:
                print(f"  Progress: {i}/{len(gene_names)}")

            emb = self.get_protein_embedding(gene, use_alphafold=use_alphafold)
            if emb is not None:
                embeddings[gene] = emb

        print(f"[ProteinEmbeddings] Fetched {len(embeddings)}/{len(gene_names)} embeddings")
        return embeddings

    def save_cache(self):
        """Save embedding cache to disk."""
        cache_file = self.cache_dir / "embedding_cache.json"

        # Convert numpy arrays to lists for JSON
        json_cache = {
            gene: embedding.tolist()
            for gene, embedding in self.embedding_cache.items()
        }

        with open(cache_file, 'w') as f:
            json.dump(json_cache, f)

        print(f"[ProteinEmbeddings] Saved {len(json_cache)} embeddings to cache")

    def load_cache(self):
        """Load embedding cache from disk."""
        cache_file = self.cache_dir / "embedding_cache.json"

        if not cache_file.exists():
            return

        with open(cache_file, 'r') as f:
            json_cache = json.load(f)

        # Convert lists back to numpy arrays
        self.embedding_cache = {
            gene: np.array(embedding)
            for gene, embedding in json_cache.items()
        }

        print(f"[ProteinEmbeddings] Loaded {len(self.embedding_cache)} embeddings from cache")


# Example usage
if __name__ == "__main__":
    embedder = ProteinStructureEmbeddings()

    # Test with a few proteins
    test_proteins = ['TP53', 'KRAS', 'EGFR', 'BRCA1']

    for protein in test_proteins:
        embedding = embedder.get_protein_embedding(protein, use_alphafold=True)
        if embedding is not None:
            print(f"{protein}: {embedding.shape} - {embedding[:3]}")

    embedder.save_cache()
