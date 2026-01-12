# backend/player_expectations_new/dataset_explorer/constants.py
from __future__ import annotations

from typing import Dict, List

GAME_NAMES = {
    367520: "Hollow Knight",
    620: "Portal 2",
    268910: "Cuphead",
    1057090: "Ori and the Will of the Wisps",
    238460: "BattleBlock Theater",
    255710: "Cities: Skylines",
    813780: "Age of Empires II",
    323190: "Frostpunk",
    949230: "Cities: Skylines II",
    1363080: "Manor Lords",
    774171: "Muse Dash",
    977950: "A Dance of Fire and Ice",
    1817230: "Hi-Fi RUSH",
    960170: "DJMAX RESPECT V",
    774181: "Rhythm Doctor",
    646570: "Slay the Spire",
    2379780: "Balatro",
    1092790: "Inscryption",
    1449850: "Yu-Gi-Oh! Master Duel",
    544810: "KARDS",
    291550: "Brawlhalla",
    678950: "DRAGON BALL FighterZ",
    1364780: "Street Fighter 6",
    1384160: "GUILTY GEAR -STRIVE-",
    310950: "Street Fighter V",
}

# ---- Genres -> AppIDs (for the left UI) ----
GENRE_APPIDS: Dict[str, List[int]] = {
    "Platformer": [367520, 620, 268910, 1057090, 238460],
    "City Builder": [255710, 813780, 323190, 949230, 1363080],
    "Rhythm": [774171, 977950, 1817230, 960170, 774181],
    "Card Game": [646570, 2379780, 1092790, 1449850, 544810],
    "2D Fighter": [291550, 678950, 1364780, 1384160, 310950],
}

ALLOWED_COARSE = ["Game Aesthetics", "Game Features", "Pain Points"]

SENTIMENT_LABELS = [
    "explicit_positive",
    "explicit_negative",
    "implicit_positive",
    "implicit_negative",
    "sarcastic_positive",
    "sarcastic_negative",
    "neutral",
    "missing",
]

POSITIVE_LABELS = {
    "explicit_positive",
    "implicit_positive",
    "sarcastic_positive",
}
NEGATIVE_LABELS = {
    "explicit_negative",
    "implicit_negative",
    "sarcastic_negative",
}
NEUTRAL_LABELS = {"neutral"}

# -----------------------------
# CODE -> TEXT mappings (same as your pipeline)
# -----------------------------
FEATURE_CODE_TO_TEXT = {
    10: "Sound",
    11: "Realistic sound effects",
    12: "Speaking characters",
    13: "Background music",
    14: "Narration",
    20: "Graphics",
    21: "High-quality realistic graphics",
    22: "Cartoon-style graphics",
    23: "Full Motion Video (FMV)",
    30: "Background and Setting",
    31: "Based on a story",
    32: "Based on film or TV",
    33: "Realistic settings",
    34: "Fantasy settings",
    40: "Duration of Game",
    41: "Long (months or years)",
    42: "Medium (days or weeks)",
    43: "Short (one session)",
    50: "Rate of Play",
    51: "Rapid absorption rate (how quickly a person could get into the game)",
    52: "Rapid advancement rate (how quickly progress is made)",
    60: "Use of Humor",
    61: "Presence of humor",
    70: "Control Options",
    71: "Sound settings",
    72: "Graphic settings",
    73: "Skill/level settings",
    74: "Choice of control methods",
    75: "Physical feedback",
    800: "Game Dynamics",
    801: "Exploring new areas",
    802: "Elements of surprise",
    803: "Fulfilling quests",
    804: "Skill development",
    805: "Sophisticated AI interactions",
    806: "Finding things (secret doors, levers)",
    807: "Surviving against the odds",
    808: "Shooting (enemies, targets, etc.)",
    809: "Different ending options",
    810: "Different modes of transport",
    811: "Collecting things (objects, keys)",
    812: "Solving puzzles",
    813: "Beating times",
    814: "Cheats / Easter eggs",
    815: "Avoiding things",
    816: "Solving time-limited problems",
    817: "Building environments",
    818: "Mapping",
    819: "Linear / non-linear game format",
    90: "Winning and Losing Features",
    91: "Potential to lose points",
    92: "Points accumulation",
    93: "Finding bonuses",
    94: "Having to start level again",
    95: "Ability to save regularly",
    100: "Character Development",
    101: "Character development over time",
    102: "Character customization",
    110: "Brand Assurance",
    111: "Brand loyalty",
    112: "Celebrity endorsement",
    120: "Multiplayer Features",
    121: "Multiplayer option (online)",
    122: "Multiplayer (LAN)",
    123: "Multiplayer communication",
    124: "Building alliances",
    125: "Beating other players or NPCs",
    130: "Price and Value",
    131: "Game price and perceived value",
    132: "In-game monetisation",
}

