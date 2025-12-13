/**
 * Composable for Context Strategy API.
 *
 * Supports 4 context engineering strategies for LLM evaluation:
 * - structural_memory: Knowledge Triples + Atomic Facts (Zeng et al. 2024)
 * - hierarchical_graph: Deterministic 4-layer graph traversal
 * - hmem: Vector embeddings with positional index routing (Sun & Zeng 2025)
 * - combined: Structural data + hierarchical organization
 */

const BASE_URL = 'http://localhost:8000/'

export type StrategyType = 'structural_memory' | 'hierarchical_graph' | 'hmem' | 'combined'

export interface StrategyInfo {
  id: StrategyType
  name: string
  description: string
  requires_embeddings: boolean
  requires_llm: boolean
}

export interface CoherenceIssue {
  type: 'prerequisite' | 'pacing' | 'story' | 'category'
  severity: 'error' | 'warning' | 'info'
  description: string
  affected_nodes: string[]
}

export interface StrategyEvaluationResult {
  node_id: string
  node_name: string
  strategy: string
  is_coherent: boolean
  issues: CoherenceIssue[]
  context_metadata: Record<string, unknown>
  error: string | null
}

export interface ComparisonSummary {
  strategies_compared: string[]
  coherent_by_strategy: Record<string, boolean>
  issues_by_strategy: Record<string, number>
  agreement: boolean
}

export interface ComparisonResult {
  node_id: string
  node_name: string
  strategies: Record<string, StrategyEvaluationResult>
  summary: ComparisonSummary
}

export interface LayerContext {
  layer: number
  layer_name: string
  content: string
  metadata: Record<string, unknown>
}

export interface ContextBuildResult {
  strategy: string
  context_string: string
  layers: LayerContext[]
  metadata: Record<string, unknown>
}

export interface EvaluateOptions {
  nodeId: string
  chartId: string
  strategy?: StrategyType
  llmModel?: string
}

export interface CompareOptions {
  nodeId: string
  chartId: string
  strategies?: StrategyType[]
  llmModel?: string
}

export interface BuildContextOptions {
  nodeId: string
  chartId: string
  strategy?: StrategyType
}

export function useContextStrategies() {
  const availableStrategies = ref<StrategyInfo[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastEvaluation = ref<StrategyEvaluationResult | null>(null)
  const lastComparison = ref<ComparisonResult | null>(null)
  const lastContext = ref<ContextBuildResult | null>(null)

  const { success: successToast, error: errorToast } = usePixeToast()

  /**
   * Fetch available strategies from the API.
   */
  async function fetchStrategies(): Promise<StrategyInfo[]> {
    try {
      const response = await $fetch<{ strategies: StrategyInfo[] }>(
        `${BASE_URL}context/strategies/`,
        {
          method: 'GET',
          credentials: 'include',
        },
      )
      availableStrategies.value = response.strategies
      return response.strategies
    } catch (err) {
      errorToast(err)
      return []
    }
  }

  /**
   * Evaluate a node using a specific strategy.
   */
  async function evaluate(options: EvaluateOptions): Promise<StrategyEvaluationResult | null> {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<{ success: boolean; result: StrategyEvaluationResult }>(
        `${BASE_URL}context/evaluate/`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'X-CSRFToken': useCookie('csrftoken').value,
          } as HeadersInit,
          body: {
            node_id: options.nodeId,
            chart_id: options.chartId,
            strategy: options.strategy ?? 'structural_memory',
            llm_model: options.llmModel ?? 'gpt-4o-mini',
          },
        },
      )

      const result = response.result
      lastEvaluation.value = result

      if (result.is_coherent) {
        successToast(`Node is coherent using ${result.strategy}`)
      } else {
        const issueCount = result.issues.length
        successToast(`Found ${issueCount} issue(s) using ${result.strategy}`)
      }

      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Evaluation failed'
      error.value = errorMessage
      errorToast(err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Compare multiple strategies for a single node.
   */
  async function compare(options: CompareOptions): Promise<ComparisonResult | null> {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<{ success: boolean; comparison: ComparisonResult }>(
        `${BASE_URL}context/compare/`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'X-CSRFToken': useCookie('csrftoken').value,
          } as HeadersInit,
          body: {
            node_id: options.nodeId,
            chart_id: options.chartId,
            strategies: options.strategies,
            llm_model: options.llmModel ?? 'gpt-4o-mini',
          },
        },
      )

      const comparison = response.comparison
      lastComparison.value = comparison

      const { summary } = comparison
      const agreementText = summary.agreement ? 'All strategies agree' : 'Strategies disagree'
      successToast(`Compared ${summary.strategies_compared.length} strategies. ${agreementText}`)

      return comparison
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Comparison failed'
      error.value = errorMessage
      errorToast(err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Build context without evaluation (for debugging/research).
   */
  async function buildContext(options: BuildContextOptions): Promise<ContextBuildResult | null> {
    loading.value = true
    error.value = null

    try {
      // Backend returns: { success, strategy, context, layers, metadata, triples_count, facts_count }
      const response = await $fetch<{
        success: boolean
        strategy: string
        context: string
        layers: LayerContext[]
        metadata: Record<string, unknown>
        triples_count: number
        facts_count: number
      }>(`${BASE_URL}context/build/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
        body: {
          node_id: options.nodeId,
          chart_id: options.chartId,
          strategy: options.strategy ?? 'structural_memory',
        },
      })

      // Map to ContextBuildResult
      const result: ContextBuildResult = {
        strategy: response.strategy,
        context_string: response.context,
        layers: response.layers,
        metadata: response.metadata,
      }

      lastContext.value = result
      successToast(`Built context using ${response.strategy}`)

      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Context build failed'
      error.value = errorMessage
      errorToast(err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear all results.
   */
  function clearResults() {
    lastEvaluation.value = null
    lastComparison.value = null
    lastContext.value = null
  }

  // Computed helpers
  const strategiesAgreement = computed(() => {
    if (!lastComparison.value) return null
    return lastComparison.value.summary.agreement
  })

  const bestStrategy = computed(() => {
    if (!lastComparison.value) return null

    const { strategies } = lastComparison.value
    let best: string | null = null
    let minIssues = Infinity

    for (const [name, result] of Object.entries(strategies)) {
      if (result.issues.length < minIssues) {
        minIssues = result.issues.length
        best = name
      }
    }

    return best
  })

  return {
    // State
    availableStrategies,
    loading,
    error,
    lastEvaluation,
    lastComparison,
    lastContext,

    // Actions
    fetchStrategies,
    evaluate,
    compare,
    buildContext,
    clearResults,

    // Computed
    strategiesAgreement,
    bestStrategy,
  }
}
