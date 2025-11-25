"""
Place aspect prompt for SPARC V2.
"""

PLACE_PROMPT = """You are a game design expert evaluating the PLACE/SETTING definition.

## ASPECT-RELEVANT CONTENT

{aspect_text}
{pillar_section}
## EVALUATION CRITERIA

A well-defined place/setting should:
1. Establish the ENVIRONMENT SETTING - the world type and feel
2. List CONCRETE KEY LOCATIONS - specific places, not just general areas
3. Be SPECIFIC enough to visualize - names, characteristics, atmosphere
4. Consider how locations connect to gameplay and narrative

## ASSESSMENT

Evaluate the content above:
- "well_defined": Clear environment, specific locations, vivid and visualizable
- "needs_work": Generic setting, vague locations, or lacks specificity

## RESPONSE

Provide:
1. status: "well_defined" or "needs_work"
2. reasoning: 2-3 sentences explaining your assessment
3. suggestions: Concrete improvements (include even if well_defined)

Return JSON with aspect_name: "place"
"""
