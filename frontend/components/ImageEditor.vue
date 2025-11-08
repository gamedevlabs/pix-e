<template>
  <UModal v-model:open="isOpen" title="Edit Image" class="max-w-4xl">
    <template #body>
      <div class="image-editor">
        <!-- Image Preview Section -->
        <div class="image-preview-section">
          <div ref="imageContainerRef" class="image-container">
            <img
              v-if="previewUrl || originalImageUrl"
              ref="imageRef"
              :src="previewUrl || originalImageUrl"
              :alt="imageTitle"
              class="preview-image"
              :class="{ 'crop-mode': cropMode }"
              @error="onImageError"
              @load="onImageLoad"
              @mousedown="onCropMouseDown"
            />
            <div v-else class="preview-placeholder">
              <UIcon name="i-heroicons-photo" class="w-24 h-24 text-gray-400" />
              <p class="text-gray-500">No image loaded</p>
            </div>

            <!-- Crop Rectangle Overlay -->
            <div
              v-if="cropMode && cropRect"
              class="crop-rectangle"
              :style="{
                left: cropRect.x + 'px',
                top: cropRect.y + 'px',
                width: cropRect.width + 'px',
                height: cropRect.height + 'px',
              }"
            >
              <div class="crop-handles">
                <div class="crop-handle nw" @mousedown.stop="onHandleMouseDown($event, 'nw')" />
                <div class="crop-handle ne" @mousedown.stop="onHandleMouseDown($event, 'ne')" />
                <div class="crop-handle sw" @mousedown.stop="onHandleMouseDown($event, 'sw')" />
                <div class="crop-handle se" @mousedown.stop="onHandleMouseDown($event, 'se')" />
              </div>
              <div class="crop-info">
                {{ Math.round(cropRect.width) }}×{{ Math.round(cropRect.height) }}
              </div>
            </div>
          </div>

          <!-- Image Info -->
          <div v-if="imageInfo" class="image-info">
            <p class="text-sm text-gray-600 dark:text-gray-400">
              {{ imageInfo.width }}×{{ imageInfo.height }}
            </p>
          </div>
        </div>

        <!-- Editor Controls -->
        <div class="editor-controls">
          <!-- Basic Adjustments -->
          <div class="control-section">
            <h3 class="section-title">Adjustments</h3>

            <div class="control-group">
              <label class="control-label">Brightness</label>
              <div class="slider-group">
                <input
                  v-model.number="edits.brightness"
                  type="range"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  class="range-slider"
                />
                <span class="value-display">{{ Number(edits.brightness).toFixed(1) }}</span>
              </div>
            </div>

            <div class="control-group">
              <label class="control-label">Contrast</label>
              <div class="slider-group">
                <input
                  v-model.number="edits.contrast"
                  type="range"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  class="range-slider"
                />
                <span class="value-display">{{ Number(edits.contrast).toFixed(1) }}</span>
              </div>
            </div>

            <div class="control-group">
              <label class="control-label">Saturation</label>
              <div class="slider-group">
                <input
                  v-model.number="edits.saturation"
                  type="range"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  class="range-slider"
                />
                <span class="value-display">{{ Number(edits.saturation).toFixed(1) }}</span>
              </div>
            </div>
          </div>

          <!-- Filters -->
          <div class="control-section">
            <h3 class="section-title">Filters</h3>

            <div class="filter-grid">
              <div
                v-for="filter in availableFilters"
                :key="filter.key"
                class="filter-item"
                :class="{ 'filter-active': edits.filters[filter.key] > 0 }"
                @click="toggleFilter(filter.key)"
              >
                <UIcon :name="filter.icon" class="w-6 h-6" />
                <span class="filter-name">{{ filter.name }}</span>
                <div v-if="edits.filters[filter.key] > 0" class="filter-intensity">
                  {{ Math.round(edits.filters[filter.key] * 100) }}%
                </div>
              </div>
            </div>

            <!-- Filter intensity sliders for all active filters -->
            <div
              v-for="filter in availableFilters.filter((f) => edits.filters[f.key] > 0)"
              :key="filter.key"
              class="control-group mt-4"
            >
              <label class="control-label">{{ filter.name }} Intensity</label>
              <div class="slider-group">
                <input
                  v-model.number="edits.filters[filter.key]"
                  type="range"
                  :min="0"
                  :max="1"
                  :step="0.1"
                  class="range-slider"
                />
                <span class="value-display"
                  >{{ Math.round(Number(edits.filters[filter.key]) * 100) }}%</span
                >
              </div>
            </div>
          </div>

          <!-- Transform -->
          <div class="control-section">
            <h3 class="section-title">Transform</h3>

            <div class="transform-controls">
              <UButton variant="outline" icon="i-heroicons-arrow-path" @click="rotateImage(90)">
                Rotate 90°
              </UButton>

              <UButton
                variant="outline"
                icon="i-heroicons-arrows-right-left"
                @click="flipHorizontal"
              >
                Flip H
              </UButton>

              <UButton variant="outline" icon="i-heroicons-arrows-up-down" @click="flipVertical">
                Flip V
              </UButton>

              <UButton
                :variant="cropMode ? 'solid' : 'outline'"
                :color="cropMode ? 'primary' : undefined"
                icon="i-heroicons-scissors"
                @click="toggleCropMode"
              >
                {{ cropMode ? 'Crop Active' : 'Crop' }}
              </UButton>
            </div>

            <!-- Rotation angle -->
            <div class="control-group">
              <label class="control-label">Rotation Angle</label>
              <div class="slider-group">
                <input
                  v-model.number="edits.rotate"
                  type="range"
                  :min="0"
                  :max="360"
                  :step="1"
                  class="range-slider"
                />
                <span class="value-display">{{ Number(edits.rotate) }}°</span>
              </div>
            </div>

            <!-- Crop Controls -->
            <div v-if="cropMode" class="crop-controls">
              <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">
                Drag on the image to select crop area or adjust the values below:
              </p>

              <div class="control-group">
                <label class="control-label">Crop X</label>
                <input
                  v-model.number="cropRect.x"
                  type="number"
                  :min="0"
                  :max="imageInfo?.width || 1000"
                  class="number-input"
                />
              </div>

              <div class="control-group">
                <label class="control-label">Crop Y</label>
                <input
                  v-model.number="cropRect.y"
                  type="number"
                  :min="0"
                  :max="imageInfo?.height || 1000"
                  class="number-input"
                />
              </div>

              <div class="control-group">
                <label class="control-label">Crop Width</label>
                <input
                  v-model.number="cropRect.width"
                  type="number"
                  :min="1"
                  :max="imageInfo?.width || 1000"
                  class="number-input"
                />
              </div>

              <div class="control-group">
                <label class="control-label">Crop Height</label>
                <input
                  v-model.number="cropRect.height"
                  type="number"
                  :min="1"
                  :max="imageInfo?.height || 1000"
                  class="number-input"
                />
              </div>

              <div class="flex gap-2 mt-2">
                <UButton variant="outline" size="sm" @click="resetCrop"> Reset Crop </UButton>
                <UButton variant="solid" color="primary" size="sm" @click="applyCrop">
                  Apply Crop
                </UButton>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="action-buttons">
            <UButton variant="outline" @click="resetEdits"> Reset </UButton>
            <UButton variant="outline" :loading="previewLoading" @click="previewEdits">
              Preview
            </UButton>
            <UButton color="primary" :loading="applying" @click="applyEdits">
              Apply Changes
            </UButton>
          </div>
        </div>
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import type { MoodboardImage } from '~/composables/useMoodboards'
import type { ImageMetadata } from '~/types/moodboard'

