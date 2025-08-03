<template>
  <div class="moodboard-container">
    <!-- Header with back to moodboards -->
    <div class="page-header">
      <h1>AI Moodboard</h1>
      <div class="header-actions">
        <UButton @click="$router.push('/moodboards')" variant="outline" icon="i-heroicons-squares-2x2-20-solid">
          Back to Moodboards
        </UButton>
      </div>
    </div>
    
    <div v-if="!sessionId">
      <div class="prompt-bar">
        <UButtonGroup>
          <UButton color="neutral" variant="subtle">
            <UIcon name="i-heroicons-cog-6-tooth-20-solid" class="mr-1 w-4 h-4" />
            Settings
          </UButton>
          <UDropdownMenu :items="dropdownItems">
            <UButton color="neutral" variant="outline" icon="i-heroicons-chevron-down-20-solid" />
            <template #item="{ item }">
              <div :class="['dropdown-item', { 'dropdown-item-selected': item.checked }]">
                <UIcon :name="item.icon || ''" class="mr-2 w-4 h-4" />
                <span>{{ item.label }}</span>
                <UIcon v-if="item.checked" name="i-heroicons-check-20-solid" class="dropdown-item-check ml-auto w-4 h-4" />
              </div>
            </template>
          </UDropdownMenu>
        </UButtonGroup>

        <UInput 
          v-model="prompt" 
          placeholder="Describe your gaming moodboard..." 
          @keyup.enter="startSessionWithPrompt" 
          @input="handlePromptInput"
          class="prompt-input" 
        />
        
        <!-- Color palette icon and popover -->
        <UPopover>
          <span
            class="palette-icon-btn"
            :style="{ background: colorPickerValue, border: '2px solid #e5e7eb' }"
            aria-label="Pick colors"
            tabindex="0"
          >
            <UIcon
              name="i-heroicons-swatch-20-solid"
              class="w-6 h-6"
              :style="{ color: getContrastColor(colorPickerValue) }"
            />
          </span>
          <template #content>
            <div class="palette-popover-panel">
              <UColorPicker v-model="colorPickerValue" class="p-2" />
              <UButton v-if="canEdit" @click="addColorToPaletteFromPicker" :disabled="colorPalette.length >= maxPaletteColors || colorPalette.includes(colorPickerValue)" size="xs" class="ml-1 mt-2">Add</UButton>
              <div class="palette-list mt-2">
                <span v-for="(color, idx) in colorPalette" :key="color" class="palette-color" :style="{ background: color }">
                  <span v-if="canEdit" class="palette-remove" @click="removeColorFromPalette(idx)">&times;</span>
                </span>
              </div>
            </div>
          </template>
        </UPopover>
        
        <!-- Show palette chips inline for quick reference -->
        <div class="palette-inline-list">
          <span v-for="color in colorPalette" :key="color" class="palette-inline-color" :style="{ background: color }"></span>
        </div>
        <UButton v-if="canGenerate" @click="startSessionWithPrompt" :disabled="!prompt" class="ml-2">Start Moodboard</UButton>
      </div>
    </div>
    
    <div v-else>
      <!-- Divider replaced with simple HR -->
      <hr v-if="loading || images.length || moodboard.length" class="my-6 border-gray-200 dark:border-gray-700" />
      
      <div v-if="images.length" class="section-card">
        <div class="section-header">
          <h2>Generated Images</h2>
        </div>
        <div class="images-list">
          <UCard v-for="img in images" :key="img.id" class="image-item">
            <img :src="getImageUrl(img.url || img.image_url)" :alt="img.prompt" />
            <template #footer>
              <UCheckbox v-if="canEdit" :model-value="selectedImageIds.includes(img.id)" @update:model-value="(value) => onCheckboxChange(value === true, img.id)" :label="'Select'" />
            </template>
          </UCard>
        </div>
      </div>
      
      <div v-if="moodboard.length" class="section-card">
        <div class="section-header">
          <h2>Your Moodboard</h2>
        </div>
        <div class="images-list">
          <UCard v-for="img in moodboard" :key="img.id" class="image-item moodboard-image-item">
            <div class="image-container">
              <img :src="getImageUrl(img.url || img.image_url)" :alt="img.prompt" />
              <UButton 
                v-if="canEdit"
                @click="removeFromMoodboard(img.id)"
                class="remove-image-btn"
                color="error"
                variant="solid"
                size="xs"
                icon="i-heroicons-x-mark-20-solid"
              />
            </div>
          </UCard>
        </div>
      </div>
      
      <div class="prompt-bar">
        <UButtonGroup>
          <UButton color="neutral" variant="subtle">
            <UIcon name="i-heroicons-cog-6-tooth-20-solid" class="mr-1 w-4 h-4" />
            Settings
          </UButton>
          <UDropdownMenu :items="dropdownItems">
            <UButton color="neutral" variant="outline" icon="i-heroicons-chevron-down-20-solid" />
            <template #item="{ item }">
              <div :class="['dropdown-item', { 'dropdown-item-selected': item.checked }]">
                <UIcon :name="item.icon || ''" class="mr-2 w-4 h-4" />
                <span>{{ item.label }}</span>
                <UIcon v-if="item.checked" name="i-heroicons-check-20-solid" class="dropdown-item-check ml-auto w-4 h-4" />
              </div>
            </template>
          </UDropdownMenu>
        </UButtonGroup>
        
        <UInput 
          v-if="canGenerate" 
          v-model="prompt" 
          placeholder="Describe your gaming moodboard..." 
          @keyup.enter="generateImages" 
          @input="handlePromptInput" 
          class="prompt-input" 
        />
        <div v-else class="prompt-input-placeholder">
          <span class="text-gray-500">View-only access - Image generation disabled</span>
        </div>
        
        <!-- Color palette icon and popover -->
        <UPopover v-if="canGenerate">
          <span
            class="palette-icon-btn"
            :style="{ background: colorPickerValue, border: '2px solid #e5e7eb' }"
            aria-label="Pick colors"
            tabindex="0"
          >
            <UIcon
              name="i-heroicons-swatch-20-solid"
              class="w-6 h-6"
              :style="{ color: getContrastColor(colorPickerValue) }"
            />
          </span>
          <template #content>
            <div class="palette-popover-panel">
              <UColorPicker v-model="colorPickerValue" class="p-2" />
              <UButton v-if="canEdit" @click="addColorToPaletteFromPicker" :disabled="colorPalette.length >= maxPaletteColors || colorPalette.includes(colorPickerValue)" size="xs" class="ml-1 mt-2">Add</UButton>
              <div class="palette-list mt-2">
                <span v-for="(color, idx) in colorPalette" :key="color" class="palette-color" :style="{ background: color }">
                  <span v-if="canEdit" class="palette-remove" @click="removeColorFromPalette(idx)">&times;</span>
                </span>
              </div>
            </div>
          </template>
        </UPopover>
        
        <!-- Show palette chips inline for quick reference (read-only for view users) -->
        <div class="palette-inline-list" :class="{ 'opacity-60': !canGenerate }">
          <span v-for="color in colorPalette" :key="color" class="palette-inline-color" :style="{ background: color }"></span>
        </div>
        
        <UButton v-if="canGenerate" @click="generateImages" :disabled="loading || !prompt" class="ml-2">Generate Images</UButton>
        <UButton v-if="canSave" @click="openSaveModal" color="primary" class="ml-2 save-btn" :disabled="moodboard.length === 0">
          Save Moodboard
        </UButton>
      </div>
    </div>

    <!-- Save Moodboard Modal -->
    <UModal 
      v-model:open="showSaveModal" 
      :key="`modal-${sessionId}`"
      title="Save Your Moodboard" 
      description="Give your moodboard a name and set its visibility settings."
      :ui="{ footer: 'justify-end' }"
    >
      <template #body>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Moodboard Name
            </label>
            <UInput 
              v-model="tempMoodboardName" 
              placeholder="Enter a name for your moodboard..."
              size="lg"
              icon="i-heroicons-identification-20-solid"
            />
            <p v-if="!isOwner && moodboardName" class="text-xs text-amber-600 dark:text-amber-400 mt-1 font-medium">
              ⚠️ You must change the name to create your own copy of this moodboard
            </p>
            <p v-else class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Give your moodboard a memorable name to help you find it later
            </p>
          </div>

          <div>
            <UCheckbox 
              v-model="isMoodboardPublic" 
              label="Make Public"
              help="Public moodboards can be viewed by other users in the gallery"
            />
          </div>

          <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
            <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <UIcon name="i-heroicons-photo-20-solid" />
              <span>{{ moodboard.length }} images selected</span>
            </div>
            <div v-if="!isOwner && moodboardName" class="mt-2 text-xs text-blue-600 dark:text-blue-400">
              <UIcon name="i-heroicons-information-circle-20-solid" class="inline mr-1" />
              This will create a new copy. The original moodboard will remain unchanged.
            </div>
          </div>
        </div>
      </template>

      <template #footer>
        <UButton 
          label="Cancel" 
          color="neutral" 
          variant="outline" 
          @click="showSaveModal = false" 
        />
        <UButton 
          label="Save Moodboard"
          color="primary" 
          @click="saveMoodboard" 
          :loading="saving"
          :disabled="isSaveDisabled"
        />
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
})

