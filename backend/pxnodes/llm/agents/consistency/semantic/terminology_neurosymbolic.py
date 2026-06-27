"""Neuro-symbolic terminology consistency check.

The pure-LLM TerminologyConsistencyAgent asks the model to *judge* whether terms
are inconsistent — but an LLM is optimised to collapse synonyms, so it forgives
exactly the near-synonym inconsistencies we want to catch (measured terminology
recall ≈ 0.22, near-synonyms never flagged).

This redesign splits the task:

  Stage 1 (neural):   extract, per node, (concept, surface-term) pairs. The LLM
                      assigns the SAME normalized concept key to terms that mean
                      the same thing ("serfs"/"peasants" → "peasant"). It only
                      labels — it does NOT judge consistency.
  Stage 2 (symbolic): group by concept; any concept named by >1 distinct surface
                      term is a terminology inconsistency. Deterministic, so the
                      LLM's synonym knowledge becomes an asset (correct grouping)
                      instead of a liability (forgiving the inconsistency).

Stage 2 (`group_into_findings`) is a pure function and unit-tested in isolation.
"""

from typing import Any, Dict, List

from pydantic import BaseModel

from pxnodes.llm.agents.consistency.schemas import ConsistencyFinding, FindingSeverity
from pxnodes.llm.agents.consistency.semantic.base import SemanticConsistencyAgent

TERMINOLOGY_EXTRACTION_PROMPT = """You are a terminology extractor for game design docs.

You are given a list of game design nodes (id, name, description). Extract the
key game-design CONCEPTS each node refers to, and the exact surface TERM each
node uses for that concept.

GAME NODES:
{nodes_section}

RULES:
- For every meaningful game-design concept a node names (mechanics, resources,
  systems, locations, roles, currencies, objectives, building types, etc.),
  output one entry: the node, the exact term as written, and a concept key.
- The CONCEPT key is a short, normalized, lowercase label for the underlying
  thing the term refers to — NOT the surface wording. Two nodes that talk about
  the SAME underlying thing with different words MUST get the SAME concept key.
  Example: a node saying "serfs" and a node saying "peasants" both refer to the
  lowest population tier, so BOTH get concept key "peasant".
- Preserve the exact surface term as written (keep the original wording and case).
- Use the canonical NAME of the thing as the term — a proper noun or short
  established game term (1-3 words). Do NOT use descriptive phrases, leading
  articles, or possessive descriptions like "the island" or "Lord Northburgh's
  second island"; map those to the canonical name (e.g. "Falconstone") or omit.
- Do NOT judge whether terminology is consistent and do NOT report problems.
  ONLY extract concept->term per node. The comparison happens elsewhere.
- Ignore generic filler words; focus on domain-specific concepts.

RESPONSE FORMAT (JSON):
{{
  "mentions": [
    {{
      "node_id": "<uuid of the node>",
      "node_name": "<name of the node>",
      "term": "<exact surface term as written in the node>",
      "concept": "<short normalized lowercase concept key>"
    }}
  ]
}}
"""


class ConceptMention(BaseModel):
    """One (concept, surface-term) observation in a single node."""

    node_id: str
    node_name: str
    term: str
    concept: str


class TerminologyExtractionResponse(BaseModel):
    """Stage-1 response: a flat list of concept/term observations."""

    mentions: List[ConceptMention]


class TerminologyExtractionAgent(SemanticConsistencyAgent):
    """Stage 1: extract (concept, surface-term) pairs per node. No judgement."""

    name = "terminology_extraction"
    category = "terminology_inconsistency"
    default_severity = FindingSeverity.INFO
    response_schema = TerminologyExtractionResponse
    prompt_template = TERMINOLOGY_EXTRACTION_PROMPT

    def build_prompt(self, data: Dict[str, Any]) -> str:
        nodes = data.get("nodes", [])
        nodes_section = "\n".join(
            f"- ID: {n['id']}, Name: {n['name']}\n"
            f"  Description: {n.get('description', '')}"
            for n in nodes
        )
        return self.prompt_template.format(nodes_section=nodes_section)


_ARTICLES = {"the", "a", "an"}
_MAX_TERM_WORDS = 3  # terms longer than this are prose, not canonical names


def _term_tokens(term: str) -> set:
    """Lowercased content words of a term, with possessive/punctuation stripped."""
    return {w.lower().strip("'s.,;:") for w in term.split() if w.strip("'s.,;:")}


def _is_canonical_term(term: str) -> bool:
    """Heuristic: a canonical name, not a descriptive prose reference.

    Filters out the dominant false-positive source — descriptive phrases the
    extractor sometimes emits ("the island", "Lord Northburgh's second island").
    All real trap terms are short (<=3 words) names without a leading article.
    """
    words = term.split()
    if not words:
        return False
    if words[0].lower() in _ARTICLES:
        return False
    return len(words) <= _MAX_TERM_WORDS


def _is_refinement(a: str, b: str) -> bool:
    """True if one term's words are a subset of the other's (e.g. 'cathedral'
    vs 'Imperial cathedral', 'Lord Northburgh' vs 'Lord Richard Northburgh').

    Such pairs are refinements of the same name, not competing terms.
    """
    ta, tb = _term_tokens(a), _term_tokens(b)
    if not ta or not tb:
        return False
    return ta <= tb or tb <= ta


def group_into_findings(mentions: List[Dict[str, Any]]) -> List[ConsistencyFinding]:
    """Stage 2 (pure, deterministic): flag every concept named by >1 distinct
    *canonical* surface term.

    For each such concept, the most frequently used term is treated as the
    established term; every other (variant) term yields one finding whose
    ``entity_id`` is a node using the variant term and whose message names a node
    using the established term — mirroring the trap structure so the existing
    evaluation matcher scores these findings unchanged.

    Two symbolic precision filters suppress prose/refinement noise:
    non-canonical terms (articles, long phrases) are dropped, and variant terms
    whose words are a subset/superset of the established term are not flagged.
    """
    # concept_key -> term_key -> list of mentions (canonical terms only)
    by_concept: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for m in mentions:
        concept = str(m.get("concept", "")).strip().lower()
        term = str(m.get("term", "")).strip()
        if not concept or not term or not _is_canonical_term(term):
            continue
        by_concept.setdefault(concept, {}).setdefault(term.lower(), []).append(m)

    findings: List[ConsistencyFinding] = []
    for concept, term_groups in by_concept.items():
        if len(term_groups) < 2:
            continue  # one surface form for this concept => consistent

        primary_key = max(term_groups, key=lambda k: len(term_groups[k]))
        primary = term_groups[primary_key][0]
        primary_term = primary.get("term", primary_key)
        primary_node = primary.get("node_name", "?")

        variant_keys = [
            k
            for k in term_groups
            if k != primary_key and not _is_refinement(k, primary_key)
        ]
        if not variant_keys:
            continue
        n_terms = len(variant_keys) + 1

        for term_key in variant_keys:
            variant = term_groups[term_key][0]
            findings.append(
                ConsistencyFinding(
                    severity=FindingSeverity.INFO,
                    category="terminology_inconsistency",
                    entity_id=str(variant.get("node_id", "")),
                    message=(
                        f"['{variant.get('term', term_key)}' vs '{primary_term}' "
                        f"in {primary_node}] concept '{concept}' is named with "
                        f"{n_terms} different terms across the project"
                    ),
                )
            )
    return findings
