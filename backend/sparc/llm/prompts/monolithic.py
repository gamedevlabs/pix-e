"""
Monolithic SPARC prompt.

Contains the original single-shot baseline prompt for comparison with agentic approach.
This is the "old way" - one big prompt trying to cover everything at once.
"""

MONOLITHIC_SPARC_PROMPT = """You are an expert game development consultant. Evaluate a game text as the foundation for a game development project.  # noqa: E501
Use the game design documents (GDDs) provided as context as reference.
Check if the following aspects are present or can be easily inferred from the game idea: player experience, theme, gameplay, place, unique features, story & narrative, goals, challenges & rewards, art direction, purpose, opportunities & risks.  # noqa: E501
Expanded details about the aspects are as follows:

Player Experience:
What do you want the player to experience? Describe it from the perspective of the player with the player in the active form. It can help to close your eyes and visualize what you want the player to experience.  # noqa: E501
It does not have to be final yet. You can come back later and iterate on it, if the process makes your picture of the idea more clear.  # noqa: E501
Create a detailed description of the player experience with the player in the active form focusing on an emotional experience.  # noqa: E501
When you have a clear description of the experience, formulate a clear High Concept Statement for your play idea.  # noqa: E501

Theme:
Define the Theme of your idea.
What is the dominant and unifying theme?
What are secondary themes?

Gameplay:
Describe the core gameplay.
Try to find 3-5 verbs that describe the gameplay experience.
Describe what Core Mechanics are relevant for your idea.
Describe what the player does by formulating a 30 Seconds of Gameplay.
If you have special Level Core Mechanics make this very clear.

Place:
Find a place in the game world where the space under construction can be set.
What is the Environment Setting?
Provide a list of concrete key locations.

Unique Features:
Describe how the idea will be unique by answering the questions:
What does your idea feature that is unique?
How is your idea different to other projects out there?
How does it improve upon existing genre/location/theme?
How is your idea (in the case of a level) different to other parts of your game?
Create a list with 3-5 features that will be the defining elements of your idea.

Story & Narrative:
Come up with a rough story. Think about how the player will experience this story: how does the game or level tell this story? Think about storytelling methods, such as environmental storytelling, gameplay, cutscenes, narrators, dialogues, ...  # noqa: E501
What is the story of the environment or game?
Write a short description of the environment from the perspective of a character that lives here or someone who has been here already (Galuzin, 2016)  # noqa: E501
What happened here before the player arrived?
What will the player experience here?
The arrival of the player.
How?
How did the player arrive in this location? Link documents of other locations here.  # noqa: E501
What were the events that brought the player here?
Why? The player goals
Why is the player traveling to this place?
What is the purpose?
What is the overall goal of the player?
How do you communicate the how and why of the player's arrival to the player?
The history of the place.
What happened in the environment before the player arrived?
How do you want to show the player what has happened in the environment? How to do you want to tell the story of the environment to the player?  # noqa: E501
The story.
How will the player navigate through the environment?
What are the key events the player will experience while traveling through the environment?  # noqa: E501

Goals, Challenges & Rewards:
We want to design the goals, challenges and rewards for the level, often also called "objectives, obstacles and set pieces" (Galuzin, 2016). For this, define the following aspects:  # noqa: E501
For the story goals you have created on why the player is at this place, create a list of objectives that the player has to complete in order to complete this level/game. These objectives will be the goals communicated to the player.  # noqa: E501
For each objective, describe where the player starts and where the objective is. Then, describe the obstacles the player has to overcome to achieve the objective. Describe how these obstacles will challenge the player.  # noqa: E501
For each objective and obstacles set, describe how you will reward the player achieving the objective.  # noqa: E501
If these rewards are story-related, describe how the player action caused the outcome or influenced its outcome.  # noqa: E501
How are you planning to communicate the objectives, obstacles, and rewards to the player?  # noqa: E501

Art Direction:
Describe a general artistic vision:
Pick an Art Style: "What visual art style will your environment be? Will it be Realistic? Exaggerated? Stylized? Cartoonish? Etc." (Galuzin, 2016)  # noqa: E501
Visually Unique: "How will your project be unique visually/stylistically? Make a list of 2-3 things that will make your stand-alone game environment or playable level design be different than most similar environment projects out there." (Galuzin, 2016)  # noqa: E501
Collect first impressions and create Reference Collections, and Reference Boards.
Define the color palette for your project.
What is the primary color? What are the secondary colors?
What is the primary light source? What is the shadow color?
"How much light vs. dark ratio is in your scene? High-contrast? Lots of dark areas? Evenly lit?" (Galuzin, 2016)  # noqa: E501
"Will your game environment use a warm or cool color palette?" (Galuzin, 2016)
Create a Mood Board for your project.

Purpose:
Understand why you want to work on this project. What do you want to achieve? Then, formulate the purpose of the project itself. Document this. Answer the following questions: [2]  # noqa: E501
What is the purpose of the game or level you want to work on? The purpose of this project is...  # noqa: E501
What is the reason and purpose why YOU want to work on this project? The reason I want to create this is...  # noqa: E501
Why would OTHERS want to work on this project?
What do YOU want to achieve with completing this project? With completing this project, I want to achieve...  # noqa: E501

Opportunities & Risks:
What are opportunities of this idea? What are possible risks?
Create a list of opportunities and describe these opportunities and how you are planning to use these opportunities  # noqa: E501
Create a list of risks of your project. How likely are those risks? How can you minimize these risks? What are possible counteractions?  # noqa: E501

GAME TEXT:
%s

The objective is to check whether fields and aspects required to start development of a game have been considered.  # noqa: E501
Add suggestions at the end of evaluation along with 2-5 other details that would make the text better suited to start game development with in addition to including aspects that aren't addressed in the game text.  # noqa: E501
Do not take into account fiscal or managerial requirements. Focus only on factors relevant for early stages of game design.  # noqa: E501
Avoid redundancy and limit your response to 1000 words.
"""
