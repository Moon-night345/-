from .recognition_agent import run as recognition_run
from .triage_agent import run as triage_run
from .navigation_agent import run as navigation_run
from .review_agent import run as review_run

def run_healthcare_agents(answers, analysis=None, lang="en", trace_id=None):
    recognition = recognition_run(analysis)
    triage = triage_run(answers, analysis, lang)
    navigation = navigation_run(triage["level"], lang)
    review = review_run(recognition, triage, navigation)
    return {"trace_id": trace_id, "recognition": recognition, "triage": {**triage, "questions": answers, "result": triage}, "navigation": navigation, "review": review, "orchestration": "recognition -> triage(hard rules) -> navigation -> review"}
