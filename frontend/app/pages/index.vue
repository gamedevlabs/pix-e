<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import type { WorkflowInstance } from '~/mock_data/mock_workflow'

// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
definePageMeta({
  pageConfig: {
    type: 'public',
    showSidebar: false,
    title: 'Projects',
  },
})
// ============================================================================

interface Card {
  id: string
  label: string
  description?: string
  icon?: string
  requiresAuth?: boolean
  isCreateCard?: boolean
  action?: () => Promise<void> | void
  updatedAt?: string
  initials?: string
}

const authentication = useAuthentication()
await authentication.checkAuthentication()

const router = useRouter()
const route = useRoute()
const toast = useToast()

// Handle error notifications from middleware redirects
onMounted(() => {
  const error = route.query.error as string | undefined
  const projectId = route.query.projectId as string | undefined
  const message = route.query.message as string | undefined

  if (error === 'no-project') {
    toast.add({
      title: 'No Project Selected',
      description: message || 'Please select a project to use this module',
      color: 'warning',
      icon: 'i-lucide-alert-circle',
    })
    router.replace({ query: {} })
  } else if (error === 'project-not-found') {
    toast.add({
      title: 'Project Not Found',
      description: `Project "${projectId}" does not exist`,
      color: 'error',
      icon: 'i-lucide-alert-triangle',
    })
    router.replace({ query: {} })
  }
})

const { switchProject, projects, deleteProject } = useProjectHandler()
const { loadForUser } = useProjectWorkflow()

const username = computed(() => authentication.user.value?.username || 'Guest')
const isLoggedIn = computed(() => authentication.isLoggedIn.value)

// Load the user-level onboarding workflow when not logged in
const projectWorkflow = useProjectWorkflow()
const overallProgress = computed(() => projectWorkflow.getProgress.value || 0)
const activeWorkflowTitle = computed(() => {
  const list = (projectWorkflow.workflows?.value || []) as WorkflowInstance[]
  const activeId = projectWorkflow.activeWorkflowId?.value
  const w = list.find((x) => x.id === activeId)
  return w?.meta?.title || 'Getting Started'
})

onMounted(async () => {
  if (!isLoggedIn.value) {
    await loadForUser()
  }
})

watch(isLoggedIn, async (loggedIn) => {
  if (!loggedIn) {
    await loadForUser()
  }
})

const getInitials = (name: string): string =>
  name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

// Project cards - sorted by most recently edited
const projectCards = computed<Card[]>(() => {
  if (!isLoggedIn.value) return []

  const list = (projects?.value ?? []).slice().sort((a, b) => {
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  })

  const mapped: Card[] = list.map((p) => ({
    id: p.id,
    label: p.name,
    description: p.shortDescription || undefined,
    icon: p.icon || undefined,
    initials: getInitials(p.name),
    updatedAt: p.updated_at,
    requiresAuth: true,
    isCreateCard: false,
    action: async () => {
      await switchProject(p.id)
    },
  }))

  // No longer append the create card here — empty state handles it
  return mapped
})

// Dropdown menu items for project actions
const getProjectMenuItems = (projectId: string): DropdownMenuItem[][] => [
  [
    {
      label: 'Edit',
      icon: 'i-lucide-pencil',
      onSelect: () => router.push(`/edit?id=${projectId}`),
    },
    {
      label: 'Duplicate',
      icon: 'i-lucide-copy',
      onSelect: () => router.push(`/create?duplicate=${projectId}`),
    },
  ],
  [
    {
      label: 'Delete',
      icon: 'i-lucide-trash',
      color: 'error' as const,
      onSelect: async () => {
        if (confirm('Are you sure you want to delete this project?')) {
          await deleteProject(projectId)
        }
      },
    },
  ],
]

// Standalone modules
const standaloneModules = ref<Card[]>([
  {
    id: 'movie-script',
    label: 'Movie Script Evaluator',
    description:
      'Evaluate movie scripts through LLMs based on available assets for virtual production.',
    icon: 'i-lucide-film',
    requiresAuth: false,
    action: () => { router.push('/movie-script-evaluator') },
  },
])

const handleCardClick = async (card: Card, event?: MouseEvent) => {
  if (event?.target && (event.target as HTMLElement).closest('.project-menu-button')) return

  if (card.requiresAuth && !isLoggedIn.value) {
    router.push('/login')
    return
  }

  if (card.action) {
    await card.action()
  }
}

// Quick stats
const projectStats = computed(() => ({
  total: projects?.value?.length || 0,
  recent:
    projects?.value?.filter((p) => {
      const updated = new Date(p.updated_at)
      const weekAgo = new Date()
      weekAgo.setDate(weekAgo.getDate() - 7)
      return updated > weekAgo
    }).length || 0,
}))
</script>

