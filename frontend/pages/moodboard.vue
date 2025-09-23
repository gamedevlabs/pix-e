<template>
  <div class="moodboard-container" :class="{ 'canvas-mode': viewMode === 'canvas', 'grid-mode': viewMode === 'grid' }">
    <!-- Header with back to moodboards -->
    <div class="page-header">
      <h1>AI Moodboard</h1>
      <div class="header-actions">
        <!-- Mode Toggle for Canvas vs Grid -->
        <div v-if="sessionId" class="mode-toggle-container">
          <UButtonGroup>
            <UButton 
              :variant="viewMode === 'grid' ? 'solid' : 'outline'"
              :color="viewMode === 'grid' ? 'primary' : 'neutral'"
              icon="i-heroicons-squares-2x2-20-solid"
              @click="setViewMode('grid')"
            >
              Grid View
            </UButton>
            <UButton 
              :variant="viewMode === 'canvas' ? 'solid' : 'outline'"
              :color="viewMode === 'canvas' ? 'primary' : 'neutral'"
              icon="i-heroicons-paint-brush-20-solid"
              @click="setViewMode('canvas')"
            >
              Canvas View
            </UButton>
          </UButtonGroup>
        </div>
        <UButton variant="outline" icon="i-heroicons-squares-2x2-20-solid" @click="$router.push('/moodboards')">
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
          class="prompt-input" 
          @keyup.enter="startSessionWithPrompt"
          @input="handlePromptInput" 
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
              <UButton v-if="canEdit" :disabled="colorPalette.length >= maxPaletteColors || colorPalette.includes(colorPickerValue)" size="xs" class="ml-1 mt-2" @click="addColorToPaletteFromPicker">Add</UButton>
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
          <span v-for="color in colorPalette" :key="color" class="palette-inline-color" :style="{ background: color }"/>
        </div>
        <UButton v-if="canGenerate" :disabled="!prompt" class="ml-2" @click="startSessionWithPrompt">Start Moodboard</UButton>
      </div>
    </div>
    
    <div v-else>
      <!-- Divider replaced with simple HR -->
      <hr v-if="(loading || images.length || moodboard.length) && viewMode !== 'canvas'" class="my-6 border-gray-200 dark:border-gray-700" />
      
      <div v-if="images.length && viewMode !== 'canvas'" class="section-card">
        <div class="section-header">
          <h2>Generated Images</h2>
        </div>
        <div class="images-list">
          <UCard v-for="img in images" :key="img.id" class="image-item">
            <div class="image-container">
              <img :src="getImageUrl(img.image_url)" :alt="img.prompt" />
              <div v-if="canEdit" class="image-overlay">
                <UButton 
                  class="edit-image-btn"
                  color="primary"
                  variant="solid"
                  size="xs"
                  icon="i-heroicons-pencil-square-20-solid"
                  @click="openImageEditor(img)"
                />
              </div>
            </div>
            <template #footer>
              <UCheckbox v-if="canEdit" :model-value="selectedImageIds.includes(img.id)" :label="'Select'" @update:model-value="(value: any) => onCheckboxChange(value === true, img.id)" />
            </template>
          </UCard>
        </div>
      </div>
      
      <div v-if="moodboard.length" class="section-card">
        <div class="section-header">
          <h2>Your Moodboard</h2>
        </div>
        
        <!-- Grid View -->
        <div v-if="viewMode === 'grid'" class="images-list" :class="{ 'full-width': viewMode === 'grid' }">
          <UCard v-for="img in moodboard" :key="img.id" class="image-item moodboard-image-item">
            <div class="image-container">
              <img :src="getImageUrl(img.image_url)" :alt="img.prompt" />
              <div v-if="canEdit" class="image-overlay">
                <UButton 
                  class="edit-image-btn"
                  color="primary"
                  variant="solid"
                  size="xs"
                  icon="i-heroicons-pencil-square-20-solid"
                  @click="openImageEditor(img)"
                />
                <UButton 
                  class="remove-image-btn"
                  color="error"
                  variant="solid"
                  size="xs"
                  icon="i-heroicons-x-mark-20-solid"
                  @click="removeFromMoodboard(img.id)"
                />
              </div>
            </div>
          </UCard>
        </div>
        
        <!-- Canvas View -->
        <div v-if="viewMode === 'canvas'" class="canvas-container">
          <!-- Drawing Tools Toolbar -->
          <div v-if="canEdit" class="drawing-tools-toolbar mb-4 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
            <div class="flex items-center gap-4 flex-wrap">
              <!-- Drawing Mode Toggle -->
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Mode:</span>
                <UButtonGroup>
                  <UButton 
                    :variant="drawingMode === 'move' ? 'solid' : 'outline'"
                    color="neutral"
                    size="xs"
                    icon="i-heroicons-cursor-arrow-rays-20-solid"
                    @click="setDrawingMode('move')"
                  >
                    Move
                  </UButton>
                  <UButton 
                    :variant="drawingMode === 'draw' ? 'solid' : 'outline'"
                    color="primary"
                    size="xs"
                    icon="i-heroicons-pencil-20-solid"
                    @click="setDrawingMode('draw')"
                  >
                    Draw
                  </UButton>
                  <UButton 
                    :variant="drawingMode === 'erase' ? 'solid' : 'outline'"
                    color="error"
                    size="xs"
                    icon="i-heroicons-trash-20-solid"
                    @click="setDrawingMode('erase')"
                  >
                    Erase
                  </UButton>
                </UButtonGroup>
              </div>

              <!-- Pen Type Selection (only show when drawing) -->
              <div v-if="drawingMode === 'draw'" class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Pen:</span>
                <UButtonGroup>
                  <UButton 
                    class="pen-btn-pen"
                    :variant="penType === 'pen' ? 'solid' : 'outline'"
                    color="primary"
                    size="xs"
                    @click="setPenType('pen')"
                  >
                    ✏️ Pen
                  </UButton>
                  <UButton 
                    :variant="penType === 'marker' ? 'solid' : 'outline'"
                    color="primary"
                    size="xs"
                    class="pen-btn-marker"
                    @click="setPenType('marker')"
                  >
                    🖍️ Marker
                  </UButton>
                  <UButton 
                    :variant="penType === 'pencil' ? 'solid' : 'outline'"
                    color="primary"
                    size="xs"
                    class="pen-btn-pencil"
                    @click="setPenType('pencil')"
                  >
                    ✏️ Pencil
                  </UButton>
                  <UButton 
                    :variant="penType === 'highlighter' ? 'solid' : 'outline'"
                    color="warning"
                    size="xs"
                    class="pen-btn-highlighter"
                    @click="setPenType('highlighter')"
                  >
                    🖍️ Highlight
                  </UButton>
                  <UButton 
                    :variant="penType === 'spray' ? 'solid' : 'outline'"
                    color="secondary"
                    size="xs"
                    class="pen-btn-spray"
                    @click="setPenType('spray')"
                  >
                    🎨 Spray
                  </UButton>
                  <UButton 
                    :variant="penType === 'watercolor' ? 'solid' : 'outline'"
                    color="info"
                    size="xs"
                    class="pen-btn-watercolor"
                    @click="setPenType('watercolor')"
                  >
                    🎨 Watercolor
                  </UButton>
                </UButtonGroup>
              </div>

              <!-- Brush Settings (only show when drawing/erasing) -->
              <div v-if="drawingMode !== 'move'" class="flex items-center gap-4">
                <!-- Brush Size -->
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Size:</span>
                  <input 
                    v-model="brushSize"
                    type="range"
                    :min="getBrushSizeRange().min"
                    :max="getBrushSizeRange().max"
                    class="w-16 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                  />
                  <span class="text-xs text-gray-500 min-w-[20px]">{{ brushSize }}</span>
                </div>

                <!-- Brush Hardness (for applicable pen types) -->
                <div v-if="showBrushHardness()" class="flex items-center gap-2">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Hardness:</span>
                  <input 
                    v-model="brushHardness"
                    type="range"
                    min="0"
                    max="100"
                    class="w-16 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                  />
                  <span class="text-xs text-gray-500 min-w-[30px]">{{ brushHardness }}%</span>
                </div>

                <!-- Flow Rate (for watercolor and spray) -->
                <div v-if="showFlowRate()" class="flex items-center gap-2">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Flow:</span>
                  <input 
                    v-model="flowRate"
                    type="range"
                    min="1"
                    max="100"
                    class="w-16 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                  />
                  <span class="text-xs text-gray-500 min-w-[30px]">{{ flowRate }}%</span>
                </div>

                <!-- Brush Color (only for drawing) -->
                <div v-if="drawingMode === 'draw'" class="flex items-center gap-2">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Color:</span>
                  <input 
                    v-model="brushColor"
                    type="color"
                    class="w-8 h-8 border border-gray-300 rounded cursor-pointer"
                  />
                </div>

                <!-- Brush Opacity -->
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Opacity:</span>
                  <input 
                    v-model="brushOpacity"
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.1"
                    class="w-16 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                  />
                  <span class="text-xs text-gray-500 min-w-[30px]">{{ Math.round(brushOpacity * 100) }}%</span>
                </div>

                <!-- Blend Mode (for advanced pen types) -->
                <div v-if="showBlendMode()" class="flex items-center gap-2">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Blend:</span>
                  <select 
                    v-model="blendMode"
                    class="text-xs border border-gray-300 rounded px-2 py-1 bg-white dark:bg-gray-700 dark:border-gray-600"
                  >
                    <option value="source-over">Normal</option>
                    <option value="multiply">Multiply</option>
                    <option value="screen">Screen</option>
                    <option value="overlay">Overlay</option>
                    <option value="soft-light">Soft Light</option>
                    <option value="hard-light">Hard Light</option>
                    <option value="color-dodge">Color Dodge</option>
                    <option value="color-burn">Color Burn</option>
                    <option value="difference">Difference</option>
                    <option value="exclusion">Exclusion</option>
                  </select>
                </div>
              </div>

              <!-- Drawing Actions -->
              <div class="flex items-center gap-2 ml-auto">
                <UButton 
                  variant="outline"
                  color="neutral"
                  size="xs"
                  icon="i-heroicons-arrow-uturn-left-20-solid"
                  :disabled="!canUndo"
                  @click="undoDrawing"
                >
                  Undo
                </UButton>
                <UButton 
                  variant="outline"
                  color="neutral"
                  size="xs"
                  icon="i-heroicons-arrow-uturn-right-20-solid"
                  :disabled="!canRedo"
                  @click="redoDrawing"
                >
                  Redo
                </UButton>
                <UButton 
                  variant="outline"
                  color="error"
                  size="xs"
                  icon="i-heroicons-trash-20-solid"
                  @click="clearDrawing"
                >
                  Clear All
                </UButton>
              </div>
            </div>
          </div>

          <MoodboardCanvas 
            v-if="currentMoodboard"
            :moodboard="currentMoodboard"
            :images="moodboard"
            :text-elements="textElements"
            :can-edit="canEdit"
            :drawing-mode="drawingMode"
            :pen-type="penType"
            :brush-size="brushSize"
            :brush-color="brushColor"
            :brush-opacity="brushOpacity"
            :brush-hardness="brushHardness"
            :flow-rate="flowRate"
            :blend-mode="blendMode"
            :drawing-history="drawingHistory"
            :history-step="historyStep"
            @image-updated="handleImageUpdate"
            @image-removed="removeFromMoodboard"
            @moodboard-updated="handleMoodboardUpdate"
            @add-image="handleAddImage"
            @add-text-element="handleAddTextElement"
            @update-text-element="handleUpdateTextElement"
            @delete-element="handleDeleteElement"
            @drawing-state-saved="saveDrawingState"
          />
        </div>
      </div>
      
      <div v-if="viewMode !== 'canvas'" class="prompt-bar">
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
          class="prompt-input" 
          @keyup.enter="generateImages" 
          @input="handlePromptInput" 
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
              <UButton v-if="canEdit" :disabled="colorPalette.length >= maxPaletteColors || colorPalette.includes(colorPickerValue)" size="xs" class="ml-1 mt-2" @click="addColorToPaletteFromPicker">Add</UButton>
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
          <span v-for="color in colorPalette" :key="color" class="palette-inline-color" :style="{ background: color }"/>
        </div>
        
        <UButton v-if="canGenerate" :disabled="loading || !prompt" color="primary" class="ml-2" @click="generateImages">Generate Images</UButton>
        <UButton v-if="canSave" color="success" class="ml-2 save-btn" :disabled="moodboard.length === 0" @click="openSaveModal">
          Save Moodboard
        </UButton>
      </div>
    </div>

    <!-- Save Moodboard Modal -->
    <UModal 
      :key="`modal-${sessionId}`" 
      v-model:open="showSaveModal"
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
          color="success" 
          :loading="saving" 
          :disabled="isSaveDisabled"
          @click="saveMoodboard"
        />
      </template>
    </UModal>

    <!-- AI Suggestions Panel -->
    <AISuggestionsPanel
      :is-visible="aiSuggestions.isVisible.value"
      :suggestions="aiSuggestions.suggestions.value"
      :loading="aiSuggestions.loading.value"
      :error="aiSuggestions.error.value"
      :mode="aiSuggestions.mode.value"
      :suggestion-type="aiSuggestions.suggestionType.value"
      :total-suggestions="aiSuggestions.totalSuggestions.value"
      :applied-suggestions-count="aiSuggestions.appliedSuggestionsCount.value"
      :last-prompt="aiSuggestions.lastPrompt.value"
      :current-prompt="prompt"
      :can-generate="canGenerate"
      :services="aiSuggestions.services.value"
      :active-service="aiSuggestions.activeService.value || undefined"
      @toggle="aiSuggestions.togglePanel"
      @apply-suggestion="handleApplySuggestion"
      @unapply-suggestion="handleUnapplySuggestion"
      @regenerate="handleRegenerateSuggestions"
      @mode-changed="handleAIModeChanged"
      @type-changed="handleAITypeChanged"
      @generate-from-input="handleGenerateAISuggestions"
      @fetch-services="handleFetchAIServices"
      @service-changed="handleServiceChanged"
      @clear-error="handleClearError"
    />

    <!-- Image Editor Modal -->
    <ImageEditor 
      v-if="showImageEditor && currentEditingImage"
      :image-id="currentEditingImage.id"
      :moodboard-id="sessionId || ''"
      :original-image-url="getImageUrl(currentEditingImage.image_url)"
      :image-title="currentEditingImage.title"
      @close="closeImageEditor"
      @image-edited="onImageEdited"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, inject, nextTick } from 'vue'
