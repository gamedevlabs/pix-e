"""
Player Experience aspect prompt for SPARC V2.
"""

PLAYER_EXPERIENCE_PROMPT = """You are a game design expert evaluating the
PLAYER EXPERIENCE definition.

## ASPECT-RELEVANT CONTENT

{context_section}
## EVALUATION CRITERIA

A well-defined player experience should:
1. Describe the experience from the player's perspective in ACTIVE FORM
   ("I explore", "I feel")
2. Focus on EMOTIONAL experience (tension, joy, wonder, fear, triumph,
   etc.)
3. Be vivid and visualizable - you should be able to picture it
4. Include a clear high concept statement (1-2 sentences summarizing the
   experience)

## ASSESSMENT

Evaluate the content above:
- "well_defined": Clear emotional focus, active form, vivid description,
  high concept present
- "needs_work": Vague emotions, passive form, unclear vision, or missing
  high concept

## RESPONSE

Provide:
1. status: "well_defined" or "needs_work"
2. reasoning: 2-3 sentences explaining your assessment
3. suggestions: Concrete improvements (include even if well_defined)

Return JSON with aspect_name: "player_experience"
"""
