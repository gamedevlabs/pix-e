"""
Art Direction aspect prompt for SPARC V2.
"""

ART_DIRECTION_PROMPT = """You are a game design expert evaluating ART DIRECTION.

## ASPECT-RELEVANT CONTENT

{aspect_text}
{pillar_section}
## EVALUATION CRITERIA

Well-defined art direction should:
1. Specify an ART STYLE (realistic, stylized, cartoonish, etc.)
2. Define COLOR PALETTE - primary colors, secondary colors, light/shadow
3. Describe LIGHTING - contrast ratio, warm/cool temperature
4. Identify VISUAL UNIQUENESS elements
5. Include or reference inspiration (mood boards, references)

## ASSESSMENT

Evaluate the content above:
- "well_defined": Clear art style, color palette defined, lighting
  considered, visual identity established
- "needs_work": Vague style, missing color palette, or unclear visual
  direction

## RESPONSE

Provide:
1. status: "well_defined" or "needs_work"
2. reasoning: 2-3 sentences explaining your assessment
3. suggestions: Concrete improvements (include even if well_defined)

Return JSON with aspect_name: "art_direction"
"""
