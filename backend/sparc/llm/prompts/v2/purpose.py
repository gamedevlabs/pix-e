"""
Purpose aspect prompt for SPARC V2.
"""

PURPOSE_PROMPT = """You are an expert game development consultant evaluating
the PURPOSE definition.

## ASPECT-RELEVANT CONTENT

{aspect_text}
{pillar_section}
## ASPECT GUIDE (SPARC)

Understand why you want to work on this project. What do you want to achieve?
Then, formulate the purpose of the project itself. Document this. Answer the
following questions: [2]
What is the purpose of the game or level you want to work on? The purpose of
this project is...
What is the reason and purpose why YOU want to work on this project? The reason
I want to create this is...
Why would OTHERS want to work on this project?
What do YOU want to achieve with completing this project? With completing this
project, I want to achieve...

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

Return JSON with aspect_name: "purpose"
"""
