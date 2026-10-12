def run(recognition, triage, navigation):
    llm_level = triage.get("llm_suggestion")
    blocked = bool(llm_level and llm_level != triage.get("level")) or not triage.get("llm_can_not_override") or triage.get("source") != "deterministic_hard_rules"
    return {"agent": "review", "review_passed": True,
            "output_allowed": not blocked, "output_passed": not blocked,
            "decision": "blocked" if blocked else "approved",
            "blocked": blocked, "triage_level": triage.get("level"), "llm_suggestion": llm_level,
            "modified_output": blocked, "reason": "Hard-rule result is authoritative; unsafe or lower-severity wording is blocked." if blocked else "Output passed deterministic safety review."}
