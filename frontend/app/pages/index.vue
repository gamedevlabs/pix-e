<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'

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

const username = computed(() => authentication.user.value?.username || 'Guest')
const isLoggedIn = computed(() => authentication.isLoggedIn.value)

// Onboarding wizard is only available when logged in, so we don't load workflows here

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
    action: () => {
      router.push('/movie-script-evaluator')
    },
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
</script>

<template>
  <div class="max-w-screen-2xl mx-auto w-full px-6 lg:px-10 xl:px-14 py-10 space-y-14">
    <!-- Onboarding wizard is only available when logged in -->
    <template v-if="isLoggedIn">
      <OnboardingSlideover />
    </template>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- LOGGED-OUT LAYOUT                                                   -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <template v-if="!isLoggedIn">
      <!-- ─── Hero ──────────────────────────────────────────────────────── -->
      <section class="text-center space-y-5 max-w-2xl mx-auto pt-6">
        <!-- Logo -->
        <div class="flex justify-center">
          <img src="/favicon.png" alt="pix:e logo" class="size-14 rounded-xl" />
        </div>

        <h1
          class="text-4xl xl:text-5xl font-bold tracking-tight text-gray-900 dark:text-gray-50 leading-tight"
        >
          Improve your player's experience<br />
          <span class="text-primary">with pix:e</span>
        </h1>

        <p class="text-base text-gray-500 dark:text-gray-400 max-w-lg mx-auto leading-relaxed">
          <span class="text-primary font-semibold">pix:e</span> helps you design, evaluate, and
          iterate on your game's player experience using research-backed methods.
        </p>

        <div class="flex flex-wrap items-center justify-center gap-3 pt-1">
          <UButton
            label="Get Started"
            icon="i-lucide-user-plus"
            color="primary"
            size="xl"
            @click="router.push('/login')"
          />
          <UButton
            label="Sign in"
            icon="i-lucide-log-in"
            color="neutral"
            variant="outline"
            size="xl"
            @click="router.push('/login')"
          />
        </div>
      </section>

      <!-- ─── Feature highlights ────────────────────────────────────────── -->
      <section class="space-y-6 max-w-5xl mx-auto">
        <div class="text-center space-y-1">
          <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">What's inside</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Tools to cover the full player experience design cycle
          </p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <UCard
            class="border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900"
            :ui="{ body: 'p-4' }"
          >
            <div class="flex items-start gap-3">
              <div class="rounded-lg p-2 bg-secondary-500/10 shrink-0 mt-0.5">
                <UIcon name="i-lucide-landmark" class="size-4 text-secondary-500" />
              </div>
              <div class="space-y-0.5 min-w-0">
                <p class="font-semibold text-sm text-gray-900 dark:text-gray-100">
                  Experience Pillars
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                  Map design decisions to validated player experience dimensions.
                </p>
              </div>
            </div>
          </UCard>

          <UCard
            class="border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900"
            :ui="{ body: 'p-4' }"
          >
            <div class="flex items-start gap-3">
              <div class="rounded-lg p-2 bg-success-500/10 shrink-0 mt-0.5">
                <UIcon
                  name="i-lucide-book-open"
                  class="size-4 text-success-600 dark:text-success-400"
                />
              </div>
              <div class="space-y-0.5 min-w-0">
                <p class="font-semibold text-sm text-gray-900 dark:text-gray-100">
                  Player Expectations
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                  Define what players expect from your game and track how your design meets it.
                </p>
              </div>
            </div>
          </UCard>

          <UCard
            class="border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900"
            :ui="{ body: 'p-4' }"
          >
            <div class="flex items-start gap-3">
              <div class="rounded-lg p-2 bg-primary/10 shrink-0 mt-0.5">
                <UIcon name="i-lucide-chart-no-axes-gantt" class="size-4 text-primary" />
              </div>
              <div class="space-y-0.5 min-w-0">
                <p class="font-semibold text-sm text-gray-900 dark:text-gray-100">
                  Player Experience
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                  Evaluate and iterate on the overall experience your game delivers.
                </p>
              </div>
            </div>
          </UCard>

          <UCard
            class="border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900"
            :ui="{ body: 'p-4' }"
          >
            <div class="flex items-start gap-3">
              <div class="rounded-lg p-2 bg-secondary-500/10 shrink-0 mt-0.5">
                <UIcon name="i-lucide-film" class="size-4 text-secondary-500" />
              </div>
              <div class="space-y-0.5 min-w-0">
                <p class="font-semibold text-sm text-gray-900 dark:text-gray-100">
                  Script Evaluator
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                  Evaluate narrative scripts via LLMs for virtual production readiness.
                </p>
              </div>
            </div>
          </UCard>
        </div>
      </section>

      <!-- ─── Standalone Modules (available without login) ─────────────── -->
      <section class="space-y-5 max-w-5xl mx-auto">
        <div class="flex items-center gap-3">
          <div class="h-6 w-1 rounded-full bg-secondary-500" />
          <div>
            <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">
              Try without an account
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              These tools are available immediately — no login required
            </p>
          </div>
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
                <div
                  class="rounded-lg p-2 bg-primary/10 group-hover:bg-primary/20 transition-colors shrink-0"
                >
                  <UIcon v-if="module.icon" :name="module.icon" class="size-5 text-primary" />
                </div>
                <div class="min-w-0">
                  <p class="font-semibold text-sm text-gray-900 dark:text-gray-100 truncate">
                    {{ module.label }}
                  </p>
                  <UBadge color="success" variant="subtle" size="xs">No login needed</UBadge>
                </div>
              </div>
            </template>
            <p class="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
              {{ module.description }}
            </p>
            <div class="flex items-center gap-1.5 text-xs text-primary font-medium pt-1">
              <span>Launch</span>
              <UIcon
                name="i-lucide-arrow-right"
                class="size-3 group-hover:translate-x-0.5 transition-transform"
              />
            </div>
          </UCard>
        </div>
      </section>

      <!-- ─── Bottom sign-up nudge ──────────────────────────────────────── -->
      <section class="max-w-5xl mx-auto">
        <UCard
          class="border border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900"
          :ui="{ body: 'px-6 py-6' }"
        >
          <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="space-y-1 text-center sm:text-left">
              <p class="font-semibold text-gray-900 dark:text-gray-100">
                Create an account to get started
              </p>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Sign up to manage projects and access all tools.
              </p>
            </div>
            <div class="flex gap-3 shrink-0">
              <UButton
                label="Create account"
                icon="i-lucide-user-plus"
                color="primary"
                size="md"
                @click="router.push('/login')"
              />
              <UButton
                label="Sign in"
                icon="i-lucide-log-in"
                color="neutral"
                variant="outline"
                size="md"
                @click="router.push('/login')"
              />
            </div>
          </div>
        </UCard>
      </section>
    </template>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- LOGGED-IN LAYOUT                                                    -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <template v-else>
      <div class="max-w-7xl mx-auto space-y-12">
        <!-- ─── Header ────────────────────────────────────────────────────── -->
        <div
          class="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-6"
        >
          <div class="space-y-1">
            <h1 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
              Projects
            </h1>
            <p class="text-gray-500 dark:text-gray-400">
              Welcome back, {{ username }}. Select a project to continue.
            </p>
          </div>

          <div class="flex gap-3">
            <UButton
              label="New Project"
              icon="i-lucide-plus"
              color="primary"
              size="md"
              @click="router.push('/create')"
            />
          </div>
        </div>

        <!-- ─── Projects Section ────────────────────────────────────────── -->
        <div class="space-y-6">
          <!-- Empty state -->
          <div
            v-if="projectCards.length === 0"
            class="flex flex-col items-center justify-center gap-4 py-20 text-center border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-xl"
          >
            <div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-full">
              <UIcon name="i-lucide-folder-open" class="size-8 text-gray-400" />
            </div>
            <div class="max-w-md space-y-1">
              <h3 class="font-semibold text-gray-900 dark:text-white">No projects yet</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Create your first project to get started with pix:e's player experience tools.
              </p>
            </div>
            <UButton
              label="Create Project"
              icon="i-lucide-plus"
              color="primary"
              variant="solid"
              @click="router.push('/create')"
            />
          </div>

          <!-- Project Cards Grid -->
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <LandingProjectCard
              v-for="project in projectCards"
              :id="project.id"
              :key="project.id"
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
        <div class="space-y-6 pt-2">
          <div class="flex items-center gap-3">
            <div class="h-6 w-1 rounded-full bg-secondary-500" />
            <div>
              <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">Additional Modules</h2>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Standalone tools that work independently from your projects
              </p>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <UCard
              v-for="module in standaloneModules"
              :key="module.id"
              class="group border border-primary-100 dark:border-primary-900/40 bg-white dark:bg-gray-900 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-md hover:-translate-y-1 transition-all duration-200 cursor-pointer flex flex-col h-full rounded-xl overflow-hidden"
              :ui="{
                body: 'p-5 flex-1 flex flex-col gap-4',
                header: '',
                footer: ''
              }"
              role="button"
              tabindex="0"
              @click="handleCardClick(module)"
              @keydown.enter="handleCardClick(module)"
            >
              <!-- Top -->
              <div class="flex items-start justify-between gap-3">
                 <div class="flex items-center gap-3 min-w-0">
                    <div class="rounded-lg p-2 bg-primary-50 text-primary-600 dark:bg-primary-950/40 dark:text-primary-400 shrink-0">
                       <UIcon v-if="module.icon" :name="module.icon" class="size-5" />
                    </div>
                    <div>
                      <h3 class="font-semibold text-base text-gray-900 dark:text-white truncate">
                        {{ module.label }}
                      </h3>
                      <p class="text-[10px] items-center font-medium text-primary-600 dark:text-primary-400 uppercase tracking-wider">Independent Module</p>
                    </div>
                 </div>
              </div>

              <!-- Content -->
              <p class="text-sm text-gray-500 dark:text-gray-400 leading-relaxed flex-1 line-clamp-2">
                {{ module.description }}
              </p>

              <!-- Bottom -->
              <div class="flex items-center justify-end pt-2 border-t border-gray-100 dark:border-gray-800/50 mt-auto">
                <div class="flex items-center gap-1 text-xs font-medium text-primary-600 dark:text-primary-400 opacity-0 group-hover:opacity-100 transition-all duration-200 transform translate-x-1 group-hover:translate-x-0">
                  <span>Launch Tool</span>
                  <UIcon
                    name="i-lucide-arrow-right"
                    class="size-3"
                  />
                </div>
              </div>
            </UCard>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped></style>
