"""Evaluate derived visual windows against consented observable labels, not mental attention.

Usage: python backend/scripts/evaluate_visual_signals.py observations.csv
The CSV must contain total_samples, valid_samples, face_samples, forward_samples,
observer_face_visible, observer_head_forward, and condition. A blank forward
label is allowed when the observer could not see a face.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.visual import summarize_visual_window  # noqa: E402


def boolean_label(value):
    value = str(value).strip().lower()
    if value in {"yes", "true", "1"}:
        return True
    if value in {"no", "false", "0"}:
        return False
    if not value:
        return None
    raise ValueError(f"Unknown observer label: {value}")


def empty_matrix():
    return {"true_positive": 0, "false_positive": 0, "true_negative": 0, "false_negative": 0}


def empty_group():
    return {"windows": 0, "missing_windows": 0,
            "face_visible": empty_matrix(), "head_forward": empty_matrix()}


def add_outcome(matrix, predicted, observed):
    key = ("true_" if predicted == observed else "false_") + ("positive" if predicted else "negative")
    matrix[key] += 1


def finish_matrix(matrix):
    tp, fp, tn, fn = (matrix[key] for key in ("true_positive", "false_positive", "true_negative", "false_negative"))
    matrix["sensitivity"] = round(tp / (tp + fn), 3) if tp + fn else None
    matrix["specificity"] = round(tn / (tn + fp), 3) if tn + fp else None
    return matrix


def evaluate_rows(rows, face_threshold=0.5, forward_threshold=0.5):
    if not (0 <= face_threshold <= 1 and 0 <= forward_threshold <= 1):
        raise ValueError("Thresholds must be between 0 and 1")
    groups = {}
    overall = empty_group()
    for row_number, row in enumerate(rows, start=2):
        condition = (row.get("condition") or "unspecified").strip()
        if not condition:
            condition = "unspecified"
        group = groups.setdefault(condition, empty_group())
        try:
            counts = {field: int(row[field]) for field in ("total_samples", "valid_samples", "face_samples", "forward_samples")}
            if not all(0 <= value <= 50 for value in counts.values()):
                raise ValueError("Sample count outside 0–50")
            result = summarize_visual_window(**counts)
            observed_face = boolean_label(row["observer_face_visible"])
            observed_forward = boolean_label(row["observer_head_forward"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Invalid CSV row {row_number}: {error}") from error
        if observed_face is None:
            raise ValueError(f"Invalid CSV row {row_number}: face-visible observer label is required")
        for target in (group, overall):
            target["windows"] += 1
            if result["quality"] != "usable":
                target["missing_windows"] += 1
                continue
            predicted_face = counts["face_samples"] / counts["valid_samples"] >= face_threshold
            add_outcome(target["face_visible"], predicted_face, observed_face)
            if observed_forward is not None and counts["face_samples"]:
                predicted_forward = counts["forward_samples"] / counts["face_samples"] >= forward_threshold
                add_outcome(target["head_forward"], predicted_forward, observed_forward)
    for group in [overall, *groups.values()]:
        group["missing_rate"] = round(group["missing_windows"] / group["windows"], 3) if group["windows"] else None
        finish_matrix(group["face_visible"])
        finish_matrix(group["head_forward"])
    return {"label_scope": "observable face and coarse orientation only",
            "thresholds": {"face_visible": face_threshold, "head_forward": forward_threshold},
            "overall": overall, "conditions": groups}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--face-threshold", type=float, default=0.5)
    parser.add_argument("--forward-threshold", type=float, default=0.5)
    args = parser.parse_args()
    with args.csv_path.open(newline="", encoding="utf-8-sig") as source:
        report = evaluate_rows(csv.DictReader(source), args.face_threshold, args.forward_threshold)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
