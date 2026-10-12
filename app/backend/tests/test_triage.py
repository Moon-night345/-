from src.triage import answer_case, start_case


def complete(case, answers):
    current = case
    for question_id, answer in answers:
        current = answer_case(current["case_id"], question_id, answer)
    return current


def test_recognition_result_is_carried_into_triage():
    analysis = {
        "product": {"name": "Household bleach", "brand": "Demo"},
        "ingredients": [{"name": "sodium hypochlorite"}],
        "risk_level": "high",
    }
    case = start_case("en", analysis)
    assert case["analysis"] == analysis
    result = complete(case, [
        ("exposure_type", "skin"),
        ("symptoms", ["none"]),
        ("age_group", "adult"),
        ("conditions", ["none"]),
        ("product_or_mix", "Household bleach"),
    ])
    assert result["result"]["level"] == "urgent"
    assert result["analysis"]["product"]["name"] == "Household bleach"


def test_red_flag_always_escalates_to_emergency():
    case = start_case("en")
    result = complete(case, [
        ("exposure_type", "inhalation"),
        ("symptoms", ["none", "breathing"]),
        ("age_group", "adult"),
        ("conditions", ["none"]),
        ("product_or_mix", "unknown"),
    ])
    assert result["result"]["level"] == "emergency"
    assert result["result"]["llm_can_not_override"] is True


def test_no_exposure_is_low():
    case = start_case("en")
    result = complete(case, [
        ("exposure_type", "none"),
        ("symptoms", ["none"]),
        ("age_group", "adult"),
        ("conditions", ["none"]),
        ("product_or_mix", "concern only"),
    ])
    assert result["result"]["level"] == "low"
