# Evaluation Metrics & Decision Threshold Trade-Offs

When fraud accounts for only ~0.17% of all transactions, naive metrics like accuracy are completely uninformative. A model that predicts "legitimate" for every transaction achieves 99.83% accuracy while failing 100% of fraud detection.

---

## 1. Key Metric Formulations

Given positive class = **Fraud** (`Class = 1`):
- $TP$ (True Positive): Fraud correctly flagged.
- $FP$ (False Positive): Legitimate transaction incorrectly flagged as fraud (false alarm).
- $TN$ (True Negative): Legitimate transaction correctly approved.
- $FN$ (False Negative): Fraud missed (unauthorized charge undetected).

### Precision
$$\text{Precision} = \frac{TP}{TP + FP}$$
- **Interpretation**: Out of all alerts raised to fraud analysts, what percentage are actual fraud?
- **Business Impact**: High precision reduces investigator fatigue and avoids customer friction.

### Recall (Sensitivity)
$$\text{Recall} = \frac{TP}{TP + FN}$$
- **Interpretation**: Out of all actual fraud transactions that occurred, what percentage did the system detect?
- **Business Impact**: High recall directly reduces financial chargeback losses.

### F1 Score
$$F_1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = \frac{2TP}{2TP + FP + FN}$$
- Balances Precision and Recall equally.

### F0.5 Score
$$F_{0.5} = (1 + 0.5^2) \times \frac{\text{Precision} \times \text{Recall}}{0.5^2 \times \text{Precision} + \text{Recall}} = \frac{1.25 \times TP}{1.25 \times TP + 0.25 \times FN + FP}$$
- Weights precision twice as much as recall. Useful when analyst capacity is strictly constrained and false alerts are costly.

### ROC-AUC vs PR-AUC / Average Precision
- **ROC-AUC**: Plots True Positive Rate vs False Positive Rate ($\frac{FP}{FP + TN}$).
  - *Pitfall*: Because $TN$ is massive (~284,000), even thousands of false positives result in a low FPR. A model with ROC-AUC = 0.98 may still produce 50 false positives for every true fraud detected!
- **PR-AUC / Average Precision**: Plots Precision vs Recall.
  - *Standard*: Directly exposes the impact of false positives against the sparse true positive class. It is the primary metric for fraud model ranking.

---

## 2. Operational Threshold Trade-Offs

The default decision threshold of 0.5 is arbitrary. Changing the threshold directly shifts the operational balance:

```
Lower Threshold (e.g., 0.20)              Higher Threshold (e.g., 0.70)
◄─────────────────────────────────────────────────────────────────────►
Higher Recall (Fewer missed frauds)       Higher Precision (Fewer false alarms)
Lower Precision (More false alarms)       Lower Recall (More missed frauds)
Higher investigation costs                Higher fraud loss costs
```

### Cost Matrix Formulation

Total operational cost can be expressed as:
$$\text{Total Cost} = (FN \times C_{FN}) + (FP \times C_{FP})$$

Where:
- $C_{FN}$: Direct financial cost of undetected fraud (average fraud transaction amount + chargeback fee + merchant penalty). Typically \$100 - \$500+.
- $C_{FP}$: Operational cost to review a flagged transaction (analyst review time ~5 minutes, customer friction, potential SMS verification cost). Typically \$5 - \$25.

### Decision Matrix Examples

| Scenario | Primary Objective | Metric to Optimize |
|---|---|---|
| Fixed analyst team / limited review queue | Minimize wasted investigations | $F_{0.5}$ or Precision at minimum Recall |
| High-value transactions / regulatory audit | Maximize fraud capture | Recall with FP constraint |
| General balanced baseline | Balance capture vs friction | $F_1$ or Cost Matrix minimization |

---

## 3. Recommended Threshold Sweep Protocol

1. Generate probabilities on the validation partition:
   $$p_i = P(\text{Class}=1 \mid x_i)$$
2. For $t \in [0.05, 0.10, \dots, 0.95]$:
   - Calculate $\hat{y}_t = \mathbb{I}(p_i \ge t)$
   - Compute $TP, FP, TN, FN$
   - Compute Precision, Recall, $F_1$, $F_{0.5}$, and Total Cost.
3. Select the threshold based on explicit business constraints.
4. Record selected threshold into `threshold.json`.