PAIN_CODE_TO_TEXT: Dict[int, str] = {
    10: "Unpredictable / inconsistent response to user's actions",
    11: "poor hit detection",
    12: "poor in-game physics",
    13: "inconsistent response to input",
    20: "Does not allow enough customization",
    21: "cannot change video or audio settings",
    22: "cannot change difficulty",
    23: "cannot change game speed",
    30: "Artificial intelligence problems",
    31: "problems with pathfinding",
    32: "problems with computer-controlled teammates",
    40: "Mismatch between camera/view and action",
    41: "bad camera angle",
    42: "view is obstructed",
    43: "view does not adjust quickly enough to user actions",
    50: "Does not let user skip non-playable content",
    51: "cannot skip video or audio clips",
    52: "frequently repeated non-playable sequences",
    60: "Clumsy input scheme",
    61: "bad input mappings",
    62: "limited device support",
    63: "limited control customization",
    70: "Difficult to control actions in the game",
    71: "oversensitive controls",
    72: "unnatural controls",
    73: "unresponsive controls",
    80: "Does not provide enough information on game status",
    81: "does not provide adequate information on character, game world, or enemies",
    82: "visual indicators, icons, and maps are inadequate",
    90: "Does not provide adequate training and help",
    91: "does not provide default or recommended choices",
    92: "does not provide suggestions or help",
    93: "does not provide adequate documentation, instructions, tutorials, and training videos",
    100: "Command sequences are too complex",
    101: "learning curve is too steep",
    102: "requires too much micromanagement",
    103: "command sequences are complex, lengthy, or awkward",
    110: "Visual representations are difficult to interpret",
    111: "bad visualization of information",
    112: "too much screen clutter",
    113: "too many characters or game elements on the screen at the same time",
    114: "difficult to visually distinguish interactive content from non-interactive content",
    120: "Response to user's action not timely enough",
    130: "Translation and localization issues",
    131: "inadequate or missing localization",
    132: "incorrect or misleading translation",
    140: "Performance and technical stability",
    141: "low or unstable frame rate (FPS drops, stuttering)",
    142: "excessive loading times",
    143: "crashes or freezes",
    150: "Connectivity and online stability",
    151: "frequent disconnects",
    152: "matchmaking or queue issues",
    153: "server instability or downtime",
}

AESTHETIC_CODE_TO_TEXT: Dict[int, str] = {
    1: "Sensation: Game as sense-pleasure",
    2: "Fantasy: Game as make-believe",
    3: "Narrative: Game as drama",
    4: "Challenge: Game as obstacle course",
    5: "Fellowship: Game as social framework",
    6: "Discovery: Game as uncharted territory",
    7: "Expression: Game as self-discovery",
    8: "Submission: Game as pastime",
}


def code_to_label(coarse_category: str, code_int: int) -> str:
    if coarse_category == "Game Features":
        return FEATURE_CODE_TO_TEXT.get(code_int, "UNKNOWN")
    if coarse_category == "Pain Points":
        return PAIN_CODE_TO_TEXT.get(code_int, "UNKNOWN")
    if coarse_category == "Game Aesthetics":
        return AESTHETIC_CODE_TO_TEXT.get(code_int, "UNKNOWN")
    return "UNKNOWN"
