<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
      <!-- Hero Section with Analytics -->
      <div
        class="relative overflow-hidden bg-gradient-to-br from-primary-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900/20 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm"
      >
        <div class="absolute inset-0 bg-grid-gray-900/[0.04] dark:bg-grid-white/[0.02]" />
        <div class="relative p-8">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h1
                class="text-4xl font-bold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent"
              >
                My Moodboards
              </h1>
              <p class="text-lg text-gray-600 dark:text-gray-400 mt-2">
                Create, manage, and share your AI-generated moodboards
              </p>
            </div>
            <div class="flex gap-4">
              <UButton
                icon="i-heroicons-arrow-path-20-solid"
                color="neutral"
                variant="solid"
                size="lg"
                :loading="isRefreshing"
                @click="refreshAll"
              >
                Refresh
              </UButton>
              <UButton
                icon="i-heroicons-plus-20-solid"
                size="lg"
                class="bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700"
                @click="createNewMoodboard"
              >
                Create New Moodboard
              </UButton>
            </div>
          </div>
        </div>
      </div>

      <!-- Analytics Dashboard -->
      <section v-if="analytics" class="analytics-section">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-semibold text-gray-900 dark:text-white">Dashboard Overview</h2>
          <UButton
            variant="ghost"
            size="sm"
            icon="i-heroicons-arrow-path-20-solid"
            class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            @click="loadAnalytics"
          >
            Refresh
          </UButton>
        </div>

        <!-- Loading skeleton for analytics -->
        <div
          v-if="!analytics || loadingAnalytics"
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          <div
            v-for="i in 4"
            :key="i"
            class="bg-gray-200 dark:bg-gray-700 rounded-lg h-32 animate-pulse flex items-center justify-center"
          >
            <UIcon
              v-if="loadingAnalytics"
              name="i-heroicons-arrow-path-20-solid"
              class="w-8 h-8 text-gray-400 animate-spin"
            />
          </div>
        </div>

        <!-- Analytics cards -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <UCard
            class="text-center bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800/30"
          >
            <div>
              <div class="flex items-center justify-center mb-2">
                <UIcon
                  name="i-heroicons-squares-2x2-20-solid"
                  class="w-8 h-8 text-blue-600 dark:text-blue-400"
                />
              </div>
              <div class="text-3xl font-bold text-blue-700 dark:text-blue-300">
                {{ analytics.total_moodboards }}
              </div>
              <div class="text-sm text-blue-600 dark:text-blue-400 mt-1">Total Moodboards</div>
              <div
                v-if="analytics.completed_moodboards > 0"
                class="text-xs text-blue-500 dark:text-blue-500 mt-1"
              >
                {{ analytics.completed_moodboards }} completed
              </div>
            </div>
          </UCard>

          <UCard
            class="text-center bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800/30"
          >
            <div>
              <div class="flex items-center justify-center mb-2">
                <UIcon
                  name="i-heroicons-photo-20-solid"
                  class="w-8 h-8 text-green-600 dark:text-green-400"
                />
              </div>
              <div class="text-3xl font-bold text-green-700 dark:text-green-300">
                {{ analytics.total_images }}
              </div>
              <div class="text-sm text-green-600 dark:text-green-400 mt-1">
                Images in Moodboards
              </div>
              <div
                v-if="analytics.avg_images_per_moodboard > 0"
                class="text-xs text-green-500 dark:text-green-500 mt-1"
              >
                {{ Math.round(analytics.avg_images_per_moodboard) }} avg per board
              </div>
            </div>
          </UCard>

          <UCard
            class="text-center bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200 dark:border-purple-800/30"
          >
            <div>
              <div class="flex items-center justify-center mb-2">
                <UIcon
                  name="i-heroicons-globe-alt-20-solid"
                  class="w-8 h-8 text-purple-600 dark:text-purple-400"
                />
              </div>
              <div class="text-3xl font-bold text-purple-700 dark:text-purple-300">
                {{ analytics.public_moodboards }}
              </div>
              <div class="text-sm text-purple-600 dark:text-purple-400 mt-1">Public Moodboards</div>
            </div>
          </UCard>

          <UCard
            class="text-center bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200 dark:border-orange-800/30"
          >
            <div>
              <div class="flex items-center justify-center mb-2">
                <UIcon
                  name="i-heroicons-clock-20-solid"
                  class="w-8 h-8 text-orange-600 dark:text-orange-400"
                />
              </div>
              <div class="text-3xl font-bold text-orange-700 dark:text-orange-300">
                {{ analytics.recent_moodboards }}
              </div>
              <div class="text-sm text-orange-600 dark:text-orange-400 mt-1">Recent (30 days)</div>
            </div>
          </UCard>
        </div>
      </section>

      <!-- Enhanced Filters and Search Section -->
      <div
        class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm"
      >
        <div class="flex flex-col md:flex-row gap-4 items-start md:items-center">
          <!-- Search Input -->
          <div class="flex-1 max-w-md">
            <UInput
              v-model="searchQuery"
              placeholder="Search moodboards..."
              icon="i-heroicons-magnifying-glass-20-solid"
              size="lg"
              class="w-full"
            />
          </div>

          <!-- Filters Row -->
          <div class="flex flex-wrap gap-4 items-center">
            <!-- Status Multi-select -->
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
                >Status:</span
              >
              <USelectMenu
                v-model="selectedStatuses"
                :items="statusOptions"
                multiple
                placeholder="All Statuses"
                class="w-48"
              />
            </div>

            <!-- Visibility Multi-select -->
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
                >Visibility:</span
              >
              <USelectMenu
                v-model="selectedVisibility"
                :items="visibilityOptions"
                multiple
                placeholder="All Types"
                class="w-40"
              />
            </div>

            <!-- Clear filters button -->
            <UButton
              v-if="hasActiveFilters"
              variant="ghost"
              size="sm"
              color="neutral"
              @click="clearFilters"
            >
              Clear Filters
            </UButton>

            <!-- Results counter -->
            <div class="text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">
              {{ totalCount }} total moodboards
            </div>
          </div>
        </div>
      </div>

      <!-- Enhanced UTabs with better styling -->
      <div
        class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden"
      >
        <UTabs :items="tabs" class="w-full">
          <template #my>
            <div class="p-6">
              <MoodboardTable
                :moodboards="filteredMoodboards"
                :loading="loading"
                :total-items="totalCount"
                :page-size="pageSize"
                :page="currentPage"
                empty-title="No moodboards found"
                empty-description="Create your first moodboard to get started"
                @action="handleMoodboardAction"
                @update:page="handlePageChange"
              />
            </div>
          </template>

          <template #shared>
            <div class="p-6">
              <MoodboardTable
                :moodboards="filteredSharedMoodboards"
                :loading="loadingShared"
                :total-items="sharedTotalCount"
                :page-size="pageSize"
                :page="sharedCurrentPage"
                empty-title="No shared moodboards"
                empty-description="Moodboards shared with you will appear here"
                @action="handleSharedMoodboardAction"
                @update:page="handleSharedPageChange"
              />
            </div>
          </template>

          <template #public>
            <div class="p-6">
              <MoodboardTable
                :moodboards="filteredPublicMoodboards"
                :loading="loadingPublic"
                :total-items="publicTotalCount"
                :page-size="pageSize"
                :page="publicCurrentPage"
                empty-title="No public moodboards"
                empty-description="Public moodboards from the community will appear here"
                @action="handlePublicMoodboardAction"
                @update:page="handlePublicPageChange"
              />
            </div>
          </template>
        </UTabs>
      </div>

      <!-- Share Modal -->
      <ShareMoodboardModal
        v-model:open="showShareModal"
        :moodboard="
          selectedMoodboardForShare
            ? {
                id: String(selectedMoodboardForShare.id),
                title: selectedMoodboardForShare.title,
                description: selectedMoodboardForShare.description,
                is_public: selectedMoodboardForShare.is_public,
                images: selectedMoodboardForShare.images?.map((img: MoodboardImage) => ({
                  image_url: img.image_url,
                })),
              }
            : undefined
        "
        @share="handleShare"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useMoodboards } from '~/composables/useMoodboards'
