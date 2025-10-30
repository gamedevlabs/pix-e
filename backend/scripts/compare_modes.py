"""
Mode Comparison Script

Compares monolithic vs agentic execution modes for pillar evaluation operations.
Tracks execution time, costs, and outputs for thesis evaluation.

Usage:
    python scripts/compare_modes.py
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

import django  # noqa: E402

django.setup()

# Import to register handlers and agents
import pillars.llm  # noqa: F401, E402
import sparc.llm  # noqa: F401, E402
from llm import LLMOrchestrator  # noqa: E402
from llm.types import LLMRequest  # noqa: E402


class ModeComparator:
    """Compares monolithic and agentic execution modes."""

    # Approximate model costs per 1M tokens (in EUR)
    MODEL_COSTS = {
        "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free tier
        "gpt-4o-mini": {"input": 0.135, "output": 0.540},  # $0.150/$0.600 per 1M
        "gpt-4o": {"input": 2.25, "output": 9.00},  # $2.50/$10.00 per 1M
    }

    def __init__(self, output_dir: str = "comparison_results"):
        """
        Initialize comparator.

        Args:
            output_dir: Directory to save comparison results
        """
        self.orchestrator = LLMOrchestrator()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def run_comparison(
        self,
        pillars_data: Dict[str, Any],
        context: str,
        test_name: str = "test",
        model_id: str = "gpt-4o-mini",
    ) -> Dict[str, Any]:
        """
        Run comparison between monolithic and agentic modes.

        Args:
            pillars_data: Pillar data for evaluation
            context: Context/description for the game
            test_name: Name for this test run
            model_id: Model to use for comparison (default: gpt-4o-mini)

        Returns:
            Comparison results
        """
        print(f"\n{'='*60}")
        print(f"Running comparison: {test_name}")
        print(f"{'='*60}\n")

        # Prepare request data
        request_data = {
            "pillars_text": self._format_pillars(pillars_data),
            "context": context,
        }

        # Run monolithic mode (3 separate operations)
        print(f"Running MONOLITHIC mode with model: {model_id}...")
        monolithic_result = self._run_monolithic_mode(request_data, model_id)

        # Run agentic mode (single operation with agents)
        print(f"\nRunning AGENTIC mode with model: {model_id}...")
        agentic_result = self._run_agentic_mode(request_data, model_id)

        # Build comparison
        comparison = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "input_data": {
                "context": context,
                "pillars": pillars_data,
            },
            "monolithic": monolithic_result,
            "agentic": agentic_result,
            "comparison": self._calculate_comparison(monolithic_result, agentic_result),
        }

        # Save results
        self._save_results(comparison, test_name)

        return comparison

    def _format_pillars(self, pillars_data: Dict[str, Any]) -> str:
        """Format pillars for LLM input."""
        if isinstance(pillars_data, list):
            return "\n\n".join(
                [
                    f"Pillar: {p['name']}\nDescription: {p['description']}"
                    for p in pillars_data
                ]
            )
        return str(pillars_data)

    def _run_monolithic_mode(
        self, request_data: Dict[str, Any], model_id: str
    ) -> Dict[str, Any]:
        """Run evaluation in monolithic mode (3 separate handler calls)."""
        start_time = time.time()

        results = {}
        operations = [
            "evaluate_completeness",
            "evaluate_contradictions",
            "suggest_additions",
        ]

        for operation in operations:
            print(f"  - Running {operation}...")
            request = LLMRequest(
                feature="pillars",
                operation=operation,
                data=request_data,
                mode="monolithic",
                model_id=model_id,
            )

            try:
                response = self.orchestrator.execute(request)

                # Extract token usage and calculate cost
                prompt_tokens = 0
                completion_tokens = 0
                cost_eur = 0.0
                model_used = None

                if response.metadata.models_used:
                    model_used = response.metadata.models_used[0].name

                if response.metadata.token_usage:
                    prompt_tokens = response.metadata.token_usage.prompt_tokens
                    completion_tokens = response.metadata.token_usage.completion_tokens
                    cost_eur = self._estimate_cost(
                        model_used or "unknown", prompt_tokens, completion_tokens
                    )

                results[operation] = {
                    "success": response.success,
                    "results": response.results,
                    "execution_time_ms": response.metadata.execution_time_ms,
                    "model_used": model_used,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost_eur": cost_eur,
                }
            except Exception as e:
                results[operation] = {"success": False, "error": str(e)}

        total_time_ms = int((time.time() - start_time) * 1000)

        # Calculate totals across all operations
        total_cost_eur = 0.0
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0

        for op_result in results.values():
            if op_result.get("success", False):
                cost = op_result.get("cost_eur", 0.0)
                if isinstance(cost, (int, float)):
                    total_cost_eur += float(cost)

                p_tokens = op_result.get("prompt_tokens", 0)
                if isinstance(p_tokens, int):
                    total_prompt_tokens += p_tokens

                c_tokens = op_result.get("completion_tokens", 0)
                if isinstance(c_tokens, int):
                    total_completion_tokens += c_tokens

        total_tokens = total_prompt_tokens + total_completion_tokens

        return {
            "mode": "monolithic",
            "total_execution_time_ms": total_time_ms,
            "individual_results": results,
            "num_operations": len(operations),
            "estimated_cost_eur": round(total_cost_eur, 8),
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
        }

    def _run_agentic_mode(
        self, request_data: Dict[str, Any], model_id: str
    ) -> Dict[str, Any]:
        """Run evaluation in agentic mode (single graph with parallel agents)."""
        start_time = time.time()

        request = LLMRequest(
            feature="pillars",
            operation="evaluate_all",
            data=request_data,
            mode="agentic",
            model_id=model_id,
        )

        try:
            response = self.orchestrator.execute(request)

            agents_info = {}
            if response.metadata.agents_used:
                for agent in response.metadata.agents_used:
                    agents_info[agent.name] = {
                        "execution_time_ms": agent.execution_time_ms,
                        "model_used": agent.model,
                    }

            # Extract token usage and calculate cost
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            cost_eur = 0.0

            if response.metadata.token_usage:
                prompt_tokens = response.metadata.token_usage.prompt_tokens
                completion_tokens = response.metadata.token_usage.completion_tokens
                total_tokens = response.metadata.token_usage.total_tokens

                # Use the first model for cost estimation
                model_name = (
                    response.metadata.models_used[0].name
                    if response.metadata.models_used
                    else "unknown"
                )
                cost_eur = self._estimate_cost(
                    model_name, prompt_tokens, completion_tokens
                )

            result = {
                "mode": "agentic",
                "success": response.success,
                "total_execution_time_ms": response.metadata.execution_time_ms,
                "results": response.results,
                "agents_info": agents_info,
                "num_agents": (
                    len(response.metadata.agents_used)
                    if response.metadata.agents_used
                    else 0
                ),
                "models_used": (
                    [m.name for m in response.metadata.models_used]
                    if response.metadata.models_used
                    else []
                ),
                "events_count": (
                    len(response.metadata.events) if response.metadata.events else 0
                ),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_eur": round(cost_eur, 8),
            }

            # Add errors/warnings if present
            if response.errors:
                result["errors"] = [e.model_dump() for e in response.errors]
            if response.warnings:
                result["warnings"] = [w.model_dump() for w in response.warnings]

        except Exception as e:
            result = {
                "mode": "agentic",
                "success": False,
                "error": str(e),
                "total_execution_time_ms": int((time.time() - start_time) * 1000),
            }

        return result

    def run_sparc_comparison(
        self,
        game_text: str,
        test_name: str = "sparc_test",
        model_id: str = "gpt-4o-mini",
    ) -> Dict[str, Any]:
        """
        Run comparison between monolithic and agentic SPARC evaluation.

        Args:
            game_text: Game description text for SPARC evaluation
            test_name: Name for this test run
            model_id: Model to use for comparison (default: gpt-4o-mini)

        Returns:
            Comparison results
        """
        print(f"\n{'='*60}")
        print(f"Running SPARC comparison: {test_name}")
        print(f"{'='*60}\n")

        # Prepare request data
        request_data = {"game_text": game_text}

        # Run monolithic mode (single SPARC monolithic call)
        print(f"Running SPARC MONOLITHIC mode with model: {model_id}...")
        monolithic_result = self._run_sparc_monolithic_mode(request_data, model_id)

        # Run agentic mode (quick scan with 10 parallel agents)
        print(f"\nRunning SPARC AGENTIC mode (10 agents) with model: {model_id}...")
        agentic_result = self._run_sparc_agentic_mode(request_data, model_id)

        # Build comparison
        comparison = {
            "test_name": test_name,
            "feature": "sparc",
            "timestamp": datetime.now().isoformat(),
            "input_data": {"game_text": game_text},
            "monolithic": monolithic_result,
            "agentic": agentic_result,
            "comparison": self._calculate_comparison(monolithic_result, agentic_result),
        }

        # Save results
        self._save_results(comparison, test_name)

        return comparison

    def _run_sparc_monolithic_mode(
        self, request_data: Dict[str, Any], model_id: str
    ) -> Dict[str, Any]:
        """Run SPARC evaluation in monolithic mode (single LLM call)."""
        start_time = time.time()

        print("  - Running monolithic SPARC evaluation...")
        request = LLMRequest(
            feature="sparc",
            operation="monolithic",
            data=request_data,
            mode="monolithic",
            model_id=model_id,
        )

        try:
            response = self.orchestrator.execute(request)

            # Extract token usage and calculate cost
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            cost_eur = 0.0
            model_used = None

            if response.metadata.models_used:
                model_used = response.metadata.models_used[0].name

            if response.metadata.token_usage:
                prompt_tokens = response.metadata.token_usage.prompt_tokens
                completion_tokens = response.metadata.token_usage.completion_tokens
                total_tokens = response.metadata.token_usage.total_tokens
                cost_eur = self._estimate_cost(
                    model_used or "unknown", prompt_tokens, completion_tokens
                )

            result = {
                "mode": "monolithic",
                "success": response.success,
                "total_execution_time_ms": response.metadata.execution_time_ms,
                "results": response.results,
                "model_used": model_used,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_eur": round(cost_eur, 8),
            }
        except Exception as e:
            result = {
                "mode": "monolithic",
                "success": False,
                "error": str(e),
                "total_execution_time_ms": int((time.time() - start_time) * 1000),
            }

        return result

    def _run_sparc_agentic_mode(
        self, request_data: Dict[str, Any], model_id: str
    ) -> Dict[str, Any]:
        """Run SPARC evaluation in agentic mode (10 agents in parallel)."""
        start_time = time.time()

        request = LLMRequest(
            feature="sparc",
            operation="quick_scan",
            data=request_data,
            mode="agentic",
            model_id=model_id,
        )

        try:
            response = self.orchestrator.execute(request)

            agents_info = {}
            if response.metadata.agents_used:
                for agent in response.metadata.agents_used:
                    agents_info[agent.name] = {
                        "execution_time_ms": agent.execution_time_ms,
                        "model_used": agent.model,
                    }

            # Extract token usage and calculate cost
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            cost_eur = 0.0

            if response.metadata.token_usage:
                prompt_tokens = response.metadata.token_usage.prompt_tokens
                completion_tokens = response.metadata.token_usage.completion_tokens
                total_tokens = response.metadata.token_usage.total_tokens

                # Use the first model for cost estimation
                model_name = (
                    response.metadata.models_used[0].name
                    if response.metadata.models_used
                    else "unknown"
                )
                cost_eur = self._estimate_cost(
                    model_name, prompt_tokens, completion_tokens
                )

            result = {
                "mode": "agentic",
                "success": response.success,
                "total_execution_time_ms": response.metadata.execution_time_ms,
                "results": response.results,
                "agents_info": agents_info,
                "num_agents": (
                    len(response.metadata.agents_used)
                    if response.metadata.agents_used
                    else 0
                ),
                "models_used": (
                    [m.name for m in response.metadata.models_used]
                    if response.metadata.models_used
                    else []
                ),
                "events_count": (
                    len(response.metadata.events) if response.metadata.events else 0
                ),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_eur": round(cost_eur, 8),
            }

            # Add errors/warnings if present
            if response.errors:
                result["errors"] = [e.model_dump() for e in response.errors]
            if response.warnings:
                result["warnings"] = [w.model_dump() for w in response.warnings]

        except Exception as e:
            result = {
                "mode": "agentic",
                "success": False,
                "error": str(e),
                "total_execution_time_ms": int((time.time() - start_time) * 1000),
            }

        return result

    def _estimate_cost(
        self, model_name: str, prompt_tokens: int = 0, completion_tokens: int = 0
    ) -> float:
        """
        Estimate cost in EUR for model usage.

        Args:
            model_name: Name of the model
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in EUR (with high precision)
        """
        costs = self.MODEL_COSTS.get(model_name, {"input": 0.0, "output": 0.0})

        input_cost = (prompt_tokens / 1_000_000) * costs["input"]
        output_cost = (completion_tokens / 1_000_000) * costs["output"]

        # Return high precision cost (8 decimal places)
        return round(input_cost + output_cost, 8)

    def _calculate_comparison(
        self, monolithic: Dict[str, Any], agentic: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comparison metrics between modes."""
        comparison = {}

        # Time comparison
        mono_time = monolithic.get("total_execution_time_ms", 0)
        agent_time = agentic.get("total_execution_time_ms", 0)

        if mono_time > 0:
            speedup = (mono_time - agent_time) / mono_time * 100
            comparison["time_saved_percentage"] = round(speedup, 2)
            comparison["time_difference_ms"] = mono_time - agent_time

        comparison["monolithic_time_ms"] = mono_time
        comparison["agentic_time_ms"] = agent_time

        # Cost comparison (if available)
        mono_cost = monolithic.get("estimated_cost_eur", 0.0)
        agent_cost = agentic.get("estimated_cost_eur", 0.0)

        comparison["monolithic_cost_eur"] = mono_cost
        comparison["agentic_cost_eur"] = agent_cost
        comparison["cost_difference_eur"] = round(agent_cost - mono_cost, 8)

        # Success comparison
        comparison["both_successful"] = monolithic.get("success", True) and agentic.get(
            "success", False
        )

        return comparison

    def _save_results(self, comparison: Dict[str, Any], test_name: str) -> None:
        """Save comparison results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON
        json_path = self.output_dir / f"{test_name}_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(comparison, f, indent=2)
        print(f"\n✅ Results saved to: {json_path}")

        # Save human-readable markdown
        md_path = self.output_dir / f"{test_name}_{timestamp}.md"
        with open(md_path, "w") as f:
            f.write(self._format_markdown(comparison))
        print(f"✅ Markdown report saved to: {md_path}")

    def _format_markdown(self, comparison: Dict[str, Any]) -> str:
        """Format comparison results as markdown."""
        feature = comparison.get("feature", "pillars")

        md = f"""# Execution Mode Comparison: {comparison['test_name']}