import { ref, computed, onMounted, onUnmounted, watch, inject, nextTick } from 'vue'
import type { Ref } from 'vue'
import axios from 'axios'
import { useRuntimeConfig, useRouter } from '#imports'
import type { DropdownMenuItem } from '@nuxt/ui'
import '@/assets/css/toast-loading-bar.css'
import { useMoodboards } from '~/composables/useMoodboards'

// Core state
const sessionId = ref<string | null>(null)
const prompt = ref('')
const moodboardName = ref('')
const images = ref<any[]>([])
const moodboard = ref<any[]>([])
const selectedImageIds = ref<any[]>([])
const loading = inject('globalLoading') as Ref<boolean>
const isInitialLoad = ref(true)
const existingImageCount = ref(0)

// Change tracking
const originalMoodboardImageIds = ref<string[]>([])
const removedImageIds = ref<string[]>([])

// Modal and saving state
const showSaveModal = ref(false)
const tempMoodboardName = ref('')
const isMoodboardPublic = ref(false)
const saving = ref(false)

// Permission states
const userPermission = ref<'view' | 'edit'>('edit')
const isOwner = ref(true)
const canEdit = computed(() => userPermission.value === 'edit')
const canGenerate = computed(() => userPermission.value === 'edit')
const canSave = computed(() => userPermission.value === 'edit')

