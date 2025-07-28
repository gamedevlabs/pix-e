ValidationPrompt = \
"""Validate the following Game Design Pillar.
Check for structural issues regarding the following points:
1. The name does not match the description.
2. The intent of the pillar is not clear.
3. The pillar focuses on more than one aspect.
4. The description uses bullet points or lists.
Name: %s
Description: %s
For each feedback limit your answer to one sentence.
Answer as if you were talking directly to the designer.
"""

ImprovePillarPrompt = \
"""Improve the following Game Design Pillar.
Check for structural issues regarding the following points:
1. The title does not match the description.
2. The intent of the pillar is not clear.
3. The pillar focuses on more than one aspect.
4. The description uses bullet points or lists.
Pillar Title: %s
Pillar Description: %s
Rewrite erroneous parts of the pillar and return a new pillar object.
"""

# Deprecated Prompt, split into multiple prompts below
PillarsInContextPrompt = \
"""Assume the role of a game design expert.
Evaluate if the following Game Design Idea is sufficiently
covered by the following Design Pillars.
Check if pillars stand in contradiction towards the game idea or are not a 
good fit for the game idea (e.g not central to the game idea).
Also evaluate if the pillars stand in contradiction towards each other.

Game Design Idea: %s

Design Pillars: %s
"""

PillarCompletenessPrompt = \
"""Assume the role of a game design expert.
Evaluate if the following Game Design Idea is sufficiently
covered by the following Game Design Pillars.
Evaluate if the pillar is a good fit for the game idea (e.g. central to the game idea).
Also check if the pillar contradicts the direction of the game idea.

Game Design Idea: %s

Design Pillars: %s
"""

PillarContradictionPrompt = \
"""Assume the role of a game design expert.
Evaluate if the following Game Design Pillars stand in contradiction
towards each other. Use the Game Design Idea as context.

Game Design Idea: %s

Design Pillars: %s
"""

PillarAdditionPrompt = \
"""Assume the role of a game design expert.
Evaluate if the following Game Design Idea is sufficiently
covered by the following Game Design Pillars.

Game Design Idea: %s

Design Pillars: %s
If not, add new pillars to cover the missing aspects.
"""

ContextInPillarsPrompt = \
"""Assume the role of a game design expert.
Evaluate how well the following idea aligns with the given Game Design Pillars.

Idea: %s

Design Pillars: %s
"""
