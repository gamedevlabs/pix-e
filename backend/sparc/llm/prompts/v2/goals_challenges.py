"""
Goals, Challenges & Rewards aspect prompt for SPARC V2.
"""

GOALS_CHALLENGES_REWARDS_PROMPT = """You are an expert game development
consultant evaluating GOALS, CHALLENGES & REWARDS.

## ASPECT-RELEVANT CONTENT

{aspect_text}
{pillar_section}
## ASPECT GUIDE (SPARC)

We want to design the goals, challenges and rewards for the level, often also
called "objectives, obstacles and set pieces" (Galuzin, 2016). For this, define
the following aspects:
For the story goals you have created on why the player is at this place, create
a list of objectives that the player has to complete in order to complete this
level/game. These objectives will be the goals communicated to the player.
For each objective, describe where the player starts and where the objective is.
Then, describe the obstacles the player has to overcome to achieve the
objective. Describe how these obstacles will challenge the player.
For each objective and obstacles set, describe how you will reward the player
achieving the objective.
If these rewards are story-related, describe how the player action caused the
outcome or influenced its outcome.
How are you planning to communicate the objectives, obstacles, and rewards to
the player?

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

Return JSON with aspect_name: "goals_challenges_rewards"
"""