import { useUsers } from '~/composables/useUsers'
import { useRouter } from '#app'
import { useToast } from '#imports'

definePageMeta({
  middleware: 'auth',
})

// TypeScript interfaces
interface MoodboardImage {
  image_url: string
  alt?: string
  is_selected?: boolean
}

interface Moodboard {
  id: number | string
  title: string
  description: string
  category: string
  status: string
  is_public: boolean
  tags: string
  images: MoodboardImage[]
  selected_image_count?: number
  created_at: string
  updated_at: string
  user?: {
    id: number
    username: string
  }
  permission?: 'view' | 'edit'
  shared_by?: {
    id: number
    username: string
  }
  shared_at?: string
}

interface Analytics {
  total_moodboards: number
  total_images: number
  public_moodboards: number
  recent_moodboards: number
  completed_moodboards: number
  avg_images_per_moodboard: number
}

const router = useRouter()
const toast = useToast()

const {
  moodboards,
  loading,
  fetchMoodboards,
  deleteMoodboard: deleteMoodboardApi,
  duplicateMoodboard: duplicateMoodboardApi,
  getSharedMoodboards,
  getPublicMoodboards,
  getMoodboardAnalytics,
  shareMoodboardWithMultipleUsers,
} = useMoodboards()

const { fetchUsers } = useUsers()