interface ImageEditorProps {
  imageId: string
  moodboardId: string
  originalImageUrl: string
  imageTitle?: string
}

interface ImageEdit {
  brightness: number
  contrast: number
  saturation: number
  rotate: number
  flip_horizontal: boolean
  flip_vertical: boolean
  filters: Record<string, number>
  crop?: {
    x: number
    y: number
    width: number
    height: number
  } | null
}

interface CropRect {
  x: number
  y: number
  width: number
  height: number
}

interface FilterOption {
  key: string
  name: string
  icon: string
}

const props = defineProps<ImageEditorProps>()

const emit = defineEmits<{
  close: []
  imageEdited: [editedImage: MoodboardImage]
}>()

// Get runtime config
const config = useRuntimeConfig()

// Reactive state
const isOpen = ref(true)
const previewUrl = ref<string | null>(null)
const previewLoading = ref(false)
const applying = ref(false)
const imageInfo = ref<ImageMetadata | null>(null)

// Crop state
const cropMode = ref(false)
const cropRect = ref<CropRect>({ x: 0, y: 0, width: 100, height: 100 })
const imageRef = ref<HTMLImageElement | null>(null)
const imageContainerRef = ref<HTMLDivElement | null>(null)
const isDragging = ref(false)
const isResizing = ref(false)
const resizeHandle = ref<string | null>(null)
const dragStart = ref({ x: 0, y: 0 })

