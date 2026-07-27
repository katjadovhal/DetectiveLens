"""Deterministic hint templates keyed by existing challenge.skillCategoryIds."""

GENERIC_FALLBACK = {
    "firstHint": "Compare both options carefully and look for small differences.",
    "strongerHint": "Check people, objects, text, colours, lighting, and backgrounds.",
    "transferTip": "Use several clues before deciding.",
    "approvedChecklist": [
        "Compare both options side by side",
        "Look for unusual details",
        "Check more than one clue before choosing",
    ],
}

PATTERN_HINT_TEMPLATES: dict[str, dict] = {
    "blurred_background": {
        "firstHint": "Compare the backgrounds in both images.",
        "strongerHint": (
            "Check whether one background appears unusually blurred "
            "or disconnected from the main subject."
        ),
        "transferTip": "Compare whether foreground and background details fit together.",
        "approvedChecklist": [
            "Compare foreground and background",
            "Look for blurred or broken edges",
            "Check whether background objects fit the scene",
        ],
    },
    "shiny_texture": {
        "firstHint": "Compare the surface textures in both images.",
        "strongerHint": (
            "Look for skin, eyes, hair, or objects that appear unusually shiny."
        ),
        "transferTip": "Unusual shine can be an investigation clue, but it is not proof.",
        "approvedChecklist": [
            "Inspect skin and eyes",
            "Compare reflections",
            "Look for surfaces that appear unnaturally glossy",
        ],
    },
    "waxy_perfect": {
        "firstHint": "Look closely at skin and smooth surfaces.",
        "strongerHint": (
            "Check whether skin appears unusually smooth, waxy, or flawless."
        ),
        "transferTip": "Natural skin usually contains small variations and texture.",
        "approvedChecklist": [
            "Look for natural skin texture",
            "Compare facial details",
            "Check whether surfaces look too perfect",
        ],
    },
    "color": {
        "firstHint": "Compare the colours in both images.",
        "strongerHint": (
            "Check whether any colours appear unusually bright or saturated."
        ),
        "transferTip": "Extreme colour saturation can be an investigation clue.",
        "approvedChecklist": [
            "Compare colour intensity",
            "Look for unnatural skin tones",
            "Check whether clothing colours appear exaggerated",
        ],
    },
    "proportions": {
        "firstHint": "Compare the shapes and sizes of people and objects.",
        "strongerHint": (
            "Check whether any face, limb, or object looks oddly sized or placed."
        ),
        "transferTip": "Unusual proportions can be a clue, but check other details too.",
        "approvedChecklist": [
            "Compare face and body proportions",
            "Look at object sizes",
            "Check whether parts look out of place",
        ],
    },
    "functional": {
        "firstHint": "Check whether objects and scenes look practical and realistic.",
        "strongerHint": (
            "Look for items that seem impossible, misplaced, or oddly arranged."
        ),
        "transferTip": "Ask whether the scene would work in real life.",
        "approvedChecklist": [
            "Check whether objects make sense",
            "Look for impossible arrangements",
            "Compare how things are usually used",
        ],
    },
    "sociocultural": {
        "firstHint": "Think about whether the scene matches what you would expect.",
        "strongerHint": (
            "Check clothing, setting, or behaviour that seems unusual for the situation."
        ),
        "transferTip": "Context clues can help, but unusual scenes are not always fake.",
        "approvedChecklist": [
            "Check whether the setting fits the subject",
            "Look for unusual clothing or behaviour",
            "Compare with what you would normally expect",
        ],
    },
    "emotions": {
        "firstHint": "Look at faces and expressions in both images.",
        "strongerHint": (
            "Check whether expressions look exaggerated, stiff, or oddly similar."
        ),
        "transferTip": "Expressions can look unusual in some images, so use other clues too.",
        "approvedChecklist": [
            "Compare facial expressions",
            "Look for stiff or exaggerated faces",
            "Check eyes and mouth details",
        ],
    },
    "blurred_textures": {
        "firstHint": "Compare textures and fine details in both images.",
        "strongerHint": (
            "Check whether some areas look unusually soft, smudged, or lacking detail."
        ),
        "transferTip": "Blurry or smudged textures can be a clue when compared carefully.",
        "approvedChecklist": [
            "Compare fine textures",
            "Look for smudged or soft areas",
            "Check edges and small details",
        ],
    },
    "anatomy": {
        "firstHint": "Look closely at hands, limbs, and body parts.",
        "strongerHint": (
            "Check whether fingers, joints, or limbs look oddly shaped or connected."
        ),
        "transferTip": "Small anatomy details are worth comparing in both images.",
        "approvedChecklist": [
            "Inspect hands and fingers",
            "Compare limbs and joints",
            "Look for odd connections or shapes",
        ],
    },
}

WORD_LIMITS = {
    "8_10": 25,
    "11_13": 45,
    "14_16": 70,
}

YOUNG_WORD_LIMIT = 20  # ages <= 7 mapped to 8_10 with stricter limit


def get_template(pattern_id: str) -> dict:
    return PATTERN_HINT_TEMPLATES.get(pattern_id, GENERIC_FALLBACK)


def resolve_templates(pattern_ids: list[str]) -> tuple[list[str], list[str]]:
    """Return known pattern ids and any unknown ids for diagnostics."""
    known: list[str] = []
    unknown: list[str] = []
    for pid in pattern_ids:
        if pid in PATTERN_HINT_TEMPLATES:
            known.append(pid)
        else:
            unknown.append(pid)
    return known, unknown