**Timestamp:** {comparison['timestamp']}
**Feature:** {feature.upper()}

## Input Data

"""
        # Handle different input data formats
        if feature == "sparc":
            md += f"### Game Text\n{comparison['input_data']['game_text']}\n"
        else:
            # Pillars format
            md += f"### Context\n{comparison['input_data']['context']}\n\n### Pillars\n"
            pillars_list = comparison["input_data"]["pillars"]
            if isinstance(pillars_list, list):
                for p in pillars_list:
                    md += f"\n**{p['name']}**\n{p['description']}\n"

        md += "\n---\n\n"

        # Performance comparison
        comp = comparison["comparison"]
        mono = comparison["monolithic"]
        agent = comparison["agentic"]

        # Build markdown table with metrics
        mono_cost = comp.get("monolithic_cost_eur", 0.0)
        agent_cost = comp.get("agentic_cost_eur", 0.0)
        cost_diff = comp.get("cost_difference_eur", 0.0)
        time_diff = comp.get("time_difference_ms", "N/A")
        time_saved = comp.get("time_saved_percentage", "N/A")

        # Extract token counts for readability
        mono_p_tokens = mono.get("total_prompt_tokens", 0)
        mono_c_tokens = mono.get("total_completion_tokens", 0)
        mono_total_tokens = mono.get("total_tokens", 0)
        agent_p_tokens = agent.get("prompt_tokens", 0)
        agent_c_tokens = agent.get("completion_tokens", 0)
        agent_total_tokens = agent.get("total_tokens", 0)

        md += f"""## Performance Comparison