// Computed for save button disabled state
const isSaveDisabled = computed(() => {
  if (!tempMoodboardName.value.trim()) return true
  // Non-owners must change the name when editing existing moodboards
  if (!isOwner.value && moodboardName.value && tempMoodboardName.value.trim() === moodboardName.value) {
    return true
  }
  return false
})

const config = useRuntimeConfig()
const apiBase = config.public.apiBase
const router = useRouter()

// Composable for API calls
const { 
  fetchMoodboard: fetchMoodboardFromAPI,
  updateMoodboard,
  createMoodboard,
  addImageToMoodboard,
  updateMoodboardImage,
  bulkImageAction,
  startAISession,
  generateAIImages,
  getAISession,
  endAISession,
  preloadAI
} = useMoodboards()

const dropdownMode = ref('default')
const colorPalette = ref<string[]>([])
const maxPaletteColors = 5
const colorPickerValue = ref('#00C16A')

const dropdownItems = computed(() => [
  {
    label: 'Default',
    icon: 'i-heroicons-sparkles-20-solid',
    type: 'checkbox' as const,
    checked: dropdownMode.value === 'default',
    onUpdateChecked(checked: boolean) {
      if (checked) dropdownMode.value = 'default'
      else if (dropdownMode.value === 'default') dropdownMode.value = 'gaming'
    }
  },
  {
    label: 'Gaming',
    icon: 'i-heroicons-command-line-20-solid',
    type: 'checkbox' as const,
    checked: dropdownMode.value === 'gaming',
    onUpdateChecked(checked: boolean) {
      if (checked) dropdownMode.value = 'gaming'
      else if (dropdownMode.value === 'gaming') dropdownMode.value = 'default'
    }
  }
])

onMounted(async () => {
  // Ensure modal is closed on component mount
  showSaveModal.value = false
  tempMoodboardName.value = ''
  saving.value = false
  
  const saved = localStorage.getItem('moodboard-dropdown-mode')
  if (saved && (saved === 'default' || saved === 'gaming')) {
    dropdownMode.value = saved
  }
  
  // Check if we're editing an existing moodboard
  const route = useRoute()
  const moodboardId = route.query.id as string
  
  if (moodboardId) {
    sessionId.value = moodboardId
    await fetchMoodboard()
  } else {
    isMoodboardPublic.value = false
    originalMoodboardImageIds.value = []
    removedImageIds.value = []
  }
})

