import pytest

from scripts.evaluate_visual_signals import evaluate_rows


def row(face, forward, observed_face, observed_forward, condition="normal"):
    return {"total_samples": "20", "valid_samples": "20", "face_samples": str(face),
            "forward_samples": str(forward), "observer_face_visible": observed_face,
            "observer_head_forward": observed_forward, "condition": condition}


def test_evaluation_reports_counts_and_missing_without_attention_claims():
    rows = [row(20, 20, "yes", "yes"), row(0, 0, "no", ""),
            row(18, 2, "yes", "no"), row(0, 0, "yes", "yes", "dim")]
    rows.append({**row(0, 0, "no", "", "dim"), "valid_samples": "2"})
    result = evaluate_rows(rows)
    assert result["label_scope"] == "observable face and coarse orientation only"
    assert result["overall"]["windows"] == 5
    assert result["conditions"]["normal"]["face_visible"]["true_positive"] == 2
    assert result["conditions"]["normal"]["face_visible"]["true_negative"] == 1
    assert result["conditions"]["normal"]["head_forward"]["true_negative"] == 1
    assert result["conditions"]["dim"]["face_visible"]["false_negative"] == 1
    assert result["conditions"]["dim"]["missing_rate"] == 0.5


def test_evaluation_rejects_invalid_rows_and_thresholds():
    with pytest.raises(ValueError, match="row 2"):
        evaluate_rows([row(0, 1, "no", "")])
    with pytest.raises(ValueError, match="Thresholds"):
        evaluate_rows([], face_threshold=1.2)