| Metric | Monolithic | Agentic | Difference |
|--------|-----------|---------|------------|
| Execution Time | {comp['monolithic_time_ms']}ms | {comp['agentic_time_ms']}ms | {time_diff}ms |  # noqa: E501
| Time Saved | - | - | {time_saved}% |
| **Cost** | **€{mono_cost:.8f}** | **€{agent_cost:.8f}** | **€{cost_diff:.8f}** |
| Prompt Tokens | {mono_p_tokens} | {agent_p_tokens} | - |
| Completion Tokens | {mono_c_tokens} | {agent_c_tokens} | - |
| Total Tokens | {mono_total_tokens} | {agent_total_tokens} | - |

> **Note:** Costs are based on actual token usage and current model pricing.

"""

        # Monolithic results
        mono_data = comparison["monolithic"]
        md += f"""## Monolithic Mode Results

**Total Time:** {mono_data['total_execution_time_ms']}ms
"""

        # Check if this is SPARC (single call) or pillars (multiple operations)
        if mono_data.get("individual_results"):
            # Pillars format with multiple operations
            md += f"**Number of Operations:** {mono_data['num_operations']}\n\n"
            for op_name, op_result in mono_data.get("individual_results", {}).items():
                md += f"### {op_name}\n"
                if op_result.get("success"):
                    p_tokens = op_result.get("prompt_tokens", 0)
                    c_tokens = op_result.get("completion_tokens", 0)
                    md += f"- **Time:** {op_result.get('execution_time_ms')}ms\n"
                    md += f"- **Model:** {op_result.get('model_used')}\n"
                    md += (
                        f"- **Tokens:** {p_tokens} prompt + {c_tokens} "
                        f"completion = {p_tokens + c_tokens} total\n"
                    )
                    cost = op_result.get("cost_eur", 0.0)
                    md += f"- **Cost:** €{cost:.8f}\n"
                    results_json = json.dumps(op_result.get("results"), indent=2)
                    md += f"- **Output:** {results_json}\n\n"
                else:
                    md += f"- **Error:** {op_result.get('error')}\n\n"
        else:
            # SPARC format with single operation
            mono_p = mono_data.get("prompt_tokens", 0)
            mono_c = mono_data.get("completion_tokens", 0)
            mono_total = mono_data.get("total_tokens", 0)
            mono_cost_display = mono_data.get("estimated_cost_eur", 0.0)
            md += f"**Model:** {mono_data.get('model_used')}\n"
            md += f"**Success:** {mono_data.get('success')}\n"
            tokens_text = f"{mono_p} prompt + {mono_c} completion = {mono_total}"
            md += f"**Tokens:** {tokens_text} total\n"
            md += f"**Cost:** €{mono_cost_display:.8f}\n\n"
            if mono_data.get("success"):
                results_json = json.dumps(mono_data.get("results"), indent=2)
                md += f"### Output\n```json\n{results_json}\n```\n"

        # Agentic results
        agent_data = comparison["agentic"]
        agent_p = agent_data.get("prompt_tokens", 0)
        agent_c = agent_data.get("completion_tokens", 0)
        agent_total = agent_data.get("total_tokens", 0)
        agent_cost_display = agent_data.get("estimated_cost_eur", 0.0)

        md += f"""## Agentic Mode Results

