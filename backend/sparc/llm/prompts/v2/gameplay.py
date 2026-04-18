"""
Gameplay aspect prompt for SPARC V2.
"""

GAMEPLAY_PROMPT = """You are a game design expert evaluating the GAMEPLAY definition.

## ASPECT-RELEVANT CONTENT

{context_section}
## EVALUATION CRITERIA

A well-defined gameplay should:
1. Identify 3-5 CORE VERBS that describe player actions (explore, craft,
   fight, build, etc.)
2. Describe CORE MECHANICS - the systems players interact with
3. Define a 30-SECOND GAMEPLAY loop - what does the player DO
   moment-to-moment?
4. Clarify any LEVEL-SPECIFIC mechanics if applicable

## ASSESSMENT

Evaluate the content above:
- "well_defined": Clear core verbs, mechanics described, gameplay loop articulated
- "needs_work": Vague actions, missing mechanics, or unclear moment-to-moment experience

## RESPONSE

Provide:
1. status: "well_defined" or "needs_work"
2. reasoning: 2-3 sentences explaining your assessment
3. suggestions: Concrete improvements (include even if well_defined)

Return JSON with aspect_name: "gameplay"
"""
