"""
Prompts for SPARC H-MEM context extraction.
"""

DOMAIN_SUMMARY_PROMPT = """Summarize the game concept at a high level.

Rules:
- 3 to 5 sentences.
- Capture core gameplay, goals, setting, and unique features.
- Do not invent information.

Game concept:
{game_text}

Summary:"""

ASPECT_SUMMARY_PROMPT = """Summarize the game concept for the following SPARC aspect.

Aspect: {aspect_name}
Aspect focus: {aspect_description}

Rules:
- 2 to 4 sentences.
- Only include content relevant to the aspect.
- Do not invent information.

Game concept:
{game_text}

Aspect summary:"""
