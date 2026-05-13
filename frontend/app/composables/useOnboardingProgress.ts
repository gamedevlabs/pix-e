import type { Ref } from 'vue'

// Routes that count as "a module" for the Getting Oriented step.
const MODULE_ROUTES = [
  '/pillars',
  '/pxcharts',
  '/pxnodes',
  '/pxcomponentdefinitions',
  '/pxcomponents',
  '/player-expectations',
  '/player-experience',
  '/sentiments',
  '/settings',
]

/**
 * Auto-completes "Getting Oriented" workflow substeps as the user discovers key
 * features: visiting a module page, opening Settings, opening the search bar.
 *
 * Pass the layout's `searchOpen` ref so the search-bar substep can be tracked.
 */
export function useOnboardingProgress(searchOpen: Ref<boolean>) {
  const route = useRoute()
  const { tryCompleteSubstep } = useProjectWorkflow()

  // onb-1-1: first visit to any module page (not the dashboard itself).
  const hasVisitedModule = ref(false)
  watch(
    () => route.path,
    (path) => {
      if (hasVisitedModule.value) return
      if (MODULE_ROUTES.some((r) => path.startsWith(r)) && path !== '/dashboard') {
        hasVisitedModule.value = true
        tryCompleteSubstep('onb-1', 'onb-1-1')
      }
    },
  )

  // onb-1-2: first visit to the Settings page (/settings).
  const hasVisitedSettings = ref(false)
  watch(
    () => route.path,
    (path) => {
      if (hasVisitedSettings.value) return
      if (path.startsWith('/settings')) {
        hasVisitedSettings.value = true
        tryCompleteSubstep('onb-1', 'onb-1-2')
      }
    },
  )

  // onb-1-3: first time the search bar is opened.
  const hasOpenedSearch = ref(false)
  watch(searchOpen, (isOpen) => {
    if (hasOpenedSearch.value || !isOpen) return
    hasOpenedSearch.value = true
    tryCompleteSubstep('onb-1', 'onb-1-3')
  })
}