import type { Ref } from 'vue'
import { useRuntimeConfig, useRouter } from '#imports'
import '@/assets/css/toast-loading-bar.css'
import { useMoodboards, type Moodboard, type MoodboardImage, type MoodboardTextElement } from '~/composables/useMoodboards'
import { useAISuggestions } from '~/composables/useAISuggestions'
import ImageEditor from '~/components/ImageEditor.vue'
import MoodboardCanvas from '~/components/MoodboardCanvas.vue'

definePageMeta({
  middleware: 'auth',
})

// Local interfaces
interface AISessionGetResponse {
  id: string
  status: string
  images: MoodboardImage[]
  moodboard?: Moodboard
  user_permission?: string
  is_owner?: boolean
}

interface AISessionStartResponse {
  session_id: string
  moodboard?: Moodboard
}

// Core state
const sessionId = ref<string | null>(null)
const prompt = ref('')
const moodboardName = ref('')
const images = ref<MoodboardImage[]>([])
const moodboard = ref<MoodboardImage[]>([])
const selectedImageIds = ref<string[]>([])
const loading = inject('globalLoading') as Ref<boolean>
const isInitialLoad = ref(true)
const existingImageCount = ref(0)

// View mode state
const viewMode = ref<'grid' | 'canvas'>('grid')