// State
const searchQuery = ref('')
const selectedStatuses = ref<string[]>([])
const selectedVisibility = ref<string[]>([])
const sharedMoodboards = ref<Moodboard[]>([])
const publicMoodboards = ref<Moodboard[]>([])
const analytics = ref<Analytics | null>(null)
const loadingShared = ref(false)
const loadingPublic = ref(false)
const loadingAnalytics = ref(false)

// Pagination state
const currentPage = ref(1)
const sharedCurrentPage = ref(1)
const publicCurrentPage = ref(1)
const pageSize = 20
const totalCount = ref(0)
const sharedTotalCount = ref(0)
const publicTotalCount = ref(0)

// Share modal state
const showShareModal = ref(false)
const selectedMoodboardForShare = ref<Moodboard | undefined>(undefined)
const shareSelectedUserIds = ref<number[]>([])
const sharePermission = ref('view')
const sharingInProgress = ref(false)
const availableUsers = ref<{ id: number; username: string }[]>([])
const loadingUsers = ref(false)

// Additional state variables needed for template
const isRefreshing = ref(false)

// Additional filter options and computed properties
const statusOptions = ref(['Draft', 'Completed'])
const visibilityOptions = ref(['Private', 'Public'])

// Computed for active filters
const hasActiveFilters = computed(() => {
  return (
    selectedStatuses.value.length > 0 ||
    selectedVisibility.value.length > 0 ||
    searchQuery.value.trim() !== ''
  )
})

// Tabs configuration
const tabs = [
  {
    label: 'My Moodboards',
    icon: 'i-heroicons-squares-2x2-20-solid',
    slot: 'my' as const,
  },
  {
    label: 'Shared with Me',
    icon: 'i-heroicons-share-20-solid',
    slot: 'shared' as const,
  },
  {
    label: 'Public Gallery',
    icon: 'i-heroicons-globe-alt-20-solid',
    slot: 'public' as const,
  },
]

// Filtered data for each table - now server-side filtering via query params
const filteredMoodboards = computed(() => moodboards.value || [])
const filteredSharedMoodboards = computed(() => sharedMoodboards.value || [])
const filteredPublicMoodboards = computed(() => publicMoodboards.value || [])

// Lifecycle hooks
onMounted(async () => {
  await loadData()
})

// Watch for filter changes and reset to page 1
watch([searchQuery, selectedStatuses, selectedVisibility], () => {
  currentPage.value = 1
  fetchMoodboardsPage(1)
})

// Data loading methods
const loadData = async () => {
  try {
    await Promise.all([
      fetchMoodboardsPage(currentPage.value),
      loadSharedMoodboards(),
      loadPublicMoodboards(),
      loadAnalytics(),
    ])
  } catch {
    // Handle error silently for production
  }
}

