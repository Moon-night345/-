"""Dependency-light smoke test for the recognition -> triage loop."""
from src.triage import answer_case, start_case

analysis = {"product": {"name": "Household bleach"}, "risk_level": "high"}
case = start_case("en", analysis)
for question_id, answer in [
    ("exposure_type", "skin"),
    ("symptoms", ["none"]),
    ("age_group", "adult"),
    ("conditions", ["none"]),
    ("product_or_mix", "Household bleach"),
]:
    case = answer_case(case["case_id"], question_id, answer)
assert case["analysis"]["product"]["name"] == "Household bleach"
assert case["result"]["level"] == "urgent"
print("PASS recognition -> triage -> hard-rule result: urgent")
