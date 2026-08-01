# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
QUARANTINED 2026-07-31 — NON-PRODUCT, EXCLUDED FROM VALIDATION.

Output from this module MUST NOT be used as a validation result, cited, or shown
on any public surface. Retained for dependency and historical review only; do not
delete without that review.

Reason: this generator is CIRCULAR BY CONSTRUCTION. It synthesises tissue in
which tumour cores are seeded with the high curvature that the curvature method
is supposed to discover, and invasive fronts with the low curvature it is
supposed to discover. Any "validation" against it confirms the generator's own
assumptions, not the biology. The original docstring below — "better than public
datasets for validation because we KNOW the answer" — states the flaw as if it
were a feature: knowing the answer because you wrote it in is exactly what makes
the result meaningless.

Legitimate uses that remain: smoke-testing the pipeline, shape/dtype checks,
performance profiling. Not evidence.

Per the roadmap, spatial work restarts by reproducing one published PUBLIC
spatial or proteogenomic task against classical baselines.

--- original docstring follows ---

Generate HIGH-QUALITY synthetic spatial transcriptomics data with KNOWN ground truth.

This is better than public datasets for validation because we KNOW the answer:
- Which regions are tumor cores (high curvature expected)
- Which regions are invasive fronts (low curvature expected)
- Which ligand-receptor pairs should exist (based on cell types)
- Which feedback loops should be detected (EGFR, immune checkpoint)

Author: KOMPOSOS-III Team
Date: 2026-04-20
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict
import json


