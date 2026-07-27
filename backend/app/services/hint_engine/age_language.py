"""Deterministic age-band language for fallback when Ollama is unavailable.

Does not change challenge pattern templates. Those remain the approved fact source
for the model. This module only rewrites user-facing fallback wording.
"""

from __future__ import annotations

import re

from app.services.hint_engine.pattern_templates import WORD_LIMITS

# Child-friendly wording for ages 8–10, keyed by the same pattern ids.
YOUNG_PATTERN_LANGUAGE: dict[str, dict[str, object]] = {
    "blurred_background": {
        "firstHint": "Look at the background in both pictures. Does one look blurry?",
        "strongerHint": "Is the background soft or fuzzy behind the main thing?",
        "transferTip": "Check if the front and the back of the picture fit together.",
        "checklist": ["Look at the background", "Is it blurry?", "Does it fit the front?"],
    },
    "shiny_texture": {
        "firstHint": "Look at shiny spots in both pictures.",
        "strongerHint": "Do skin, eyes, hair, or objects look too shiny?",
        "transferTip": "Too much shine can be a clue, but check more than one thing.",
        "checklist": ["Look at skin and eyes", "Compare shiny spots", "Does it look too shiny?"],
    },
    "waxy_perfect": {
        "firstHint": "Look at the skin in both pictures. Does one look too smooth?",
        "strongerHint": "Does the skin look plastic, or too perfect?",
        "transferTip": "Real skin usually has tiny bumps and little changes.",
        "checklist": ["Look at the skin", "Compare faces", "Does it look too perfect?"],
    },
    "color": {
        "firstHint": "Compare the colours in both pictures.",
        "strongerHint": "Do any colours look too bright or too strong?",
        "transferTip": "Very bright colours can be a clue.",
        "checklist": ["Compare colours", "Look at skin colour", "Do colours look too strong?"],
    },
    "proportions": {
        "firstHint": "Compare the shapes and sizes in both pictures.",
        "strongerHint": "Does a face, arm, or object look the wrong size?",
        "transferTip": "Odd sizes can be a clue. Check other details too.",
        "checklist": ["Compare sizes", "Look at faces and arms", "Does anything look out of place?"],
    },
    "functional": {
        "firstHint": "Do the things in the picture make sense in real life?",
        "strongerHint": "Is something in a strange place, or hard to use?",
        "transferTip": "Ask: would this work in real life?",
        "checklist": ["Do objects make sense?", "Is anything impossible?", "Would this work for real?"],
    },
    "sociocultural": {
        "firstHint": "Does the scene look like something you would expect?",
        "strongerHint": "Do clothes, places, or actions look unusual here?",
        "transferTip": "Odd scenes can be a clue, but they are not always fake.",
        "checklist": ["Does the setting fit?", "Look at clothes and actions", "Is this what you would expect?"],
    },
    "emotions": {
        "firstHint": "Look at the faces in both pictures.",
        "strongerHint": "Do the faces look stiff, funny, or too alike?",
        "transferTip": "Faces can look odd. Use other clues too.",
        "checklist": ["Compare faces", "Do they look stiff?", "Check eyes and mouths"],
    },
    "blurred_textures": {
        "firstHint": "Compare small details in both pictures.",
        "strongerHint": "Do some parts look soft, smudged, or missing detail?",
        "transferTip": "Soft or smudged spots can be a clue.",
        "checklist": ["Compare small details", "Look for soft spots", "Check the edges"],
    },
    "anatomy": {
        "firstHint": "Look at hands, arms, and body parts.",
        "strongerHint": "Do fingers or arms look bent in a strange way?",
        "transferTip": "Small body details are worth a careful look.",
        "checklist": ["Look at hands", "Compare arms", "Does anything look odd?"],
    },
}

YOUNG_GENERIC = {
    "firstHint": "Look carefully at both pictures. What looks different?",
    "strongerHint": "Check people, objects, colours, and backgrounds.",
    "transferTip": "Use more than one clue before you choose.",
    "checklist": ["Compare both pictures", "Look for odd details", "Check more than one clue"],
}

