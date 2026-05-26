#!/usr/bin/env python3
"""
MASTER PIPELINE: Run all extraction and quantification phases.

YOLO MODE - Execute everything!
"""

import subprocess
import sys
import time

def run_phase(name: str, script: str):
    """Run a phase and report results."""
    print("\n" + "="*70)
    print(f"PHASE: {name}")
    print("="*70)

    start = time.time()

    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=1800  # 30 min timeout per phase
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        elapsed = time.time() - start

        if result.returncode == 0:
            print(f"\n[OK] {name} complete ({elapsed:.1f}s)")
            return True
        else:
            print(f"\n[ERROR] {name} failed (exit code {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n[TIMEOUT] {name} exceeded 30 minutes")
        return False
    except Exception as e:
        print(f"\n[ERROR] {name} crashed: {e}")
        return False

def main():
    print("="*70)
    print("FULL EVIDENCE QUANTIFICATION PIPELINE")
    print("YOLO MODE - ALL PHASES")
    print("="*70)

    phases = [
        ("Phase 1: Evidence Tier Classification", "scripts/classify_evidence_tiers.py"),
        ("Phase 2: cBioPortal Genomic Data", "scripts/extract_cbioportal.py"),
        ("Phase 5: NLP PMID Extraction", "scripts/extract_all_pmids.py"),
    ]

    results = {}

    for name, script in phases:
        success = run_phase(name, script)
        results[name] = success

        if not success:
            print(f"\n[WARN] {name} failed, continuing anyway (YOLO!)")

    # Final summary
    print("\n" + "="*70)
    print("PIPELINE COMPLETE")
    print("="*70)

    for name, success in results.items():
        status = "[OK]" if success else "[FAILED]"
        print(f"  {status} {name}")

    success_count = sum(results.values())
    print(f"\n  Total: {success_count}/{len(phases)} phases successful")

    print("\nNext steps:")
    print("  1. Review: data/pmid_extraction_report.txt")
    print("  2. Test UI: streamlit run app.py")
    print("  3. Benchmark: python validation/repurposing_benchmark.py")

if __name__ == "__main__":
    main()