def generate_nsclc_tissue_with_ground_truth(
    n_cells: int = 1000,
    n_genes: int = 50,
    seed: int = 42,
    output_dir: Path = None
) -> Tuple[pd.DataFrame, Dict]:
    """
    Generate realistic NSCLC tissue with known spatial structure.

    Creates 5 distinct regions:
    1. Tumor core (high KRAS/EGFR, high curvature expected)
    2. Invasive front (high MMP9/VIM, low curvature expected)
    3. Immune-rich stroma (high CD8/PD1/PDL1)
    4. Necrotic center (low expression, void expected)
    5. Normal lung (low oncogenes, medium curvature)

    Returns:
        (cells_dataframe, ground_truth_dict)
    """
    np.random.seed(seed)

    if output_dir is None:
        output_dir = Path("data/spatial/validation")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Gene panel (50 key markers)
    genes = [
        # Oncogenes (NSCLC drivers)
        'KRAS', 'EGFR', 'TP53', 'MYC', 'BRAF', 'ALK', 'ROS1', 'MET',
        'ERBB2', 'PIK3CA',

        # Immune markers
        'CD8A', 'CD4', 'CD3E', 'CD3D', 'FOXP3',  # T cells
        'CD19', 'CD20', 'MS4A1',  # B cells
        'CD68', 'CD163', 'CD14',  # Macrophages
        'PDCD1', 'CD274', 'PDCD1LG2',  # PD-1/PD-L1/PD-L2
        'CTLA4', 'LAG3', 'HAVCR2', 'TIGIT',  # Other checkpoints
        'IFNG', 'TNF', 'IL2', 'IL10', 'IL6',  # Cytokines

        # EMT/invasion markers
        'MMP9', 'MMP2', 'VIM', 'CDH1', 'CDH2', 'SNAI1', 'TWIST1',

        # Angiogenesis
        'VEGFA', 'FLT1', 'KDR', 'ANGPT1', 'ANGPT2',

        # Proliferation/apoptosis
        'MKI67', 'PCNA', 'BCL2', 'BAX', 'CASP3',
    ][:n_genes]

    cells = []
    ground_truth = {
        'regions': [],
        'cell_annotations': {},
        'expected_curvature': {},
        'expected_loops': [],
        'expected_voids': [],
        'ligand_receptor_pairs': [],
    }

    cell_id = 0

    # Region 1: Tumor Core (center, high density, spherical geometry)
    # Expected: HIGH positive curvature (clustered, stable)
    tumor_core_center = (100, 100)
    tumor_core_radius = 30
    n_tumor_core = int(n_cells * 0.3)

    for i in range(n_tumor_core):
        # Clustered around center with some noise
        angle = np.random.uniform(0, 2 * np.pi)
        r = np.random.rayleigh(tumor_core_radius / 3)
        x = tumor_core_center[0] + r * np.cos(angle)
        y = tumor_core_center[1] + r * np.sin(angle)

        # High oncogene expression
        expression = {
            'KRAS': np.random.lognormal(2.5, 0.3),  # Very high
            'EGFR': np.random.lognormal(2.8, 0.3),  # Very high
            'TP53': np.random.lognormal(2.0, 0.4),  # Mutated = high
            'MYC': np.random.lognormal(1.8, 0.4),
            'MKI67': np.random.lognormal(2.0, 0.3),  # High proliferation
            'PCNA': np.random.lognormal(1.8, 0.3),

            # Low immune
            'CD8A': np.random.lognormal(-1.5, 0.5),  # Excluded
            'CD4': np.random.lognormal(-1.0, 0.5),

            # PD-L1 high (immune escape)
            'CD274': np.random.lognormal(1.5, 0.4),
        }

        # Fill remaining genes
        row = {'cell_id': cell_id, 'x': x, 'y': y}
        for gene in genes:
            row[gene] = expression.get(gene, np.random.lognormal(-2.0, 0.3))

        cells.append(row)
        ground_truth['cell_annotations'][cell_id] = 'tumor_core'
        ground_truth['expected_curvature'][cell_id] = 'high_positive'  # Stable, clustered
        cell_id += 1

    # Region 2: Invasive Front (ring around core, hyperbolic geometry)
    # Expected: NEGATIVE curvature (expanding, unstable)
    invasive_inner_radius = 35
    invasive_outer_radius = 55
    n_invasive = int(n_cells * 0.25)

    for i in range(n_invasive):
        angle = np.random.uniform(0, 2 * np.pi)
        r = np.random.uniform(invasive_inner_radius, invasive_outer_radius)
        x = tumor_core_center[0] + r * np.cos(angle)
        y = tumor_core_center[1] + r * np.sin(angle)

        # EMT/invasion signature
        expression = {
            'KRAS': np.random.lognormal(1.5, 0.5),  # Medium (escaping)
            'MMP9': np.random.lognormal(2.5, 0.3),  # Very high (invasive)
            'MMP2': np.random.lognormal(2.0, 0.3),
            'VIM': np.random.lognormal(2.2, 0.3),  # High vimentin (EMT)
            'CDH2': np.random.lognormal(1.8, 0.3),  # N-cadherin up (EMT)
            'CDH1': np.random.lognormal(-1.5, 0.5),  # E-cadherin down (EMT)
            'SNAI1': np.random.lognormal(1.5, 0.4),  # SNAIL (EMT TF)
            'TWIST1': np.random.lognormal(1.3, 0.4),  # TWIST (EMT TF)

            # Some immune (TME)
            'CD8A': np.random.lognormal(0.5, 0.5),
        }

        row = {'cell_id': cell_id, 'x': x, 'y': y}
        for gene in genes:
            row[gene] = expression.get(gene, np.random.lognormal(-2.0, 0.3))

        cells.append(row)
        ground_truth['cell_annotations'][cell_id] = 'invasive_front'
        ground_truth['expected_curvature'][cell_id] = 'negative'  # Expanding, unstable
        cell_id += 1

    # Region 3: Immune-Rich Stroma (patches, medium curvature)
    # Expected: Moderate curvature, H1 loops (feedback circuits)
    n_immune = int(n_cells * 0.25)

    # Create 3 immune patches
    immune_centers = [(50, 150), (150, 50), (150, 150)]

    for i in range(n_immune):
        # Pick random patch
        patch_center = immune_centers[i % len(immune_centers)]
        angle = np.random.uniform(0, 2 * np.pi)
        r = np.random.rayleigh(15)
        x = patch_center[0] + r * np.cos(angle)
        y = patch_center[1] + r * np.sin(angle)

        # Immune signature
        expression = {
            # T cells
            'CD8A': np.random.lognormal(2.5, 0.3),  # High CD8
            'CD4': np.random.lognormal(1.8, 0.3),
            'CD3E': np.random.lognormal(2.3, 0.3),
            'CD3D': np.random.lognormal(2.2, 0.3),
            'FOXP3': np.random.lognormal(0.5, 0.5),  # Some Tregs

            # Checkpoints (active)
            'PDCD1': np.random.lognormal(2.0, 0.3),  # PD-1 high
            'LAG3': np.random.lognormal(1.5, 0.4),
            'HAVCR2': np.random.lognormal(1.3, 0.4),  # TIM-3
            'TIGIT': np.random.lognormal(1.2, 0.4),

            # Cytokines (feedback loop)
            'IFNG': np.random.lognormal(1.8, 0.3),
            'TNF': np.random.lognormal(1.5, 0.4),
            'IL2': np.random.lognormal(1.3, 0.4),

            # Macrophages
            'CD68': np.random.lognormal(1.0, 0.5),
            'CD163': np.random.lognormal(0.8, 0.5),  # M2 macrophages
        }

        row = {'cell_id': cell_id, 'x': x, 'y': y}
        for gene in genes:
            row[gene] = expression.get(gene, np.random.lognormal(-2.0, 0.3))

        cells.append(row)
        ground_truth['cell_annotations'][cell_id] = 'immune_stroma'
        ground_truth['expected_curvature'][cell_id] = 'moderate'
        cell_id += 1

    # Region 4: Necrotic Center (inner core, very low expression)
    # Expected: H2 void (topological cavity)
    necrotic_radius = 10
    n_necrotic = int(n_cells * 0.1)

    # NOTE: We create a RING of dead cells (void in center)
    for i in range(n_necrotic):
        angle = np.random.uniform(0, 2 * np.pi)
        r = np.random.uniform(8, 12)  # Ring
        x = tumor_core_center[0] + r * np.cos(angle)
        y = tumor_core_center[1] + r * np.sin(angle)

        # Very low expression (dead cells)
        expression = {gene: np.random.lognormal(-3.0, 0.5) for gene in genes}

        row = {'cell_id': cell_id, 'x': x, 'y': y}
        row.update(expression)

        cells.append(row)
        ground_truth['cell_annotations'][cell_id] = 'necrotic'
        ground_truth['expected_curvature'][cell_id] = 'undefined'
        cell_id += 1

    # Region 5: Normal Lung (scattered, low density)
    # Expected: Euclidean geometry (medium curvature, near zero)
    n_normal = n_cells - cell_id

    for i in range(n_normal):
        # Scattered across tissue
        x = np.random.uniform(0, 200)
        y = np.random.uniform(0, 200)

        # Skip if too close to tumor
        dist_to_tumor = np.sqrt((x - tumor_core_center[0])**2 +
                                (y - tumor_core_center[1])**2)
        if dist_to_tumor < 60:
            continue  # Re-sample

        # Normal lung signature
        expression = {
            'KRAS': np.random.lognormal(-1.0, 0.5),  # Low
            'EGFR': np.random.lognormal(0.0, 0.5),  # Baseline
            'TP53': np.random.lognormal(-0.5, 0.5),  # WT = low

            # No immune activation
            'CD8A': np.random.lognormal(-0.5, 0.5),
            'CD4': np.random.lognormal(-0.5, 0.5),
        }

        row = {'cell_id': cell_id, 'x': x, 'y': y}
        for gene in genes:
            row[gene] = expression.get(gene, np.random.lognormal(-2.0, 0.3))

        cells.append(row)
        ground_truth['cell_annotations'][cell_id] = 'normal_lung'
        ground_truth['expected_curvature'][cell_id] = 'near_zero'
        cell_id += 1

    # Build DataFrame
    df = pd.DataFrame(cells)

    # Add ground truth metadata
    ground_truth['regions'] = [
        {'name': 'tumor_core', 'center': tumor_core_center, 'radius': tumor_core_radius,
         'expected_geometry': 'spherical', 'expected_curvature': 'high_positive'},
        {'name': 'invasive_front', 'inner_radius': invasive_inner_radius,
         'outer_radius': invasive_outer_radius, 'expected_geometry': 'hyperbolic',
         'expected_curvature': 'negative'},
        {'name': 'immune_stroma', 'centers': immune_centers, 'expected_geometry': 'mixed',
         'expected_curvature': 'moderate'},
        {'name': 'necrotic', 'center': tumor_core_center, 'radius': necrotic_radius,
         'expected_geometry': 'undefined', 'expected_void': True},
        {'name': 'normal_lung', 'expected_geometry': 'euclidean',
         'expected_curvature': 'near_zero'},
    ]

    # Expected topological features
    ground_truth['expected_loops'] = [
        {'region': 'immune_stroma', 'pathway': 'IFNg_TNF_IL2_feedback',
         'genes': ['IFNG', 'TNF', 'IL2', 'PDCD1', 'CD274']},
        {'region': 'tumor_core', 'pathway': 'EGFR_autocrine',
         'genes': ['EGFR', 'EGF', 'AREG', 'EREG']},
    ]

    ground_truth['expected_voids'] = [
        {'region': 'necrotic', 'center': tumor_core_center, 'radius': necrotic_radius},
    ]

    # Expected ligand-receptor pairs (based on cell types)
    ground_truth['ligand_receptor_pairs'] = [
        {'source_region': 'tumor_core', 'target_region': 'immune_stroma',
         'ligand': 'CD274', 'receptor': 'PDCD1', 'pathway': 'PD-L1_PD-1'},
        {'source_region': 'immune_stroma', 'target_region': 'immune_stroma',
         'ligand': 'IFNG', 'receptor': 'IFNGR1', 'pathway': 'IFNg_signaling'},
    ]

    # Save files
    csv_path = output_dir / "nsclc_validation_1000cells.csv"
    df.to_csv(csv_path, index=False)

    ground_truth_path = output_dir / "ground_truth.json"
    with open(ground_truth_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)

    print(f"Generated validation dataset:")
    print(f"  CSV: {csv_path}")
    print(f"  Ground truth: {ground_truth_path}")
    print(f"  Total cells: {len(df)}")
    print(f"\nRegion breakdown:")
    for region, count in df.groupby(df.cell_id.map(ground_truth['cell_annotations'])).size().items():
        print(f"    {region}: {count} cells")

    return df, ground_truth


if __name__ == '__main__':
    generate_nsclc_tissue_with_ground_truth(
        n_cells=1000,
        n_genes=50,
        seed=42
    )
