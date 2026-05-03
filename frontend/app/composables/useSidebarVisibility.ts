import type { PageConfig } from '~/types/page-config'

/**
 * Decides whether the dashboard sidebar should be rendered for the current route.
 *
 * Resolution order:
 *  1. Explicit `pageConfig.showSidebar` on the route wins.
 *  2. `pageConfig.type` (`public` / `standalone` / `project-required`) drives the default.
 *  3. Backwards-compatibility fallback for pages that don't yet declare a `pageConfig`.
 */
export function useSidebarVisibility() {
  const route = useRoute()
  const authentication = useAuthentication()
  const { currentProjectId } = useProjectHandler()

  const showSidebar = computed(() => {
    const pageConfig = route.meta.pageConfig as PageConfig | undefined

    if (pageConfig?.showSidebar !== undefined) {
      return pageConfig.showSidebar
    }

    if (pageConfig?.type === 'public') return false
    if (pageConfig?.type === 'standalone') return false

    if (pageConfig?.type === 'project-required') {
      const hasCurrentProject = !!currentProjectId.value || !!route.query?.id
      return authentication.isLoggedIn.value && hasCurrentProject
    }

    // Fallback: pages without a pageConfig.
    const path = route.path || ''
    const name = route.name ? String(route.name) : ''
    const alwaysShowSidebar: string[] = ['dashboard', 'settings']
    const alwaysHideSidebar: string[] = ['login', '/movie-script-evaluator', 'create']

    if (!name || path === '/') return false

    if (alwaysHideSidebar.some((p) => p && (p === name || path === p || path.startsWith(p)))) {
      return false
    }

    if (alwaysShowSidebar.some((p) => p && (p === name || path === p || path.startsWith(p)))) {
      return true
    }

    const hasCurrentProject = !!currentProjectId.value || !!route.query?.id
    return hasCurrentProject && authentication.isLoggedIn.value
  })

  return { showSidebar }
}
