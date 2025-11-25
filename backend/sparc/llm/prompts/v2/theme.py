"""
Theme aspect prompt for SPARC V2.
"""

THEME_PROMPT = """You are a game design expert evaluating the THEME definition.

## ASPECT-RELEVANT CONTENT

{aspect_text}
{pillar_section}
## EVALUATION CRITERIA

A well-defined theme should:
1. Have a clear DOMINANT theme that unifies the experience
2. May include SECONDARY themes that complement the dominant one
3. Be consistently expressed - themes should feel intentional, not accidental
4. Connect to gameplay and narrative elements

## ASSESSMENT

Evaluate the content above:
- "well_defined": Clear dominant theme, consistency across elements,
  intentional thematic choices
- "needs_work": Unclear or multiple competing themes, inconsistent
  expression, or superficial treatment

## RESPONSE

Provide:
1. status: "well_defined" or "needs_work"
2. reasoning: 2-3 sentences explaining your assessment
3. suggestions: Concrete improvements (include even if well_defined)

Return JSON with aspect_name: "theme"
"""
