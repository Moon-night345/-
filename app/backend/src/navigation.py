SINGAPORE_NAVIGATION = [
    {"id": "scdf_995", "type": "emergency", "name": {"zh": "新加坡急救救护车", "en": "Singapore emergency ambulance"}, "phone": "995", "action": {"zh": "出现红旗症状时立即拨打。", "en": "Call immediately for red-flag symptoms."}},
    {"id": "police_999", "type": "emergency", "name": {"zh": "新加坡警察紧急服务", "en": "Singapore Police emergency"}, "phone": "999", "action": {"zh": "用于警务或现场安全协助。", "en": "Police or scene-safety assistance."}},
    {"id": "pharmacist", "type": "pharmacist", "name": {"zh": "药师或医院药房", "en": "Pharmacist or hospital pharmacy"}, "phone": None, "action": {"zh": "带上产品标签和暴露情况。", "en": "Bring the product label and exposure details."}},
    {"id": "hospital_ed", "type": "hospital", "name": {"zh": "最近的医院急诊", "en": "Nearest hospital emergency department"}, "phone": "需要紧急转运时拨打 995", "action": {"zh": "不要延误临床评估。", "en": "Do not delay clinician assessment."}},
    {"id": "poison_information", "type": "poison_information", "name": {"zh": "毒物信息咨询渠道", "en": "Poison information channel"}, "phone": None, "action": {"zh": "联系前先向医院药师或急诊核验当地机构号码。", "en": "Ask a hospital pharmacist or ED and verify the number before calling."}},
]
def navigation_for(level, lang="en"):
    emergency = level == "emergency"
    order = ["scdf_995", "hospital_ed", "pharmacist", "poison_information"] if emergency else ["pharmacist", "poison_information", "hospital_ed", "scdf_995"]
    return {"country": "Singapore", "level": level, "must_call_emergency": emergency, "options": [next(item for item in SINGAPORE_NAVIGATION if item["id"] == item_id) for item_id in order], "disclaimer": "这是就医导航，不是医疗诊断；危急情况请先拨打 995。" if lang == "zh" else "This is care navigation, not a medical diagnosis; call 995 first for emergencies."}
