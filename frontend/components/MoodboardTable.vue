<template>
  <div class="moodboard-table-container">
    <!-- Loading State -->
    <div v-if="loading" class="space-y-4">
      <div v-for="i in 5" :key="i" class="animate-pulse">
        <div class="bg-gray-200 dark:bg-gray-700 rounded-lg h-20"/>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!moodboards.length" class="empty-state">
      <div class="text-center py-16">
        <UIcon name="i-heroicons-squares-2x2-20-solid" class="w-16 h-16 text-gray-400 mx-auto mb-6" />
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">{{ emptyTitle }}</h3>
        <p class="text-gray-500 dark:text-gray-400 mb-6 max-w-md mx-auto">{{ emptyDescription }}</p>
      </div>
    </div>

    <!-- Moodboards List -->
    <div v-else class="space-y-4">
      <UCard 
        v-for="moodboard in moodboards" 
        :key="moodboard.id"
        class="moodboard-card hover:shadow-lg transition-all duration-200 cursor-pointer border border-gray-200 dark:border-gray-700"
        @click="handleCardClick(moodboard)"
      >
        <div class="flex items-start gap-4 p-2">
          <!-- Thumbnail -->
          <div class="flex-shrink-0">
            <div class="w-20 h-20 rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
              <img 
                v-if="moodboard.images?.length > 0"
                :src="getImageUrl(moodboard.images[0]?.image_url || '')"
                :alt="moodboard.title"
                class="w-full h-full object-cover"
                loading="lazy"
              />
              <div v-else class="w-full h-full flex items-center justify-center">
                <UIcon name="i-heroicons-photo-20-solid" class="w-8 h-8 text-gray-400" />
              </div>
            </div>
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0 pr-4">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate mb-1">
                  {{ moodboard.title }}
                </h3>
                
                <p v-if="moodboard.description" class="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                  {{ moodboard.description }}
                </p>
                
                <!-- Metadata Row -->
                <div class="flex items-center gap-3 mb-2">
                  <!-- Status Badge -->
                  <UBadge 
                    :color="getStatusColor(moodboard.status)"
                    variant="subtle"
                    size="sm"
                    class="flex items-center gap-1"
                  >
                    <UIcon 
                      :name="moodboard.status === 'completed' ? 'i-heroicons-check-circle-20-solid' : 'i-heroicons-clock-20-solid'" 
                      class="w-3 h-3"
                    />
                    {{ formatStatus(moodboard.status) }}
                  </UBadge>

                  <!-- Visibility Badge -->
                  <UBadge 
                    :color="moodboard.is_public ? 'success' : 'neutral'"
                    variant="subtle"
                    size="sm"
                    class="flex items-center gap-1"
                  >
                    <UIcon 
                      :name="moodboard.is_public ? 'i-heroicons-globe-alt-20-solid' : 'i-heroicons-lock-closed-20-solid'" 
                      class="w-3 h-3"
                    />
                    {{ moodboard.is_public ? 'Public' : 'Private' }}
                  </UBadge>

                  <!-- Images Count -->
                  <div class="flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <UIcon name="i-heroicons-photo-20-solid" class="w-4 h-4 mr-1" />
                    {{ getSelectedImageCount(moodboard) }} images
                  </div>
                </div>

                <!-- Last Updated -->
                <div class="text-xs text-gray-500 dark:text-gray-400">
                  Updated {{ formatRelativeDate(moodboard.updated_at) }}
                </div>
              </div>

              <!-- Actions -->
              <div class="flex-shrink-0" @click.stop>
                <UDropdownMenu :items="getMoodboardActions(moodboard)">
                  <UButton 
                    color="neutral" 
                    variant="ghost" 
                    icon="i-heroicons-ellipsis-vertical-20-solid"
                    size="sm"
                    class="hover:bg-gray-100 dark:hover:bg-gray-700"
                  />
                  <template #item="{ item }">
                    <div class="dropdown-item" @click="handleActionClick(item.key, moodboard)">
                      <UIcon :name="item.icon" class="mr-2 w-4 h-4" />
                      <span>{{ item.label }}</span>
                    </div>
                  </template>
                </UDropdownMenu>
              </div>
            </div>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
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

interface Props {
  moodboards: Moodboard[]
  loading?: boolean
  emptyTitle?: string
  emptyDescription?: string
}

withDefaults(defineProps<Props>(), {
  loading: false,
  emptyTitle: 'No moodboards found',
  emptyDescription: 'Create your first moodboard to get started'
})

const emit = defineEmits<{
  action: [action: string, moodboard: Moodboard]
}>()

const { $config } = useNuxtApp()

// Helper functions
const getImageUrl = (url: string) => {
  if (!url) return ''
  return url.startsWith('http') ? url : `${$config.public.apiBase}${url}`
}

const getStatusColor = (status: string): 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral' | undefined => {
  const colorMap: Record<string, 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral'> = {
    'draft': 'warning',
    'in_progress': 'info',
    'completed': 'success',
    'archived': 'neutral'
  }
  return colorMap[status] || 'neutral'
}

const formatStatus = (status: string) => {
  const statusMap: Record<string, string> = {
    'draft': 'Draft',
    'in_progress': 'In Progress',
    'completed': 'Completed',
    'archived': 'Archived'
  }
  return statusMap[status] || status
}

const formatRelativeDate = (date: string) => {
  if (!date) return 'unknown'
  
  try {
    const dateObj = new Date(date)
    if (isNaN(dateObj.getTime())) return 'invalid date'
    
    const now = new Date()
    const diffMs = now.getTime() - dateObj.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffMinutes = Math.floor(diffMs / (1000 * 60))
    
    if (diffMinutes < 1) return 'just now'
    if (diffMinutes < 60) return `${diffMinutes}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
    if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`
    return `${Math.floor(diffDays / 365)}y ago`
  } catch (error) {
    console.error('Error formatting relative date:', error)
    return 'unknown'
  }
}

const getSelectedImageCount = (moodboard: Moodboard): number => {
  if (typeof moodboard.selected_image_count === 'number') {
    return moodboard.selected_image_count
  }
  
  const images = moodboard.images as MoodboardImage[]
  if (images && Array.isArray(images)) {
    return images.filter(img => img.is_selected).length
  }
  
  return 0
}

const getMoodboardActions = (_moodboard: Moodboard) => {
  return [
    {
      label: 'Open',
      icon: 'i-heroicons-arrow-top-right-on-square-20-solid',
      key: 'open'
    }, 
    {
      label: 'Edit',
      icon: 'i-heroicons-pencil-square-20-solid',
      key: 'edit'
    },
    {
      label: 'Duplicate',
      icon: 'i-heroicons-document-duplicate-20-solid',
      key: 'duplicate'
    }, 
    {
      label: 'Share',
      icon: 'i-heroicons-share-20-solid',
      key: 'share'
    },
    {
      label: 'Delete',
      icon: 'i-heroicons-trash-20-solid',
      key: 'delete'
    }
  ]
}

const handleActionClick = (action: string, moodboard: Moodboard) => {
  emit('action', action, moodboard)
}

const handleCardClick = (moodboard: Moodboard) => {
  emit('action', 'open', moodboard)
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.moodboard-card:hover {
  transform: translateY(-2px);
}

.moodboard-card {
  transition: all 0.2s ease-in-out;
}

.dropdown-item {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.dropdown-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .dropdown-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
}
</style>
