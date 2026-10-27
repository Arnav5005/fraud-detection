#!/usr/bin/env python3
"""
audit_dataset.py - Dataset validation script for Kaggle Credit Card Fraud dataset.
Validates schema, nulls, duplicates, label distribution, and value ranges.
"""

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd


def audit_dataset(data_path: str, output_json: str = None) -> dict:
    path = Path(data_path)
    if not path.exists():
        print(f"❌ Error: Dataset file not found at '{data_path}'")
        return {"status": "error", "message": f"File not found: {data_path}"}

    print(f"🔍 Auditing dataset: {path.resolve()}")
    try:
        df = pd.read_csv(path)
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return {"status": "error", "message": str(e)}

    # 1. Shape & Columns
    rows, cols = df.shape
    expected_v = [f"V{i}" for i in range(1, 29)]
    expected_cols = ["Time"] + expected_v + ["Amount", "Class"]
    missing_cols = [c for c in expected_cols if c not in df.columns]
    extra_cols = [c for c in df.columns if c not in expected_cols]

    # 2. Missing & Infinite values
    null_counts = df.isnull().sum()
    total_nulls = int(null_counts.sum())

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    inf_counts = np.isinf(df[numeric_cols]).sum()
    total_infs = int(inf_counts.sum())

    # 3. Duplicate rows
    duplicate_rows = int(df.duplicated().sum())

    # 4. Target variable analysis
    if "Class" in df.columns:
        class_counts = df["Class"].value_counts().to_dict()
        unique_classes = [int(c) for c in sorted(list(df["Class"].unique()))]
        fraud_count = int(class_counts.get(1, 0))
        legit_count = int(class_counts.get(0, 0))
        fraud_ratio = (fraud_count / rows * 100) if rows > 0 else 0.0
        target_valid = (set(unique_classes) == {0, 1})
    else:
        class_counts = {}
        unique_classes = []
        fraud_count = legit_count = 0
        fraud_ratio = 0.0
        target_valid = False

    # 5. Value integrity checks
    neg_time_count = int((df["Time"] < 0).sum()) if "Time" in df.columns else 0
    neg_amount_count = int((df["Amount"] < 0).sum()) if "Amount" in df.columns else 0

    amount_stats = {}
    if "Amount" in df.columns:
        amount_stats = {
            "min": float(df["Amount"].min()),
            "max": float(df["Amount"].max()),
            "mean": float(df["Amount"].mean()),
            "median": float(df["Amount"].median()),
            "p95": float(df["Amount"].quantile(0.95))
        }

    time_stats = {}
    if "Time" in df.columns:
        time_stats = {
            "min": float(df["Time"].min()),
            "max": float(df["Time"].max()),
            "duration_hours": float(df["Time"].max() / 3600.0) if df["Time"].max() > 0 else 0.0
        }

    # Defect summary
    defects = []
    if missing_cols:
        defects.append({"severity": "Critical", "description": f"Missing expected columns: {missing_cols}"})
    if not target_valid:
        defects.append({"severity": "Critical", "description": f"Target 'Class' is invalid: {unique_classes}"})
    if total_nulls > 0:
        defects.append({"severity": "High", "description": f"Found {total_nulls} null values"})
    if total_infs > 0:
        defects.append({"severity": "High", "description": f"Found {total_infs} infinite values"})
    if neg_time_count > 0:
        defects.append({"severity": "High", "description": f"Found {neg_time_count} negative Time entries"})
    if neg_amount_count > 0:
        defects.append({"severity": "High", "description": f"Found {neg_amount_count} negative Amount entries"})
    if duplicate_rows > 0:
        defects.append({"severity": "Low", "description": f"Found {duplicate_rows} duplicate rows (~{duplicate_rows/rows*100:.2f}%)"})

    report = {
        "status": "PASS" if not defects or all(d["severity"] == "Low" for d in defects) else "FAIL",
        "file_path": str(path.resolve()),
        "rows": rows,
        "columns": cols,
        "missing_columns": missing_cols,
        "extra_columns": extra_cols,
        "total_nulls": total_nulls,
        "total_infs": total_infs,
        "duplicate_rows": duplicate_rows,
        "target_variable": {
            "valid": target_valid,
            "classes": unique_classes,
            "legitimate_count": legit_count,
            "fraud_count": fraud_count,
            "fraud_percentage": round(fraud_ratio, 4)
        },
        "time_stats": time_stats,
        "amount_stats": amount_stats,
        "defects": defects
    }

    # Print summary
    print("\n" + "=" * 60)
    print("📋 DATASET AUDIT SUMMARY")
    print("=" * 60)
    print(f"Rows:               {rows:,}")
    print(f"Columns:            {cols}")
    print(f"Schema Compliant:   {'✅ Yes' if not missing_cols else '❌ No (' + str(missing_cols) + ')'}")
    print(f"Total Nulls:        {total_nulls}")
    print(f"Total Infs:         {total_infs}")
    print(f"Duplicate Rows:     {duplicate_rows:,} ({duplicate_rows/rows*100:.2f}%)")
    print(f"Legitimate (0):     {legit_count:,} ({100 - fraud_ratio:.3f}%)")
    print(f"Fraud (1):          {fraud_count:,} ({fraud_ratio:.3f}%)")
    if amount_stats:
        print(f"Amount Range:       ${amount_stats['min']:.2f} to ${amount_stats['max']:.2f} (Median: ${amount_stats['median']:.2f})")
    if time_stats:
        print(f"Time Span:          {time_stats['duration_hours']:.1f} hours")
    print(f"Overall Status:     {'✅ PASS' if report['status'] == 'PASS' else '⚠️ WARN / FAIL'}")

    if defects:
        print("\nFindings:")
        for d in defects:
            print(f"  - [{d['severity']}] {d['description']}")
    print("=" * 60 + "\n")

    if output_json:
        out_path = Path(output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"💾 Report saved to: {out_path.resolve()}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Audit Kaggle Credit Card Fraud Dataset")
    parser.add_argument("--data-path", default="creditcard.csv", help="Path to creditcard.csv")
    parser.add_argument("--output-json", default=None, help="Optional output JSON path")
    args = parser.parse_args()

    report = audit_dataset(args.data_path, args.output_json)
    if report.get("status") == "FAIL":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