// Default edit values
const defaultEdits: ImageEdit = {
  brightness: 1.0,
  contrast: 1.0,
  saturation: 1.0,
  rotate: 0,
  flip_horizontal: false,
  flip_vertical: false,
  filters: {
    blur: 0,
    sharpen: 0,
    edge_enhance: 0,
    emboss: 0,
    sepia: 0,
    vintage: 0,
  },
  crop: null,
}

const edits = ref<ImageEdit>({ ...defaultEdits })

// Available filters
const availableFilters: FilterOption[] = [
  { key: 'blur', name: 'Blur', icon: 'i-heroicons-eye-slash' },
  { key: 'sharpen', name: 'Sharpen', icon: 'i-heroicons-sparkles' },
  { key: 'edge_enhance', name: 'Edge Enhance', icon: 'i-heroicons-square-3-stack-3d' },
  { key: 'emboss', name: 'Emboss', icon: 'i-heroicons-cube' },
  { key: 'sepia', name: 'Sepia', icon: 'i-heroicons-sun' },
  { key: 'vintage', name: 'Vintage', icon: 'i-heroicons-camera' },
]

// Active filter (for intensity slider)
const activeFilter = ref<FilterOption | null>(null)

// Initialize component
onMounted(() => {
  // Load initial preview with default edits (should show original image)
  previewEdits()
})

// API functions
async function previewEdits() {
  previewLoading.value = true
  try {
    const response = (await $fetch(
      `${config.public.apiBase}/moodboards/${props.moodboardId}/images/${props.imageId}/preview-edit/`,
      {
        method: 'POST',
        body: { edits: edits.value },
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      },
    )) as { preview: string; image_info: ImageMetadata }

    if (response.preview) {
      previewUrl.value = response.preview
      imageInfo.value = response.image_info
    }
  } catch (error: unknown) {
    // More detailed error handling
    let errorMessage = 'Could not generate preview. Please try again.'
    const err = error as { statusCode?: number; data?: { error?: string } }
    if (err?.statusCode === 401) {
      errorMessage = 'Authentication required. Please log in.'
    } else if (err?.statusCode === 403) {
      errorMessage = 'You do not have permission to edit this image.'
    } else if (err?.statusCode === 404) {
      errorMessage = 'Image not found.'
    } else if (err?.data?.error) {
      errorMessage = err.data.error
    }

    useToast().add({
      title: 'Preview Failed',
      description: errorMessage,
      color: 'error',
    })

    // Reset to original image on error
    previewUrl.value = null
  } finally {
    previewLoading.value = false
  }
}

async function applyEdits() {
  applying.value = true
  try {
    const response = (await $fetch(
      `${config.public.apiBase}/moodboards/${props.moodboardId}/images/${props.imageId}/edit/`,
      {
        method: 'POST',
        body: { edits: edits.value },
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      },
    )) as { edited_image: MoodboardImage; message: string }

    // Emit the edited image (toast will be shown by parent component)
    emit('imageEdited', response.edited_image)
    closeEditor()
  } catch {
    useToast().add({
      title: 'Edit Failed',
      description: 'Could not apply changes. Please try again.',
      color: 'error',
    })
  } finally {
    applying.value = false
  }
}

