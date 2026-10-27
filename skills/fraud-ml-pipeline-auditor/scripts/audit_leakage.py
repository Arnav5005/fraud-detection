#!/usr/bin/env python3
"""
audit_leakage.py - Static and runtime auditor for data leakage and partitioning rules.
Scans Python scripts, pipelines, or partitions for leakage patterns.
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def audit_code_file(file_path: Path) -> list:
    """Analyze Python code for leakage anti-patterns using regex and AST analysis."""
    findings = []
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    # Pattern 1: Scaling before train_test_split
    scaler_fit_line = None
    split_line = None
    smote_line = None

    for idx, line in enumerate(lines, 1):
        clean_line = line.strip()
        if clean_line.startswith("#"):
            continue

        if re.search(r"(StandardScaler|RobustScaler|MinMaxScaler)\s*\(", line):
            if re.search(r"\.fit(_transform)?\s*\(\s*(X|df|data)[,\)]", line):
                scaler_fit_line = idx

        if "train_test_split(" in line.replace(" ", "") and not clean_line.startswith("import") and not clean_line.startswith("from"):
            split_line = idx
            # Check stratification
            if "stratify" not in line:
                # Check next 4 lines if multiline call
                extended = "".join(lines[idx - 1: min(idx + 5, len(lines))])
                if "stratify" not in extended:
                    findings.append({
                        "file": str(file_path),
                        "line": idx,
                        "severity": "Critical",
                        "rule": "Mandatory Stratification",
                        "message": "train_test_split call appears to lack 'stratify' parameter."
                    })

        if re.search(r"(SMOTE|ADASYN|RandomOverSampler)\s*\(", line):
            smote_line = idx

    # Compare ordering: Scaler fit before split
    if scaler_fit_line and split_line and scaler_fit_line < split_line:
        findings.append({
            "file": str(file_path),
            "line": scaler_fit_line,
            "severity": "Critical",
            "rule": "Pre-Split Scaler Fit Leakage",
            "message": f"Scaler fit/fit_transform called at line {scaler_fit_line} before train_test_split at line {split_line}."
        })

    # Compare ordering: SMOTE before split
    if smote_line and split_line and smote_line < split_line:
        findings.append({
            "file": str(file_path),
            "line": smote_line,
            "severity": "Critical",
            "rule": "Global Resampling Leakage",
            "message": f"SMOTE resampler initialized/called at line {smote_line} before train_test_split at line {split_line}."
        })

    # Check for threshold tuning on test set
    for idx, line in enumerate(lines, 1):
        if re.search(r"(f1_score|precision_recall_curve|roc_curve|fbeta_score)", line):
            if re.search(r"(y_test|test_y|y_true_test|test_probs)", line) and ("threshold" in line.lower() or "best" in line.lower()):
                findings.append({
                    "file": str(file_path),
                    "line": idx,
                    "severity": "Critical",
                    "rule": "Threshold Test-Set Leakage",
                    "message": f"Threshold selection or curve optimization appears to directly reference test set (y_test/test_probs) at line {idx}."
                })

    return findings


def audit_leakage_in_directory(target_dir: str) -> dict:
    target = Path(target_dir)
    if not target.exists():
        return {"status": "error", "message": f"Target path '{target_dir}' does not exist."}

    all_findings = []
    py_files = list(target.rglob("*.py")) if target.is_dir() else [target]

    print(f"🔍 Auditing {len(py_files)} Python file(s) in: {target.resolve()}")
    for py_file in py_files:
        # Skip virtualenvs, git, and skill/tool directories
        if any(part in py_file.parts for part in [".venv", "venv", ".git", "site-packages", "skill-creator", ".agents", "skills"]):
            continue
        findings = audit_code_file(py_file)
        all_findings.extend(findings)

    status = "FAIL" if any(f["severity"] == "Critical" for f in all_findings) else "PASS"

    print("\n" + "=" * 60)
    print("🛡️ DATA LEAKAGE AUDIT REPORT")
    print("=" * 60)
    print(f"Files Scanned:      {len(py_files)}")
    print(f"Total Findings:     {len(all_findings)}")
    print(f"Audit Status:       {'✅ PASS (No leakage patterns detected)' if status == 'PASS' else '❌ CRITICAL DEFECTS DETECTED'}")

    if all_findings:
        print("\nIdentified Issues:")
        for idx, f in enumerate(all_findings, 1):
            print(f"  {idx}. [{f['severity']}] {f['rule']}")
            print(f"     Location: {f['file']}:{f['line']}")
            print(f"     Details:  {f['message']}")
    print("=" * 60 + "\n")

    return {
        "status": status,
        "scanned_files_count": len(py_files),
        "findings": all_findings
    }


def main():
    parser = argparse.ArgumentParser(description="Audit pipeline code for data leakage and partition anti-patterns")
    parser.add_argument("path", nargs="?", default=".", help="File or directory to audit")
    parser.add_argument("--output-json", default=None, help="Save report to JSON")
    args = parser.parse_args()

    report = audit_leakage_in_directory(args.path)
    if args.output_json:
        with open(args.output_json, "w") as f:
            json.dump(report, f, indent=2)
    sys.exit(1 if report["status"] == "FAIL" else 0)


if __name__ == "__main__":
    main()
