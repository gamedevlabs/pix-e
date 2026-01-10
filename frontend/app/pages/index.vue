<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'

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
        console.log('Duplicate project:', projectId)
        // TODO: Implement duplicate functionality
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
</script>

<template>
  <UContainer class="py-10 space-y-10">
    <!-- Hero Section -->
    <section class="text-center">
      <h1 class="text-4xl font-bold mb-4">
        Welcome <span v-if="isLoggedIn" class="text-primary">{{ username }}</span> 🎉
      </h1>
      <p class="text-gray-500 dark:text-gray-400 mb-6">
        <span class="text-primary font-semibold">pix:e</span> enables you to design games with
        research.
      </p>
    </section>

    <!-- Projects Section -->
    <section>
      <h2 class="text-3xl font-bold mb-6">Projects</h2>

      <!-- Project Cards -->
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
            class="hover:shadow-lg transition cursor-pointer h-full flex items-center justify-center min-h-[200px]"
            :class="{ 'opacity-75': project.requiresAuth && !isLoggedIn }"
            role="button"
            tabindex="0"
            @click="!(project.requiresAuth && !isLoggedIn) && handleCardClick(project)"
            @keydown.enter="!(project.requiresAuth && !isLoggedIn) && handleCardClick(project)"
          >
            <div
              class="flex flex-col items-center justify-center py-8 text-gray-400 dark:text-gray-500"
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
              class="hover:shadow-lg transition cursor-pointer h-full"
              :class="{ 'opacity-75': project.requiresAuth && !isLoggedIn }"
              :ui="{ footer: 'py-2 px-6 border-t-0', root: 'h-full flex flex-col', body: 'flex-1' }"
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
                      size="md"
                    />
                    <UAvatar
                      v-else
                      :alt="project.label"
                      size="md"
                      :text="project.initials || 'PR'"
                    />
                    <h2 class="font-semibold text-lg truncate">{{ project.label }}</h2>
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
    </section>

    <!-- Standalone Modules Section -->
    <section class="mt-16">
      <h2 class="text-2xl font-bold mb-6">Standalone Modules</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="module in standaloneModules"
          :key="module.id"
          class="relative"
          role="button"
          tabindex="0"
          @click.capture="handleCardClick(module)"
          @keydown.enter="handleCardClick(module)"
        >
          <!-- Module Card -->
          <UCard class="hover:shadow-lg transition cursor-pointer h-full">
            <template #header>
              <div class="flex items-center gap-3">
                <UIcon v-if="module.icon" :name="module.icon" class="text-2xl" />
                <h2 class="font-semibold text-lg">{{ module.label }}</h2>
              </div>
            </template>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              {{ module.description }}
            </p>
          </UCard>
        </div>
      </div>
    </section>
  </UContainer>
</template>

<style scoped></style>