// Canvas mode state
const currentMoodboard = ref<Moodboard | null>(null)
const textElements = ref<MoodboardTextElement[]>([])

// Drawing state
const drawingMode = ref<'move' | 'draw' | 'erase'>('move')
const penType = ref<'pen' | 'marker' | 'pencil' | 'highlighter' | 'spray' | 'watercolor'>('pen')
const brushSize = ref(5)
const brushColor = ref('#000000')
const brushOpacity = ref(1)
const brushHardness = ref(80)
const flowRate = ref(50)
const blendMode = ref<'source-over' | 'multiply' | 'screen' | 'overlay' | 'soft-light' | 'hard-light' | 'color-dodge' | 'color-burn' | 'difference' | 'exclusion'>('source-over')
const drawingHistory = ref<ImageData[]>([])
const historyStep = ref(-1)

// Drawing computed properties
const canUndo = computed(() => historyStep.value > 0)
const canRedo = computed(() => historyStep.value < drawingHistory.value.length - 1)

// View mode functions
const setViewMode = (mode: 'grid' | 'canvas') => {
  viewMode.value = mode
}

// Canvas event handlers
const handleImageUpdate = async (imageData: Partial<MoodboardImage>) => {
  // Update image position and properties
  const index = moodboard.value.findIndex((img: MoodboardImage) => img.id === imageData.id)
  if (index !== -1) {
    moodboard.value[index] = { ...moodboard.value[index], ...imageData }
  }
}

