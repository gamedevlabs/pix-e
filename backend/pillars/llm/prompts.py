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
4. The description uses bullet points or lists (e.g., lines starting with •, -, *, or numbered items like 1. 2. 3., or line breaks creating a list structure).

IMPORTANT: For issue #4, only flag actual bullet points, dashes, asterisks, or numbered lists. Do NOT flag prose text that uses "and" or has multiple clauses. Prose paragraphs are NOT lists.

Pillar Title: %s
Pillar Description: %s

For each issue found, provide feedback. If no issues are found for a point, do not mention it.
For each feedback limit your answer to one sentence.
Answer as if you were talking directly to the designer.
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

VALIDATION ISSUES DETECTED BY VALIDATION SYSTEM (YOU MUST ADDRESS ALL OF THESE):
%s

CURRENT PILLAR:
Name: %s
Description: %s

CRITICAL INSTRUCTIONS:
1. You MUST address ALL validation issues listed above. The validation system has already determined these issues exist, so you must fix them all.
2. Do NOT skip any issues. Do NOT decide that an issue "doesn't apply" - the validation system has already flagged it.
3. For each issue, make appropriate changes to fix it. If multiple issues can be addressed with the same change, that's fine, but ensure ALL issues are addressed.

4. FOR EACH CHANGE YOU MAKE:
   - Explain WHY it improves the pillar
   - Identify which validation issues this change fixes (a single change can fix multiple issues)
   - List ALL of those issues in the "issues_addressed" array for that change
   - Use the EXACT issue titles from the validation issues list above
   - IMPORTANT: If your description change fixes "Issue A" AND "Issue B", then that change's "issues_addressed" must be ["Issue A", "Issue B"] - include BOTH

5. In your response, list ALL issues in the "validation_issues_fixed" array - you must fix all of them, using their exact titles from the list above.

6. VERIFICATION STEP (CRITICAL): Before finalizing your response:
   - Count the issues in "validation_issues_fixed" 
   - For each issue in that list, verify it appears in at least one change's "issues_addressed" array
   - If any issue is missing from all "issues_addressed" arrays, you MUST add it to the appropriate change's array
   - Example: If "validation_issues_fixed" = ["Issue 1", "Issue 2", "Issue 3"], then:
     * "Issue 1" must appear in at least one change's "issues_addressed"
     * "Issue 2" must appear in at least one change's "issues_addressed"  
     * "Issue 3" must appear in at least one change's "issues_addressed"

RULES FOR GOOD PILLARS (use these to guide your fixes):
- Title must directly reflect what the description talks about
- Intent must be clear and unambiguous
- Focus on ONE aspect only (not multiple concerns)
- Use flowing prose, NOT bullet points or lists

MAPPING ISSUES TO CHANGES:
- Issues related to title/name mismatch typically require name changes
- Issues related to clarity, intent, focus, or structure typically require description changes
- A single description change can fix MULTIPLE issues (e.g., if you rewrite the description to be clearer and more focused, it may fix both an "Unclear Intent" issue AND a "Focus on Multiple Aspects" issue simultaneously)
- When a description change fixes multiple issues, ALL of them must be listed in that change's "issues_addressed" array - do not list only the "primary" issue

RESPOND WITH THIS EXACT JSON STRUCTURE:
{
  "name": "Improved pillar name",
  "description": "Improved pillar description in prose form",
  "changes": [
    {
      "field": "name",
      "after": "The new name value",
      "reasoning": "Explanation of why this name is better",
      "issues_addressed": ["<use exact issue title from the list above>"]
    },
    {
      "field": "description",
      "after": "The new description value",
      "reasoning": "Explanation of why this description is better",
      "issues_addressed": ["<use exact issue titles from the list above, can include multiple>"]
    }
  ],
  "overall_summary": "Summary of why improved pillar is better",
  "validation_issues_fixed": ["<must include ALL issue titles from the list above>"]
}

IMPORTANT RULES:
1. The "validation_issues_fixed" array must include ALL issues from the list above (use their exact titles).
2. If you address multiple issues with one change, list ALL of them in that change's "issues_addressed" array (use exact issue titles). DO NOT list only the "primary" issue - list ALL issues that change addresses.
3. Every issue in "validation_issues_fixed" MUST appear in at least one change's "issues_addressed" array. This is non-negotiable.
4. Use the EXACT issue titles from the validation issues list above - do not make up new issue names or use examples from this prompt.
5. If a single change (e.g., a description rewrite) fixes multiple issues from the list above, ALL of those issues must be included in that change's "issues_addressed" array. Do not list only one issue if the change actually fixes multiple issues.
6. Before submitting, double-check: every issue title in "validation_issues_fixed" must appear in at least one "issues_addressed" array in the "changes" array.
"""
