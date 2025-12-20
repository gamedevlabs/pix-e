"""
Prompts for SPARC structural memory extraction and retrieval.
"""

ATOMICS_PROMPT = """You are extracting atomic facts from a game concept.

Return the smallest, indivisible facts that are explicitly stated.
Rules:
- Each fact must be a short sentence.
- No numbering or bullet symbols.
- Do not invent information.

Game concept:
{game_text}

Atomic facts:"""

TRIPLES_PROMPT = """Extract knowledge triples from the game concept.

Rules:
- Format each triple as: (Head, Relation, Tail)
- One triple per line.
- Use concise relation phrases.
- Do not invent information.

Game concept:
{game_text}

Triples:"""

SUMMARY_PROMPT = """Provide a concise summary of the game concept.

Rules:
- 3 to 5 sentences.
- Capture core gameplay, goals, setting, and unique features.
- Do not invent information.

Game concept:
{game_text}

Summary:"""

REFINE_QUERY_PROMPT = """Refine the retrieval query for a SPARC aspect.

Aspect: {aspect_name}
Aspect focus: {aspect_description}
Current query: {query}

Relevant memory snippets:
{snippets}

Return a single, more specific query line that will retrieve the most relevant
information for this aspect. Do not include extra text."""
