// Page configuration types for pix:e modules

export type PageType = 'project-required' | 'standalone' | 'public'

export interface PageConfig {
  /**
   * Type of page:
   * - 'project-required': Requires a project to be selected (e.g., /pillars?id=projectId)
   * - 'standalone': Doesn't require a project (e.g., /movie-script-evaluator)
   * - 'public': Public pages like login, index
   */
  type: PageType

  /**
   * Whether to show the sidebar navigation
   * @default false for 'public', true for others with project context
   */
  showSidebar?: boolean

  /**
   * Custom title for the page (optional)
   */
  title?: string

  /**
   * Icon for navigation (optional)
   */
  icon?: string
}

declare module '#app' {
  interface PageMeta {
    pageConfig?: PageConfig
  }
}

export {}
