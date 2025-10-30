"""
Test script for SPARC quick scan graph.

Validates that the graph can run all agents in parallel and aggregate results.
"""

import asyncio

from llm.config import Config
from llm.providers.manager import ModelManager
from llm.types import LLMRequest
from sparc.llm.graphs import SPARCQuickScanGraph


async def test_quick_scan_graph():
    """Test the SPARC quick scan graph execution."""
    print("=" * 60)
    print("SPARC Quick Scan Graph Test")
    print("=" * 60 + "\n")

    # Sample game text for testing
    sample_game_text = """
    A dark souls-like game set in a post-apocalyptic sci-fi world.
    Players take on the role of a lone warrior navigating through
    abandoned space stations filled with hostile AI and mutated creatures.
    The game features challenging combat, environmental storytelling,
    and a mysterious narrative about the fall of humanity's space colonies.
    """

    # Create request
    request = LLMRequest(
        feature="sparc",
        operation="quick_scan",
        data={"game_text": sample_game_text.strip()},
        model_id="gpt-4o-mini",  # Using OpenAI for testing
    )

    # Initialize graph
    config = Config()
    model_manager = ModelManager(config)
    graph = SPARCQuickScanGraph(model_manager, config)

    print("Testing graph components...\n")

    # Test 1: Build agents
    print("1. Testing build_agents()...")
    agents = graph.build_agents(request)
    assert len(agents) == 10, f"Expected 10 agents, got {len(agents)}"
    print(f"   ✅ Built {len(agents)} agents")

    agent_names = [agent.name for agent in agents]
    print(f"   Agents: {', '.join(agent_names)}\n")

    # Test 2: Run graph (full execution)
    print("2. Testing full graph execution...")
    print("   Running all 10 agents in parallel...")

    result = await graph.run(request)

    if not result.success:
        print("   ❌ Graph execution failed")
        if result.errors:
            for error in result.errors:
                print(f"      Error: {error.message}")
        return

    print("   ✅ Graph executed successfully")
    print(f"   Execution time: {result.total_execution_time_ms}ms")
    print(f"   Agent results: {len(result.agent_results)}\n")

    # Test 3: Check aggregated results
    print("3. Testing aggregated results...")

    aggregated = result.aggregated_data
    assert "readiness_score" in aggregated, "Missing readiness_score"
    assert "readiness_status" in aggregated, "Missing readiness_status"
    assert "aspect_scores" in aggregated, "Missing aspect_scores"

    print(f"   ✅ Readiness Score: {aggregated['readiness_score']}/100")
    print(f"   ✅ Status: {aggregated['readiness_status']}")
    print(f"   ✅ Aspect Scores: {len(aggregated['aspect_scores'])} aspects")

    # Print aspect scores
    print("\n   Aspect Breakdown:")
    for aspect_score in aggregated["aspect_scores"]:
        print(
            f"      - {aspect_score['aspect']}: {aspect_score['score']}/100 "
            f"({aspect_score['status']}, priority: {aspect_score['priority']})"
        )

    print(f"\n   Strongest: {', '.join(aggregated['strongest_aspects'])}")
    print(f"   Weakest: {', '.join(aggregated['weakest_aspects'])}")

    if aggregated.get("critical_gaps"):
        print("\n   Critical Gaps:")
        for gap in aggregated["critical_gaps"]:
            print(f"      - {gap}")

    print(f"\n   Estimated time to ready: {aggregated['estimated_time_to_ready']}")

    print("\n   Next Steps:")
    for i, step in enumerate(aggregated.get("next_steps", []), 1):
        print(f"      {i}. {step}")

    print("\n" + "=" * 60)
    print("✨ All graph tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_quick_scan_graph())