onUnmounted(async () => {
  if (sessionId.value) {
    try {
      await endAISession(sessionId.value || '', [])
    } catch (error) {
      console.warn('Failed to cleanup session on unmount:', error)
    }
  }
})

watch(dropdownMode, (val) => {
  localStorage.setItem('moodboard-dropdown-mode', val)
})

// Watch for route changes to handle switching between different moodboards
const route = useRoute()
watch(() => route.query.id, async (newId, oldId) => {
  if (newId !== oldId) {
    if (newId) {
      sessionId.value = newId as string
      isInitialLoad.value = true
      images.value = []
      moodboard.value = []
      moodboardName.value = ''
      isMoodboardPublic.value = false
      originalMoodboardImageIds.value = []
      removedImageIds.value = []
      await fetchMoodboard()
    } else {
      sessionId.value = null
      isMoodboardPublic.value = false
      moodboardName.value = ''
      images.value = []
      moodboard.value = []
      isInitialLoad.value = true
      originalMoodboardImageIds.value = []
      removedImageIds.value = []
    }
  }
}, { immediate: false })

function onCheckboxChange(checked: boolean, id: any) {
  if (checked) {
    if (!selectedImageIds.value.includes(id)) {
      selectedImageIds.value.push(id)
      
      // If this image was previously removed, remove it from the removed list
      if (removedImageIds.value.includes(id)) {
        removedImageIds.value = removedImageIds.value.filter(removedId => removedId !== id)
      }
      
      // Move the selected image from images to moodboard immediately
      const selectedImage = images.value.find((img: any) => img.id === id)
      if (selectedImage) {
        images.value = images.value.filter((img: any) => img.id !== id)
        moodboard.value.push(selectedImage)
      }
    }
  } else {
    selectedImageIds.value = selectedImageIds.value.filter((i: any) => i !== id)
    
    // Move the image back from moodboard to images
    const deselectedImage = moodboard.value.find((img: any) => img.id === id)
    if (deselectedImage) {
      moodboard.value = moodboard.value.filter((img: any) => img.id !== id)
      images.value.push(deselectedImage)
    }
  }
}

function removeFromMoodboard(imageId: any) {
  // Find the image to remove from moodboard
  const imageToRemove = moodboard.value.find((img: any) => img.id === imageId)
  if (imageToRemove) {
    // Remove from moodboard
    moodboard.value = moodboard.value.filter((img: any) => img.id !== imageId)
    
    // Track this as a removed image if it was part of the original moodboard
    if (originalMoodboardImageIds.value.includes(imageId)) {
      if (!removedImageIds.value.includes(imageId)) {
        removedImageIds.value.push(imageId)
      }
    }
    
    // Remove from selectedImageIds if it was recently selected
    selectedImageIds.value = selectedImageIds.value.filter((id: any) => id !== imageId)
    
    // Move it back to the generated images section so user can re-select if needed
    images.value.push(imageToRemove)
    
    showToast('Image removed from moodboard', 'info')
  }
}

const toast = useToast()

function showMoodboardToast() {
  toast.add({
    title: 'Generating Images...',
    description: 'Your AI moodboard is being created. This may take a few moments.',
    color: 'primary',
    class: 'moodboard-toast',
  })
}

function clearMoodboardToast() {
  toast.clear()
}

function showToast(message: string, type: 'success' | 'error' | 'info' = 'info') {
  const colors = {
    success: 'success' as const,
    error: 'error' as const, 
    info: 'primary' as const
  }
  
  toast.add({
    title: message,
    color: colors[type]
  })
}