const handleMoodboardUpdate = async (moodboardData: Partial<Moodboard>) => {
  if (currentMoodboard.value) {
    currentMoodboard.value = { ...currentMoodboard.value, ...moodboardData }
  }
}

const handleAddTextElement = async (textElement: MoodboardTextElement) => {
  // Add the text element returned from the API (which already has the correct ID)
  if (currentMoodboard.value) {
    textElements.value.push(textElement)

  }
}

const handleAddImage = async (imageData: Partial<MoodboardImage>) => {
  // Add the image returned from the API to the moodboard

  if (currentMoodboard.value) {
    if (imageData.id) {
      moodboard.value.push(imageData as MoodboardImage)

    }
  }
}

// Handle text element updates
const handleUpdateTextElement = async (updatedText: MoodboardTextElement) => {
  if (!currentMoodboard.value) {

    return
  }
  
  try {
    await updateTextElement(currentMoodboard.value.id, updatedText.id, updatedText)
    // Update local state
    const index = textElements.value.findIndex((te: MoodboardTextElement) => te.id === updatedText.id)
    if (index !== -1) {
      textElements.value[index] = updatedText
    }

  } catch {

    // Reload text elements to sync state
    await loadTextElements(currentMoodboard.value.id)
  }
}

// Handle text element deletion
const handleDeleteTextElement = async (elementId: string) => {
  if (!currentMoodboard.value) {

    return
  }
  
  try {
    // Remove from local state
    textElements.value = textElements.value.filter((te: MoodboardTextElement) => te.id !== elementId)

  } catch {

    // Reload text elements to sync state
    await loadTextElements(currentMoodboard.value.id)
  }
}

// Drawing mode functions
const setDrawingMode = (mode: 'move' | 'draw' | 'erase') => {
  drawingMode.value = mode
}

const undoDrawing = () => {
  if (canUndo.value) {
    historyStep.value--
    // The canvas component will handle the actual undo
  }
}

const redoDrawing = () => {
  if (canRedo.value) {
    historyStep.value++
    // The canvas component will handle the actual redo
  }
}

const clearDrawing = () => {
  // Clear drawing history and notify canvas component
  drawingHistory.value = []
  historyStep.value = -1
  
  // Remove the saved drawing image from moodboard
  const drawingImage = moodboard.value.find((img: MoodboardImage) => 
    img.title === '__moodboard_drawing__'
  )
  
  if (drawingImage && drawingImage.id) {
    removeFromMoodboard(drawingImage.id)
  }
  
  // The canvas component will handle the actual clear
}

const saveDrawingState = (imageData: ImageData) => {
  // Remove any redo states when new drawing is made
  drawingHistory.value = drawingHistory.value.slice(0, historyStep.value + 1)
  drawingHistory.value.push(imageData)
  historyStep.value++
}

// Advanced drawing functions
const setPenType = (type: 'pen' | 'marker' | 'pencil' | 'highlighter' | 'spray' | 'watercolor') => {
  penType.value = type
  
  // Auto-adjust brush settings based on pen type
  switch (type) {
    case 'pen':
      brushSize.value = Math.min(brushSize.value, 10)
      brushHardness.value = 90
      flowRate.value = 80
      break
    case 'marker':
      brushSize.value = Math.max(brushSize.value, 8)
      brushHardness.value = 60
      flowRate.value = 70
      break
    case 'pencil':
      brushSize.value = Math.min(brushSize.value, 8)
      brushHardness.value = 95
      flowRate.value = 60
      break
    case 'highlighter':
      brushSize.value = Math.max(brushSize.value, 15)
      brushHardness.value = 20
      brushOpacity.value = 0.4
      flowRate.value = 90
      break
    case 'spray':
      brushSize.value = Math.max(brushSize.value, 20)
      brushHardness.value = 0
      flowRate.value = 30
      break
    case 'watercolor':
      brushSize.value = Math.max(brushSize.value, 12)
      brushHardness.value = 10
      flowRate.value = 40
      break
  }
}

const getBrushSizeRange = () => {
  switch (penType.value) {
    case 'pen':
      return { min: 1, max: 15 }
    case 'marker':
      return { min: 5, max: 30 }
    case 'pencil':
      return { min: 1, max: 12 }
    case 'highlighter':
      return { min: 10, max: 50 }
    case 'spray':
      return { min: 15, max: 80 }
    case 'watercolor':
      return { min: 8, max: 60 }
    default:
      return { min: 1, max: 50 }
  }
}

const showBrushHardness = () => {
  return penType.value !== 'spray' && penType.value !== 'watercolor'
}

const showFlowRate = () => {
  return penType.value === 'spray' || penType.value === 'watercolor' || penType.value === 'marker'
}