**Total Time:** {agent_data.get('total_execution_time_ms')}ms
**Number of Agents:** {agent_data.get('num_agents', 0)}
**Success:** {agent_data.get('success')}
**Total Tokens:** {agent_p} prompt + {agent_c} completion = {agent_total} total
**Total Cost:** €{agent_cost_display:.8f}

"""
        if agent_data.get("success"):
            models = agent_data.get("models_used", [])
            md += f"**Models Used:** {', '.join(models)}\n\n"

            if agent_data.get("agents_info"):
                md += "### Agent Execution Times\n\n"
                for agent_name, info in agent_data.get("agents_info", {}).items():
                    time_ms = info["execution_time_ms"]
                    model = info["model_used"]
                    md += f"- **{agent_name}:** {time_ms}ms (model: {model})\n"

            md += "\n### Aggregated Output\n\n"
            results_json = json.dumps(agent_data.get("results"), indent=2)
            md += f"```json\n{results_json}\n```\n"

        return md


def main():
    """Run comparison with sample data."""
    # Sample pillar data
    sample_pillars = [
        {
            "name": "Fast-Paced Action",
            "description": (
                "Combat encounters should be quick and intense, "
                "keeping players engaged."
            ),
        },
        {
            "name": "Strategic Depth",
            "description": (
                "Players must think carefully about positioning " "and ability usage."
            ),
        },
        {
            "name": "Accessibility",
            "description": "Easy to learn basics, but skill ceiling should be high.",
        },
    ]

    sample_context = (
        "A multiplayer battle arena game with 5v5 team-based combat. "
        "Players control heroes with unique abilities in fast-paced matches."
    )

    # Create comparator
    comparator = ModeComparator()

    # Run comparison with OpenAI (has token tracking)
    results = comparator.run_comparison(
        pillars_data=sample_pillars,
        context=sample_context,
        test_name="sample_evaluation",
        model_id="gpt-4o-mini",  # Use OpenAI for cost tracking
    )

    # Print summary
    print("\n" + "=" * 60)
    print("PILLARS SUMMARY")
    print("=" * 60)
    comp = results["comparison"]
    print(f"Monolithic time: {comp['monolithic_time_ms']}ms")
    print(f"Agentic time: {comp['agentic_time_ms']}ms")
    if "time_saved_percentage" in comp:
        print(f"Time saved: {comp['time_saved_percentage']}%")
    print(f"\nMonolithic cost: €{comp.get('monolithic_cost_eur', 0.0):.8f}")
    print(f"Agentic cost: €{comp.get('agentic_cost_eur', 0.0):.8f}")
    print(f"Cost difference: €{comp.get('cost_difference_eur', 0.0):.8f}")
    print(f"\nBoth successful: {comp['both_successful']}")
    print("\n✅ Cost tracking enabled with real token usage from OpenAI.")

    # Run SPARC comparison
    print("\n" + "=" * 60)
    print("Running SPARC Comparison")
    print("=" * 60)

    sample_game_text = """
    A roguelike dungeon crawler in a procedurally generated dark fantasy world.
    Players explore dangerous dungeons filled with monsters, traps, and treasures.
    Features permadeath, turn-based combat, and deep character customization.
    Each run is unique due to procedural generation of levels, items, and enemies.
    Players must manage resources carefully and make strategic decisions.
    """

    sparc_results = comparator.run_sparc_comparison(
        game_text=sample_game_text.strip(),
        test_name="sample_sparc_evaluation",
        model_id="gpt-4o-mini",
    )

    # Print SPARC summary
    print("\n" + "=" * 60)
    print("SPARC SUMMARY")
    print("=" * 60)
    sparc_comp = sparc_results["comparison"]
    print(f"Monolithic time: {sparc_comp['monolithic_time_ms']}ms")
    print(f"Agentic time (10 agents): {sparc_comp['agentic_time_ms']}ms")
    if "time_saved_percentage" in sparc_comp:
        print(f"Time saved: {sparc_comp['time_saved_percentage']}%")
    mono_cost = sparc_comp.get("monolithic_cost_eur", 0.0)
    agent_cost = sparc_comp.get("agentic_cost_eur", 0.0)
    cost_diff = sparc_comp.get("cost_difference_eur", 0.0)
    print(f"\nMonolithic cost: €{mono_cost:.8f}")
    print(f"Agentic cost: €{agent_cost:.8f}")
    print(f"Cost difference: €{cost_diff:.8f}")
    num_agents = sparc_results["agentic"].get("num_agents", 0)
    print(f"\nNumber of agents executed: {num_agents}")
    print(f"Both successful: {sparc_comp['both_successful']}")
    print("\n✅ SPARC comparison complete with 10 parallel agents.")


if __name__ == "__main__":
    main()
