# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
CosMx spatial transcriptomics adapter for KOMPOSOS-III.

Converts NanoString CosMx CSV data into categorical network representation
for Ricci curvature analysis, persistent homology, and compositional reasoning.

Author: KOMPOSOS-III Team
Date: 2026-04-20
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import sys
import sqlite3
import json
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.store import KomposOSStore, StoredObject, StoredMorphism
from spatial_biology.ligand_receptor_db import LigandReceptorDatabase
from geometry.ricci import compute_graph_curvature
from topology.persistence import PersistentHomologyAnalyzer


@dataclass
class SpatialCell:
    """Represents a single cell from CosMx data."""
    cell_id: str
    x: float
    y: float
    expression: Dict[str, float]  # gene -> expression level
    cell_type: str = "Unknown"

    def distance_to(self, other: 'SpatialCell') -> float:
        """Euclidean distance to another cell (micrometers)."""
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


class CosMxAdapter:
    """
    Adapter for converting CosMx spatial transcriptomics data into
    categorical network representation for KOMPOSOS analysis.
    """

    def __init__(self,
                 proximity_threshold: float = 20.0,
                 expression_threshold: float = 0.5):
        """
        Initialize adapter.

        Args:
            proximity_threshold: Distance threshold for spatial edges (micrometers)
            expression_threshold: Minimum expression level to consider gene active
        """
        self.proximity_threshold = proximity_threshold
        self.expression_threshold = expression_threshold
        self.lr_db = LigandReceptorDatabase()
        self.ligand_receptor_pairs = self.lr_db.to_dict()
        self.tier1_relationships = self._load_tier1_relationships()

    def _load_tier1_relationships(self) -> Set[Tuple[str, str]]:
        """Load the 329 high-fidelity relationships from tier1.db."""
        relationships = set()
        db_path = Path(__file__).parent.parent / 'data' / 'drugs' / 'tier1.db'
        
        if not db_path.exists():
            print(f"Warning: {db_path} not found. Using empty tier1 relationships.")
            return relationships

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT source_name, target_name FROM morphisms")
            for source, target in cursor.fetchall():
                relationships.add((source, target))
            conn.close()
            print(f"Loaded {len(relationships)} relationships from tier1.db")
        except Exception as e:
            print(f"Error loading tier1.db: {e}")
            
        return relationships

    def load_cosmx_csv(self, filepath: str) -> List[SpatialCell]:
        """
        Load NanoString CosMx CSV file into cell list.

        Handles multiple header formats:
        - Synthetic: cell_id, x, y
        - Real CosMx: cell_ID, center_x, center_y (or x_center, y_center)
        - Gene columns follow metadata.

        Args:
            filepath: Path to CosMx CSV file

        Returns:
            List of SpatialCell objects
        """
        df = pd.read_csv(filepath)
        
        # Determine column names for ID and coordinates
        id_col = next((c for c in ['cell_ID', 'cell_id', 'CellID'] if c in df.columns), None)
        x_col = next((c for c in ['center_x', 'x_center', 'x', 'center_X'] if c in df.columns), None)
        y_col = next((c for c in ['center_y', 'y_center', 'y', 'center_Y'] if c in df.columns), None)
        
        if not all([id_col, x_col, y_col]):
            raise ValueError(f"Could not find required columns (ID, X, Y) in {filepath}. "
                             f"Columns found: {list(df.columns)}")

        # Identify gene columns (exclude metadata)
        metadata_cols = {id_col, x_col, y_col, 'fov', 'FOV', 'Area', 'area'}
        gene_cols = [col for col in df.columns if col not in metadata_cols]

        cells = []
        for _, row in df.iterrows():
            # Handle cell_id conversion (avoid .0 suffix if it's a number)
            raw_id = row[id_col]
            if isinstance(raw_id, float) and raw_id.is_integer():
                cell_id_str = str(int(raw_id))
            else:
                cell_id_str = str(raw_id)
                
            expression = {gene: float(row[gene]) for gene in gene_cols}
            cell = SpatialCell(
                cell_id=cell_id_str,
                x=float(row[x_col]),
                y=float(row[y_col]),
                expression=expression
            )
            cell.cell_type = self._infer_cell_type(cell)
            cells.append(cell)

        print(f"Loaded {len(cells)} cells from {filepath}")
        return cells

    def build_network(self, cells: List[SpatialCell]) -> KomposOSStore:
        """
        Build categorical network from spatial cells using the 329-relationship filter.
        
        MASTER DIRECTIVE Logic:
        Only create a morphism (arrow) between Cell A and Cell B if:
        1. Distance: They are within 20 micrometers (physical permission).
        2. Logic: Cell A has a Ligand and Cell B has a Receptor (or vice versa) 
           that exists in our 0.760 AUROC 'Gold Standard' list.
        3. Threshold: Both proteins meet a minimum expression count in the CosMx data.

        Args:
            cells: List of SpatialCell objects

        Returns:
            KomposOSStore with categorical network
        """
        store = KomposOSStore()

        # Create objects (one per cell)
        for cell in cells:
            obj = StoredObject(
                name=cell.cell_id,
                type_name='Cell',
                metadata={
                    'description': f"{cell.cell_type} at ({cell.x:.1f}, {cell.y:.1f})",
                    'x': cell.x,
                    'y': cell.y,
                    'cell_type': cell.cell_type,
                    'expression': cell.expression
                },
                provenance='cosmx_spatial_transcriptomics'
            )
            store.add_object(obj)

        # Create morphisms with the 329-relationship sieve
        morphism_count = 0
        
        # Spatial indexing (simple grid-based optimization for larger datasets)
        # For small sets, nested loop is fine
        n_cells = len(cells)
        for i in range(n_cells):
            cell_a = cells[i]
            
            # --- NEW: Intracellular Signaling (Self-Morphisms) ---
            # Check for signaling within the SAME cell (e.g., EGFR -> KRAS)
            for source_gene, target_gene in self.tier1_relationships:
                source_expr = cell_a.expression.get(source_gene, 0.0)
                target_expr = cell_a.expression.get(target_gene, 0.0)
                
                if source_expr >= self.expression_threshold and target_expr >= self.expression_threshold:
                    morph = StoredMorphism(
                        name=f"{source_gene}->{target_gene}_internal",
                        source_name=cell_a.cell_id,
                        target_name=cell_a.cell_id,
                        confidence=min(source_expr, target_expr),
                        metadata={
                            'mechanism': 'intracellular_signaling',
                            'source_gene': source_gene,
                            'target_gene': target_gene,
                            'distance_um': 0.0
                        },
                        provenance='cosmx_logic_audit_internal'
                    )
                    store.add_morphism(morph)
                    morphism_count += 1

            # --- Intercellular Signaling (Cell-to-Cell) ---
            for j in range(n_cells):
                if i == j: continue
                cell_b = cells[j]
                
                # 1. Distance constraint (< 20 micrometers)
                distance = cell_a.distance_to(cell_b)
                if distance > self.proximity_threshold:
                    continue
                
                # 2 & 3. Logic & Threshold constraint
                # Check for any valid relationship from our gold standard list
                valid_morphisms = []
                
                # Check L-R pairs from expanded DB
                for ligand, receptors in self.ligand_receptor_pairs.items():
                    ligand_expr = cell_a.expression.get(ligand, 0.0)
                    if ligand_expr < self.expression_threshold:
                        continue
                        
                    for receptor in receptors:
                        receptor_expr = cell_b.expression.get(receptor, 0.0)
                        if receptor_expr < self.expression_threshold:
                            continue
                        
                        # Check if this pair is in our "Gold Standard" (tier1 or high-conf LR)
                        is_gold = (ligand, receptor) in self.tier1_relationships
                        
                        if is_gold or self._is_high_fidelity_lr(ligand, receptor):
                            lr_pair = self.lr_db.get_pair(ligand, receptor)
                            # --- Probabilistic Physics Fix ---
                            # Use Gaussian-like decay instead of linear
                            # sigma = 1/2 of proximity threshold for smooth dropoff
                            sigma = self.proximity_threshold / 2.0
                            prob_distance = np.exp(-(distance**2) / (2 * sigma**2))
                            
                            confidence = min(ligand_expr, receptor_expr) * prob_distance
                            
                            valid_morphisms.append({
                                'type': 'ligand_receptor',
                                'source_gene': ligand,
                                'target_gene': receptor,
                                'confidence': confidence,
                                'distance': distance,
                                'pathway': lr_pair.pathway if lr_pair else 'tier1_logic',
                                'evidence': lr_pair.evidence if lr_pair else 'tier1.db',
                                'tissue_specificity': lr_pair.tissue_specificity if lr_pair else 'general',
                                'pair_confidence': lr_pair.confidence if lr_pair else 1.0,
                            })

                # If we found valid logic-gated relationships, add to store
                for vm in valid_morphisms:
                    morph = StoredMorphism(
                        name=f"{vm['source_gene']}->{vm['target_gene']}",
                        source_name=cell_a.cell_id,
                        target_name=cell_b.cell_id,
                        confidence=vm['confidence'],
                        metadata={
                            'mechanism': vm['type'],
                            'ligand': vm['source_gene'],
                            'receptor': vm['target_gene'],
                            'distance_um': vm['distance'],
                            'pathway': vm['pathway'],
                            'evidence': vm['evidence'],
                            'tissue_specificity': vm['tissue_specificity'],
                            'pair_confidence': vm['pair_confidence'],
                        },
                        provenance='cosmx_logic_audit'
                    )
                    store.add_morphism(morph)
                    morphism_count += 1

        print(f"Built logic-filtered network: {len(cells)} cells, {morphism_count} morphisms")
        return store

    def _is_high_fidelity_lr(self, ligand: str, receptor: str) -> bool:
        """Check if an L-R pair is considered high-fidelity for the audit."""
        # For now, we trust the LigandReceptorDatabase pairs as high-fidelity
        # especially if they are NSCLC specific.
        pair = self.lr_db.get_pair(ligand, receptor)
        return pair.confidence >= 0.8 if pair else False

    def build_categorical_network(self, cells: List[SpatialCell]) -> KomposOSStore:
        """Legacy method, now points to build_network."""
        return self.build_network(cells)

    def run_geometric_audit(self, store: KomposOSStore) -> Dict[str, any]:
        """
        Run Ricci Curvature and Spectral analysis on the categorical network.
        
        Highlights bottlenecks (negative curvature) and network robustness (spectral gap).
        """
        print("Running geometric audit (Ricci + Spectral)...")
        
        # 1. Ricci Curvature
        curvature_result = compute_graph_curvature(store)
        
        # 2. Spectral Analysis (simple Laplacian implementation)
        # We'll use a simplified version here
        spectral_gap = self._compute_spectral_gap(store)
        
        # 3. Identify Bottlenecks
        bottlenecks = []
        for (u, v), kappa in curvature_result.edge_curvatures.items():
            if kappa < -0.2:  # Negative curvature = bottleneck
                bottlenecks.append({
                    'source': u,
                    'target': v,
                    'curvature': kappa
                })
        
        return {
            'curvature': curvature_result,
            'spectral_gap': spectral_gap,
            'bottlenecks': sorted(bottlenecks, key=lambda x: x['curvature']),
            'summary': curvature_result.analysis
        }

    def _compute_spectral_gap(self, store: KomposOSStore) -> float:
        """Compute the spectral gap of the graph Laplacian."""
        # Simple implementation using adjacency matrix
        objects = store.list_objects(limit=10000)
        obj_names = [obj.name for obj in objects]
        n = len(obj_names)
        if n < 2: return 0.0
        
        name_to_idx = {name: i for i, name in enumerate(obj_names)}
        adj = np.zeros((n, n))
        
        for morph in store.list_morphisms(limit=100000):
            if morph.source_name in name_to_idx and morph.target_name in name_to_idx:
                i, j = name_to_idx[morph.source_name], name_to_idx[morph.target_name]
                adj[i, j] = 1.0
                adj[j, i] = 1.0  # Undirected Laplacian
                
        degree = np.diag(np.sum(adj, axis=1))
        laplacian = degree - adj
        
        try:
            eigenvalues = np.linalg.eigvalsh(laplacian)
            # Second smallest eigenvalue is the spectral gap (Fiedler value)
            if len(eigenvalues) > 1:
                return float(eigenvalues[1])
        except:
            pass
            
        return 0.0

    def generate_audit_report(self, 
                              cells: List[SpatialCell],
                              store: KomposOSStore,
                              audit_results: Dict[str, any],
                              predictions: List[Dict] = None) -> str:
        """
        Generate Noetik_Audit_Report.json comparing AI predictions vs KOMPOSOS proofs.
        """
        report = {
            'metadata': {
                'project': 'KOMPOSOS-III Noetik Validation',
                'dataset': 'NanoString CosMx NSCLC (Public Sample 1, FOV 1)',
                'timestamp': '2026-04-21',
                'audit_logic': '329-Relationship Sieve'
            },
            'network_stats': {
                'cell_count': len(cells),
                'morphism_count': len(store.list_morphisms(limit=100000)),
                'spectral_gap': audit_results['spectral_gap']
            },
            'geometric_insights': {
                'bottleneck_count': len(audit_results['bottlenecks']),
                'mean_curvature': audit_results['curvature'].statistics['mean'],
                'bottlenecks': audit_results['bottlenecks'][:10] # Top 10
            },
            'sheaf_coherence': []
        }
        
        if predictions:
            for pred in predictions:
                coherence = self.check_sheaf_coherence(store, pred)
                report['sheaf_coherence'].append(coherence)
        
        output_path = Path(__file__).parent.parent / 'Noetik_Audit_Report.json'
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        print(f"Generated Audit Report: {output_path}")
        return str(output_path)

    def _infer_cell_type(self, cell: SpatialCell) -> str:
        """
        Infer cell type from expression markers.

        Simplified marker-based classification.
        """
        expr = cell.expression
        threshold = self.expression_threshold

        # T cells
        if expr.get('CD3E', 0) > threshold or expr.get('CD3D', 0) > threshold:
            if expr.get('CD8A', 0) > threshold:
                return 'CD8_T_cell'
            elif expr.get('CD4', 0) > threshold:
                return 'CD4_T_cell'
            return 'T_cell'

        # B cells
        if (expr.get('CD19', 0) > threshold or expr.get('CD20', 0) > threshold or
                expr.get('MS4A1', 0) > threshold or expr.get('CD79A', 0) > threshold):
            return 'B_cell'

        # Macrophages
        if (expr.get('CD68', 0) > threshold or expr.get('CD163', 0) > threshold or
                expr.get('LYZ', 0) > threshold or expr.get('C1QA', 0) > threshold):
            return 'Macrophage'

        # Cancer / epithelial cells
        epithelial_score = (
            expr.get('EPCAM', 0) + expr.get('KRT5', 0) + expr.get('KRT8', 0) +
            expr.get('KRT18', 0) + expr.get('KRT19', 0) + expr.get('MUC1', 0)
        )
        oncogene_score = (expr.get('KRAS', 0) + expr.get('EGFR', 0) +
                         expr.get('MYC', 0) + expr.get('TP53', 0))
        if epithelial_score > threshold * 1.5 or oncogene_score > threshold * 2:
            return 'Cancer_cell'

        # Fibroblasts
        fibro_score = (
            expr.get('COL1A1', 0) + expr.get('COL1A2', 0) + expr.get('COL3A1', 0) +
            expr.get('DCN', 0) + expr.get('ACTA2', 0) + expr.get('FAP', 0)
        )
        if fibro_score > threshold * 1.5:
            return 'Fibroblast'

        # Endothelial
        if (expr.get('PECAM1', 0) > threshold or expr.get('VWF', 0) > threshold or
                expr.get('KDR', 0) > threshold):
            return 'Endothelial_cell'

        return 'Unknown'

    def check_sheaf_coherence(self,
                              store: KomposOSStore,
                              prediction: Dict[str, any]) -> Dict[str, any]:
        """
        Check if a prediction (e.g., from OCTO) is coherent with categorical structure.

        Validates:
        1. Morphism existence (does predicted edge exist?)
        2. Compositional path (is there a compositional chain?)
        3. Geometric consistency (Ricci curvature check)

        Args:
            store: Categorical network
            prediction: Dict with 'source', 'target', 'prediction_type'

        Returns:
            Dict with coherence result
        """
        source = prediction.get('source')
        target = prediction.get('target')
        pred_type = prediction.get('prediction_type', 'interaction')

        # Check direct morphism
        direct_morphism = None
        for morph in store.list_morphisms(limit=100000):
            if morph.source_name == source and morph.target_name == target:
                direct_morphism = morph
                break

        # Check compositional path
        paths = self._find_paths(store, source, target, max_length=3)

        # Compute coherence score
        score = 0.0
        reasons = []

        if direct_morphism:
            score += 0.5
            reasons.append(f"Direct morphism exists (confidence={direct_morphism.confidence:.2f})")

        if paths:
            score += 0.3
            reasons.append(f"{len(paths)} compositional paths found")

        # Geometric check (if Ricci available)
        if hasattr(store, 'curvature_cache'):
            edge_curv = store.curvature_cache.get((source, target), 0.0)
            if edge_curv > 0:  # Positive curvature = stable interaction
                score += 0.2
                reasons.append(f"Positive Ricci curvature ({edge_curv:.3f})")

        coherent = score > 0.3  # Threshold for coherence

        return {
            'coherent': coherent,
            'score': score,
            'reasons': reasons,
            'direct_morphism': direct_morphism is not None,
            'path_count': len(paths),
            'prediction': prediction
        }

    def _find_paths(self,
                    store: KomposOSStore,
                    source: str,
                    target: str,
                    max_length: int = 3) -> List[List[str]]:
        """
        Find compositional paths from source to target.

        Args:
            store: Categorical network
            source: Source object name
            target: Target object name
            max_length: Maximum path length

        Returns:
            List of paths (each path is list of object names)
        """
        # Build adjacency list
        adj = {}
        for morph in store.list_morphisms(limit=100000):
            if morph.source_name not in adj:
                adj[morph.source_name] = []
            adj[morph.source_name].append(morph.target_name)

        # BFS to find paths
        paths = []
        queue = [(source, [source])]

        while queue:
            node, path = queue.pop(0)

            if len(path) > max_length:
                continue

            if node == target and len(path) > 1:
                paths.append(path)
                continue

            for neighbor in adj.get(node, []):
                if neighbor not in path:  # Avoid cycles
                    queue.append((neighbor, path + [neighbor]))

        return paths


