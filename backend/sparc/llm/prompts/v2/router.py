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
Content about the player experience definition.
- What the player experiences, from the player's perspective in active form
- Emotional experience and vivid, visualizable description
- High concept statement describing the experience

### THEME
Content about the game's theme.
- Dominant and unifying theme
- Secondary themes

### PURPOSE
Content about why this project exists.
- Purpose of the game or level
- Reason and purpose why the creator wants to work on this
- Why others would want to work on this
- What the creator wants to achieve

### GAMEPLAY
Content describing core gameplay.
- 3-5 verbs that describe gameplay experience
- Core mechanics relevant to the idea
- 30 seconds of gameplay (moment-to-moment actions)
- Special level core mechanics if mentioned

### GOALS, CHALLENGES & REWARDS
Content about objectives, obstacles, and rewards.
- Objectives required to complete the level/game
- Where the player starts and where the objective is
- Obstacles and how they challenge the player
- Rewards for achieving objectives and story-related outcomes
- How objectives, obstacles, and rewards are communicated to the player

### PLACE
Content about the place/setting.
- Environment setting
- Concrete key locations

### STORY & NARRATIVE
Content about story and narrative.
- Rough story and how the player experiences it
- Story of the environment or game
- What happened before the player arrived
- The arrival of the player (how and why)
- Player goals and purpose
- How the arrival is communicated to the player
- History of the place
- How the story of the environment is told
- Key events the player experiences while traveling
- Storytelling methods (environmental, gameplay, cutscenes, narrators, dialogues)

### UNIQUE FEATURES
Content about unique features.
- What is unique about the idea
- How it differs from other projects
- How it improves upon existing genre/location/theme
- Defining elements (3-5 features)

### ART DIRECTION
Content about artistic vision.
- Art style (realistic, stylized, cartoonish, etc.)
- Visual uniqueness elements
- Reference collections/boards and mood board
- Color palette: primary/secondary, light source, shadow color
- Light vs. dark ratio and warm/cool palette

### OPPORTUNITIES & RISKS
Content about opportunities and risks.
- Opportunities and how to use them
- Risks, likelihood, and counteractions

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
