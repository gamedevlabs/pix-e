<script setup lang="ts">
import OnboardingSlideOverButton from '~/components/OnboardingSlideOverButton.vue'

/**
 * Single source of truth for the workflow trigger button + its slideover host.
 * Used in two places with the same visual, just different wrappers:
 *
 *  - `mode="sidebar"`  — inline in the sidebar footer. Always rendered. Pass
 *                        `collapsed` for the icon-only variant. Title/progress
 *                        follow the currently viewed/active workflow.
 *  - `mode="floating"` — fixed bottom-left on pages that hide the sidebar
 *                        (landing + create). Renders only while the
 *                        "Getting Started" workflow is unfinished. Title/progress
 *                        always reflect Getting Started.
 */
interface Props {
  mode?: 'sidebar' | 'floating'
  collapsed?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'sidebar',
  collapsed: false,
})

const projectWorkflow = useProjectWorkflow()

// Floating mode is the only place that may render before the slideover's own
// watcher has loaded workflows (e.g. on the public landing page where the user
// isn't logged in). Make sure data is available so we can decide what to show.
onMounted(() => {
  if (props.mode === 'floating' && projectWorkflow.workflows.value.length === 0) {
    projectWorkflow.loadForUser()
  }
})

const gettingStarted = computed(() =>
  projectWorkflow.workflows.value.find((w) => w.id === 'user-onboarding'),
)

const shouldShow = computed(() => {
  if (props.mode === 'sidebar') return true
  const wf = gettingStarted.value
  return wf ? !wf.finished_at : false
})

const title = computed(() => {
  if (props.mode === 'floating') {
    return gettingStarted.value?.meta?.title || 'Getting Started'
  }
  const list = projectWorkflow.workflows.value
  const selectedId =
    projectWorkflow.viewedWorkflowId?.value ?? projectWorkflow.activeWorkflowId?.value
  const w = list.find((x) => x.id === selectedId)
  return w?.meta?.title || 'Onboarding Wizard'
})

const progress = computed(() => {
  if (props.mode === 'floating') {
    const wf = gettingStarted.value
    if (!wf) return 0
    const all = wf.steps.flatMap((s) => s.substeps)
    if (all.length === 0) return 0
    const completed = all.filter((ss) => ss.status === 'complete').length
    return Math.round((completed / all.length) * 100)
  }
  return projectWorkflow.getSelectedWorkflowProgress.value || 0
})
</script>

<template>
  <template v-if="shouldShow">
    <div
      v-if="mode === 'floating'"
      class="fixed left-4 bottom-4 z-40 w-72 max-w-[calc(100vw-2rem)]"
    >
      <OnboardingSlideOverButton :title="title" :progress="progress" />
    </div>

    <OnboardingSlideOverButton
      v-else
      :collapsed="collapsed"
      :title="title"
      :progress="progress"
    />

    <OnboardingSlideover :collapsed="mode === 'sidebar' ? collapsed : false" />
  </template>
</template>
