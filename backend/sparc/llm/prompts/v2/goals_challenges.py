"""
Goals, Challenges & Rewards aspect prompt for SPARC V2.
"""

GOALS_CHALLENGES_REWARDS_PROMPT = """You are a game design expert evaluating
GOALS, CHALLENGES & REWARDS.

## ASPECT-RELEVANT CONTENT

{context_section}
## EVALUATION CRITERIA

A well-defined goals/challenges/rewards structure should:
1. List clear OBJECTIVES the player must complete
2. Define OBSTACLES/CHALLENGES for each objective
3. Describe how challenges TEST the player
4. Explain REWARDS for achieving objectives
5. Consider how objectives and rewards are COMMUNICATED to the player

## ASSESSMENT

Evaluate the content above:
- "well_defined": Clear objectives, meaningful challenges, appropriate
  rewards, communication considered
- "needs_work": Vague goals, missing challenges, unclear rewards, or no
  communication plan

## RESPONSE

Provide:
1. status: "well_defined" or "needs_work"
2. reasoning: 2-3 sentences explaining your assessment
3. suggestions: Concrete improvements (include even if well_defined)

Return JSON with aspect_name: "goals_challenges_rewards"
"""