const showBlendMode = () => {
  return penType.value === 'watercolor' || penType.value === 'marker' || penType.value === 'highlighter'
}

// Save drawing as an image in the moodboard
const saveDrawingAsImage = async () => {
  if (!currentMoodboard.value) return
  
  // Get the drawing canvas from the child component
  const canvasContainer = document.querySelector('.moodboard-canvas')
  const drawingCanvas = canvasContainer?.querySelector('.drawing-canvas') as HTMLCanvasElement
  
  if (!drawingCanvas) return
  
  const ctx = drawingCanvas.getContext('2d')
  if (!ctx) return
  
  // Check if there's actually any drawing content
  const imageData = ctx.getImageData(0, 0, drawingCanvas.width, drawingCanvas.height)
  const hasDrawing = imageData.data.some((value, index) => {
    return index % 4 === 3 && value > 0  // Check alpha channel
  })
  
  if (!hasDrawing) return  // No drawing to save
  
  try {
    // Convert canvas to blob
    const blob = await new Promise<Blob>((resolve, reject) => {
      drawingCanvas.toBlob((blob) => {
        if (blob) resolve(blob)
        else reject(new Error('Failed to create blob'))
      }, 'image/png')
    })
    
    // Remove any existing drawing image (to replace it)
    const existingDrawingImage = moodboard.value.find((img: MoodboardImage) => 
      img.title === '__moodboard_drawing__'
    )
    
    if (existingDrawingImage) {
      await removeFromMoodboard(existingDrawingImage.id || '')
    }
    
    // Create form data to upload the drawing
    const formData = new FormData()
    formData.append('image_file', blob, 'moodboard_drawing.png')
    formData.append('title', '__moodboard_drawing__')  // Special marker for drawings
    formData.append('source', 'drawing')
    formData.append('x_position', '0')
    formData.append('y_position', '0')
    formData.append('canvas_width', drawingCanvas.width.toString())
    formData.append('canvas_height', drawingCanvas.height.toString())
    formData.append('is_selected', 'false')
    formData.append('z_index', '999')  // Keep drawings on top
    formData.append('opacity', '1')
    
    const config = useRuntimeConfig()
    const csrfToken = useCookie('csrftoken').value
    
    const headers: Record<string, string> = {
      ...useRequestHeaders(['cookie'])
    }
    
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken
    }
    
    const response = await $fetch(`${config.public.apiBase}/moodboards/${currentMoodboard.value.id}/images/`, {
      method: 'POST',
      credentials: 'include',
      headers,
      body: formData
    })
    
    // Add to local moodboard
    moodboard.value.push(response as MoodboardImage)
    
  } catch {
    // Silently handle drawing save errors in production
  }
}

// Load drawing from saved image
const loadDrawingFromImage = async () => {
  if (!currentMoodboard.value) return
  
  // Find the drawing image
  const drawingImage = moodboard.value.find((img: MoodboardImage) => 
    img.title === '__moodboard_drawing__'
  )
  
  if (!drawingImage || !drawingImage.image_url) return
  
  // Wait for canvas to be ready
  await nextTick()
  
  const canvasContainer = document.querySelector('.moodboard-canvas')
  const drawingCanvas = canvasContainer?.querySelector('.drawing-canvas') as HTMLCanvasElement
  
  if (!drawingCanvas) return
  
  const ctx = drawingCanvas.getContext('2d')
  if (!ctx) return
  
  try {
    // Load the drawing image
    const img = new Image()
    img.crossOrigin = 'anonymous'
    
    await new Promise<void>((resolve, reject) => {
      img.onload = () => {
        // Clear canvas and draw the saved drawing
        ctx.clearRect(0, 0, drawingCanvas.width, drawingCanvas.height)
        ctx.drawImage(img, 0, 0)
        
        // Save initial state to drawing history
        const imageData = ctx.getImageData(0, 0, drawingCanvas.width, drawingCanvas.height)
        drawingHistory.value = [imageData]
        historyStep.value = 0
        
        resolve()
      }
      img.onerror = reject
      
      let imageUrl = drawingImage.image_url
      if (imageUrl?.startsWith('/')) {
        const config = useRuntimeConfig()
        imageUrl = `${config.public.apiBase}${imageUrl}`
      }
      img.src = imageUrl || ''
    })
    
    // Hide the drawing image element so it doesn't show as a regular image
    const drawingImageElement = document.querySelector(`[data-image-id="${drawingImage.id}"]`) as HTMLElement
    if (drawingImageElement) {
      drawingImageElement.style.display = 'none'
    }
    
  } catch {
    // Silently handle drawing load errors in production
  }
}

// Handle element deletion (both images and text)
const handleDeleteElement = async (elementId: string) => {
  // Check if it's a text element
  const textElement = textElements.value.find((te: MoodboardTextElement) => te.id === elementId)
  if (textElement) {
    await handleDeleteTextElement(elementId)
  } else {
    // It's an image element
    removeFromMoodboard(elementId)
  }
}

// Load text elements for canvas view
const loadTextElements = async (moodboardId: string) => {
  try {

    const response = await getTextElements(moodboardId) as { results?: MoodboardTextElement[] }
    if (response?.results) {
      textElements.value = response.results

    } else {
      textElements.value = []

    }
  } catch {

    textElements.value = [] // Clear state on error
  }
}

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

// Image Editor state
const showImageEditor = ref(false)
const currentEditingImage = ref<MoodboardImage | null>(null)
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
  removeImageFromMoodboard,
  bulkImageAction: _bulkImageAction,
  startAISession,
  generateAIImages,
  getAISession,
  endAISession,
  preloadAI: _preloadAI,
  getTextElements,
  updateTextElement,
  createTextElement
} = useMoodboards()

