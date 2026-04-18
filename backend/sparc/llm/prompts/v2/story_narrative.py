"""
Story & Narrative aspect prompt for SPARC V2.
"""

STORY_NARRATIVE_PROMPT = """You are an expert game development consultant
evaluating STORY & NARRATIVE.

## ASPECT-RELEVANT CONTENT

{aspect_text}
{pillar_section}
## ASPECT GUIDE (SPARC)

Come up with a rough story. Think about how the player will experience this
story: how does the game or level tell this story? Think about storytelling
methods, such as environmental storytelling, gameplay, cutscenes, narrators,
dialogues, ...
What is the story of the environment or game?
Write a short description of the environment from the perspective of a
character that lives here or someone who has been here already (Galuzin, 2016)
What happened here before the player arrived?
What will the player experience here?
The arrival of the player.
How?
How did the player arrive in this location? Link documents of other locations
here.
What were the events that brought the player here?
Why? The player goals
Why is the player traveling to this place?
What is the purpose?
What is the overall goal of the player?
How do you communicate the how and why of the player's arrival to the player?
The history of the place.
What happened in the environment before the player arrived?
How do you want to show the player what has happened in the environment? How
to do you want to tell the story of the environment to the player?
The story.
How will the player navigate through the environment?
What are the key events the player will experience while traveling through the
environment?

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

Return JSON with aspect_name: "story_narrative"
"""
