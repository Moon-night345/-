from src.evaluation import evaluate_cases

def test_safety_benchmark():
    report=evaluate_cases()
    assert report["case_count"] == 30
    assert report["red_flag_emergency_recall"] == 1.0
    assert report["dangerous_mix_detection_rate"] == 1.0
    assert report["llm_override_count"] == 0
    assert report["passed"] is True
