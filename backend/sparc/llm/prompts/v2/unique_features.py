"""
Unique Features aspect prompt for SPARC V2.
"""

UNIQUE_FEATURES_PROMPT = """You are an expert game development consultant
evaluating UNIQUE FEATURES.

## ASPECT-RELEVANT CONTENT

{aspect_text}
{pillar_section}
## ASPECT GUIDE (SPARC)

Describe how the idea will be unique by answering the questions:
What does your idea feature that is unique?
How is your idea different to other projects out there?
How does it improve upon existing genre/location/theme?
How is your idea (in the case of a level) different to other parts of your game?
Create a list with 3-5 features that will be the defining elements of your idea.

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

Return JSON with aspect_name: "unique_features"
"""
