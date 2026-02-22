export type MockRecentActivityType = 'edit' | 'create' | 'delete'

export interface MockRecentActivityItem {
  title: string
  timestamp: string
  icon: string
  type?: MockRecentActivityType
}

/**
 * Mock recent activity displayed on landing + project dashboards.
 * Replace with backend-provided activity feed when available.
 */
export const mockRecentActivity: MockRecentActivityItem[] = [
  {
    title: 'Created PX Node “Combat Loop”',
    timestamp: '12 min ago',
    icon: 'i-lucide-plus',
    type: 'create',
  },
  {
    title: 'Updated Design Pillar “Clarity”',
    timestamp: '1 hour ago',
    icon: 'i-lucide-edit',
    type: 'edit',
  },
  {
    title: 'Removed expectation “Too grindy”',
    timestamp: 'Yesterday',
    icon: 'i-lucide-trash',
    type: 'delete',
  },
]
