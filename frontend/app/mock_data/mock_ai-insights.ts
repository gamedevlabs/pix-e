export type MockAiInsightType = 'info' | 'warning' | 'success'

export interface MockAiInsight {
  type: MockAiInsightType
  title: string
  message: string
}

/**
 * Mock AI insights displayed on landing + project dashboards.
 * Replace with backend-provided insights when available.
 */
export const mockAiInsights: MockAiInsight[] = [
  {
    type: 'warning',
    title: 'Mid-game pacing dip',
    message: 'A quieter stretch around the midpoint — consider adding a beat or escalation.',
  },
  {
    type: 'success',
    title: 'Strong pillar alignment',
    message: 'Your design pillars map well to your top expectations.',
  },
]
