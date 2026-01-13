"""
Unique Features aspect prompt for SPARC V2.
"""

UNIQUE_FEATURES_PROMPT = """You are a game design expert evaluating UNIQUE FEATURES.

## ASPECT-RELEVANT CONTENT

{context_section}
## EVALUATION CRITERIA

Well-defined unique features should:
1. Identify what makes this game UNIQUE
2. Explain how it DIFFERS from similar games
3. Describe how it IMPROVES upon existing genre/themes
4. List 3-5 DEFINING ELEMENTS that set it apart
5. Features should be VALIDATED - actually unique, not just claimed

## ASSESSMENT

Evaluate the content above:
- "well_defined": Clear unique features, differentiation explained,
  defining elements listed
- "needs_work": Generic features, weak differentiation, or unvalidated
  uniqueness claims

## RESPONSE

Provide:
1. status: "well_defined" or "needs_work"
2. reasoning: 2-3 sentences explaining your assessment
3. suggestions: Concrete improvements (include even if well_defined)

Return JSON with aspect_name: "unique_features"
"""