<template>
  <div class="max-w-screen-2xl mx-auto w-full px-6 lg:px-10 xl:px-14 py-10 space-y-14">

    <!-- Workflow button + slideover for logged-out users -->
    <template v-if="!isLoggedIn">
      <div class="fixed left-4 bottom-4 z-40 w-72 max-w-[calc(100vw-2rem)]">
        <WorkflowSlideOverButton :title="activeWorkflowTitle" :progress="overallProgress" />
      </div>
      <WorkflowSlideover />
    </template>

    <!-- ─── Hero ─────────────────────────────────────────────────────────── -->
    <section class="text-center space-y-3 max-w-2xl mx-auto">
      <h1 class="text-4xl xl:text-5xl font-bold tracking-tight bg-linear-to-br from-primary-500 to-primary-700 bg-clip-text text-transparent">
        Welcome<span v-if="isLoggedIn">, {{ username }}</span> 👋
      </h1>
      <p class="text-base text-gray-500 dark:text-gray-400 max-w-lg mx-auto">
        <span class="text-primary font-semibold">pix:e</span> enables you to design games with
        research-backed player experience tools.
      </p>
    </section>

    <!-- ─── Main 3-col layout ─────────────────────────────────────────────── -->
    <div class="grid grid-cols-1 xl:grid-cols-[260px_1fr_260px] gap-6 items-start">

      <!-- Left Side Panel -->
      <aside class="hidden xl:flex flex-col gap-4">
        <QuickStatsCard :total="projectStats.total" :recent="projectStats.recent" />
        <AiInsightsCard />
      </aside>

      <!-- ─── CENTER COLUMN ─────────────────────────────────────────────── -->
      <div class="space-y-12 min-w-0">

        <!-- Projects section header -->
        <div class="space-y-5">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="h-6 w-1 rounded-full bg-primary" />
              <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">Your Projects</h2>
            </div>
            <UButton
              v-if="isLoggedIn"
              label="New Project"
              icon="i-lucide-plus"
              color="primary"
              variant="soft"
              size="md"
              @click="router.push('/create')"
            />
          </div>

          <!-- Login required state -->
          <UCard
            v-if="!isLoggedIn"
            class="border-2 border-dashed border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
          >
            <div class="py-16 flex flex-col items-center gap-6 text-center">
              <div class="rounded-full bg-gray-100 dark:bg-gray-800 p-5 aspect-square flex items-center justify-center">
                <UIcon name="i-lucide-lock" class="size-10 text-gray-400 dark:text-gray-500" />
              </div>
              <div class="space-y-1.5 max-w-sm">
                <h3 class="text-xl font-bold text-gray-900 dark:text-gray-100">Login Required</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Please log in to view and manage your projects. Create a free account to get
                  started with pix:e.
                </p>
              </div>
              <div class="flex gap-3">
                <UButton
                  label="Login"
                  icon="i-lucide-log-in"
                  color="primary"
                  size="md"
                  @click="router.push('/login')"
                />
                <UButton
                  label="Register"
                  icon="i-lucide-user-plus"
                  color="neutral"
                  variant="outline"
                  size="md"
                  @click="router.push('/login')"
                />
              </div>
            </div>
          </UCard>

          <!-- Empty state – logged in but no projects yet -->
          <div
            v-else-if="projectCards.length === 0"
            class="flex flex-col items-center gap-4 py-14 text-center"
          >
            <p class="text-base text-gray-500 dark:text-gray-400">
              You don't have any projects yet. Create your first one to get started with pix:e.
            </p>
            <UButton
              label="New Project"
              icon="i-lucide-plus"
              color="primary"
              variant="soft"
              size="md"
              @click="router.push('/create')"
            />
          </div>

          <!-- Project cards grid -->
          <div
            v-else
            class="grid grid-cols-1 sm:grid-cols-2 2xl:grid-cols-3 gap-4"
          >
            <LandingProjectCard
              v-for="project in projectCards"
              :key="project.id"
              :id="project.id"
              :label="project.label"
              :description="project.description"
              :icon="project.icon"
              :initials="project.initials"
              :updated-at="project.updatedAt"
              :is-create-card="project.isCreateCard"
              :menu-items="project.isCreateCard ? [] : getProjectMenuItems(project.id)"
              @click="handleCardClick(project, $event)"
            />
          </div>
        </div>

        <!-- ─── Standalone Modules ──────────────────────────────────────── -->
        <div class="space-y-5">
          <div class="flex items-center gap-3">
            <div class="h-6 w-1 rounded-full bg-secondary-500" />
            <div>
              <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">Additional Modules</h2>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Standalone tools that work independently from your projects
              </p>
            </div>
            <UBadge color="neutral" variant="soft" size="sm" class="ml-2 self-start mt-0.5">
              <UIcon name="i-lucide-puzzle" class="mr-1 size-3" />
              Standalone
            </UBadge>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <UCard
              v-for="module in standaloneModules"
              :key="module.id"
              class="group border border-primary-200 dark:border-primary-900/50 bg-linear-to-br from-primary-50 to-white dark:from-primary-950/40 dark:to-gray-900 hover:shadow-md hover:border-primary hover:-translate-y-0.5 transition-all duration-200 cursor-pointer"
              :ui="{
                header: 'px-4 py-3',
                body: 'px-4 py-3 space-y-3',
              }"
              role="button"
              tabindex="0"
              @click="handleCardClick(module)"
              @keydown.enter="handleCardClick(module)"
            >
              <template #header>
                <div class="flex items-center gap-3">
                  <div class="rounded-lg p-2 bg-primary/10 group-hover:bg-primary/20 transition-colors shrink-0">
                    <UIcon v-if="module.icon" :name="module.icon" class="size-5 text-primary" />
                  </div>
                  <div class="min-w-0">
                    <p class="font-semibold text-sm text-gray-900 dark:text-gray-100 truncate">
                      {{ module.label }}
                    </p>
                    <UBadge color="primary" variant="subtle" size="xs">Independent</UBadge>
                  </div>
                </div>
              </template>
              <p class="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                {{ module.description }}
              </p>
              <div class="flex items-center gap-1.5 text-xs text-primary font-medium pt-1">
                <span>Launch</span>
                <UIcon name="i-lucide-arrow-right" class="size-3 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </UCard>
          </div>
        </div>

      </div>
      <!-- END CENTER COLUMN -->

      <!-- Right Side Panel -->
      <aside class="hidden xl:flex flex-col gap-4">
        <ContinueWorkflowCard />
        <WhatsNewCard />
        <NeedHelpCard />
      </aside>

    </div>

  </div>
</template>

<style scoped></style>
