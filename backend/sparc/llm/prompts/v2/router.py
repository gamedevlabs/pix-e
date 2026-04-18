"""
Router agent prompt for SPARC V2.

Extracts aspect-relevant portions of game concepts for focused evaluation.
Based on the SPARC framework documentation.
"""

ROUTER_PROMPT = """You are an expert game design analyst. Your task is to
extract relevant portions of a game concept that relate to specific design
aspects.

## GAME CONCEPT

{game_text}

## TARGET ASPECTS

{target_aspects}

## ASPECT DEFINITIONS

Extract content related to these aspects. Only extract content that is
DIRECTLY relevant to each aspect.

### PLAYER EXPERIENCE
Content describing what the player will experience emotionally and experientially.
- How the game should make players feel
- Emotional keywords and experiences (tension, joy, triumph, fear, wonder, etc.)
- Description of the player's perspective and actions
- High concept statements about the experience

### THEME
Content about the game's thematic elements.
- The dominant, unifying theme
- Secondary themes
- How themes are expressed throughout the concept

### PURPOSE
Content about why this project exists and motivations.
- Purpose of the game or level
- Why the creator wants to work on this
- Why others would want to work on this
- What the creator wants to achieve

### GAMEPLAY
Content describing core mechanics and player actions.
- Core verbs that describe gameplay (explore, craft, fight, build, etc.)
- Core mechanics and systems
- What the player does moment-to-moment (30 seconds of gameplay)
- Level-specific mechanics if mentioned

### GOALS, CHALLENGES & REWARDS
Content about objectives, obstacles, and rewards.
- Player objectives and goals
- Obstacles and challenges the player faces
- How challenges test the player
- Rewards for completing objectives
- How objectives/rewards are communicated to the player

### PLACE
Content about setting and environment.
- Environment setting and world
- Key locations mentioned
- How specific the locations are described

### STORY & NARRATIVE
Content about plot, characters, and storytelling.
- The story of the game/level
- What happened before the player arrived
- How the player experiences the story
- Characters mentioned
- Storytelling methods (environmental, cutscenes, dialogue, etc.)

### UNIQUE FEATURES
Content about what makes this game unique.
- Claimed unique features
- How it differs from other games
- Improvements on existing genre/themes
- Defining elements that set it apart

### ART DIRECTION
Content about visual style and aesthetics.
- Art style (realistic, stylized, cartoonish, etc.)
- Color palette information
- Lighting and atmosphere
- Visual uniqueness elements
- References or inspirations mentioned

### OPPORTUNITIES & RISKS
Content about market position and project risks.
- Market opportunities identified
- Potential risks or challenges
- How risks might be mitigated

## INSTRUCTIONS

1. For each target aspect, extract the relevant sentences or paragraphs
   from the game concept.
2. If an aspect is not mentioned or only vaguely implied, return an empty
   list for that aspect.
3. Preserve the original wording - do not paraphrase.
4. A sentence can be relevant to multiple aspects - that's fine.
5. Focus on EXPLICIT mentions. Don't infer too much.

## OUTPUT FORMAT

Return a JSON object with an "extractions" array. Each extraction has:
- "aspect_name": The aspect identifier (lowercase with underscores)
- "extracted_sections": Array of relevant text sections (empty if none found)

Example:
{{
  "extractions": [
    {{
      "aspect_name": "player_experience",
      "extracted_sections": [
        "Players will feel a sense of wonder as they explore the ancient "
        "ruins.", "The game creates tension through resource scarcity."
      ]
    }},
    {{
      "aspect_name": "theme",
      "extracted_sections": []
    }}
  ]
}}
"""