// AI Suggestions
const aiSuggestions = useAISuggestions()

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
  },
  {
    label: aiSuggestions.totalSuggestions.value > 0 
      ? `AI Suggestions (${aiSuggestions.totalSuggestions.value})` 
      : 'AI Suggestions',
    icon: 'i-heroicons-cpu-chip-20-solid',
    type: 'checkbox' as const,
    checked: aiSuggestions.isVisible.value,
    onUpdateChecked(checked: boolean) {
      if (checked) {
        aiSuggestions.showPanel()
        // Auto-fetch services when panel is opened
        aiSuggestions.fetchServices()
      } else {
        aiSuggestions.hidePanel()
      }
    }
  }
])

onMounted(async () => {
  // Ensure modal is closed on component mount
  showSaveModal.value = false
  tempMoodboardName.value = ''
  saving.value = false
  
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

  // Fetch AI services when component mounts (async, don't wait)
  aiSuggestions.fetchServices()
})

onUnmounted(async () => {
  if (sessionId.value) {
    try {
      await endAISession(sessionId.value || '', [])
    } catch {
      // Silently handle AI session end errors
    }
  }
})

// Watch for route changes to handle switching between different moodboards
const route = useRoute()
watch(() => route.query.id, async (newId: unknown, oldId: unknown) => {
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

function onCheckboxChange(checked: boolean, id: string) {
  if (checked) {
    if (!selectedImageIds.value.includes(id)) {
      selectedImageIds.value.push(id)
      
      // If this image was previously removed, remove it from the removed list
      if (removedImageIds.value.includes(id)) {
        removedImageIds.value = removedImageIds.value.filter((removedId: string) => removedId !== id)
      }
      
      // Move the selected image from images to moodboard immediately
      const selectedImage = images.value.find((img: MoodboardImage) => img.id === id)
      if (selectedImage) {
        images.value = images.value.filter((img: MoodboardImage) => img.id !== id)
        moodboard.value.push(selectedImage)
      }
    }
  } else {
    selectedImageIds.value = selectedImageIds.value.filter((i: string) => i !== id)
    
    // Move the image back from moodboard to images
    const deselectedImage = moodboard.value.find((img: MoodboardImage) => img.id === id)
    if (deselectedImage) {
      moodboard.value = moodboard.value.filter((img: MoodboardImage) => img.id !== id)
      images.value.push(deselectedImage)
    }
  }
}

async function removeFromMoodboard(imageId: string) {
  // Find the image to remove from moodboard
  const imageToRemove = moodboard.value.find((img: MoodboardImage) => img.id === imageId)
  if (imageToRemove) {
    const isExistingImage = originalMoodboardImageIds.value.includes(imageId)
    
    // If this is an existing image in the database, delete it via API
    if (isExistingImage && sessionId.value) {
      try {
        await removeImageFromMoodboard(sessionId.value, imageId)
        // Note: composable already shows success toast, so we don't show one here
      } catch {
        showToast('Failed to remove image', 'error')
        return // Don't remove from UI if API call failed
      }
    } else {
      // For newly added images that aren't in the database yet
      showToast('Image removed from moodboard', 'info')
    }
    
    // Remove from moodboard UI
    moodboard.value = moodboard.value.filter((img: MoodboardImage) => img.id !== imageId)
    
    // Track this as a removed image if it was part of the original moodboard
    if (isExistingImage) {
      if (!removedImageIds.value.includes(imageId)) {
        removedImageIds.value.push(imageId)
      }
    }
    
    // Remove from selectedImageIds if it was recently selected
    selectedImageIds.value = selectedImageIds.value.filter((id: string) => id !== imageId)
    
    // Move it back to the generated images section so user can re-select if needed
    images.value.push(imageToRemove)
  }
}

const toast = useToast()

// Image Editor functions
function openImageEditor(image: MoodboardImage) {
  currentEditingImage.value = image
  showImageEditor.value = true
}

function closeImageEditor() {
  showImageEditor.value = false
  currentEditingImage.value = null
}

function onImageEdited(editedImage: MoodboardImage) {
  // Update the existing image instead of adding a new one
  if (currentEditingImage.value) {
    // Find and update in moodboard list
    const moodboardIndex = moodboard.value.findIndex((img: MoodboardImage) => img.id === currentEditingImage.value!.id)
    if (moodboardIndex !== -1) {
      moodboard.value[moodboardIndex] = editedImage
    }
    
    // Find and update in images list
    const imagesIndex = images.value.findIndex((img: MoodboardImage) => img.id === currentEditingImage.value!.id)
    if (imagesIndex !== -1) {
      images.value[imagesIndex] = editedImage
    }
    
    showToast('Image edited successfully!', 'success')
  }
  
  closeImageEditor()
}

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
    existingImageCount.value = (preGenResponse as AISessionGetResponse)?.images ? (preGenResponse as AISessionGetResponse).images.length : 0
    
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
    
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { error?: string } } }

    loading.value = false
    clearMoodboardToast()
    
    const errorMessage = apiError.response?.data?.error || 'Failed to generate images'
    showToast(errorMessage, 'error')
  }
}

