from ..triage import hard_rule_result

def run(answers, analysis=None, lang="en"):
    return {"agent": "triage", **hard_rule_result(answers, analysis, lang=lang)}
