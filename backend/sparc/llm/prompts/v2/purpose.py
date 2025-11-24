"""
Purpose aspect prompt for SPARC V2.
"""

PURPOSE_PROMPT = """You are a game design expert evaluating the PURPOSE definition.

## ASPECT-RELEVANT CONTENT

{aspect_text}

## EVALUATION CRITERIA

A well-defined purpose should:
1. Clearly state WHY this project exists
2. Explain the CREATOR'S motivation - why they want to work on this
3. Articulate what the creator wants to ACHIEVE
4. Consider why OTHERS might want to work on or play this

## ASSESSMENT

Evaluate the content above:
- "well_defined": Clear project purpose, strong creator motivation, defined goals
- "needs_work": Vague purpose, unclear motivation, or missing achievement goals

## RESPONSE

Provide:
1. status: "well_defined" or "needs_work"
2. reasoning: 2-3 sentences explaining your assessment
3. suggestions: Concrete improvements (include even if well_defined)

Return JSON with aspect_name: "purpose"
"""