YOUNG_TITLES = {
    "pre_answer_hint": "Detective Clue",
    "stronger_hint": "Detective Clue",
    "answer_explanation": "Why?",
    "detective_tip": "Detective Tip",
    "practice_recommendation": "Try this next",
}


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text))


def _trim_words(text: str, limit: int) -> str:
    words = re.findall(r"\S+", text)
    if len(words) <= limit:
        return text.strip()
    return " ".join(words[:limit]).rstrip(".,;:") + "."


def _young_pattern_bits(pattern_ids: list[str]) -> list[dict]:
    bits = []
    for pid in pattern_ids:
        if pid in YOUNG_PATTERN_LANGUAGE:
            bits.append(YOUNG_PATTERN_LANGUAGE[pid])
    return bits or [YOUNG_GENERIC]


def _simplify_explanation(text: str) -> str:
    """Keep explanation facts, but use shorter child-friendly sentences."""
    # Prefer the first sentence-like chunk and soften a few adult words.
    replacements = [
        (r"\bAI-generated\b", "made by a computer"),
        (r"\bai-generated\b", "made by a computer"),
        (r"\bgenerated using AI\b", "made by a computer"),
        (r"\banthropomorphic\b", "human-like"),
        (r"\boversaturated\b", "too bright"),
        (r"\blightning\b", "lighting"),
        (r"\bphotograph\b", "photo"),
        (r"\bunusually\b", "very"),
        (r"\bflawless\b", "too perfect"),
        (r"\bwaxy\b", "plastic-looking"),
        (r"\btextures?\b", "details"),
        (r"\bsurfaces?\b", "parts"),
    ]
    softened = text
    for pattern, repl in replacements:
        softened = re.sub(pattern, repl, softened, flags=re.I)

    # Take up to two short sentences.
    parts = re.split(r"(?<=[.!?])\s+", softened.strip())
    kept = [p.strip() for p in parts if p.strip()][:2]
    if not kept:
        return "Look again at the clues that helped you decide."
    return _trim_words(" ".join(kept), WORD_LIMITS["8_10"])


def apply_age_language(approved: dict, age_band: str, stage: str) -> dict:
    """Return a copy of approved content rewritten for the age band fallback."""
    result = dict(approved)
    if age_band != "8_10":
        # 11_13 / 14_16 keep approved wording in fallback; Ollama adapts when available.
        if age_band == "11_13":
            limit = WORD_LIMITS["11_13"]
            result["text"] = _trim_words(str(result.get("text") or ""), limit)
        return result

    pattern_ids = list(result.get("pattern_ids") or [])
    bits = _young_pattern_bits(pattern_ids)
    title = YOUNG_TITLES.get(stage, result.get("title") or "Detective Clue")

    if stage in ("pre_answer_hint", "stronger_hint"):
        key = "strongerHint" if stage == "stronger_hint" else "firstHint"
        # One idea at a time for ages 8–10.
        text = str(bits[0].get(key) or YOUNG_GENERIC[key])
        checklist = list(bits[0].get("checklist") or YOUNG_GENERIC["checklist"])[:2]
    elif stage == "answer_explanation":
        text = _simplify_explanation(str(result.get("text") or ""))
        checklist = []
    elif stage == "practice_recommendation":
        tip = str(bits[0].get("transferTip") or YOUNG_GENERIC["transferTip"])
        text = f"This is a good next practice. {tip}"
        checklist = []
        title = YOUNG_TITLES["practice_recommendation"]
    else:
        # detective_tip / learning insight
        tip = str(bits[0].get("transferTip") or YOUNG_GENERIC["transferTip"])
        mode = ""
        original = str(result.get("text") or "")
        if original.lower().startswith("this round was tricky"):
            mode = "This one was tricky. "
        elif "recognised useful clues" in original.lower() or "recognizing useful clues" in original.lower():
            mode = "Nice work spotting clues. "
        text = _trim_words(mode + tip, WORD_LIMITS["8_10"])
        checklist = list(bits[0].get("checklist") or YOUNG_GENERIC["checklist"])[:2]

    result["title"] = title
    result["text"] = _trim_words(text, WORD_LIMITS["8_10"])
    result["checklist"] = checklist
    result["tone"] = result.get("tone") or "supportive"
    return result
