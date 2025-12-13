/**
 * Composable for Structural Memory generation.
 *
 * Handles generating knowledge triples, atomic facts, and embeddings
 * for PX nodes in selected charts.
 */

const BASE_URL = 'http://localhost:8000/'

export interface GenerationOptions {
  chartIds: string[]
  forceRegenerate?: boolean
  skipEmbeddings?: boolean
  llmModel?: string
  embeddingModel?: string
}

export interface ChartResult {
  chart_id: string
  chart_name: string
  processed: number
  skipped: number
  total_triples: number
  total_facts: number
  total_embeddings: number
  processed_nodes: Array<{
    node_id: string
    node_name: string
    triples: number
    facts: number
    embeddings: number
  }>
  skipped_nodes: Array<{
    node_id: string
    node_name: string
  }>
  errors: string[]
}

export interface GenerationResponse {
  success: boolean
  summary: {
    charts_processed: number
    nodes_processed: number
    nodes_skipped: number
    total_triples: number
    total_facts: number
    total_embeddings: number
  }
  charts: ChartResult[]
}

export interface ChartStats {
  chart_id: string
  chart_name: string
  total_nodes: number
  processed_nodes: number
  pending_nodes: number
  total_triples: number
  total_facts: number
  total_embeddings: number
}

export interface StatsResponse {
  charts: ChartStats[]
}

// Evaluation types
export interface EvaluationOptions {
  chartId: string
  nodeIds?: string[]
  iterations?: number
  llmModel?: string
}

export interface CoherenceIssue {
  type: 'prerequisite' | 'pacing' | 'story' | 'category'
  severity: 'error' | 'warning' | 'info'
  description: string
  affected_nodes: string[]
}

export interface NodeEvaluationResult {
  node_id: string
  node_name: string
  is_coherent: boolean
  issues: CoherenceIssue[]
  context_used: string
  error: string | null
}

export interface ChartEvaluationResult {
  chart_id: string
  chart_name: string
  summary: {
    total_nodes: number
    coherent_nodes: number
    total_errors: number
    total_warnings: number
  }
  nodes: NodeEvaluationResult[]
}

export interface EvaluationResponse {
  success: boolean
  evaluation: ChartEvaluationResult
}

export function useStructuralMemory() {
  const loading = ref(false)
  const evaluating = ref(false)
  const error = ref<string | null>(null)
  const lastResult = ref<GenerationResponse | null>(null)
  const lastEvaluation = ref<ChartEvaluationResult | null>(null)
  const stats = ref<ChartStats[]>([])

  const { success: successToast, error: errorToast } = usePixeToast()

  /**
   * Generate structural memory for selected charts.
   */
  async function generate(options: GenerationOptions): Promise<GenerationResponse | null> {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<GenerationResponse>(
        `${BASE_URL}structural-memory/generate/`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'X-CSRFToken': useCookie('csrftoken').value,
          } as HeadersInit,
          body: {
            chart_ids: options.chartIds,
            force_regenerate: options.forceRegenerate ?? false,
            skip_embeddings: options.skipEmbeddings ?? false,
            llm_model: options.llmModel ?? 'gpt-4o-mini',
            embedding_model: options.embeddingModel ?? 'text-embedding-3-small',
          },
        },
      )

      lastResult.value = response

      if (response.success) {
        const { summary } = response
        successToast(
          `Generated structural memory: ${summary.nodes_processed} nodes processed, ` +
            `${summary.nodes_skipped} skipped, ${summary.total_triples} triples, ` +
            `${summary.total_facts} facts, ${summary.total_embeddings} embeddings`,
        )
      }

      return response
    }
    catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Generation failed'
      error.value = errorMessage
      errorToast(err)
      return null
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Get processing statistics for charts.
   */
  async function getStats(chartIds: string[]): Promise<ChartStats[]> {
    try {
      const response = await $fetch<StatsResponse>(`${BASE_URL}structural-memory/stats/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
        body: {
          chart_ids: chartIds,
        },
      })

      stats.value = response.charts
      return response.charts
    }
    catch (err) {
      errorToast(err)
      return []
    }
  }

  /**
   * Check if any nodes need processing in selected charts.
   */
  function hasPendingNodes(chartIds: string[]): boolean {
    return stats.value
      .filter(s => chartIds.includes(s.chart_id))
      .some(s => s.pending_nodes > 0)
  }

  /**
   * Get total pending nodes across selected charts.
   */
  function getTotalPendingNodes(chartIds: string[]): number {
    return stats.value
      .filter(s => chartIds.includes(s.chart_id))
      .reduce((sum, s) => sum + s.pending_nodes, 0)
  }

  /**
   * Evaluate node coherence for a chart.
   */
  async function evaluate(options: EvaluationOptions): Promise<ChartEvaluationResult | null> {
    evaluating.value = true
    error.value = null

    try {
      const response = await $fetch<EvaluationResponse>(
        `${BASE_URL}structural-memory/evaluate/`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'X-CSRFToken': useCookie('csrftoken').value,
          } as HeadersInit,
          body: {
            chart_id: options.chartId,
            node_ids: options.nodeIds,
            iterations: options.iterations ?? 3,
            llm_model: options.llmModel ?? 'gpt-4o-mini',
          },
        },
      )

      lastEvaluation.value = response.evaluation

      if (response.success) {
        const { summary } = response.evaluation
        const issueText = summary.total_errors > 0 || summary.total_warnings > 0
          ? ` Found ${summary.total_errors} errors, ${summary.total_warnings} warnings.`
          : ' No issues found!'
        successToast(
          `Evaluated ${summary.total_nodes} nodes. ${summary.coherent_nodes} coherent.${issueText}`,
        )
      }

      return response.evaluation
    }
    catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Evaluation failed'
      error.value = errorMessage
      errorToast(err)
      return null
    }
    finally {
      evaluating.value = false
    }
  }

  /**
   * Clear evaluation results.
   */
  function clearEvaluation() {
    lastEvaluation.value = null
  }

  return {
    // State
    loading,
    evaluating,
    error,
    lastResult,
    lastEvaluation,
    stats,

    // Actions
    generate,
    getStats,
    evaluate,
    clearEvaluation,

    // Helpers
    hasPendingNodes,
    getTotalPendingNodes,
  }
}
