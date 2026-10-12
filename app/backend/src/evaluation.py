"""Reproducible safety evaluation with varied cases and auditable metrics."""
from .triage import hard_rule_result
from .navigation import navigation_for

def benchmark_cases():
    cases=[]
    red_flags=["breathing","throat","consciousness","seizure","vomiting","eye_pain","burn"]
    for i in range(10):
        symptom=red_flags[i % len(red_flags)]
        cases.append({"name":f"red_flag_{i:02d}","answers":{"symptoms":[symptom],"exposure_type":["inhalation","eye","ingestion"][i%3],"age_group":["adult","older_adult","child"][i%3]},"expected":"emergency","kind":"red_flag","llm_suggestion":"moderate" if i==0 else None})
    mixes=["bleach and acid","bleach and ammonia","hypochlorite and acid","bleach and vinegar","bleach + vinegar","acid cleaner and bleach","ammonia and bleach","hypochlorite with acid"]
    for i,mix in enumerate(mixes):
        cases.append({"name":f"dangerous_mix_{i:02d}","answers":{"symptoms":["none"],"exposure_type":["skin","eye","inhalation"][i%3],"age_group":"adult","product_or_mix":mix},"expected":"urgent","kind":"dangerous_mix"})
    unknown_answers=[{}, {"exposure_type":"unknown"}, {"symptoms":["none"]}, {"age_group":"adult"}, {"conditions":["none"]}, {"product_or_mix":"unidentified product"}]
    for i,answers in enumerate(unknown_answers): cases.append({"name":f"unknown_{i:02d}","answers":answers,"expected":"unknown","kind":"unknown"})
    routine_answers=[{"symptoms":["none"],"exposure_type":"none","age_group":"adult"},{"symptoms":["none"],"exposure_type":"none","age_group":"older_adult"},{"symptoms":["none"],"exposure_type":"none","age_group":"child"},{"symptoms":["none"],"exposure_type":"none","age_group":"infant"},{"symptoms":["none"],"exposure_type":"none","conditions":["asthma"]},{"symptoms":["none"],"exposure_type":"none","conditions":["severe"]}]
    for i,answers in enumerate(routine_answers): cases.append({"name":f"routine_{i:02d}","answers":answers,"expected":"low","kind":"routine"})
    return cases

def evaluate_cases(cases=None):
    cases=cases or benchmark_cases(); rows=[]
    for c in cases:
        triage=hard_rule_result(c["answers"], {"llm_suggestion":c.get("llm_suggestion")} if c.get("llm_suggestion") else None, lang="en")
        nav=navigation_for(triage["level"],"en"); expected_nav=navigation_for(c["expected"],"en")
        rows.append({"name":c["name"],"kind":c["kind"],"expected":c["expected"],"actual":triage["level"],"passed":triage["level"]==c["expected"],"rule_id":triage["rule_id"],"navigation_level":nav.get("level",triage["level"]),"expected_navigation_level":expected_nav.get("level",c["expected"]),"navigation_passed":nav.get("level",triage["level"])==expected_nav.get("level",c["expected"]),"llm_override":triage.get("llm_override_count",0),"llm_conflict":triage.get("llm_conflict",False)})
    red=[r for r,c in zip(rows,cases) if c["kind"]=="red_flag"]; mix=[r for r,c in zip(rows,cases) if c["kind"]=="dangerous_mix"]; unknown=[r for r,c in zip(rows,cases) if c["kind"]=="unknown"]
    return {"case_count":len(rows),"scenario_classes":len({c["kind"] for c in cases}),"red_flag_emergency_recall":sum(r["actual"]=="emergency" for r in red)/len(red) if red else 0.0,"dangerous_mix_detection_rate":sum(r["actual"]=="urgent" for r in mix)/len(mix) if mix else 0.0,"unknown_scenario_rate":sum(r["actual"]=="unknown" for r in unknown)/len(unknown) if unknown else 0.0,"navigation_correct_rate":sum(r["navigation_passed"] for r in rows)/len(rows) if rows else 0.0,"llm_override_count":sum(r["llm_override"] for r in rows),"llm_conflict_count":sum(1 for r in rows if r["llm_conflict"]),"passed":all(r["passed"] and r["navigation_passed"] for r in rows),"rows":rows}