function getContrastColor(hexColor: string): string {
  const color = hexColor.replace('#', '')
  const r = parseInt(color.substring(0, 2), 16)
  const g = parseInt(color.substring(2, 4), 16)
  const b = parseInt(color.substring(4, 6), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.5 ? '#000000' : '#ffffff'
}

function getImageUrl(url: string): string {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${apiBase}${url}`
}

function addColorToPaletteFromPicker() {
  const color = colorPickerValue.value.trim()
  if (colorPalette.value.length < maxPaletteColors && !colorPalette.value.includes(color)) {
    colorPalette.value.push(color)
  }
}

function removeColorFromPalette(idx: number) {
  colorPalette.value.splice(idx, 1)
}

function handlePromptInput() {
  // Simplified - no AI suggestions for now
}

async function generateImages() {
  if (!sessionId.value || !prompt.value) return
  loading.value = true
  showMoodboardToast()
  
  try {
    // Get current image count before generating new ones
    const preGenResponse = await getAISession(sessionId.value || '')
    existingImageCount.value = (preGenResponse as any)?.images ? (preGenResponse as any).images.length : 0
    
    let fullPrompt = prompt.value
    if (colorPalette.value.length) {
      fullPrompt += `, color palette: ${colorPalette.value.join(', ')}`
    }
    
    await generateAIImages(
      sessionId.value || '',
      fullPrompt,
      selectedImageIds.value,
      dropdownMode.value
    )
    
    await fetchMoodboard()
    loading.value = false
    clearMoodboardToast()
    prompt.value = ''
    selectedImageIds.value = []
    
    showToast('Images generated successfully!', 'success')
    
  } catch (error: any) {
    console.error('Error generating images:', error)
    loading.value = false
    clearMoodboardToast()
    
    const errorMessage = error.response?.data?.error || 'Failed to generate images'
    showToast(errorMessage, 'error')
  }
}

async function startSessionWithPrompt() {
  if (!prompt.value) return
  const res = await startAISession()
  sessionId.value = (res as any)?.session_id
  isInitialLoad.value = false
  
  // Generate a default moodboard name based on the prompt
  if (!moodboardName.value) {
    const promptWords = prompt.value.split(' ').slice(0, 4).join(' ')
    moodboardName.value = promptWords.charAt(0).toUpperCase() + promptWords.slice(1) + ' Moodboard'
  }
  
  await fetchMoodboard()
  await generateImages()
}

async function fetchMoodboard() {
  if (!sessionId.value) return
  
  try {
    let res: any
    if (isInitialLoad.value) {
      // For initial load of existing moodboards, use the regular REST API
      res = await fetchMoodboardFromAPI(sessionId.value)
      if (!res) {
        const toast = useToast()
        toast.add({
          title: 'Moodboard Not Found',
          description: 'The requested moodboard could not be loaded.',
          color: 'error'
        })
        await router.push('/moodboards')
        return
      }
    } else {
      // For AI session data during generation, use the AI session API
      res = await getAISession(sessionId.value || '')
    }
    
    if (isInitialLoad.value) {
      // Clear existing data before loading fresh data
      images.value = []
      moodboard.value = []
      
      // Use images from API for the moodboard (filter for selected images)
      const allImages = (res as any)?.images || []
      const selectedImages = allImages.filter((img: any) => img.is_selected)
      moodboard.value = selectedImages
      
      // Store the original image IDs for tracking changes
      originalMoodboardImageIds.value = selectedImages.map((img: any) => img.id)
      removedImageIds.value = []
      
      // Set moodboard metadata
      if ((res as any)?.title || (res as any)?.name) {
        moodboardName.value = (res as any)?.title || (res as any)?.name || ''
      }
      if ((res as any)?.is_public !== undefined) {
        isMoodboardPublic.value = Boolean((res as any).is_public)
      } else if ((res as any)?.public !== undefined) {
        isMoodboardPublic.value = Boolean((res as any).public)
      } else {
        isMoodboardPublic.value = false
      }
      if ((res as any)?.user_permission) {
        userPermission.value = (res as any).user_permission
      }
      if ((res as any)?.is_owner !== undefined) {
        isOwner.value = Boolean((res as any).is_owner)
      }
      
      isInitialLoad.value = false
      existingImageCount.value = (res as any)?.images ? (res as any).images.length : 0
    } else {
      // Handle AI session fetch
      const allImages = (res as any)?.images || []
      const newImages = allImages.slice(existingImageCount.value)
      const existingMoodboardImageIds = moodboard.value.map((img: any) => img.id)
      
      const filteredImages = newImages.filter((img: any) => {
        const isSelected = img.is_selected
        const isAlreadyInMoodboard = existingMoodboardImageIds.includes(img.id)
        return !isSelected && !isAlreadyInMoodboard
      })
      
      images.value = filteredImages
    }
  } catch (error) {
    console.error('Error fetching moodboard:', error)
  }
}

function openSaveModal() {
  tempMoodboardName.value = moodboardName.value || 'Untitled Moodboard'
  showSaveModal.value = true
}

// SIMPLE SAVE FUNCTION - NO OVERCOMPLICATIONS
async function saveMoodboard() {
  if (!sessionId.value) return
  
  if (!tempMoodboardName.value.trim()) {
    showToast('Please enter a moodboard name', 'error')
    return
  }
  
  saving.value = true
  
  try {
    // Calculate current image selection
    const finalImageIds = [
      ...originalMoodboardImageIds.value.filter(id => !removedImageIds.value.includes(id)),
      ...selectedImageIds.value
    ]
    const allSelectedImageIds = [...new Set(finalImageIds)]
    
    const hasExistingMoodboard = !!moodboardName.value
    const nameChanged = tempMoodboardName.value.trim() !== moodboardName.value
    
    // SIMPLE DECISION LOGIC:
    // 1. Owner + existing moodboard + same name = UPDATE
    // 2. Everything else = CREATE NEW
    
    if (isOwner.value && hasExistingMoodboard && !nameChanged) {
      // UPDATE existing moodboard
      
      await updateMoodboard(sessionId.value || '', {
        is_public: isMoodboardPublic.value
      })
      
      // Update image selection
      const currentData = await fetchMoodboardFromAPI(sessionId.value || '')
      if (currentData && (currentData as any).images) {
        const allImages = (currentData as any).images
        
        for (const image of allImages) {
          const shouldBeSelected = allSelectedImageIds.includes(image.id)
          if (image.is_selected !== shouldBeSelected) {
            try {
              await updateMoodboardImage(sessionId.value || '', image.id, {
                is_selected: shouldBeSelected
              })
            } catch (error) {
              console.warn('Failed to update image:', error)
            }
          }
        }
      }
      
      showToast('Moodboard updated successfully!', 'success')
    } else {
      // CREATE new moodboard
      
      const res = await createMoodboard({
        title: tempMoodboardName.value.trim(),
        is_public: isMoodboardPublic.value,
        color_palette: colorPalette.value
      })
      
      // Add images to new moodboard
      if (res && allSelectedImageIds.length > 0) {
        for (const imageId of allSelectedImageIds) {
          try {
            await addImageToMoodboard((res as any).id, imageId)
          } catch (error) {
            console.warn('Failed to add image:', error)
          }
        }
      }
      
      if (res) {
        showToast('Moodboard created successfully!', 'success')
        await router.push('/moodboards')
      }
    }
    
    showSaveModal.value = false
    
  } catch (error: any) {
    console.error('Error saving moodboard:', error)
    showToast(error.response?.data?.error || 'Failed to save moodboard', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.moodboard-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
  padding-bottom: 7rem;
}

:root {
  --moodboard-header-bg: var(--ui-color-primary-50, #f5f3ff);
  --moodboard-header-text: var(--ui-primary, #8b5cf6);
  --moodboard-section-bg: var(--ui-color-primary-50, #f5f3ff);
  --moodboard-section-text: var(--ui-primary, #8b5cf6);
}

html[data-theme="dark"], .dark {
  --moodboard-header-bg: linear-gradient(90deg, #2e1065 0%, #4c1d95 100%);
  --moodboard-header-text: #ede9fe;
  --moodboard-section-bg: #18181b;
  --moodboard-section-text: #a78bfa;
}

.page-header {
  background: var(--moodboard-header-bg);
  border-radius: 1.25rem;
  padding: 2.5rem 2rem 2rem 2rem;
  margin-bottom: 2.5rem;
  box-shadow: 0 4px 24px 0 rgba(139,92,246,0.10);
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: background 0.3s, color 0.3s;
}

.page-header h1 {
  font-size: 2.8rem;
  font-weight: 900;
  color: var(--moodboard-header-text);
  margin: 0;
  letter-spacing: -1px;
  transition: color 0.3s;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.prompt-bar {
  position: fixed;
  left: 256px;
  right: 0;
  bottom: 0;
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--prompt-bar-bg, #fff);
  padding: 1rem 2rem;
  box-shadow: 0 -2px 16px 0 rgba(0,0,0,0.08);
  border-top: 1px solid #e5e7eb;
  transition: background 0.3s, color 0.3s;
}

@media (max-width: 900px) {
  .prompt-bar {
    left: 0;
    right: 0;
    max-width: 100vw;
    padding: 1rem 0.5rem;
  }
}

.section-card {
  background: var(--moodboard-section-bg);
  border-radius: 1.25rem;
  padding: 2rem 2rem 2.5rem 2rem;
  margin-bottom: 2.5rem;
  box-shadow: 0 4px 24px 0 rgba(139,92,246,0.08);
  transition: background 0.3s, color 0.3s;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.section-header h2 {
  font-size: 2rem;
  font-weight: 800;
  color: var(--moodboard-section-text);
  margin: 0;
  letter-spacing: -0.5px;
  transition: color 0.3s;
}

:deep(.dropdown-item-check) {
  margin-left: auto;
  padding-left: 0.5rem;
  color: var(--ui-primary, #8b5cf6);
}

.dropdown-item {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background 0.15s;
}

.dropdown-item-selected {
  background: var(--ui-color-primary-50, #f5f3ff);
  color: var(--ui-primary, #8b5cf6);
}

html[data-theme="dark"] .dropdown-item-selected, .dark .dropdown-item-selected {
  background: var(--ui-color-primary-900, #4c1d95);
  color: var(--ui-color-primary-100, #ede9fe);
}

html[data-theme="dark"] .prompt-bar, .dark .prompt-bar {
  --prompt-bar-bg: #18181b;
  border-top: 1px solid #23272f;
}

.prompt-input {
  flex: 1;
  max-width: 600px;
  margin: 0 1rem;
}

.prompt-input-placeholder {
  flex: 1;
  max-width: 600px;
  margin: 0 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: #f9fafb;
  font-style: italic;
}

.prompt-input-placeholder span {
  color: #6b7280;
}

html[data-theme="dark"] .prompt-input-placeholder, .dark .prompt-input-placeholder {
  background: #1f2937;
  border-color: #374151;
}

html[data-theme="dark"] .prompt-input-placeholder span, .dark .prompt-input-placeholder span {
  color: #9ca3af;
}

.images-list {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1rem;
}

.image-item {
  border: 1px solid #ccc;
  padding: 0.5rem;
  border-radius: 8px;
  background: var(--image-card-bg);
  width: 200px;
  text-align: center;
  transition: background 0.2s;
}

/* Moodboard image container with remove button */
.moodboard-image-item .image-container {
  position: relative;
  display: inline-block;
}

.remove-image-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  min-width: 24px;
  min-height: 24px;
  border-radius: 50%;
  padding: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.remove-image-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

:root, html[data-theme="light"] {
  --image-card-bg: #fafafa;
}

html[data-theme="dark"], .dark {
  --image-card-bg: #23272f;
}

.palette-popover-panel {
  padding: 0.5rem 1rem 1rem 1rem;
  background: var(--moodboard-section-bg);
  border-radius: 1rem;
  box-shadow: 0 4px 24px 0 rgba(139,92,246,0.10);
}

.palette-list {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.palette-color {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  margin-right: 0.15rem;
  box-shadow: 0 1px 4px 0 rgba(0,0,0,0.08);
  cursor: pointer;
  transition: border 0.2s;
}

.palette-color:hover {
  border: 2px solid var(--ui-primary, #8b5cf6);
}

.palette-remove {
  position: absolute;
  top: -7px;
  right: -7px;
  background: #fff;
  color: #a1a1aa;
  border-radius: 50%;
  font-size: 0.9rem;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px 0 rgba(0,0,0,0.10);
  cursor: pointer;
  border: 1px solid #e5e7eb;
  z-index: 2;
}

.palette-remove:hover {
  color: #ef4444;
  background: #fef2f2;
}

.palette-inline-list {
  display: flex;
  align-items: center;
  gap: 0.15rem;
  margin-left: 0.5rem;
}

.palette-inline-color {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #e5e7eb;
  box-shadow: 0 1px 4px 0 rgba(0,0,0,0.08);
  margin-right: 0.1rem;
}

.palette-icon-btn {
  margin-left: 0.5rem;
  min-width: 36px;
  min-height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

html[data-theme="dark"] .palette-color, .dark .palette-color {
  border: 2px solid #23272f;
  background: #23272f;
}

html[data-theme="dark"] .palette-remove, .dark .palette-remove {
  background: #18181b;
  color: #a1a1aa;
  border: 1px solid #23272f;
}

html[data-theme="dark"] .palette-remove:hover, .dark .palette-remove:hover {
  color: #ef4444;
  background: #2e1065;
}

html[data-theme="dark"] .palette-inline-color, .dark .palette-inline-color {
  border: 2px solid #23272f;
  background: #23272f;
}
</style>
