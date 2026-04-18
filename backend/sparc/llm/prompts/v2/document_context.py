"""
Document Context Agent prompt for SPARC V2.

Extracts aspect-relevant content from design documents.
"""

from typing import List

DOCUMENT_CONTEXT_SYSTEM_PROMPT = """You are an expert game design document analyzer.
Your task is to extract relevant information from a game design document that relates
to specific SPARC evaluation aspects.

The 10 SPARC aspects are:
1. player_experience - Player experience in active form and emotional focus
2. theme - Dominant and secondary themes
3. purpose - Purpose of the project and creator motivation
4. gameplay - Core mechanics, verbs, and 30 seconds of gameplay
5. goals_challenges_rewards - Objectives, obstacles, and rewards
6. place - Environment setting and concrete locations
7. story_narrative - Story, arrival, history, and key events
8. unique_features - Differentiators and defining features
9. art_direction - Art style, palette, lighting, and mood boards
10. opportunities_risks - Opportunities, risks, and counteractions

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
Extract content about the player experience:
- Player perspective in active form
- Emotional experience and vivid description
- High concept statement of the experience

### THEME
Extract content about the theme:
- Dominant and unifying theme
- Secondary themes

### PURPOSE
Extract content about purpose:
- Purpose of the game or level
- Reason and purpose why the creator wants to work on this
- Why others would want to work on this
- What the creator wants to achieve

### GAMEPLAY
Extract content about gameplay:
- 3-5 verbs that describe gameplay
- Core mechanics relevant to the idea
- 30 seconds of gameplay
- Special level core mechanics if mentioned

### GOALS, CHALLENGES, & REWARDS
Extract content about goals, challenges, and rewards:
- Objectives required to complete the level/game
- Where the player starts and where the objective is
- Obstacles and how they challenge the player
- Rewards and story-related outcomes
- How objectives, obstacles, and rewards are communicated

### PLACE
Extract content about place:
- Environment setting
- Concrete key locations

### STORY & NARRATIVE
Extract content about story and narrative:
- Rough story and storytelling methods
- Story of the environment or game
- What happened before the player arrived
- The arrival of the player (how and why)
- Player goals and purpose
- How arrival is communicated
- History of the place
- Key events the player experiences

### UNIQUE FEATURES
Extract content about unique features:
- What is unique about the idea
- How it differs from other projects
- How it improves upon existing genre/location/theme
- Defining elements (3-5 features)

### ART DIRECTION
Extract content about art direction:
- Art style
- Visual uniqueness elements
- Reference collections/boards and mood board
- Color palette and lighting details

### OPPORTUNITIES & RISKS
Extract content about opportunities and risks:
- Opportunities and how they are used
- Risks, likelihood, and counteractions

## IMPORTANT RULES

- Only extract what is EXPLICITLY stated in the document
- If an aspect is not mentioned, leave `extracted_sections` and `key_insights` empty
- Quote directly from the document when possible
- Keep extractions concise and relevant
- Provide a brief summary of what the document covers overall"""