// Helper functions
function resetEdits() {
  edits.value = { ...defaultEdits }
  previewUrl.value = null
  activeFilter.value = null
}

function toggleFilter(filterKey: string) {
  const filter = availableFilters.find((f) => f.key === filterKey)
  if (!filter) return

  if (edits.value.filters[filterKey] > 0) {
    // Turn off filter
    edits.value.filters[filterKey] = 0
    if (activeFilter.value?.key === filterKey) {
      activeFilter.value = null
    }
  } else {
    // Turn on filter with default intensity
    edits.value.filters[filterKey] = 0.5
    activeFilter.value = filter
  }
}

function rotateImage(angle: number) {
  edits.value.rotate = (edits.value.rotate + angle) % 360
  triggerPreview()
}

function flipHorizontal() {
  edits.value.flip_horizontal = !edits.value.flip_horizontal
  triggerPreview()
}

function flipVertical() {
  edits.value.flip_vertical = !edits.value.flip_vertical
  triggerPreview()
}

// Crop functions
function toggleCropMode() {
  cropMode.value = !cropMode.value
  if (cropMode.value && imageInfo.value) {
    // Initialize crop rectangle to center of image with 80% size
    const width = Math.floor(imageInfo.value.width * 0.8)
    const height = Math.floor(imageInfo.value.height * 0.8)
    const x = Math.floor((imageInfo.value.width - width) / 2)
    const y = Math.floor((imageInfo.value.height - height) / 2)
    cropRect.value = { x, y, width, height }
  }
}

function resetCrop() {
  if (imageInfo.value) {
    const width = Math.floor(imageInfo.value.width * 0.8)
    const height = Math.floor(imageInfo.value.height * 0.8)
    const x = Math.floor((imageInfo.value.width - width) / 2)
    const y = Math.floor((imageInfo.value.height - height) / 2)
    cropRect.value = { x, y, width, height }
  }
}

function applyCrop() {
  if (!cropMode.value || !cropRect.value) return

  // Set the crop in edits
  edits.value.crop = {
    x: Math.round(cropRect.value.x),
    y: Math.round(cropRect.value.y),
    width: Math.round(cropRect.value.width),
    height: Math.round(cropRect.value.height),
  }

  // Disable crop mode after applying
  cropMode.value = false

  // Preview the crop
  triggerPreview()

  useToast().add({
    title: 'Crop Applied',
    description: 'Click "Apply Changes" to save the cropped image',
    color: 'success',
  })
}

function onCropMouseDown(e: MouseEvent) {
  if (!cropMode.value || !imageRef.value) return

  e.preventDefault()

  // Get image position and dimensions
  const rect = imageRef.value.getBoundingClientRect()
  const imageWidth = imageInfo.value?.width || rect.width
  const imageHeight = imageInfo.value?.height || rect.height

  // Calculate scale factors
  const scaleX = imageWidth / rect.width
  const scaleY = imageHeight / rect.height

  // Get click position relative to image
  const clickX = (e.clientX - rect.left) * scaleX
  const clickY = (e.clientY - rect.top) * scaleY

  // Start new crop rectangle
  isDragging.value = true
  dragStart.value = { x: clickX, y: clickY }
  cropRect.value = {
    x: clickX,
    y: clickY,
    width: 0,
    height: 0,
  }

  // Add mouse move and up listeners
  document.addEventListener('mousemove', onCropMouseMove)
  document.addEventListener('mouseup', onCropMouseUp)
}

