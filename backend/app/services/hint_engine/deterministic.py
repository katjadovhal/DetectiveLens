"""Build deterministic approved messages before optional LLM adaptation."""

from __future__ import annotations

from app.services.hint_engine.pattern_templates import (
    GENERIC_FALLBACK,
    get_template,
    resolve_templates,
)


def _join_hints(parts: list[str], max_parts: int = 2) -> str:
    unique = []
    for part in parts:
        cleaned = part.strip()
        if cleaned and cleaned not in unique:
            unique.append(cleaned)
    if not unique:
        return GENERIC_FALLBACK["firstHint"]
    return " ".join(unique[:max_parts])


def build_pre_answer_hint(pattern_ids: list[str], stage: str) -> dict:
    known, unknown = resolve_templates(pattern_ids)
    templates = [get_template(pid) for pid in known]
    if not templates:
        templates = [GENERIC_FALLBACK]

    if stage == "stronger_hint":
        text = _join_hints([t["strongerHint"] for t in templates], max_parts=2)
        title = "Detective Clue"
    else:
        text = _join_hints([t["firstHint"] for t in templates], max_parts=2)
        title = "Detective Clue"

    checklist: list[str] = []
    for pid in known[:1]:
        checklist = get_template(pid)["approvedChecklist"][:3]
        break

    return {
        "title": title,
        "text": text,
        "checklist": checklist,
        "tone": "supportive",
        "pattern_ids": known,
        "unknown_pattern_ids": unknown,
        "evidence_claim": None,
        "reveals_answer": False,
    }


def build_answer_explanation(bullets: list[str]) -> dict:
    cleaned = [b.strip() for b in bullets if b and b.strip()]
    text = ""
    for bullet in cleaned:
        candidate = f"{text} {bullet}".strip() if text else bullet
        if len(candidate) > 500:
            break
        text = candidate
    if not text:
        text = "Review the clues that helped identify the answer."
    return {
        "title": "Why?",
        "text": text,
        "checklist": [],
        "tone": "neutral",
        "pattern_ids": [],
        "unknown_pattern_ids": [],
        "evidence_claim": None,
        "reveals_answer": False,
    }


def build_detective_tip(
    pattern_ids: list[str],
    personalization_mode: str,
    evidence_count: int | None,
) -> dict:
    known, unknown = resolve_templates(pattern_ids)
    templates = [get_template(pid) for pid in known] if known else [GENERIC_FALLBACK]

    tips = [t["transferTip"] for t in templates]
    text = tips[0] if tips else GENERIC_FALLBACK["transferTip"]

    if personalization_mode == "practice_support":
        prefix = "This round was tricky. A useful check is "
        text = prefix + text
    elif personalization_mode == "recent_recovery":
        text = "You recognised useful clues successfully this time. " + text
    elif personalization_mode == "developing_strength" and evidence_count:
        text = (
            f"Based on your last {evidence_count} relevant challenges, "
            f"these clues are going well. {text}"
        )
    elif personalization_mode == "hint_scaffolding":
        text = "Clues can help you compare details. " + text
    elif personalization_mode == "insufficient_data":
        text = "A useful strategy is to compare small details in both images. " + text

    checklist: list[str] = []
    for template in templates:
        for item in template["approvedChecklist"]:
            if item not in checklist:
                checklist.append(item)
            if len(checklist) >= 3:
                break
        if len(checklist) >= 3:
            break

    return {
        "title": "Detective Tip",
        "text": text,
        "checklist": checklist[:3],
        "tone": "encouraging" if personalization_mode in ("recent_recovery", "developing_strength") else "supportive",
        "pattern_ids": known,
        "unknown_pattern_ids": unknown,
        "evidence_claim": str(evidence_count) if evidence_count else None,
        "reveals_answer": False,
    }


def build_practice_recommendation(pattern_id: str | None = None) -> dict:
    if pattern_id:
        template = get_template(pattern_id)
        tip = template.get("transferTip") or GENERIC_FALLBACK["transferTip"]
        text = f"This is a useful next practice area. {tip}"
    else:
        text = "This is a useful next practice area. Try another challenge with similar clues."
    return {
        "title": "Practise this skill",
        "text": text,
        "checklist": [],
        "tone": "encouraging",
        "pattern_ids": [pattern_id] if pattern_id else [],
        "unknown_pattern_ids": [],
        "evidence_claim": None,
        "reveals_answer": False,
    }


def build_learning_insight(
    personalization_mode: str,
    practice_pattern: str | None = None,
    developing_strength: str | None = None,
) -> dict:
    if personalization_mode == "insufficient_data":
        text = "Keep practising challenges to build your personal detective insights."
    elif practice_pattern:
        tip = get_template(practice_pattern).get("transferTip") or GENERIC_FALLBACK["transferTip"]
        text = f"A useful next focus is this clue type. {tip}"
    elif developing_strength:
        tip = get_template(developing_strength).get("transferTip") or GENERIC_FALLBACK["transferTip"]
        text = f"These clues are becoming a strength. {tip}"
    elif personalization_mode == "recent_recovery":
        text = "You are recognising useful clues more successfully. Keep comparing carefully."
    else:
        text = "Compare small details across both images before you decide."

    return {
        "title": "Learning insight",
        "text": text,
        "checklist": [],
        "tone": "encouraging",
        "pattern_ids": [p for p in [practice_pattern, developing_strength] if p],
        "unknown_pattern_ids": [],
        "evidence_claim": None,
        "reveals_answer": False,
    }
