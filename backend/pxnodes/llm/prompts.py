"""
Prompts for node validation operations.

These prompts are used by node handlers to generate LLM requests.
"""

NodeValidationPrompt = """Analyze the following Game Design Node for coherence issues.

A Node represents a discrete game element (scene, event, object, state) with:
- A name (title) that identifies what it is
- A description that explains its purpose and behavior
- Component values that define its properties

Check for these coherence issues:

1. **Title/Description Mismatch (title_description_mismatch)**:
   The name doesn't match what the description says.

2. **Component Value Contradictions (component_value_contradiction)**:
   Component values contradict the node's stated purpose.
   Examples:
   - A "relaxing scene" node with an "intensity" component set to 10
   - A "fast-paced action" node with "speed" set to 0
   - A "dark atmosphere" node with "brightness" set to 10

3. **Component Conflicts (component_conflict)**:
   Multiple component values contradict each other.
   Example: "peaceful" = true but "danger_level" = 10

4. **Irrelevant Components (component_irrelevance)**:
   Components that don't make sense for this node type.
   Example: A "Menu Screen" node with a "damage" component

5. **Unclear Purpose (unclear_purpose)**:
   The node's purpose is vague or ambiguous.
   Example: Name "Thing", Description "Does stuff"

NODE TO VALIDATE:
Name: %s
Description: %s

COMPONENTS:
%s

CRITICAL RULES FOR REPORTING ISSUES:
1. ONLY include issues that ACTUALLY EXIST in the issues array.
2. If a check passes (no issue found), DO NOT include it in the response at all.
3. DO NOT add issues with descriptions like "this doesn't apply" or "no issue found".
4. Severity 1-5 is ONLY for real issues. Don't use low severity to mean "doesn't apply".
5. Empty issues array is perfectly valid when no issues exist.
6. Consider the component TYPE when evaluating values.
   Examples:
   - For "number" type: Consider if the numeric value makes sense in context
   - For "string" type: Consider if the text value aligns with the node's purpose
   - For "boolean" type: Consider if true/false makes sense for this node

For each ACTUAL issue found:
- Provide a clear title
- Explain what's wrong and why it's a problem
- Rate severity (1=minor inconsistency, 5=major contradiction)
- Use the correct issue_type from the list above
- Identify which components are involved (if any) in related_components

Provide an overall_coherence_score from 1 (completely incoherent) to 5
(perfectly coherent).
Write a brief summary describing the node's coherence state.

Answer as if you were advising a game designer directly.
"""

ImproveNodeWithExplanationPrompt = """
Improve the following Game Design Node and explain your improvements.

VALIDATION ISSUES DETECTED (YOU MUST ADDRESS ALL OF THESE):
%s

CURRENT NODE:
Name: %s
Description: %s

COMPONENTS:
%s

CRITICAL INSTRUCTIONS:
1. You MUST address ALL validation issues listed above. The validation system
   has already determined these issues exist, so you must fix them all.
2. Do NOT skip any issues. Do NOT decide that an issue "doesn't apply".

3. FOR TEXT-RELATED ISSUES (name/description problems):
   - Make changes to the "changes" array
   - Each change should specify field ("name" or "description")
   - Explain WHY it improves the node
   - List which validation issues this change fixes in "issues_addressed"

4. FOR COMPONENT-RELATED ISSUES (value contradictions, conflicts):
   - Add entries to the "component_changes" array
   - Include the component_id from the list above
   - Specify the component_name (definition name)
   - Show current_value and suggested_value
   - Explain WHY this value change improves coherence
   - List which validation issues this change fixes in "issues_addressed"

5. Use the EXACT issue titles from the validation issues list above in
   "issues_addressed" and "validation_issues_fixed" arrays.

6. Every issue in "validation_issues_fixed" MUST appear in at least one
   change's or component_change's "issues_addressed" array.

RULES FOR GOOD NODES:
- Name should clearly identify what the node represents
- Description should explain purpose and expected behavior
- Component values should align with the node's stated purpose
- All components should be relevant to this type of node

RESPOND WITH THIS JSON STRUCTURE:
{
  "name": "Improved node name",
  "description": "Improved node description",
  "changes": [
    {
      "field": "name" or "description",
      "after": "The new value",
      "reasoning": "Why this is better",
      "issues_addressed": ["Issue Title 1", "Issue Title 2"]
    }
  ],
  "component_changes": [
    {
      "component_id": "uuid-from-components-list",
      "component_name": "intensity",
      "current_value": 100,
      "suggested_value": 20,
      "reasoning": "A relaxing scene should have low intensity",
      "issues_addressed": ["Component Value Contradiction"]
    }
  ],
  "overall_summary": "Summary of why improved node is better",
  "validation_issues_fixed": ["All issue titles that were fixed"]
}

IMPORTANT: If the issue is about component values, you MUST include a
component_change entry. Don't just describe the problem - provide the fix.
"""
