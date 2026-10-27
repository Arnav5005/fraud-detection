#!/usr/bin/env python3
"""
evaluate_thresholds.py - Sweep and audit classification decision thresholds on validation data.
Optimizes thresholds for Recall, F1, F0.5, and operational cost trade-offs.
"""

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_auc_score, average_precision_score


def evaluate_threshold_sweep(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    cost_fn: float = 200.0,
    cost_fp: float = 10.0,
    thresholds: list = None
) -> dict:
    if thresholds is None:
        thresholds = [round(t, 2) for t in np.arange(0.05, 0.96, 0.05)]

    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)

    total_samples = len(y_true)
    actual_positives = int(np.sum(y_true == 1))
    actual_negatives = int(np.sum(y_true == 0))

    roc_auc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.0
    pr_auc = float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.0

    rows = []
    best_f1 = {"f1": -1.0, "threshold": 0.5}
    best_f05 = {"f05": -1.0, "threshold": 0.5}
    min_cost = {"cost": float("inf"), "threshold": 0.5}
    target_recalls = {}

    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        tp = int(np.sum((y_true == 1) & (y_pred == 1)))
        fp = int(np.sum((y_true == 0) & (y_pred == 1)))
        tn = int(np.sum((y_true == 0) & (y_pred == 0)))
        fn = int(np.sum((y_true == 1) & (y_pred == 0)))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        # F0.5: beta = 0.5, beta^2 = 0.25
        beta2 = 0.25
        f05 = (1 + beta2) * (prec * rec) / (beta2 * prec + rec) if (beta2 * prec + rec) > 0 else 0.0

        cost = (fn * cost_fn) + (fp * cost_fp)

        entry = {
            "threshold": float(t),
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1": round(float(f1), 4),
            "f05": round(float(f05), 4),
            "cost": round(float(cost), 2)
        }
        rows.append(entry)

        if f1 > best_f1["f1"]:
            best_f1 = {"f1": round(float(f1), 4), "threshold": float(t), "entry": entry}
        if f05 > best_f05["f05"]:
            best_f05 = {"f05": round(float(f05), 4), "threshold": float(t), "entry": entry}
        if cost < min_cost["cost"]:
            min_cost = {"cost": round(float(cost), 2), "threshold": float(t), "entry": entry}

        for target_rec in [0.80, 0.85, 0.90]:
            key = f"recall_gte_{int(target_rec*100)}"
            if rec >= target_rec:
                if key not in target_recalls or entry["precision"] > target_recalls[key]["precision"]:
                    target_recalls[key] = entry

    return {
        "dataset_summary": {
            "total_samples": total_samples,
            "actual_positives": actual_positives,
            "actual_negatives": actual_negatives,
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4)
        },
        "cost_assumptions": {
            "cost_fn": cost_fn,
            "cost_fp": cost_fp
        },
        "optima": {
            "best_f1": best_f1,
            "best_f05": best_f05,
            "min_cost": min_cost,
            "target_recalls": target_recalls
        },
        "sweep_table": rows
    }


def print_report(results: dict):
    summary = results["dataset_summary"]
    optima = results["optima"]
    costs = results["cost_assumptions"]

    print("\n" + "=" * 78)
    print("🎯 DECISION THRESHOLD AUDIT & OPTIMIZATION REPORT")
    print("=" * 78)
    print(f"Validation Samples: {summary['total_samples']:,} (Fraud: {summary['actual_positives']}, Legit: {summary['actual_negatives']})")
    print(f"ROC-AUC:            {summary['roc_auc']:.4f}")
    print(f"PR-AUC (Avg Prec):  {summary['pr_auc']:.4f}")
    print(f"Cost Assumptions:   Cost(FN)=${costs['cost_fn']}, Cost(FP)=${costs['cost_fp']}")
    print("-" * 78)
    print(f"{'Threshold':<10} {'Precision':<10} {'Recall':<10} {'F1':<8} {'F0.5':<8} {'TP':<6} {'FP':<8} {'FN':<6} {'Total Cost':<10}")
    print("-" * 78)

    for r in results["sweep_table"]:
        print(f"{r['threshold']:<10.2f} {r['precision']:<10.4f} {r['recall']:<10.4f} {r['f1']:<8.4f} {r['f05']:<8.4f} {r['tp']:<6} {r['fp']:<8} {r['fn']:<6} ${r['cost']:<10.0f}")

    print("-" * 78)
    print("🏆 RECOMMENDED THRESHOLD CANDIDATES:")
    print(f"  • Max F1:       Threshold = {optima['best_f1']['threshold']} (F1: {optima['best_f1']['f1']}, Prec: {optima['best_f1']['entry']['precision']}, Rec: {optima['best_f1']['entry']['recall']}, FP: {optima['best_f1']['entry']['fp']}, FN: {optima['best_f1']['entry']['fn']})")
    print(f"  • Max F0.5:     Threshold = {optima['best_f05']['threshold']} (F0.5: {optima['best_f05']['f05']}, Prec: {optima['best_f05']['entry']['precision']}, Rec: {optima['best_f05']['entry']['recall']}, FP: {optima['best_f05']['entry']['fp']}, FN: {optima['best_f05']['entry']['fn']})")
    print(f"  • Min Cost:     Threshold = {optima['min_cost']['threshold']} (Cost: ${optima['min_cost']['cost']}, FP: {optima['min_cost']['entry']['fp']}, FN: {optima['min_cost']['entry']['fn']})")

    for key, val in optima["target_recalls"].items():
        print(f"  • {key.upper()}: Threshold = {val['threshold']} (Rec: {val['recall']}, Prec: {val['precision']}, FP: {val['fp']}, FN: {val['fn']})")

    print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluate threshold trade-offs on validation predictions")
    parser.add_argument("--val-preds", help="CSV with 'y_true' and 'y_prob' columns")
    parser.add_argument("--cost-fn", type=float, default=200.0, help="Cost of false negative ($)")
    parser.add_argument("--cost-fp", type=float, default=10.0, help="Cost of false positive ($)")
    parser.add_argument("--output-json", default=None, help="Save evaluation to JSON")
    args = parser.parse_args()

    if not args.val_preds:
        print("ℹ️ No predictions file provided. Generating demonstration evaluation curve...")
        # Synthetic evaluation on simulated imbalanced distribution for verification
        np.random.seed(42)
        n_samples = 45000
        n_fraud = 78
        y_true = np.zeros(n_samples, dtype=int)
        y_true[:n_fraud] = 1
        # Fraud probabilities typically skew higher for fraud
        y_prob = np.random.beta(0.5, 30, size=n_samples)
        y_prob[:n_fraud] = np.random.beta(5, 2, size=n_fraud)
    else:
        df = pd.read_csv(args.val_preds)
        y_true = df["y_true"].values if "y_true" in df.columns else df["Class"].values
        y_prob = df["y_prob"].values if "y_prob" in df.columns else df["fraud_prob"].values

    results = evaluate_threshold_sweep(y_true, y_prob, cost_fn=args.cost_fn, cost_fp=args.cost_fp)
    print_report(results)

    if args.output_json:
        with open(args.output_json, "w") as f:
            json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
