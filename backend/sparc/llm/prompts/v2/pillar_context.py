"""
Pillar Context agent prompts for SPARC V2.

Determines which pillars are relevant to which SPARC aspects.
"""

PILLAR_ASSIGNMENT_PROMPT = """You are analyzing design pillars to determine \
which are relevant to specific game design aspects in a SPARC evaluation.

## DESIGN PILLARS

{pillars_text}

## SPARC ASPECTS

The 10 SPARC aspects are:
1. **player_experience** - Emotional player experience and engagement
2. **theme** - Thematic elements, setting, tone, atmosphere
3. **purpose** - Project purpose, target audience, design goals
4. **gameplay** - Core mechanics, systems, player interactions
5. **goals_challenges_rewards** - Objectives, progression, reward structures
6. **place** - Game world, environment, spatial design
7. **story_narrative** - Story, narrative structure, characters
8. **unique_features** - Unique selling points, differentiators
9. **art_direction** - Visual style, aesthetics, art approach
10. **opportunities_risks** - Market opportunities, development risks

## YOUR TASK

For each SPARC aspect, identify which pillars (if any) are relevant.

A pillar is relevant to an aspect if:
- The pillar's design principles directly inform that aspect
- The pillar sets constraints or guidelines for that aspect
- The aspect evaluation should check alignment with that pillar

**IMPORTANT:**
- A pillar can be relevant to multiple aspects
- An aspect can have multiple relevant pillars
- Some aspects might have no relevant pillars (empty list)
- Use only the pillar IDs from the list above

## RESPONSE FORMAT

Return a JSON object with a "filtered_assignments" key containing a
mapping of aspect names to lists of relevant pillar IDs.

Example:
```json
{{
  "filtered_assignments": {{
    "player_experience": [1, 3],
    "theme": [2],
    "gameplay": [1, 4],
    "art_direction": [2, 5],
    "story_narrative": [],
    "purpose": [1],
    "goals_challenges_rewards": [3, 4],
    "place": [2],
    "unique_features": [],
    "opportunities_risks": [1, 5]
  }}
}}
```

Include all 10 aspects in your response, even if the list is empty.
"""
