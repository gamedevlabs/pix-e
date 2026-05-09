export interface MockWhatsNewItem {
  title: string
  description: string
  icon?: string
}

/**
 * Mock "What's New" items displayed on landing + dashboards.
 * Replace with backend-provided release notes when available.
 */
export const mockWhatsNew: MockWhatsNewItem[] = [
  {
    title: 'Workflow-driven navigation',
    description: 'Pick up where you left off with contextual next steps for each project.',
    icon: 'i-lucide-list-checks',
  },
  {
    title: 'Improved dashboards',
    description: 'Cleaner cards, better layout, and faster access to modules.',
    icon: 'i-lucide-layout-dashboard',
  },
  {
    title: 'More import/export options',
    description: 'Move data between tools with a more flexible import/export flow.',
    icon: 'i-lucide-arrow-left-right',
  },
]