const fetchMoodboardsPage = async (page: number) => {
  loading.value = true
  try {
    // Build query parameters with filters
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const params: any = { page, page_size: pageSize }

    // Add search query
    if (searchQuery.value.trim()) {
      params.search = searchQuery.value.trim()
    }

    // Add status filter (backend uses lowercase)
    if (selectedStatuses.value.length > 0) {
      const statuses = selectedStatuses.value
        .map((s) => {
          if (s === 'Completed') return 'completed,in_progress'
          if (s === 'Draft') return 'draft'
          return s.toLowerCase()
        })
        .join(',')
      params.status = statuses
    }

    // Add visibility filter
    if (selectedVisibility.value.length > 0) {
      if (
        selectedVisibility.value.includes('Public') &&
        !selectedVisibility.value.includes('Private')
      ) {
        params.is_public = 'true'
      } else if (
        selectedVisibility.value.includes('Private') &&
        !selectedVisibility.value.includes('Public')
      ) {
        params.is_public = 'false'
      }
      // If both selected, don't filter by is_public
    }

    const result = await fetchMoodboards(params)
    if (result) {
      const paginatedResult = result as { results?: Moodboard[]; count?: number }
      if (paginatedResult.count !== undefined) {
        totalCount.value = paginatedResult.count
      }
    }
  } catch {
    // Handle error silently for production
  } finally {
    loading.value = false
  }
}

const loadSharedMoodboards = async () => {
  loadingShared.value = true
  try {
    const result = await getSharedMoodboards({ page: sharedCurrentPage.value, page_size: pageSize })
    if (result) {
      const paginatedResult = result as { results?: Moodboard[]; count?: number }
      sharedMoodboards.value = paginatedResult.results || (result as Moodboard[])
      if (paginatedResult.count !== undefined) {
        sharedTotalCount.value = paginatedResult.count
      }
    }
  } catch {
    // Handle error silently for production
  } finally {
    loadingShared.value = false
  }
}

const loadPublicMoodboards = async () => {
  loadingPublic.value = true
  try {
    const result = await getPublicMoodboards({ page: publicCurrentPage.value, page_size: pageSize })
    if (result) {
      const paginatedResult = result as { results?: Moodboard[]; count?: number }
      publicMoodboards.value = paginatedResult.results || (result as Moodboard[])
      if (paginatedResult.count !== undefined) {
        publicTotalCount.value = paginatedResult.count
      }
    }
  } catch {
    // Handle error silently for production
  } finally {
    loadingPublic.value = false
  }
}

const loadAnalytics = async () => {
  loadingAnalytics.value = true
  try {
    const result = await getMoodboardAnalytics()
    if (result) {
      analytics.value = result as Analytics
    }
  } catch {
    // Handle error silently for production
  } finally {
    loadingAnalytics.value = false
  }
}

// Methods needed for template
const refreshAll = async () => {
  isRefreshing.value = true
  try {
    await forceReload()
  } finally {
    isRefreshing.value = false
  }
}

const createNewMoodboard = async () => {
  await createAIMoodboard()
}

const clearFilters = () => {
  selectedStatuses.value = []
  selectedVisibility.value = []
  searchQuery.value = ''
}

// Pagination handlers
const handlePageChange = async (page: number) => {
  currentPage.value = page
  await fetchMoodboardsPage(page)
}

const handleSharedPageChange = async (page: number) => {
  sharedCurrentPage.value = page
  await loadSharedMoodboards()
}

const handlePublicPageChange = async (page: number) => {
  publicCurrentPage.value = page
  await loadPublicMoodboards()
}

// Action methods
const forceReload = async () => {
  try {
    loading.value = true
    loadingShared.value = true
    loadingPublic.value = true

    await nextTick()

    if (moodboards.value) moodboards.value = []
    if (sharedMoodboards.value) sharedMoodboards.value = []
    if (publicMoodboards.value) publicMoodboards.value = []

    await loadData()
  } catch {
    // Handle error silently for production
    loading.value = false
    loadingShared.value = false
    loadingPublic.value = false
  }
}

const createAIMoodboard = async () => {
  await router.push('/moodboard')
}

const openMoodboard = async (id: string) => {
  try {
    await router.push(`/moodboard?id=${id}`)
  } catch {
    toast.add({
      title: 'Navigation Error',
      description: 'Failed to open moodboard. Please try again.',
      color: 'error',
    })
  }
}

