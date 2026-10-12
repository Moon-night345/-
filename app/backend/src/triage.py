"""Deterministic chemical-exposure triage. LLM may explain but never decides urgency."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

STANDARD_QUESTION_ORDER = ["exposure_type", "symptoms", "age_group", "conditions", "product_or_mix"]
CAREGIVER_QUESTION_ORDER = [
    "exposure_type", "age_group", "consciousness_status", "breathing_status",
    "symptoms", "conditions", "accompaniment", "emergency_called", "product_or_mix", "share_result",
]
QUESTIONS = {
    "exposure_type": {"id": "exposure_type", "type": "choice", "text": {"zh": "发生了哪种暴露？", "en": "How did the exposure happen?"}, "options": [
        {"value": "none", "zh": "没有实际暴露，仅担心", "en": "Concern only; no exposure"}, {"value": "skin", "zh": "皮肤接触", "en": "Skin contact"}, {"value": "eye", "zh": "眼睛接触", "en": "Eye contact"}, {"value": "inhalation", "zh": "吸入", "en": "Inhalation"}, {"value": "ingestion", "zh": "误食或吞咽", "en": "Ingestion"}]},
    "symptoms": {"id": "symptoms", "type": "multi", "text": {"zh": "目前有哪一些症状？可以多选。", "en": "What symptoms are present now? Select all that apply."}, "options": [
        {"value": "none", "zh": "没有明显症状", "en": "No obvious symptoms"}, {"value": "breathing", "zh": "呼吸困难、喘鸣或嘴唇发青", "en": "Breathing difficulty, wheeze, or blue lips"}, {"value": "throat", "zh": "喉咙或舌头肿胀", "en": "Throat or tongue swelling"}, {"value": "consciousness", "zh": "意识改变、昏厥或无反应", "en": "Altered consciousness, fainting, or unresponsive"}, {"value": "seizure", "zh": "抽搐", "en": "Seizure"}, {"value": "vomiting", "zh": "持续呕吐", "en": "Persistent vomiting"}, {"value": "eye_pain", "zh": "严重眼痛或视力变化", "en": "Severe eye pain or vision change"}, {"value": "burn", "zh": "大面积化学灼伤", "en": "Large chemical burn"}]},
    "age_group": {"id": "age_group", "type": "choice", "text": {"zh": "受影响者的年龄段？", "en": "How old is the person?"}, "options": [
        {"value": "adult", "zh": "普通成年人", "en": "Typical adult"}, {"value": "older_adult", "zh": "老年人（65岁以上）", "en": "Older adult (65+)"}, {"value": "child", "zh": "儿童", "en": "Child"}, {"value": "infant", "zh": "婴幼儿", "en": "Infant or toddler"}]},
    "conditions": {"id": "conditions", "type": "multi", "text": {"zh": "是否有基础疾病？可以多选。", "en": "Are any health conditions present? Select all that apply."}, "options": [
        {"value": "none", "zh": "没有已知基础疾病", "en": "No known condition"}, {"value": "asthma", "zh": "哮喘或慢性呼吸系统疾病", "en": "Asthma or chronic respiratory disease"}, {"value": "severe", "zh": "严重心肺、免疫或其他重大疾病", "en": "Serious heart/lung, immune, or other major disease"}]},
    "product_or_mix": {"id": "product_or_mix", "type": "text", "text": {"zh": "请描述产品、成分，或是否混用了两种产品。", "en": "Describe the product, ingredients, or whether two products were mixed."}, "options": []},
    "consciousness_status": {"id": "consciousness_status", "type": "choice", "text": {"zh": "受影响者现在清醒、有反应吗？", "en": "Is the person awake and responding?"}, "options": [
        {"value": "awake", "zh": "清醒并有反应", "en": "Awake and responding"}, {"value": "not_responsive", "zh": "不清醒、昏厥或没有反应", "en": "Not awake, fainted, or not responding"}]},
    "breathing_status": {"id": "breathing_status", "type": "choice", "text": {"zh": "受影响者现在能正常呼吸吗？", "en": "Is the person breathing normally?"}, "options": [
        {"value": "normal", "zh": "能正常呼吸", "en": "Breathing normally"}, {"value": "not_normal", "zh": "不能正常呼吸、喘不上气或嘴唇发青", "en": "Not breathing normally, gasping, or blue lips"}]},
    "accompaniment": {"id": "accompaniment", "type": "choice", "text": {"zh": "现在有人陪在受影响者身边吗？", "en": "Is someone with the exposed person now?"}, "options": [
        {"value": "yes", "zh": "有人陪同", "en": "Yes, someone is with them"}, {"value": "no", "zh": "没有人陪同", "en": "No, they are alone"}]},
    "emergency_called": {"id": "emergency_called", "type": "choice", "text": {"zh": "是否已经拨打急救电话？", "en": "Have you called emergency services?"}, "options": [
        {"value": "yes", "zh": "已经拨打", "en": "Yes, already called"}, {"value": "no", "zh": "还没有拨打", "en": "No, not yet"}]},
    "share_result": {"id": "share_result", "type": "choice", "text": {"zh": "是否需要把结果分享给家人或陪同者？", "en": "Would you like to share the result with family or a helper?"}, "options": [
        {"value": "yes", "zh": "需要分享", "en": "Yes, share it"}, {"value": "no", "zh": "暂时不需要", "en": "No, not now"}]},
}
EMERGENCY_SYMPTOMS = {"breathing", "throat", "consciousness", "seizure", "vomiting", "eye_pain", "burn"}
DANGEROUS_MIXES = [("bleach", "acid"), ("bleach", "ammonia"), ("hypochlorite", "acid"), ("bleach", "vinegar")]


@dataclass
class ExposureCase:
    case_id: str
    lang: str = "en"
    mode: str = "self"
    answers: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    result: dict | None = None
    analysis: dict | None = None
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)

RULES_VERSION = "triage-rules-v1.2"
_CASES = {}

def _text(value): return " ".join(map(str, value)).lower() if isinstance(value, list) else str(value or "").lower()
def _pick(lang, en, zh): return zh if lang == "zh" else en
def _persist(case):
    from .case_store import save_case
    save_case(case)
def _hydrate(case_id):
    from .case_store import load_case
    row=load_case(case_id)
    if not row: return None
    return ExposureCase(row["case_id"], row["lang"], row["mode"], row["answers"], row["created_at"], row["result"], row["analysis"], row["trace_id"])

def hard_rule_result(answers, analysis=None, lang="en"):
    symptoms = set(answers.get("symptoms") if isinstance(answers.get("symptoms"), list) else [answers.get("symptoms")]); symptoms.discard(None); symptoms.discard("none")
    if answers.get("breathing_status") == "not_normal": symptoms.add("breathing")
    if answers.get("consciousness_status") == "not_responsive": symptoms.add("consciousness")
    age = str(answers.get("age_group", "")); conditions = set(answers.get("conditions") if isinstance(answers.get("conditions"), list) else [answers.get("conditions")]); conditions.discard(None); conditions.discard("none")
    exposure = str(answers.get("exposure_type", "")); text = _text(answers.get("product_or_mix"))
    if symptoms & EMERGENCY_SYMPTOMS:
        level, rule_id, en, zh = "emergency", "RED_FLAG_SYMPTOM", "A red-flag symptom was selected; call Singapore emergency ambulance 995 now.", "出现红旗症状；请立即拨打新加坡急救电话 995。"
    elif any(a in text and b in text for a, b in DANGEROUS_MIXES):
        level, rule_id, en, zh = "urgent", "DANGEROUS_MIX", "A dangerous product combination may be involved; get professional advice today.", "可能涉及危险混用；请今天寻求专业帮助。"
    elif exposure != "none" and (age in {"older_adult", "child", "infant"} or conditions):
        level, rule_id, en, zh = "urgent", "VULNERABLE_PERSON", "A vulnerable person or health condition is involved; contact a pharmacist or clinician today.", "涉及脆弱人群或基础疾病；请今天联系药师或医生。"
    elif exposure in {"eye", "ingestion", "inhalation"}:
        level, rule_id, en, zh = "moderate", "EXPOSURE_ROUTE", "Rinse or move to fresh air and monitor symptoms; seek help if symptoms persist or worsen.", "冲洗或转移到新鲜空气处并观察；症状持续或加重时求医。"
    elif exposure == "skin":
        level, rule_id, en, zh = "moderate", "EXPOSURE_ROUTE", "Rinse exposed skin with running water for at least 15 minutes.", "用流动清水冲洗暴露皮肤至少 15 分钟。"
    elif exposure == "none":
        level, rule_id, en, zh = "low", "NO_EXPOSURE", "No exposure was reported; continue safe storage and do not mix products.", "未报告实际暴露；继续安全存放，不要混用产品。"
    else:
        level, rule_id, en, zh = "unknown", "INSUFFICIENT_DATA", "More exposure details are needed before a safe triage level can be assigned.", "需要更多暴露信息后才能安全判断风险等级。"
    if analysis and level in {"low", "moderate"} and str(analysis.get("risk_level")) in {"high", "critical"}:
        level, rule_id, en, zh = "urgent", "PRODUCT_HAZARD_SIGNAL", "The identified product has a high or critical hazard signal; obtain professional advice.", "识别到的产品有高或危害信号；请尽快寻求专业帮助。"
    actions = {
      "emergency": (["Call Singapore emergency ambulance 995 now.", "Move away from fumes; do not induce vomiting; take the product label with you.", "Do not wait for this app. Ask someone nearby to help."], ["请立即拨打新加坡急救电话 995。", "远离烟雾；不要催吐；带上产品包装标签。", "不要等待本应用；请附近的人帮助你。"]),
      "urgent": (["Contact a pharmacist, poison information service, or emergency department today.", "Keep the container/label available and do not mix or give home remedies."], ["请今天联系药师、毒物信息服务或急诊。", "保留容器和标签；不要混用，也不要自行使用偏方。"]),
      "moderate": (["Rinse exposed skin with running water for at least 15 minutes.", "Escalate if pain, redness, breathing symptoms, or other symptoms worsen."], ["用流动清水冲洗暴露皮肤至少 15 分钟。", "若疼痛、发红、呼吸或其他症状加重，请升级求助。"]),
      "low": (["Store locked, labelled, and separate from food and medicines.", "Use the scan page to check hazards and forbidden mixtures."], ["将产品上锁、贴好标签，并与食物和药品分开存放。", "使用识别页面查看危害和禁忌混用信息。"]),
      "unknown": (["Do not guess or mix products.", "Provide missing exposure details or seek professional advice."], ["不要猜测，也不要混用产品。", "补充缺失的暴露信息，或寻求专业帮助。"]),
    }[level]
    llm_suggestion = (analysis or {}).get("llm_suggestion")
    valid_levels = {"unknown", "low", "moderate", "urgent", "emergency"}
    llm_conflict = llm_suggestion in valid_levels and llm_suggestion != level
    llm_override_attempted = bool(llm_conflict)
    llm_override_count = 0  # this deterministic path never applies an LLM level
    return {"level": level, "reason": _pick(lang, en, zh), "source": "deterministic_hard_rules", "llm_can_not_override": True,
            "actions": actions[1] if lang == "zh" else actions[0], "disclaimer": _pick(lang, "This is safety triage, not a medical diagnosis. Call 995 first for emergencies.", "这是安全分诊，不是医疗诊断。危急情况先拨打 995。"),
            "urgent": level in {"urgent", "emergency"}, "rule_id": rule_id, "rules_version": RULES_VERSION,
            "llm_suggestion": llm_suggestion, "llm_conflict": llm_conflict,
            "llm_override_attempted": llm_override_attempted, "llm_override_count": llm_override_count, "confidence": 1.0}

def next_question(answers, mode="self"):
    order = CAREGIVER_QUESTION_ORDER if mode == "caregiver" else STANDARD_QUESTION_ORDER
    return next((QUESTIONS[k] for k in order if k not in answers), None)
def case_view(case, analysis=None):
    active_analysis = analysis if analysis is not None else case.analysis
    result = case.result or (hard_rule_result(case.answers, active_analysis, case.lang) if next_question(case.answers, case.mode) is None else None)
    from .case_store import trace_view
    return {"case_id": case.case_id, "trace_id": case.trace_id, "lang": case.lang, "mode": case.mode, "answers": case.answers,
            "analysis": active_analysis, "next_question": next_question(case.answers, case.mode), "result": result,
            "trace": trace_view(case.trace_id), "source": "deterministic_hard_rules"}
def start_case(lang="en", analysis=None, mode="self"):
    from .case_store import append_trace
    mode = mode if mode in {"self", "caregiver"} else "self"
    case = ExposureCase(uuid.uuid4().hex, lang if lang in {"zh", "en"} else "en", mode, analysis=analysis)
    _CASES[case.case_id] = case; _persist(case)
    append_trace(case.trace_id, case.case_id, "recognition", {"input": {"has_analysis": bool(analysis)}, "result": analysis or {}})
    return case_view(case)
def answer_case(case_id, question_id, answer, analysis=None):
    from .case_store import append_trace
    case = _CASES.get(case_id) or _hydrate(case_id)
    if not case: raise KeyError(case_id)
    _CASES[case_id] = case
    if analysis is not None: case.analysis = analysis
    case.answers[question_id] = answer
    if question_id == "symptoms":
        trace_answer = {"selected_count": len(answer) if isinstance(answer, list) else (0 if answer in (None, "none") else 1)}
    elif question_id == "product_or_mix":
        trace_answer = "[redacted_free_text]"
    else:
        trace_answer = answer
    append_trace(case.trace_id, case.case_id, "triage", {"question_id": question_id, "answer": trace_answer, "structured": question_id not in {"symptoms", "product_or_mix"}})
    if next_question(case.answers, case.mode) is None:
        case.result = hard_rule_result(case.answers, case.analysis, case.lang)
        append_trace(case.trace_id, case.case_id, "rule", {"rule_id": case.result["rule_id"], "rules_version": RULES_VERSION, "level": case.result["level"]})
    _persist(case); return case_view(case)
def get_case(case_id):
    case = _CASES.get(case_id) or _hydrate(case_id)
    if not case: return None
    _CASES[case_id] = case; return case_view(case)
def delete_case(case_id):
    from .case_store import delete_case as _delete
    _CASES.pop(case_id, None); return _delete(case_id)
