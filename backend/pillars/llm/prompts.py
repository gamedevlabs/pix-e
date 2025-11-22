"""
Prompts for pillar operations.

These prompts are used by pillar handlers to generate LLM requests.
All prompts are migrated from backend/llm/llm_links/prompts.py to centralize
pillar-specific logic in the orchestrator.
"""

ValidationPrompt = """Validate the following Game Design Pillar.
Check for structural issues regarding the following points:
1. The title does not match the description.
2. The intent of the pillar is not clear.
3. The pillar focuses on more than one aspect.
4. The description uses bullet points or lists.
Pillar Title: %s
Pillar Description: %s
For each feedback limit your answer to one sentence.
Answer as if you were talking directly to the designer.
"""

ImprovePillarPrompt = """Improve the following Game Design Pillar.
Check for structural issues regarding the following points:
1. The title does not match the description.
2. The intent of the pillar is not clear.
3. The pillar focuses on more than one aspect.
4. The description uses bullet points or lists.
Pillar Title: %s
Pillar Description: %s
Rewrite erroneous parts of the pillar and return a new pillar object.
"""

PillarCompletenessPrompt = """Assume the role of a game design expert.
Evaluate if the following Game Design Pillars are a good fit
for the game idea, explain why.
Also check if the pillar contradicts the direction of the game idea.

Game Design Idea: %s

Design Pillars: %s
"""

PillarContradictionPrompt = """Assume the role of a game design expert.
Evaluate if the following Game Design Pillars stand in contradiction
towards each other. Use the Game Design Idea as context.

Game Design Idea: %s

Design Pillars: %s
"""

PillarAdditionPrompt = """Assume the role of a game design expert.
Evaluate if the following Game Design Idea is sufficiently
covered by the following Game Design Pillars.

Game Design Idea: %s

Design Pillars: %s
If not, add new pillars to cover the missing aspects.
"""

ContextInPillarsPrompt = """Assume the role of a game design expert.
Evaluate how well the following idea aligns with the given Game Design Pillars.

Idea: %s

Design Pillars: %s
"""

# noqa: E501
ImprovePillarWithExplanationPrompt = """
Improve the following Game Design Pillar and explain your improvements.

VALIDATION ISSUES DETECTED:
%s

CURRENT PILLAR:
Name: %s
Description: %s

INSTRUCTIONS:
1. Fix the structural issues listed above
2. For each change you make, explain WHY it improves the pillar
3. Reference which validation issue(s) each change addresses

RULES FOR GOOD PILLARS:
- Title must directly reflect what the description talks about
- Intent must be clear and unambiguous
- Focus on ONE aspect only (not multiple concerns)
- Use flowing prose, NOT bullet points or lists

RESPOND WITH THIS EXACT JSON STRUCTURE:
{
  "name": "Improved pillar name",
  "description": "Improved pillar description in prose form",
  "changes": [
    {
      "field": "name",
      "after": "The new name value",
      "reasoning": "Explanation of why this name is better",
      "issues_addressed": e.g. ["Title Mismatch"]
    },
    {
      "field": "description",
      "after": "The new description value",
      "reasoning": "Explanation of why this description is better",
      "issues_addressed": e.g. ["Unclear Intent", "Use of Bullet Points"]
    }
  ],
  "overall_summary": "Summary of why improved pillar is better",
  "validation_issues_fixed": ["Title Mismatch", "Unclear Intent"]
}

Only include changes for fields you actually modified.
"""
