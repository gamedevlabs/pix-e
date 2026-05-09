"""
Prompts for Structural Memory Context extraction.

Based on prompts from Zeng et al. (2024) "On the Structural Memory of LLM Agents".
"""

from typing import Any

# Prompt for extracting atomic facts from node descriptions AND components
ATOMIC_FACT_EXTRACTION_PROMPT = (
    "You are an intelligent assistant tasked with meticulously extracting "
    "both key elements and atomic facts from a game design node.\n\n"
    "1. Key Elements: The essential nouns (e.g., characters, items, enemies, "
    "locations, abilities), verbs (e.g., actions, events), and adjectives "
    "(e.g., states, feelings) that are pivotal to the game design.\n\n"
    "2. Atomic Fact: The smallest, indivisible facts, presented as concise "
    "sentences. These include game mechanics, items granted, abilities required, "
    "events that occur, and implicit elements like causality, sequences, "
    "and relationships.\n\n"
    "Requirements:\n"
    "1. Ensure that all atomic facts contain full and complete information, "
    "reflecting the entire context without omitting any key details.\n"
    "2. Ensure that all identified key elements are reflected within the "
    "corresponding atomic facts.\n"
    "3. Include facts about the node's components (intensity, category, etc.) "
    "and how they relate to the narrative.\n"
    "4. Focus on extractable game design information: items, abilities, "
    "enemies, events, prerequisites, rewards, pacing, intensity.\n\n"
    "Format your output as a numbered list of atomic facts, one per line.\n\n"
    "Example:\n"
    "Title: Ambush\n"
    "Description: The player is attacked by 3 enemies and finds the "
    "Double Jump boots hidden in a chest.\n"
    "Components:\n"
    "- intensity (number): 85\n"
    "- gameplay_category (string): Combat\n\n"
    "Atomic Facts:\n"
    "1. The player is attacked by 3 enemies.\n"
    "2. The player finds Double Jump boots.\n"
    "3. The Double Jump boots are hidden in a chest.\n"
    "4. This node involves combat with enemies.\n"
    "5. This node grants the player a new ability item.\n"
    "6. This node has high intensity (85).\n"
    "7. This node is categorized as Combat.\n"
    "8. The high intensity matches the combat encounter.\n\n"
    "---\n\n"
    "Now extract atomic facts from this game design node:\n\n"
    "Title: {title}\n"
    "Description: {description}\n"
    "Components:\n{components}\n\n"
    "Atomic Facts:"
)


# LLM-based knowledge triple extraction prompt from Zeng et al. (2024)
# Used to extract relationship triples from narrative text
KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT = (
    "You are a knowledge graph constructor tasked with extracting knowledge "
    "triples in the form of <head entity; relation; tail entity> from a "
    "game design node. Each triple denotes a specific relationship between "
    "entities or an event. The head entity and tail entity can be the "
    "provided title or phrases in the text. If multiple tail entities share "
    "the same relation with a head entity, aggregate these tail entities "
    "using commas.\n"
    "Format your output in the form of <head entity; relation; tail entity>.\n\n"
    "Demonstrations:\n"
    "Title: Ambush\n"
    "Text: The player is attacked by 3 enemies and finds the Double Jump "
    "boots hidden in a chest. This is a high-intensity combat encounter.\n"
    "Components:\n"
    "- intensity: 85\n"
    "- gameplay_category: Combat\n\n"
    "Knowledge Triples:\n"
    "<Ambush; involves; 3 enemies>\n"
    "<Ambush; grants item; Double Jump boots>\n"
    "<Double Jump boots; found in; chest>\n"
    "<Ambush; type; combat encounter>\n"
    "<Ambush; intensity level; 85>\n"
    "<Ambush; category; Combat>\n\n"
    "# Please strictly follow the above format. Let's begin.\n\n"
    "Title: {title}\n"
    "Text: {description}\n"
    "Components:\n{components}\n\n"
    "Knowledge Triples:"
)


# Template for the mixed structural context output
MIXED_CONTEXT_TEMPLATE = (
    "TASK: Evaluate the coherence of {target_node_name} "
    "based on the following Mixed Structural Memory:\n\n"
    "[CONTEXT: PREVIOUS NODE(S)]\n"
    "{previous_context}\n\n"
    "[TARGET: {target_node_name} ANALYSIS]\n"
    "{target_context}\n\n"
    "[CONTEXT: NEXT NODE(S)]\n"
    "{next_context}\n\n"
    "[LOGIC CHECKS]\n"
    "{logic_checks}"
)


# Template for individual triple formatting
TRIPLE_FORMAT = "- Triple: ({head}, {relation}, {tail})"

# Template for individual fact formatting
FACT_FORMAT = "- Fact: {fact}"


def format_components_for_prompt(components: list[dict[str, Any]]) -> str:
    """Format component list for inclusion in prompts."""
    if not components:
        return "- No components attached"

    lines = []
    for comp in components:
        name = comp.get("definition_name", comp.get("name", "unknown"))
        comp_type = comp.get("definition_type", comp.get("type", ""))
        value = comp.get("value", "N/A")
        if comp_type:
            lines.append(f"- {name} ({comp_type}): {value}")
        else:
            lines.append(f"- {name}: {value}")

    return "\n".join(lines)


def format_triple(head: str, relation: str, tail: Any) -> str:
    """Format a knowledge triple as a string."""
    if isinstance(tail, bool):
        tail_str = str(tail).lower()
    elif isinstance(tail, (int, float)):
        tail_str = str(tail)
    else:
        tail_str = f'"{tail}"' if isinstance(tail, str) else str(tail)

    return TRIPLE_FORMAT.format(head=head, relation=relation, tail=tail_str)


def format_fact(fact: str) -> str:
    """Format an atomic fact as a string."""
    return FACT_FORMAT.format(fact=fact)
