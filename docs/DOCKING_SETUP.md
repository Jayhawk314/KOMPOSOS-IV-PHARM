# Docking Setup (AutoDock Vina) — Milestone 4

The docking adapter (`scripts/docking_adapter.py`) and CLI
(`scripts/dock_candidate.py`) use AutoDock Vina as a downstream verifier for the
Category M engine: the engine detects a pocket and proposes molecules, Vina
estimates binding and a docked pose. Everything is optional and graceful — if
the tools below are missing, calls raise `DockingUnavailable` and the CLI exits
with a clear message rather than crashing.

## Install

1. **Vina binary.** Download the AutoDock-Vina release binary for your OS from
   https://github.com/ccsb-scripps/AutoDock-Vina/releases and make it findable
   one of these ways (checked in order):
   - pass `vina_binary=...` / `--center` style explicit path,
   - set the `VINA_BINARY` environment variable,
   - put it on `PATH` as `vina` / `vina.exe`,
   - drop it at `tools/vina/vina.exe` (Windows) or `tools/vina/vina` in the repo
     (this directory is gitignored).

2. **Prep tools** (Python, cross-platform):

   ```
   pip install meeko gemmi rdkit
   ```

   This provides the `mk_prepare_receptor` and `mk_prepare_ligand` console
   scripts plus RDKit for 3D ligand embedding.

## Usage

```powershell
# Dock a SMILES into the engine-detected pocket (box auto-centered on the pocket)
python scripts/dock_candidate.py `
  --pdb data\cache\pdb_templates\1M17.pdb `
  --smiles "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1"

# Override the box center with a residue or explicit coordinates
python scripts/dock_candidate.py --pdb target.pdb --smiles "..." --residue A:797
python scripts/dock_candidate.py --pdb target.pdb --smiles "..." --center 23.1,2.2,52.3
```

When the PDB contains a bound ligand, the report also prints how far the docked
pose and the detected pocket center are from that crystal ligand.

## Validation status

Validated end-to-end on **1M17 (EGFR / erlotinib)**: receptor prep, ligand prep,
and a Vina run boxed on the engine-detected pocket scored the cognate ligand at
**-7.1 kcal/mol** with the docked pose **4.2 A** from the crystal ligand centroid
(the detected pocket center itself was 2.3 A from the crystal ligand). A
network-free unit suite plus a tool-gated live redock test live in
`tests/docking_adapter_test.py`.

## Honest limitations

- Receptor prep is the fragile step. `mk_prepare_receptor` is run with
  `--allow_bad_res --default_altloc A`; structures with gaps, unusual residues,
  or heavy altloc/heteroatom content may still fail prep. It is best-effort, not
  guaranteed across arbitrary PDBs.
- This is rigid-receptor docking with a single embedded ligand conformer seed.
  It estimates binding plausibility and pose location; it is not a free-energy
  calculation and does not replace MD or experiment.
- Centroid distance is reported as a pose-location proxy. Full symmetry-aware
  redock RMSD is a planned refinement.
