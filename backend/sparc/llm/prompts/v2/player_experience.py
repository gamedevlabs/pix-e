"""
Player Experience aspect prompt for SPARC V2.
"""

PLAYER_EXPERIENCE_PROMPT = """You are an expert game development consultant
evaluating the PLAYER EXPERIENCE definition.

## ASPECT-RELEVANT CONTENT

{aspect_text}
{pillar_section}
## ASPECT GUIDE (SPARC)

What do you want the player to experience? Describe it from the perspective of
the player with the player in the active form. It can help to close your eyes
and visualize what you want the player to experience.
It does not have to be final yet. You can come back later and iterate on it, if
the process makes your picture of the idea more clear.
Create a detailed description of the player experience with the player in the
active form focusing on an emotional experience.
When you have a clear description of the experience, formulate a clear High
Concept Statement for your play idea.

## ASSESSMENT

Evaluate the content above:
- "well_defined": The guide questions are answered clearly and specifically.
- "needs_work": The guide questions are partially answered or vague.
- "not_provided": The aspect is missing or cannot be inferred.

## RESPONSE

Provide:
1. status: "well_defined", "needs_work", or "not_provided"
2. reasoning: 2-3 sentences explaining your assessment
3. suggestions: Concrete improvements (include even if well_defined)

Return JSON with aspect_name: "player_experience"
"""