function onCropMouseMove(e: MouseEvent) {
  if (!isDragging.value || !imageRef.value) return

  const rect = imageRef.value.getBoundingClientRect()
  const imageWidth = imageInfo.value?.width || rect.width
  const imageHeight = imageInfo.value?.height || rect.height

  const scaleX = imageWidth / rect.width
  const scaleY = imageHeight / rect.height

  const currentX = (e.clientX - rect.left) * scaleX
  const currentY = (e.clientY - rect.top) * scaleY

  // Calculate crop rectangle
  const x = Math.min(dragStart.value.x, currentX)
  const y = Math.min(dragStart.value.y, currentY)
  const width = Math.abs(currentX - dragStart.value.x)
  const height = Math.abs(currentY - dragStart.value.y)

  // Constrain to image bounds
  cropRect.value = {
    x: Math.max(0, Math.min(x, imageWidth)),
    y: Math.max(0, Math.min(y, imageHeight)),
    width: Math.min(width, imageWidth - x),
    height: Math.min(height, imageHeight - y),
  }
}

function onCropMouseUp() {
  isDragging.value = false
  document.removeEventListener('mousemove', onCropMouseMove)
  document.removeEventListener('mouseup', onCropMouseUp)
}

function onHandleMouseDown(e: MouseEvent, handle: string) {
  if (!cropMode.value) return

  e.preventDefault()
  e.stopPropagation()

  isResizing.value = true
  resizeHandle.value = handle

  const rect = imageRef.value?.getBoundingClientRect()
  if (!rect) return

  const imageWidth = imageInfo.value?.width || rect.width
  const imageHeight = imageInfo.value?.height || rect.height
  const scaleX = imageWidth / rect.width
  const scaleY = imageHeight / rect.height

  dragStart.value = {
    x: e.clientX * scaleX,
    y: e.clientY * scaleY,
  }

  document.addEventListener('mousemove', onHandleMouseMove)
  document.addEventListener('mouseup', onHandleMouseUp)
}

function onHandleMouseMove(e: MouseEvent) {
  if (!isResizing.value || !resizeHandle.value || !imageRef.value) return

  const rect = imageRef.value.getBoundingClientRect()
  const imageWidth = imageInfo.value?.width || rect.width
  const imageHeight = imageInfo.value?.height || rect.height

  const scaleX = imageWidth / rect.width
  const scaleY = imageHeight / rect.height

  const currentX = e.clientX * scaleX
  const currentY = e.clientY * scaleY

  const deltaX = currentX - dragStart.value.x
  const deltaY = currentY - dragStart.value.y

  const newRect = { ...cropRect.value }

  // Update crop rectangle based on which handle is being dragged
  switch (resizeHandle.value) {
    case 'nw':
      newRect.x += deltaX
      newRect.y += deltaY
      newRect.width -= deltaX
      newRect.height -= deltaY
      break
    case 'ne':
      newRect.y += deltaY
      newRect.width += deltaX
      newRect.height -= deltaY
      break
    case 'sw':
      newRect.x += deltaX
      newRect.width -= deltaX
      newRect.height += deltaY
      break
    case 'se':
      newRect.width += deltaX
      newRect.height += deltaY
      break
  }

  // Constrain to image bounds and minimum size
  newRect.x = Math.max(0, Math.min(newRect.x, imageWidth - 10))
  newRect.y = Math.max(0, Math.min(newRect.y, imageHeight - 10))
  newRect.width = Math.max(10, Math.min(newRect.width, imageWidth - newRect.x))
  newRect.height = Math.max(10, Math.min(newRect.height, imageHeight - newRect.y))

  cropRect.value = newRect
  dragStart.value = { x: currentX, y: currentY }
}

function onHandleMouseUp() {
  isResizing.value = false
  resizeHandle.value = null
  document.removeEventListener('mousemove', onHandleMouseMove)
  document.removeEventListener('mouseup', onHandleMouseUp)
}

function closeEditor() {
  isOpen.value = false
  emit('close')
}

function onImageError(_event: Event) {
  // Fall back to original image if preview fails
  if (previewUrl.value) {
    previewUrl.value = null
  }
}

function onImageLoad(_event: Event) {
  // Image loaded successfully
}

// Helper function to trigger preview with debouncing
function triggerPreview() {
  if (previewTimeout) clearTimeout(previewTimeout)
  previewTimeout = setTimeout(() => {
    previewEdits()
  }, 300) // Reduced debounce for better responsiveness
}