const duplicateMoodboard = async (id: string) => {
  try {
    await duplicateMoodboardApi(id)
    await fetchMoodboardsPage(currentPage.value)
    toast.add({
      title: 'Success',
      description: 'Moodboard duplicated successfully',
      color: 'success',
    })
  } catch {
    // Handle error silently for production
    toast.add({
      title: 'Error',
      description: 'Failed to duplicate moodboard',
      color: 'error',
    })
  }
}

const deleteMoodboard = async (id: string) => {
  if (confirm('Are you sure you want to delete this moodboard?')) {
    try {
      await deleteMoodboardApi(id)
      toast.add({
        title: 'Success',
        description: 'Moodboard deleted successfully',
        color: 'success',
      })
    } catch {
      // Handle error silently for production
      toast.add({
        title: 'Error',
        description: 'Failed to delete moodboard',
        color: 'error',
      })
    }
  }
}

const shareMoodboard = async (moodboard: Moodboard) => {
  selectedMoodboardForShare.value = {
    ...moodboard,
    id: String(moodboard.id),
  } as Moodboard
  shareSelectedUserIds.value = []
  sharePermission.value = 'view'

  await loadAvailableUsers()
  showShareModal.value = true
}

const loadAvailableUsers = async () => {
  try {
    loadingUsers.value = true
    const users = await fetchUsers()
    availableUsers.value = users
  } catch {
    // Handle error silently for production
    toast.add({
      title: 'Error',
      description: 'Failed to load users list',
      color: 'error',
    })
  } finally {
    loadingUsers.value = false
  }
}

const closeShareModal = () => {
  showShareModal.value = false
  shareSelectedUserIds.value = []
  sharePermission.value = 'view'
  selectedMoodboardForShare.value = undefined
  availableUsers.value = []
}

const handleShare = async (data: { userId: string; permission: string }) => {
  if (!data.userId || !selectedMoodboardForShare.value) {
    toast.add({
      title: 'Error',
      description: 'Please select a user to share with',
      color: 'error',
    })
    return
  }

  try {
    sharingInProgress.value = true

    await shareMoodboardWithMultipleUsers(
      String(selectedMoodboardForShare.value.id),
      [data.userId],
      data.permission as 'view' | 'edit',
    )

    closeShareModal()
    toast.add({
      title: 'Success',
      description: 'Moodboard shared successfully',
      color: 'success',
    })
  } catch (error: unknown) {
    const apiError = error as { message?: string }
    toast.add({
      title: 'Error',
      description: apiError.message || 'Failed to share moodboard',
      color: 'error',
    })
  } finally {
    sharingInProgress.value = false
  }
}

// Event handlers for MoodboardTable actions
const handleMoodboardAction = async (action: string, moodboard: Moodboard) => {
  switch (action) {
    case 'open':
      await openMoodboard(String(moodboard.id))
      break
    case 'edit':
      await router.push(`/moodboard?id=${moodboard.id}`)
      break
    case 'duplicate':
      await duplicateMoodboard(String(moodboard.id))
      break
    case 'share':
      await shareMoodboard(moodboard)
      break
    case 'delete':
      await deleteMoodboard(String(moodboard.id))
      break
    default:
    // Unknown action - handle silently for production
  }
}

const handleSharedMoodboardAction = async (action: string, moodboard: Moodboard) => {
  switch (action) {
    case 'open':
    case 'edit':
      await openMoodboard(String(moodboard.id))
      break
    default:
    // Unknown shared action - handle silently for production
  }
}

const handlePublicMoodboardAction = async (action: string, moodboard: Moodboard) => {
  switch (action) {
    case 'open':
      await openMoodboard(String(moodboard.id))
      break
    default:
    // Unknown public action - handle silently for production
  }
}
</script>

<style scoped>
/* Enhanced gradient button styling */
.bg-gradient-to-r {
  transition: all 0.2s ease-in-out;
}

/* Enhanced card hover effects */
.rounded-xl {
  transition: box-shadow 0.2s ease-in-out;
}

.rounded-xl:hover {
  box-shadow:
    0 10px 25px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

/* Dark mode enhancements */
.dark .rounded-xl:hover {
  box-shadow:
    0 10px 25px -3px rgba(0, 0, 0, 0.25),
    0 4px 6px -2px rgba(0, 0, 0, 0.1);
}

/* Enhanced gradient text */
.bg-clip-text {
  -webkit-background-clip: text;
  background-clip: text;
}
</style>
