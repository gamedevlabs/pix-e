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
    // Clean up URL
    router.replace({ query: {} })
  } else if (error === 'project-not-found') {
    toast.add({
      title: 'Project Not Found',
      description: `Project "${projectId}" does not exist`,
      color: 'error',
      icon: 'i-lucide-alert-triangle',
      timeout: 5000,
    })
    // Clean up URL
    router.replace({ query: {} })
  }
})

const { switchProject, projects, deleteProject } = useProjectHandler()

const username = computed(() => authentication.user.value?.username || 'Guest')
const isLoggedIn = computed(() => authentication.isLoggedIn.value)

// Helper function to get initials from project name
const getInitials = (name: string): string => {
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

// Helper function to format relative time
const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  if (diffDays < 30)
    return `${Math.floor(diffDays / 7)} week${Math.floor(diffDays / 7) > 1 ? 's' : ''} ago`
  if (diffDays < 365)
    return `${Math.floor(diffDays / 30)} month${Math.floor(diffDays / 30) > 1 ? 's' : ''} ago`
  return `${Math.floor(diffDays / 365)} year${Math.floor(diffDays / 365) > 1 ? 's' : ''} ago`
}

// Project cards - dynamically generated from the project handler
const projectCards = computed<Card[]>(() => {
  // Copy and sort projects by updated_at descending (most recently edited first)
  const list = (projects?.value ?? []).slice().sort((a, b) => {
    const ta = new Date(a.updated_at).getTime()
    const tb = new Date(b.updated_at).getTime()
    return tb - ta
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

  // Always append the 'Create New Project' card at the end
  mapped.push({
    id: 'create-project',
    label: 'Create New Project',
    description: 'Create your new project here',
    requiresAuth: true,
    isCreateCard: true,
    initials: 'NP',
    action: async () => {
      await router.push('/create')
    },
  })

  return mapped
})

// Dropdown menu items for project actions
const getProjectMenuItems = (projectId: string): DropdownMenuItem[][] => [
  [
    {
      label: 'Edit',
      icon: 'i-lucide-pencil',
      onSelect: () => {
        router.push(`/edit?id=${projectId}`)
      },
    },
    {
      label: 'Duplicate',
      icon: 'i-lucide-copy',
      onSelect: () => {
        router.push(`/create?duplicate=${projectId}`)
      },
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

// Standalone modules - modules that don't require a project
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
  // Prevent action if clicking on dropdown menu
  if (event?.target && (event.target as HTMLElement).closest('.project-menu-button')) {
    return
  }

  if (card.requiresAuth && !isLoggedIn.value) {
    router.push('/login')
    return
  }

  // Execute the card's action (e.g. switchProject or route to create page)
  if (card.action) {
    await card.action()
  }

  // Let individual actions handle routing (switchProject already navigates to dashboard).
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
  <UContainer class="py-10 space-y-10">
    <!-- Hero Section -->
    <section class="text-center max-w-4xl mx-auto">
      <h1
        class="text-5xl font-bold mb-4 bg-linear-to-r from-primary-500 to-primary-700 bg-clip-text text-transparent"
      >
        Welcome <span v-if="isLoggedIn">{{ username }}</span> 🎉
      </h1>
      <p class="text-lg text-gray-600 dark:text-gray-400 mb-6">
        <span class="text-primary font-semibold">pix:e</span> enables you to design games with
        research-backed player experience tools.
      </p>
    </section>

    <!-- Projects Section with Side Panels -->
    <section>
      <h2 class="text-3xl font-bold mb-6 text-center">Your Projects</h2>

      <div class="grid grid-cols-1 xl:grid-cols-[300px_1fr_300px] gap-12">
        <!-- Left Side Panel - Quick Stats -->
        <aside class="hidden xl:block space-y-4">
          <QuickStatsCard :total="projectStats.total" :recent="projectStats.recent" />
          <AiInsightsCard />
        </aside>

        <!-- Center - Project Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div v-for="project in projectCards" :key="project.id" class="relative">
            <!-- Login Overlay for auth-required projects -->
            <div
              v-if="project.requiresAuth && !isLoggedIn"
              class="absolute inset-0 bg-black/60 dark:bg-black/70 backdrop-blur-sm z-10 rounded-lg flex items-center justify-center"
            >
              <UButton
                label="Login"
                icon="i-lucide-log-in"
                color="primary"
                size="lg"
                @click="router.push('/login')"
              />
            </div>

            <!-- Create New Project Card (centered icon style) -->
            <UCard
              v-if="project.isCreateCard"
              class="hover:shadow-2xl hover:scale-[1.025] transition-all cursor-pointer h-full flex items-center justify-center min-h-50 border-2 border-dashed border-gray-200 dark:border-gray-700 hover:border-primary bg-white dark:bg-gray-900"
              :class="{ 'opacity-75': project.requiresAuth && !isLoggedIn }"
              role="button"
              tabindex="0"
              @click="!(project.requiresAuth && !isLoggedIn) && handleCardClick(project)"
              @keydown.enter="!(project.requiresAuth && !isLoggedIn) && handleCardClick(project)"
            >
              <div
                class="flex flex-col items-center justify-center py-8 text-gray-400 dark:text-gray-500 hover:text-primary transition-colors"
              >
                <UIcon name="i-heroicons-plus-circle" class="text-6xl mb-2" />
                <p class="text-sm font-medium">New Project</p>
              </div>
            </UCard>

            <!-- Regular Project Card with Context Menu -->
            <UContextMenu
              v-else
              :items="getProjectMenuItems(project.id)"
              :disabled="project.requiresAuth && !isLoggedIn"
              class="h-full"
            >
              <UCard
                class="hover:shadow-2xl hover:scale-[1.025] transition-all cursor-pointer h-full bg-gradient-to-br from-white to-gray-50 dark:from-gray-900 dark:to-gray-800 border-2 border-gray-200 dark:border-gray-700 hover:border-primary dark:hover:border-primary hover:from-primary-50 hover:to-white dark:hover:from-primary-950/30 dark:hover:to-gray-900"
                :class="{ 'opacity-75': project.requiresAuth && !isLoggedIn }"
                :ui="{
                  footer: 'py-2 px-6 border-t-0',
                  root: 'h-full flex flex-col',
                  body: 'flex-1',
                }"
                role="button"
                tabindex="0"
                @click="!(project.requiresAuth && !isLoggedIn) && handleCardClick(project, $event)"
                @keydown.enter="!(project.requiresAuth && !isLoggedIn) && handleCardClick(project)"
              >
                <template #header>
                  <div class="flex items-center justify-between gap-3">
                    <div class="flex items-center gap-3 flex-1 min-w-0">
                      <!-- Avatar with icon or initials -->
                      <UAvatar
                        v-if="project.icon"
                        :src="project.icon"
                        :alt="project.label"
                        size="lg"
                      />
                      <UAvatar
                        v-else
                        :alt="project.label"
                        size="lg"
                        :text="project.initials || 'PR'"
                      />
                      <h2 class="font-bold text-xl truncate">{{ project.label }}</h2>
                    </div>

                    <!-- 3-dot menu button -->
                    <UDropdownMenu
                      :items="getProjectMenuItems(project.id)"
                      class="project-menu-button"
                    >
                      <UButton
                        icon="i-lucide-more-vertical"
                        color="neutral"
                        variant="ghost"
                        size="sm"
                        @click.stop
                      />
                    </UDropdownMenu>
                  </div>
                </template>

                <!-- Short description in body -->
                <p v-if="project.description" class="text-sm text-gray-600 dark:text-gray-400">
                  {{ project.description }}
                </p>
                <p v-else class="text-sm text-gray-400 dark:text-gray-500 italic">No description</p>

                <template #footer>
                  <!-- Last edited timestamp - bottom left, smaller -->
                  <div class="text-[10px] text-gray-400 dark:text-gray-500 flex items-center gap-1">
                    <UIcon name="i-lucide-clock" class="inline-block size-2.5" />
                    Last edited {{ formatRelativeTime(project.updatedAt!) }}
                  </div>
                </template>
              </UCard>
            </UContextMenu>
          </div>
        </div>

        <!-- Right Side Panel - Recent Activity & Help -->
        <aside class="hidden xl:block space-y-4">
          <WhatsNewCard />
          <ContinueWorkflowCard />
          <NeedHelpCard />
        </aside>
      </div>
    </section>

    <!-- Standalone Modules Section - Visually Distinct -->
    <section class="mt-20">
      <div class="text-center mb-8">
        <UBadge color="primary" variant="subtle" size="lg" class="mb-3">
          <UIcon name="i-lucide-puzzle" class="mr-1" />
          Standalone Tools
        </UBadge>
        <h2 class="text-3xl font-bold mb-2">Additional Modules</h2>
        <p class="text-gray-600 dark:text-gray-400">
          Specialized tools that work independently from your projects
        </p>
      </div>

      <div class="max-w-4xl mx-auto">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div
            v-for="module in standaloneModules"
            :key="module.id"
            class="relative"
            role="button"
            tabindex="0"
            @click.capture="handleCardClick(module)"
            @keydown.enter="handleCardClick(module)"
          >
            <!-- Module Card - Different styling -->
            <UCard
              class="hover:shadow-2xl hover:scale-105 transition-all cursor-pointer h-full border-2 border-primary/20 hover:border-primary bg-linear-to-br from-primary-50 to-white dark:from-primary-950 dark:to-gray-900"
              :ui="{ body: 'space-y-3' }"
            >
              <template #header>
                <div class="flex items-center gap-3">
                  <div class="p-2 bg-primary/10 rounded-lg">
                    <UIcon v-if="module.icon" :name="module.icon" class="text-3xl text-primary" />
                  </div>
                  <div>
                    <h2 class="font-bold text-xl">{{ module.label }}</h2>
                    <UBadge color="primary" variant="subtle" size="xs">Independent Module</UBadge>
                  </div>
                </div>
              </template>
              <p class="text-sm text-gray-700 dark:text-gray-300">
                {{ module.description }}
              </p>
              <div class="flex items-center gap-2 text-xs text-primary font-medium pt-2">
                <span>Launch Module</span>
                <UIcon name="i-lucide-arrow-right" />
              </div>
            </UCard>
          </div>
        </div>
      </div>
    </section>
  </UContainer>
</template>

<style scoped></style>