// Watch for changes to auto-preview
let previewTimeout: ReturnType<typeof setTimeout> | null = null
watch(
  () => edits.value,
  () => {
    triggerPreview()
  },
  { deep: true },
)

// Close modal handler
watch(isOpen, (newValue) => {
  if (!newValue) {
    emit('close')
  }
})

// Cleanup on unmount
onUnmounted(() => {
  if (previewTimeout) clearTimeout(previewTimeout)
})
</script>

<style scoped>
.image-editor {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 1.5rem;
  min-height: 600px;
}

.image-preview-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.image-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border-radius: 0.5rem;
  border: 2px dashed #e2e8f0;
  min-height: 400px;
  position: relative;
  overflow: hidden;
}

.dark .image-container {
  background: #1e293b;
  border-color: #334155;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 0.25rem;
}

.preview-image.crop-mode {
  cursor: crosshair;
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

/* Crop rectangle overlay */
.crop-rectangle {
  position: absolute;
  border: 2px solid #6366f1;
  background: rgba(99, 102, 241, 0.1);
  pointer-events: none;
  z-index: 10;
}

.crop-handles {
  pointer-events: auto;
}

.crop-handle {
  position: absolute;
  width: 12px;
  height: 12px;
  background: #fff;
  border: 2px solid #6366f1;
  border-radius: 50%;
  cursor: pointer;
  pointer-events: auto;
}

.crop-handle:hover {
  background: #6366f1;
  transform: scale(1.2);
}

.crop-handle.nw {
  top: -6px;
  left: -6px;
  cursor: nw-resize;
}

.crop-handle.ne {
  top: -6px;
  right: -6px;
  cursor: ne-resize;
}

.crop-handle.sw {
  bottom: -6px;
  left: -6px;
  cursor: sw-resize;
}

.crop-handle.se {
  bottom: -6px;
  right: -6px;
  cursor: se-resize;
}

.crop-info {
  position: absolute;
  bottom: -30px;
  left: 50%;
  transform: translateX(-50%);
  background: #6366f1;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  white-space: nowrap;
  pointer-events: none;
}

.crop-controls {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
}

.dark .crop-controls {
  background: #1e293b;
  border-color: #334155;
}

.number-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  background: white;
  font-size: 0.875rem;
  color: #374151;
}

.dark .number-input {
  background: #1e293b;
  border-color: #334155;
  color: #d1d5db;
}

.number-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.image-info {
  text-align: center;
}

.editor-controls {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-height: 600px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.control-section {
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 1rem;
}

.dark .control-section {
  border-color: #334155;
}

.control-section:last-child {
  border-bottom: none;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #374151;
}

.dark .section-title {
  color: #d1d5db;
}

.control-group {
  margin-bottom: 1rem;
}

.control-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #6b7280;
}

.dark .control-label {
  color: #9ca3af;
}

.slider-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.range-slider {
  flex: 1;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  appearance: none;
  cursor: pointer;
}

.range-slider::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  background: #6366f1;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.range-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: #6366f1;
  border-radius: 50%;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.dark .range-slider {
  background: #374151;
}

.value-display {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  min-width: 3rem;
  text-align: right;
}

.dark .value-display {
  color: #d1d5db;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.filter-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.75rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
}

.dark .filter-item {
  border-color: #334155;
}

.filter-item:hover {
  border-color: #6366f1;
  background: #f8fafc;
}

.dark .filter-item:hover {
  border-color: #6366f1;
  background: #1e293b;
}

.filter-active {
  border-color: #6366f1 !important;
  background: #eef2ff !important;
}

.dark .filter-active {
  background: #312e81 !important;
}

.filter-name {
  font-size: 0.75rem;
  font-weight: 500;
  text-align: center;
}

.filter-intensity {
  position: absolute;
  top: 0.25rem;
  right: 0.25rem;
  font-size: 0.625rem;
  background: #6366f1;
  color: white;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
}

.transform-controls {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.action-buttons {
  display: flex;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.dark .action-buttons {
  border-color: #334155;
}

@media (max-width: 768px) {
  .image-editor {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .editor-controls {
    max-height: none;
    overflow-y: visible;
  }

  .filter-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
