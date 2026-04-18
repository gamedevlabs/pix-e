"""
Monolithic RQ1 prompt.

Produces the same structured output as the agentic SPARC V2 pipeline
in a single LLM call: 10 per-aspect evaluations + 1 synthesis.

Guide questions are taken VERBATIM from the V2 individual aspect prompts
(backend/sparc/llm/prompts/v2/*.py). Synthesis criteria match
backend/sparc/llm/prompts/v2/synthesis.py.
"""

MONOLITHIC_RQ1_PROMPT = """You are an expert game development consultant. \
Evaluate the game concept below against the SPARC framework.

## GAME CONCEPT

{game_text}

## TASK

Evaluate the game concept against each of the 10 SPARC aspects listed below. \
For EACH aspect, determine its status and provide reasoning and suggestions. \
Then provide an overall synthesis.

## SPARC ASPECTS AND GUIDE QUESTIONS

### 1. PLAYER EXPERIENCE (player_experience)
What do you want the player to experience? Describe it from the perspective of \
the player with the player in the active form. It can help to close your eyes \
and visualize what you want the player to experience.
It does not have to be final yet. You can come back later and iterate on it, if \
the process makes your picture of the idea more clear.
Create a detailed description of the player experience with the player in the \
active form focusing on an emotional experience.
When you have a clear description of the experience, formulate a clear High \
Concept Statement for your play idea.

### 2. THEME (theme)
Define the Theme of your idea.
What is the dominant and unifying theme?
What are secondary themes?

### 3. PURPOSE (purpose)
Understand why you want to work on this project. What do you want to achieve?
Then, formulate the purpose of the project itself. Document this. Answer the \
following questions: [2]
What is the purpose of the game or level you want to work on? The purpose of \
this project is...
What is the reason and purpose why YOU want to work on this project? The reason \
I want to create this is...
Why would OTHERS want to work on this project?
What do YOU want to achieve with completing this project? With completing this \
project, I want to achieve...

### 4. GAMEPLAY (gameplay)
Describe the core gameplay.
Try to find 3-5 verbs that describe the gameplay experience.
Describe what Core Mechanics are relevant for your idea.
Describe what the player does by formulating a 30 Seconds of Gameplay.
If you have special Level Core Mechanics make this very clear.

### 5. GOALS, CHALLENGES & REWARDS (goals_challenges_rewards)
We want to design the goals, challenges and rewards for the level, often also \
called "objectives, obstacles and set pieces" (Galuzin, 2016). For this, define \
the following aspects:
For the story goals you have created on why the player is at this place, create \
a list of objectives that the player has to complete in order to complete this \
level/game. These objectives will be the goals communicated to the player.
For each objective, describe where the player starts and where the objective is. \
Then, describe the obstacles the player has to overcome to achieve the \
objective. Describe how these obstacles will challenge the player.
For each objective and obstacles set, describe how you will reward the player \
achieving the objective.
If these rewards are story-related, describe how the player action caused the \
outcome or influenced its outcome.
How are you planning to communicate the objectives, obstacles, and rewards to \
the player?

### 6. PLACE (place)
Find a place in the game world where the space under construction can be set.
What is the Environment Setting?
Provide a list of concrete key locations.

### 7. STORY & NARRATIVE (story_narrative)
Come up with a rough story. Think about how the player will experience this \
story: how does the game or level tell this story? Think about storytelling \
methods, such as environmental storytelling, gameplay, cutscenes, narrators, \
dialogues, ...
What is the story of the environment or game?
Write a short description of the environment from the perspective of a \
character that lives here or someone who has been here already (Galuzin, 2016)
What happened here before the player arrived?
What will the player experience here?
The arrival of the player.
How?
How did the player arrive in this location? Link documents of other locations \
here.
What were the events that brought the player here?
Why? The player goals
Why is the player traveling to this place?
What is the purpose?
What is the overall goal of the player?
How do you communicate the how and why of the player's arrival to the player?
The history of the place.
What happened in the environment before the player arrived?
How do you want to show the player what has happened in the environment? How \
to do you want to tell the story of the environment to the player?
The story.
How will the player navigate through the environment?
What are the key events the player will experience while traveling through the \
environment?

### 8. UNIQUE FEATURES (unique_features)
Describe how the idea will be unique by answering the questions:
What does your idea feature that is unique?
How is your idea different to other projects out there?
How does it improve upon existing genre/location/theme?
How is your idea (in the case of a level) different to other parts of your game?
Create a list with 3-5 features that will be the defining elements of your idea.

### 9. ART DIRECTION (art_direction)
Describe a general artistic vision:
Pick an Art Style: "What visual art style will your environment be? Will it be \
Realistic? Exaggerated? Stylized? Cartoonish? Etc." (Galuzin, 2016)
Visually Unique: "How will your project be unique visually/stylistically? Make \
a list of 2-3 things that will make your stand-alone game environment or \
playable level design be different than most similar environment projects out \
there." (Galuzin, 2016)
Collect first impressions and create Reference Collections, and Reference \
Boards.
Define the color palette for your project.
What is the primary color? What are the secondary colors?
What is the primary light source? What is the shadow color?
"How much light vs. dark ratio is in your scene? High-contrast? Lots of dark \
areas? Evenly lit?" (Galuzin, 2016)
"Will your game environment use a warm or cool color palette?" (Galuzin, 2016)
Create a Mood Board for your project.

### 10. OPPORTUNITIES & RISKS (opportunities_risks)
What are opportunities of this idea? What are possible risks?
Create a list of opportunities and describe these opportunities and how you are \
planning to use these opportunities
Create a list of risks of your project. How likely are those risks? How can you \
minimize these risks? What are possible counteractions?

## ASSESSMENT CRITERIA PER ASPECT

For each aspect, assign exactly one status:
- "well_defined": The guide questions are answered clearly and specifically.
- "needs_work": The guide questions are partially answered or vague.
- "not_provided": The aspect is missing or cannot be inferred from the game concept.

## SYNTHESIS CRITERIA

After evaluating all 10 aspects, provide an overall synthesis.

**Overall Status:**
- "ready": All key aspects are well_defined, no critical gaps
- "nearly_ready": Most aspects defined, minor gaps remain (1-2 needs_work)
- "needs_work": Significant gaps (3+ needs_work or any not_provided in core aspects)

**Core Aspects** (critical for prototyping):
- player_experience
- gameplay
- goals_challenges_rewards

**Rules:**
- strongest_aspects: Up to 3 aspects with "well_defined" status (list of aspect names)
- weakest_aspects: ONLY aspects with "needs_work" or "not_provided" status. \
Do not include well-defined aspects just because they are relatively weaker.
- critical_gaps: Must be a subset of weakest_aspects. Only aspects with \
"not_provided" status or critical "needs_work" that block prototyping.
- If overall_status is "ready", weakest_aspects and critical_gaps must be empty lists.
- next_steps: 3-5 prioritized actions to improve the concept
- consistency_notes: Cross-aspect inconsistencies or synergies (null if none)

## CONSTRAINTS

- Do not take into account fiscal or managerial requirements.
- Focus only on factors relevant for early stages of game design.
- Do not include marketing, business, or managerial advice.
- Use ONLY these aspect names (snake_case): player_experience, theme, purpose, \
gameplay, goals_challenges_rewards, place, story_narrative, unique_features, \
art_direction, opportunities_risks.

## RESPONSE FORMAT

Return a single JSON object with this exact structure:

{{
  "aspect_results": {{
    "player_experience": {{
      "aspect_name": "player_experience",
      "status": "well_defined" | "needs_work" | "not_provided",
      "reasoning": "2-3 sentences explaining your assessment",
      "suggestions": ["suggestion 1", "suggestion 2"]
    }},
    "theme": {{ ... }},
    "purpose": {{ ... }},
    "gameplay": {{ ... }},
    "goals_challenges_rewards": {{ ... }},
    "place": {{ ... }},
    "story_narrative": {{ ... }},
    "unique_features": {{ ... }},
    "art_direction": {{ ... }},
    "opportunities_risks": {{ ... }}
  }},
  "synthesis": {{
    "overall_status": "ready" | "nearly_ready" | "needs_work",
    "overall_reasoning": "2-3 sentence summary",
    "strongest_aspects": ["aspect_name", "...up to 3"],
    "weakest_aspects": ["aspect_name", "...only needs_work or not_provided"],
    "critical_gaps": ["aspect_name", "...blockers for prototyping"],
    "next_steps": ["action", "...3-5 items"],
    "consistency_notes": "cross-aspect inconsistencies or synergies, or null"
  }}
}}

Return ALL 10 aspects. Return valid JSON only.
"""
