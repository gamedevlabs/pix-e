"""
Document Context Agent prompt for SPARC V2.

Extracts aspect-relevant content from design documents.
"""

from typing import List

DOCUMENT_CONTEXT_SYSTEM_PROMPT = """You are an expert game design document analyzer.
Your task is to extract relevant information from a game design document that relates
to specific SPARC evaluation aspects.

The 10 SPARC aspects are:
1. player_experience - Emotional journey, feelings players should experience
2. theme - Thematic elements, setting tone, atmosphere
3. purpose - Project goals, target audience, vision
4. gameplay - Core mechanics, systems, player interactions
5. goals_challenges_rewards - Objectives, progression, difficulty
6. place - World, setting, environments, locations
7. story_narrative - Plot, characters, narrative structure
8. unique_features - Unique selling points, innovations
9. art_direction - Visual style, aesthetics, art pipeline
10. opportunities_risks - Market opportunities, risks, constraints

Extract ONLY what is explicitly mentioned in the document. If an aspect is
not covered, leave extracted_sections empty."""


def build_document_context_prompt(target_aspects: List[str]) -> str:
    """
    Build the document context extraction prompt.

    Args:
        target_aspects: List of aspect names to extract for

    Returns:
        Formatted prompt
    """
    aspects_list = ", ".join(target_aspects)

    return f"""Analyze the provided game design document and extract
relevant information for these aspects: {aspects_list}

For each aspect, identify:
- **Extracted Sections**: Direct quotes or sections from the document
  that discuss this aspect
- **Key Insights**: Important design decisions, constraints, or
  intentions mentioned for this aspect

## ASPECT DEFINITIONS

### PLAYER EXPERIENCE
Extract content about what the player will experience emotionally:
- How the game should make players feel
- Emotional keywords (tension, joy, triumph, fear, wonder)
- Target player experience and feelings

### THEME
Extract content about thematic elements:
- The dominant unifying theme
- Secondary themes
- How themes are expressed

### PURPOSE
Extract content about project goals and motivation:
- Purpose of the game/level
- Target audience
- Vision and objectives

### GAMEPLAY
Extract content about mechanics and player actions:
- Core mechanics and systems
- What the player does (core verbs: explore, craft, fight, etc.)
- Moment-to-moment gameplay description

### GOALS, CHALLENGES, & REWARDS
Extract content about objectives and progression:
- Goals and objectives
- Challenge design
- Reward systems and progression

### PLACE
Extract content about world and setting:
- Physical spaces and environments
- World setting and locations
- Atmosphere and mood

### STORY & NARRATIVE
Extract content about narrative elements:
- Plot and story
- Characters
- Narrative structure

### UNIQUE FEATURES
Extract content about innovations:
- Unique selling points
- What makes it different
- Innovative features

### ART DIRECTION
Extract content about visual style:
- Art style and aesthetics
- Visual design direction
- Reference art or inspirations

### OPPORTUNITIES & RISKS
Extract content about market and challenges:
- Market opportunities
- Potential risks
- Technical or design constraints

## IMPORTANT RULES

- Only extract what is EXPLICITLY stated in the document
- If an aspect is not mentioned, leave `extracted_sections` and `key_insights` empty
- Quote directly from the document when possible
- Keep extractions concise and relevant
- Provide a brief summary of what the document covers overall"""
