import type { NavigationMenuItem } from '@nuxt/ui'
import type { PageConfig } from '~/types/page-config'
import { MOCK_EXTERNAL_LINKS } from '~/mock_data/mock_external-links'

function normalizePath(p?: string) {
  const v = p ?? ''
  const head = v.split('?')[0] ?? ''
  return head.replace(/\/$/, '') || '/'
}

function isRouteTo(to: unknown): to is string {
  return typeof to === 'string' && !!to && !/^https?:\/\//.test(to)
}

function computeActiveParentValue(items: NavigationMenuItem[], path: string): string | undefined {
  const current = normalizePath(path)

  for (const item of items) {
    const parentValue = typeof item.value === 'string' ? item.value : undefined

    if (item.children?.length) {
      for (const child of item.children) {
        const childTo = isRouteTo(child.to) ? normalizePath(child.to) : ''
        if (childTo && (current === childTo || current.startsWith(childTo + '/'))) {
          return parentValue
        }
      }
    }

    const itemTo = isRouteTo(item.to) ? normalizePath(item.to) : ''
    if (itemTo && (current === itemTo || current.startsWith(itemTo + '/'))) {
      return parentValue
    }
  }
}

/**
 * Builds the sidebar navigation tree from page metadata declared in `definePageMeta`.
 *
 * Returns three lists: `[mainItems, toolItems, externalLinks]`.
 * Routes opt in via `pageConfig.title + icon`; opt out via `showInNav: false`.
 * Project-scoped routes (`type: 'project-required'`) get the current project id
 * appended as a `?id=` query so they keep working when navigating directly.
 *
 * Also exposes:
 *  - `openNavValue` — the currently expanded accordion parent (kept in sync with the route)
 *  - `groups` — flattened items packaged for the command-palette search
 */
export function useNavigationLinks() {
  const router = useRouter()
  const route = useRoute()
  const { currentProjectId } = useProjectHandler()

  const projectQuery = computed(() =>
    currentProjectId.value ? `?id=${currentProjectId.value}` : '',
  )

  const openNavValue = ref<string | undefined>(undefined)

  const links = computed<NavigationMenuItem[][]>(() => {
    const routes = router.getRoutes()

    const navRoutes = routes.filter((r) => {
      const pageConfig = r.meta.pageConfig as PageConfig | undefined
      return pageConfig?.showInNav !== false && pageConfig?.title && pageConfig?.icon
    })

    const sortedRoutes = navRoutes.sort((a, b) => {
      const aConfig = a.meta.pageConfig as PageConfig
      const bConfig = b.meta.pageConfig as PageConfig
      return (aConfig.navOrder || 999) - (bConfig.navOrder || 999)
    })

    const routesByParent = new Map<string, typeof sortedRoutes>()
    const topLevelRoutes: typeof sortedRoutes = []

    sortedRoutes.forEach((r) => {
      const pageConfig = r.meta.pageConfig as PageConfig
      if (pageConfig.navParent) {
        const existing = routesByParent.get(pageConfig.navParent) || []
        routesByParent.set(pageConfig.navParent, [...existing, r])
      } else {
        topLevelRoutes.push(r)
      }
    })

    const buildNavItem = (r: (typeof sortedRoutes)[number]): NavigationMenuItem => {
      const pageConfig = r.meta.pageConfig as PageConfig
      const routePath = r.path
      const childRoutes = routesByParent.get(routePath.replace(/^\//, ''))
      const needsProjectQuery = pageConfig.type === 'project-required'
      const to = needsProjectQuery ? `${routePath}${projectQuery.value}` : routePath
      const parentValue = normalizePath(routePath)

      const navItem: NavigationMenuItem = {
        label: pageConfig.title!,
        icon: pageConfig.icon!,
        to,
        value: parentValue,
      }

      if (childRoutes && childRoutes.length > 0) {
        // Clicking a parent both opens its accordion and navigates to the parent route.
        navItem.onSelect = (e: Event) => {
          e?.preventDefault?.()
          openNavValue.value = parentValue
          router.push(to)
        }

        navItem.children = childRoutes.map((childRoute) => {
          const childConfig = childRoute.meta.pageConfig as PageConfig
          const childNeedsProjectQuery = childConfig.type === 'project-required'
          const childTo = childNeedsProjectQuery
            ? `${childRoute.path}${projectQuery.value}`
            : childRoute.path
          return {
            label: childConfig.title!,
            icon: childConfig.icon!,
            to: childTo,
            // Keep the parent expanded while navigating into a child.
            onSelect: () => {
              openNavValue.value = parentValue
            },
          } satisfies NavigationMenuItem
        })
      }

      return navItem
    }

    const mainItems: NavigationMenuItem[] = topLevelRoutes
      .filter((r) => {
        const cfg = r.meta.pageConfig as PageConfig
        return !cfg.navGroup || cfg.navGroup === 'main'
      })
      .map(buildNavItem)

    const toolItems: NavigationMenuItem[] = topLevelRoutes
      .filter((r) => {
        const cfg = r.meta.pageConfig as PageConfig
        return cfg.navGroup === 'tools'
      })
      .map(buildNavItem)

    const externalLinks: NavigationMenuItem[] = [
      {
        label: 'Wiki',
        icon: 'i-lucide-book-text',
        to: MOCK_EXTERNAL_LINKS.wiki,
        target: '_blank',
      },
      {
        label: 'Discord',
        icon: 'i-lucide-message-circle',
        to: MOCK_EXTERNAL_LINKS.discord,
        target: '_blank',
      },
    ]

    return [mainItems, toolItems, externalLinks]
  })

  // Search palette items — flattened so children don't appear twice.
  const groups = computed(() => [
    {
      id: 'links',
      label: 'Go to',
      items: links.value.flat(),
    },
  ])

  watch(
    () => route.path,
    () => {
      openNavValue.value = computeActiveParentValue(links.value[0] || [], route.path)
    },
    { immediate: true },
  )

  return { links, openNavValue, groups }
}