async function startSessionWithPrompt() {
  if (!prompt.value) return
  const res = await startAISession()
  sessionId.value = (res as AISessionStartResponse)?.session_id
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
    let res: AISessionGetResponse | Moodboard | null = null
    if (isInitialLoad.value) {
      // For initial load of existing moodboards, use the regular REST API
      res = await fetchMoodboardFromAPI(sessionId.value) as Moodboard | null
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
      res = await getAISession(sessionId.value || '') as AISessionGetResponse | null
    }
    
    if (isInitialLoad.value) {
      // Clear existing data before loading fresh data
      images.value = []
      moodboard.value = []
      
      // Use images from API for the moodboard (filter for selected images)
      let allImages: MoodboardImage[] = []
      if (isInitialLoad.value) {
        // When loading existing moodboard via REST API, we get a direct Moodboard object
        const moodboard = res as Moodboard
        allImages = moodboard?.images || []
      } else {
        // AI session response structure
        const aiSession = res as AISessionGetResponse
        allImages = aiSession?.images || []
      }
      
      const selectedImages = allImages.filter((img: MoodboardImage) => img.is_selected)
      moodboard.value = selectedImages
      
      // Store the original image IDs for tracking changes
      originalMoodboardImageIds.value = selectedImages.map((img: MoodboardImage) => img.id)
      removedImageIds.value = []
      
      // Set moodboard metadata
      // Check if this is a direct moodboard response or AI session response
      if (isInitialLoad.value) {
        // When loading existing moodboard via REST API, we get a direct Moodboard object
        const moodboard = res as Moodboard
        if (moodboard?.title) {
          moodboardName.value = moodboard.title
        }
        if (moodboard?.is_public !== undefined) {
          isMoodboardPublic.value = Boolean(moodboard.is_public)
        }
        // Set current moodboard for canvas view
        currentMoodboard.value = moodboard
        
        // Load text elements for canvas view
        if (moodboard?.id) {
          await loadTextElements(moodboard.id)
          // Load drawing data
          await loadDrawingFromImage()
        }
        
        // For direct moodboard responses, we need to set default user permissions
        userPermission.value = 'edit' // Assume user has edit permission for their own moodboards
        isOwner.value = true // Assume user is owner when accessing via REST API
      } else {
        // AI session response structure
        const aiSession = res as AISessionGetResponse
        if (aiSession?.moodboard?.title) {
          moodboardName.value = aiSession.moodboard.title
        }
        if (aiSession?.moodboard?.is_public !== undefined) {
          isMoodboardPublic.value = Boolean(aiSession.moodboard.is_public)
        }
        // Set current moodboard for canvas view
        currentMoodboard.value = aiSession?.moodboard || null
        
        // Load text elements for canvas view
        if (aiSession?.moodboard?.id) {
          await loadTextElements(aiSession.moodboard.id)
          // Load drawing data
          await loadDrawingFromImage()
        }
        
        if (aiSession?.user_permission) {
          userPermission.value = aiSession.user_permission as 'view' | 'edit' || 'edit'
        }
        if (aiSession?.is_owner !== undefined) {
          isOwner.value = Boolean(aiSession.is_owner)
        }
      }
      
      // Set default if no value found
      if (!isMoodboardPublic.value) {
        isMoodboardPublic.value = false
      }
      
      isInitialLoad.value = false
      existingImageCount.value = allImages.length
    } else {
      // Handle AI session fetch
      const allImages = res?.images || []
      const newImages = allImages.slice(existingImageCount.value)
      const existingMoodboardImageIds = moodboard.value.map((img: MoodboardImage) => img.id)
      
      const filteredImages = newImages.filter((img: MoodboardImage) => {
        const isSelected = img.is_selected
        const isAlreadyInMoodboard = existingMoodboardImageIds.includes(img.id)
        return !isSelected && !isAlreadyInMoodboard
      })
      
      images.value = filteredImages
    }
  } catch {
    // Silently handle image load errors
  }
}

function openSaveModal() {
  tempMoodboardName.value = moodboardName.value || 'Untitled Moodboard'
  showSaveModal.value = true
}

