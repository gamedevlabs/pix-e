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

OverallFeedbackPrompt = \
"""Assume the role of a game design expert.
Evaluate if the following Game Design Pillars fit the
following Game Design Description.
Game Design Description: %s

Pillars: %s
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

PillarInContextPrompt = \
"""Assume the role of a game design expert.
Evaluate if the following Game Design Idea is sufficiently
covered by the following Design Pillars.
Check if pillars stand in contradiction towards the game idea or are not a 
good fit for the game idea (e.g not central to the game idea).
Also evaluate if the pillars stand in contradiction towards each other.

Game Design Idea: %s

Design Pillars: %s

"""

