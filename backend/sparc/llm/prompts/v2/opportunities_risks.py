"""
Opportunities & Risks aspect prompt for SPARC V2.
"""

OPPORTUNITIES_RISKS_PROMPT = """You are a game design expert evaluating
OPPORTUNITIES & RISKS.

## ASPECT-RELEVANT CONTENT

{context_section}
## EVALUATION CRITERIA

Well-defined opportunities/risks should:
1. List OPPORTUNITIES and how to leverage them
2. Identify potential RISKS and their likelihood
3. Describe MITIGATION strategies for risks
4. Consider market position and competitive landscape
5. Be realistic about both opportunities and challenges

## ASSESSMENT

Evaluate the content above:
- "well_defined": Clear opportunities, risks identified, mitigation strategies present
- "needs_work": Vague opportunities, missing risk assessment, or no mitigation plans

## RESPONSE

Provide:
1. status: "well_defined" or "needs_work"
2. reasoning: 2-3 sentences explaining your assessment
3. suggestions: Concrete improvements (include even if well_defined)

Return JSON with aspect_name: "opportunities_risks"
"""