// ENHANCED SAVE FUNCTION - HANDLES CANVAS CHANGES
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
      ...originalMoodboardImageIds.value.filter((id: string) => !removedImageIds.value.includes(id)),
      ...selectedImageIds.value
    ]
    const _allSelectedImageIds = [...new Set(finalImageIds)]
    
    const hasExistingMoodboard = !!moodboardName.value
    const isEditingExisting = hasExistingMoodboard && isOwner.value
    
    // IMPROVED DECISION LOGIC:
    // 1. If editing existing moodboard and owner = UPDATE (regardless of name change)
    // 2. Otherwise = CREATE NEW
    
    if (isEditingExisting) {
      // UPDATE existing moodboard (allow name changes)
      
      await updateMoodboard(sessionId.value || '', {
        title: tempMoodboardName.value.trim(),
        is_public: isMoodboardPublic.value
      })
      
      // Save all canvas images with their current properties (position, size, etc.)
      for (const image of moodboard.value) {
        try {
          await updateMoodboardImage(sessionId.value || '', image.id, {
            is_selected: true,
            x_position: image.x_position,
            y_position: image.y_position,
            canvas_width: image.canvas_width,
            canvas_height: image.canvas_height,
            z_index: image.z_index,
            opacity: image.opacity,
            rotation: image.rotation || 0
          })
        } catch {
          // Silently handle individual image save errors
        }
      }
      
      // Save all text elements
      for (const textElement of textElements.value) {
        try {
          if (textElement.id) {
            // Update existing text element
            await updateTextElement(sessionId.value || '', textElement.id, textElement)
          } else {
            // Create new text element (shouldn't happen, but just in case)
            await createTextElement(sessionId.value || '', textElement)
          }
        } catch {
          // Silently handle individual text element save errors
        }
      }
      
      // Save drawing data
      await saveDrawingAsImage()
      
      // Update the moodboard name if it changed
      moodboardName.value = tempMoodboardName.value.trim()
      
      // Redirect to the moodboards list
      await router.push('/moodboards')
      
    } else {
      // CREATE new moodboard
      
      const res = await createMoodboard({
        title: tempMoodboardName.value.trim(),
        is_public: isMoodboardPublic.value,
        color_palette: colorPalette.value
      })
      
      // Add canvas images to new moodboard with their positions
      if (res && moodboard.value.length > 0) {
        for (const image of moodboard.value) {
          try {
            await addImageToMoodboard((res as Moodboard).id, {
              id: image.id,
              moodboard: (res as Moodboard).id,
              image_url: image.image_url,
              title: image.title,
              source: image.source || 'uploaded',
              is_selected: true,
              x_position: image.x_position,
              y_position: image.y_position,
              canvas_width: image.canvas_width,
              canvas_height: image.canvas_height,
              z_index: image.z_index,
              opacity: image.opacity,
              rotation: image.rotation || 0,
              order_index: 0,
              created_at: new Date().toISOString()
            })
          } catch {
            // Silently handle individual image creation errors
          }
        }
      }
      
      // Add text elements to new moodboard
      if (res && textElements.value.length > 0) {
        for (const textElement of textElements.value) {
          try {
            await createTextElement((res as Moodboard).id, textElement)
          } catch {
            // Silently handle individual text element creation errors
          }
        }
      }
      
      // Set current moodboard for drawing save
      if (res) {
        currentMoodboard.value = res as Moodboard
        // Save drawing data
        await saveDrawingAsImage()
      }
      
      if (res) {
        await router.push('/moodboards')
      }
    }
    
    showSaveModal.value = false
    showToast('Moodboard saved successfully!', 'success')
    
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { error?: string } } }

    showToast(apiError.response?.data?.error || 'Failed to save moodboard', 'error')
  } finally {
    saving.value = false
  }
}

// AI Suggestions Handlers
const handleApplySuggestion = (index: number) => {
  const newPrompt = aiSuggestions.applySuggestion(index, prompt.value)
  prompt.value = newPrompt
}

const handleUnapplySuggestion = (index: number) => {
  aiSuggestions.unapplySuggestion(index)
}

const handleRegenerateSuggestions = () => {
  aiSuggestions.regenerateSuggestions({
    numSuggestions: 3
  })
}

const handleAIModeChanged = (mode: 'default' | 'gaming') => {
  aiSuggestions.setMode(mode)
}

const handleAITypeChanged = (type: 'short' | 'long') => {
  aiSuggestions.setSuggestionType(type)
}

const handleGenerateAISuggestions = () => {
  if (prompt.value.trim().length >= 3) {
    aiSuggestions.generateSuggestions(prompt.value, {
      mode: dropdownMode.value as 'default' | 'gaming',
      numSuggestions: 3
    })
  } else if (prompt.value.trim()) {
    // Let the composable handle the validation error
    aiSuggestions.generateSuggestions(prompt.value, {
      mode: dropdownMode.value as 'default' | 'gaming',
      numSuggestions: 3
    })
  } else {
    // Handle case when no prompt is provided
  }
}

const handleFetchAIServices = () => {
  aiSuggestions.fetchServices()
}

const handleServiceChanged = (serviceId: string) => {
  // Update the active service in the AI suggestions composable
  aiSuggestions.setActiveService(serviceId || null)
}

const handleClearError = () => {
  // Clear the error when service changes
  aiSuggestions.clearError()
}

// Note: Auto-generation removed - suggestions are only generated when user clicks the Generate button
</script>

<style scoped>
.moodboard-container {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 1rem;
  padding-bottom: 7rem;
}

.moodboard-container.grid-mode {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  padding-bottom: 7rem;
}

.moodboard-container.canvas-mode {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 1rem;
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

.mode-toggle-container {
  margin-right: 1rem;
}

.canvas-container {
  width: 100%;
  height: 70vh;
  min-height: 600px;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
}

.mode-toggle-container {
  margin-right: 1rem;
}

.canvas-container {
  width: 100%;
  height: 70vh;
  min-height: 600px;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
}

.mode-toggle-container {
  margin-right: 1rem;
}

.canvas-container {
  width: 100%;
  height: calc(100vh - 180px);
  min-height: 600px;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
  background: #f9fafb;
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

.images-list.full-width {
  justify-content: center;
  max-width: none;
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

/* Image container with overlay for edit/remove buttons */
.image-container {
  position: relative;
  display: inline-block;
}

.image-container:hover .image-overlay {
  opacity: 1;
}

.image-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s ease;
  z-index: 10;
}

.edit-image-btn {
  min-width: 32px;
  min-height: 32px;
  border-radius: 0.375rem;
  padding: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.edit-image-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

/* Moodboard image container with remove button */
.moodboard-image-item .image-container {
  position: relative;
  display: inline-block;
}

.remove-image-btn {
  min-width: 32px;
  min-height: 32px;
  border-radius: 0.375rem;
  padding: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.remove-image-btn:hover {
  transform: scale(1.05);
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

/* Drawing Tools Styling */
.drawing-tools-toolbar {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.pen-btn-pen {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
}

.pen-btn-marker {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
}

.pen-btn-pencil {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
}

.pen-btn-highlighter {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.pen-btn-spray {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.pen-btn-watercolor {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
}

html[data-theme="dark"] .drawing-tools-toolbar, .dark .drawing-tools-toolbar {
  background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
  border: 1px solid #374151;
}
</style>
