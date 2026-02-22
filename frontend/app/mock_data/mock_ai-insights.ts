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
    type: 'info',
    title: 'Unlinked expectations',
    message:
      'You have player expectations that aren’t connected to any PX nodes yet. Linking them will improve traceability.',
  },
  {
    type: 'warning',
    title: 'Mid-game pacing dip',
    message:
      'Your pacing diagram has a quieter stretch around the midpoint. Consider adding a new beat, location, or escalation.',
  },
  {
    type: 'success',
    title: 'Strong pillar alignment',
    message:
      'Your design pillars map well to your top expectations. Nice consistency across the experience goals.',
  },
]