def generate_synthetic_cosmx_data(output_path: str,
                                  n_cells: int = 100,
                                  n_genes: int = 20,
                                  seed: int = 42):
    """
    Generate synthetic CosMx data for demo purposes.

    Creates realistic spatial patterns:
    - Tumor core (high KRAS/EGFR, low immune)
    - Invasive front (medium KRAS, high MMP9)
    - Immune region (high CD8/PD1/PDL1)

    Args:
        output_path: Path to save CSV
        n_cells: Number of cells to generate
        n_genes: Number of genes to include
        seed: Random seed
    """
    np.random.seed(seed)

    # Gene panel (key markers)
    genes = [
        'CD8A', 'CD4', 'CD3E', 'PDCD1', 'CD274',  # Immune
        'KRAS', 'EGFR', 'TP53', 'MYC', 'BRAF',  # Oncogenes
        'MMP9', 'VIM', 'CDH1', 'CDH2',  # EMT/invasion
        'VEGFA', 'FLT1', 'KDR',  # Angiogenesis
        'IL2', 'IL6', 'IFNG'  # Cytokines
    ][:n_genes]

    data = []

    for i in range(n_cells):
        # Random spatial position (200 x 200 μm tissue)
        x = np.random.uniform(0, 200)
        y = np.random.uniform(0, 200)

        # Determine region
        if x < 70 and y < 70:
            # Tumor core
            expression = {
                'KRAS': np.random.lognormal(2.0, 0.5),
                'EGFR': np.random.lognormal(2.5, 0.5),
                'TP53': np.random.lognormal(1.5, 0.5),
                'MYC': np.random.lognormal(1.0, 0.5),
                'CD8A': np.random.lognormal(-1.0, 0.5),
                'CD4': np.random.lognormal(-1.0, 0.5),
                'PDCD1': np.random.lognormal(-0.5, 0.5),
                'CD274': np.random.lognormal(1.0, 0.5),  # PD-L1 high
            }
        elif x > 150 or y > 150:
            # Invasive front
            expression = {
                'KRAS': np.random.lognormal(1.0, 0.5),
                'MMP9': np.random.lognormal(2.0, 0.5),
                'VIM': np.random.lognormal(1.5, 0.5),
                'CDH2': np.random.lognormal(1.5, 0.5),
                'CDH1': np.random.lognormal(-1.0, 0.5),
                'CD8A': np.random.lognormal(0.0, 0.5),
            }
        else:
            # Immune region
            expression = {
                'CD8A': np.random.lognormal(2.0, 0.5),
                'CD4': np.random.lognormal(1.5, 0.5),
                'CD3E': np.random.lognormal(2.0, 0.5),
                'PDCD1': np.random.lognormal(1.5, 0.5),
                'IFNG': np.random.lognormal(1.0, 0.5),
                'IL2': np.random.lognormal(0.5, 0.5),
            }

        # Fill in remaining genes with low noise
        row = {'cell_id': i+1, 'x': x, 'y': y}
        for gene in genes:
            row[gene] = expression.get(gene, np.random.lognormal(-2.0, 0.3))

        data.append(row)

    # Create DataFrame and save
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Generated synthetic CosMx data: {output_path}")
    print(f"  {n_cells} cells x {n_genes} genes")
    print(f"  Spatial range: 200 x 200 micrometers")


if __name__ == '__main__':
    # Test: generate synthetic data
    output_path = Path(__file__).parent.parent / 'data' / 'spatial' / 'sample_nsclc_tissue.csv'
    generate_synthetic_cosmx_data(str(output_path), n_cells=100, n_genes=20)

    # Test: load and build network
    adapter = CosMxAdapter(proximity_threshold=15.0)
    cells = adapter.load_cosmx_csv(str(output_path))
    store = adapter.build_categorical_network(cells)

    print(f"\nNetwork stats:")
    print(f"  Objects: {len(store.list_objects(limit=100000))}")
    print(f"  Morphisms: {len(store.list_morphisms(limit=100000))}")

    # Test: coherence check
    prediction = {
        'source': '1',
        'target': '2',
        'prediction_type': 'interaction'
    }
    result = adapter.check_sheaf_coherence(store, prediction)
    print(f"\nCoherence check:")
    print(f"  Coherent: {result['coherent']}")
    print(f"  Score: {result['score']:.2f}")
    print(f"  Reasons: {result['reasons']}")
