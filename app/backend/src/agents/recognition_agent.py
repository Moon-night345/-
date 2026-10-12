def run(analysis):
    analysis = analysis or {}
    ingredients = analysis.get("ingredients", [])
    evidence = analysis.get("visual_evidence", [])
    confidence = max([float(x.get("confidence", 0)) for x in ingredients + analysis.get("hazards", []) if isinstance(x, dict)] or [0.0])
    needs_confirmation = bool(analysis.get("uncertainties") or analysis.get("needs_more_images") or not evidence)
    return {"agent": "recognition", "input": {"analysis_present": bool(analysis)}, "product": analysis.get("product") or {}, "ingredients": ingredients, "evidence": evidence, "confidence": confidence, "needs_confirmation": needs_confirmation, "not_confirmed_notice": "Not confirmed from the available image." if needs_confirmation else None, "role": "identify evidence; never decide urgency"}
