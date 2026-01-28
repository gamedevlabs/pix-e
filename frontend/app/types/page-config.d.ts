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

  /**
   * Navigation group for sidebar organization
   * Pages with the same group will be grouped together
   */
  navGroup?: string

  /**
   * Parent navigation item for nested menus
   * e.g., 'player-experience' for nested items under Player Experience
   */
  navParent?: string

  /**
   * Order within navigation group (lower numbers appear first)
   */
  navOrder?: number

  /**
   * Whether to show this page in navigation
   * @default true
   */
  showInNav?: boolean
}

declare module '#app' {
  interface PageMeta {
    pageConfig?: PageConfig
  }
}

export {}
