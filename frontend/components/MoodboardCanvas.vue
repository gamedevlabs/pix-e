<template>
  <div class="moodboard-canvas-wrapper">
    <div class="moodboard-canvas-container">
    <!-- Canvas Toolbar -->
    <div class="canvas-toolbar">
      <div class="toolbar-section">
        <h3>Canvas Tools</h3>
        <UButtonGroup>
          <UButton 
            :variant="canvasMode === 'select' ? 'solid' : 'outline'"
            icon="i-heroicons-cursor-arrow-rays"
            @click="setCanvasMode('select')"
          >
            Select
          </UButton>
          <UButton 
            :variant="canvasMode === 'text' ? 'solid' : 'outline'"
            icon="i-heroicons-document-text"
            @click="setCanvasMode('text')"
          >
            Text
          </UButton>
          <UButton 
            :variant="canvasMode === 'image' ? 'solid' : 'outline'"
            icon="i-heroicons-photo"
            @click="openImageMode"
          >
            Image
          </UButton>
        </UButtonGroup>
      </div>

      <div class="toolbar-section">
        <h3>View</h3>
        <UButtonGroup>
          <UButton 
            :variant="showGrid ? 'solid' : 'outline'"
            icon="i-heroicons-squares-2x2"
            @click="toggleGrid"
          >
            Grid
          </UButton>
          <UButton 
            icon="i-heroicons-minus"
            @click="zoomOut"
          >
            {{ Math.round(zoomLevel * 100) }}%
          </UButton>
          <UButton 
            icon="i-heroicons-plus"
            @click="zoomIn"
          />
        </UButtonGroup>
      </div>

      <div class="toolbar-section">
        <h3>Layout</h3>
        <UButtonGroup>
          <UButton 
            icon="i-heroicons-arrow-up"
            :disabled="selectedElements.length < 2"
            @click="alignTop"
          >
            Align Top
          </UButton>
          <UButton 
            icon="i-heroicons-arrow-left"
            :disabled="selectedElements.length < 2"
            @click="alignLeft"
          >
            Align Left
          </UButton>
          <UButton 
            icon="i-heroicons-squares-plus"
            :disabled="selectedElements.length < 3"
            @click="distributeHorizontally"
          >
            Distribute
          </UButton>
        </UButtonGroup>
      </div>

      <div class="toolbar-section">
        <h3>Layering</h3>
        <UButtonGroup>
          <UButton 
            icon="i-heroicons-arrow-up-20-solid"
            size="xs"
            :disabled="selectedElements.length !== 1 || !canBringToFront()"
            @click="bringToFront"
            title="Bring to Front"
          >
            Front
          </UButton>
          <UButton 
            icon="i-heroicons-arrow-up-20-solid"
            size="xs"
            :disabled="selectedElements.length !== 1 || !canBringForward()"
            @click="bringForward"
            title="Bring Forward"
          >
            Forward
          </UButton>
          <UButton 
            icon="i-heroicons-arrow-down-20-solid"
            size="xs"
            :disabled="selectedElements.length !== 1 || !canSendBackward()"
            @click="sendBackward"
            title="Send Backward"
          >
            Backward
          </UButton>
          <UButton 
            icon="i-heroicons-arrow-down-20-solid"
            size="xs"
            :disabled="selectedElements.length !== 1 || !canSendToBack()"
            @click="sendToBack"
            title="Send to Back"
          >
            Back
          </UButton>
        </UButtonGroup>
      </div>

      <div class="toolbar-section">
        <h3>Export</h3>
        <UButton icon="i-heroicons-arrow-down-tray" @click="() => exportCanvas('png')">
          Export PNG
        </UButton>
      </div>
    </div>

    <!-- Canvas Area -->
    <div 
      class="canvas-wrapper" 
      :style="{ 
        '--zoom-level': zoomLevel,
        '--canvas-width': `${canvasSettings.canvas_width}px`,
        '--canvas-height': `${canvasSettings.canvas_height}px`
      }"
    >
      <div 
        ref="canvasElement"
        class="moodboard-canvas"
        :class="{ 
          'show-grid': showGrid,
          'snap-enabled': snapToGrid,
          'mode-text': canvasMode === 'text',
          'mode-image': canvasMode === 'image',
          'mode-select': canvasMode === 'select'
        }"
        :style="{
          width: `${canvasSettings.canvas_width}px`,
          height: `${canvasSettings.canvas_height}px`,
          backgroundColor: canvasSettings.canvas_background_color,
          backgroundImage: canvasSettings.canvas_background_image ? `url(${canvasSettings.canvas_background_image})` : 'none'
        }"
        @click="handleCanvasClick"
        @dragover.prevent
        @drop="handleDrop"
      >
        <!-- Grid overlay -->
        <div 
          v-if="showGrid" 
          class="grid-overlay"
          :style="{
            backgroundSize: `${canvasSettings.grid_size}px ${canvasSettings.grid_size}px`
          }"
        />

        <!-- Images on canvas -->
        <CanvasImageElement
          v-for="image in canvasImages"
          :key="image.id"
          :image="image"
          :selected="selectedElements.includes(image.id)"
          :zoom-level="zoomLevel"
          :snap-to-grid="snapToGrid"
          :grid-size="canvasSettings.grid_size"
          @select="selectElement"
          @update="updateImagePosition"
          @delete="deleteElement"
          @drag-start="bringImageToFrontOnDrag"
        />

        <!-- Text elements on canvas -->
        <CanvasTextElement
          v-for="textElement in canvasTextElements"
          :key="textElement.id"
          :text-element="textElement"
          :selected="selectedElements.includes(textElement.id)"
          :zoom-level="zoomLevel"
          :snap-to-grid="snapToGrid"
          :grid-size="canvasSettings.grid_size"
          @select="selectElement"
          @update="updateTextElement"
          @delete="deleteElement"
        />

        <!-- Drawing Canvas Overlay -->
        <canvas
          v-if="props.drawingMode && props.drawingMode !== 'move'"
          ref="drawingCanvas"
          class="drawing-canvas"
          :width="canvasSettings.canvas_width"
          :height="canvasSettings.canvas_height"
          :style="{
            position: 'absolute',
            top: 0,
            left: 0,
            zIndex: 1000,
            pointerEvents: props.drawingMode === 'draw' || props.drawingMode === 'erase' ? 'auto' : 'none',
            cursor: props.drawingMode === 'draw' ? 'crosshair' : props.drawingMode === 'erase' ? 'grab' : 'default'
          }"
          @mousedown="startDrawing"
          @mousemove="draw"
          @mouseup="stopDrawing"
          @mouseleave="stopDrawing"
          @touchstart="handleTouchStart"
          @touchmove="handleTouchMove"
          @touchend="handleTouchEnd"
        />

        <!-- Selection box -->
        <div 
          v-if="selectionBox.visible"
          class="selection-box"
          :style="{
            left: `${selectionBox.x}px`,
            top: `${selectionBox.y}px`,
            width: `${selectionBox.width}px`,
            height: `${selectionBox.height}px`
          }"
        />
      </div>
    </div>

    <!-- Properties Panel -->
    <div v-if="selectedElements.length > 0" class="properties-panel">
      <h3>Properties</h3>
      <div v-if="selectedElementData">
        <!-- Position controls -->
        <div class="property-group">
          <label>Position</label>
          <div class="input-row">
            <UInput 
              v-model.number="selectedElementData.x_position" 
              placeholder="X"
              @update:model-value="updateSelectedElement"
            />
            <UInput 
              v-model.number="selectedElementData.y_position" 
              placeholder="Y"
              @update:model-value="updateSelectedElement"
            />
          </div>
        </div>

        <!-- Size controls -->
        <div class="property-group">
          <label>Size</label>
          <div class="input-row">
            <UInput 
              :model-value="getElementWidth(selectedElementData)" 
              placeholder="Width"
              @update:model-value="updateElementWidth"
            />
            <UInput 
              :model-value="getElementHeight(selectedElementData)" 
              placeholder="Height"
              @update:model-value="updateElementHeight"
            />
          </div>
        </div>

        <!-- Typography controls (for text elements) -->
        <div v-if="isTextElement(selectedElementData)" class="property-group">
          <label class="font-semibold text-gray-700 mb-3 block">Typography</label>
          
          <!-- Font Family -->
          <div class="mb-3">
            <label class="text-sm text-gray-600 mb-1 block">Font Family</label>
            <USelect
              :model-value="(selectedElementData as MoodboardTextElement).font_family"
              :options="fontOptions"
              placeholder="Select font"
              @update:model-value="updateTextProperty('font_family', $event)"
            />
          </div>

          <!-- Font Size & Weight -->
          <div class="grid grid-cols-2 gap-2 mb-3">
            <div>
              <label class="text-sm text-gray-600 mb-1 block">Size</label>
              <UInput 
                :model-value="(selectedElementData as MoodboardTextElement).font_size" 
                placeholder="16"
                type="number"
                min="8"
                max="200"
                @update:model-value="updateTextProperty('font_size', Number($event))"
              />
            </div>
            <div>
              <label class="text-sm text-gray-600 mb-1 block">Weight</label>
              <USelect
                :model-value="(selectedElementData as MoodboardTextElement).font_weight"
                :options="fontWeightOptions"
                @update:model-value="updateTextProperty('font_weight', Number($event))"
              />
            </div>
          </div>

          <!-- Text Alignment -->
          <div class="mb-3">
            <label class="text-sm text-gray-600 mb-1 block">Alignment</label>
            <UButtonGroup class="w-full">
              <UButton 
                :variant="(selectedElementData as MoodboardTextElement).text_align === 'left' ? 'solid' : 'outline'"
                icon="i-heroicons-bars-3-bottom-left"
                size="sm"
                @click="updateTextProperty('text_align', 'left')"
              />
              <UButton 
                :variant="(selectedElementData as MoodboardTextElement).text_align === 'center' ? 'solid' : 'outline'"
                icon="i-heroicons-bars-3"
                size="sm"
                @click="updateTextProperty('text_align', 'center')"
              />
              <UButton 
                :variant="(selectedElementData as MoodboardTextElement).text_align === 'right' ? 'solid' : 'outline'"
                icon="i-heroicons-bars-3-bottom-right"
                size="sm"
                @click="updateTextProperty('text_align', 'right')"
              />
              <UButton 
                :variant="(selectedElementData as MoodboardTextElement).text_align === 'justify' ? 'solid' : 'outline'"
                icon="i-heroicons-bars-4"
                size="sm"
                @click="updateTextProperty('text_align', 'justify')"
              />
            </UButtonGroup>
          </div>

          <!-- Line Height & Letter Spacing -->
          <div class="grid grid-cols-2 gap-2 mb-3">
            <div>
              <label class="text-sm text-gray-600 mb-1 block">Line Height</label>
              <UInput 
                :model-value="(selectedElementData as MoodboardTextElement).line_height" 
                placeholder="1.4"
                type="number"
                step="0.1"
                min="0.5"
                max="3"
                @update:model-value="updateTextProperty('line_height', Number($event))"
              />
            </div>
            <div>
              <label class="text-sm text-gray-600 mb-1 block">Letter Spacing</label>
              <UInput 
                :model-value="(selectedElementData as MoodboardTextElement).letter_spacing" 
                placeholder="0"
                type="number"
                step="0.5"
                min="-5"
                max="10"
                @update:model-value="updateTextProperty('letter_spacing', Number($event))"
              />
            </div>
          </div>

          <!-- Colors -->
          <div class="mb-3">
            <label class="text-sm text-gray-600 mb-1 block">Text Color</label>
            <div class="flex gap-2">
              <UInput 
                :model-value="(selectedElementData as MoodboardTextElement).text_color" 
                type="color"
                class="w-16"
                @update:model-value="updateTextProperty('text_color', $event)"
              />
              <UInput 
                :model-value="(selectedElementData as MoodboardTextElement).text_color" 
                placeholder="#000000"
                class="flex-1"
                @update:model-value="updateTextProperty('text_color', $event)"
              />
            </div>
          </div>

          <!-- Background Color -->
          <div class="mb-3">
            <label class="text-sm text-gray-600 mb-1 block">Background</label>
            <div class="flex gap-2">
              <UInput 
                :model-value="(selectedElementData as MoodboardTextElement).background_color || '#ffffff'" 
                type="color"
                class="w-16"
                @update:model-value="updateTextProperty('background_color', $event)"
              />
              <UInput 
                :model-value="(selectedElementData as MoodboardTextElement).background_color || ''" 
                placeholder="Transparent"
                class="flex-1"
                @update:model-value="updateTextProperty('background_color', $event)"
              />
              <UButton 
                size="sm" 
                variant="outline"
                @click="updateTextProperty('background_color', '')"
              >
                Clear
              </UButton>
            </div>
          </div>

          <!-- Border -->
          <div class="mb-3">
            <label class="text-sm text-gray-600 mb-1 block">Border</label>
            <div class="grid grid-cols-2 gap-2 mb-2">
              <UInput 
                :model-value="(selectedElementData as MoodboardTextElement).border_width" 
                placeholder="Width"
                type="number"
                min="0"
                max="20"
                @update:model-value="updateTextProperty('border_width', Number($event))"
              />
              <UInput 
                :model-value="(selectedElementData as MoodboardTextElement).border_color || '#000000'" 
                type="color"
                @update:model-value="updateTextProperty('border_color', $event)"
              />
            </div>
          </div>

          <!-- Text Style Presets -->
          <div class="mb-3">
            <label class="text-sm text-gray-600 mb-1 block">Quick Styles</label>
            <div class="grid grid-cols-2 gap-1">
              <UButton size="xs" variant="outline" @click="applyTextStyle('heading')">Heading</UButton>
              <UButton size="xs" variant="outline" @click="applyTextStyle('subheading')">Subheading</UButton>
              <UButton size="xs" variant="outline" @click="applyTextStyle('body')">Body Text</UButton>
              <UButton size="xs" variant="outline" @click="applyTextStyle('caption')">Caption</UButton>
              <UButton size="xs" variant="outline" @click="applyTextStyle('quote')">Quote</UButton>
              <UButton size="xs" variant="outline" @click="applyTextStyle('accent')">Accent</UButton>
            </div>
          </div>
        </div>

        <!-- Layer controls -->
        <div class="property-group">
          <label>Layer</label>
          <div class="input-row">
            <UInput 
              v-model.number="selectedElementData.z_index" 
              placeholder="Z-Index"
              @update:model-value="updateSelectedElement"
            />
            <UInput 
              v-model.number="selectedElementData.opacity" 
              placeholder="Opacity"
              step="0.1"
              min="0"
              max="1"
              @update:model-value="updateSelectedElement"
            />
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Image Upload Modal -->
  <UModal 
    v-model:open="showImageUpload"
    title="Add Image" 
    description="Upload an image file or paste an image URL to add to your moodboard."
    :ui="{ footer: 'justify-end' }"
  >
    <template #body>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Upload Image
          </label>
          <input 
            type="file" 
            accept="image/*" 
            class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            @change="handleImageUpload"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Or paste URL
          </label>
          <UInput v-model="imageUrl" placeholder="https://example.com/image.jpg" />
        </div>
      </div>
    </template>
    
    <template #footer>
      <UButton 
        label="Cancel" 
        color="neutral" 
        variant="outline" 
        @click="closeImageModal" 
      />
      <UButton 
        label="Add Image"
        :disabled="!imageUrl" 
        @click="addImageFromUrl"
      />
    </template>
  </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRuntimeConfig } from '#imports'
import type { MoodboardImage, MoodboardTextElement, Moodboard } from '~/composables/useMoodboards'
import { useMoodboards } from '~/composables/useMoodboards'

interface DrawingLayer {
  id: string
  name: string
  canvas: HTMLCanvasElement
  visible: boolean
  opacity: number
  blendMode: string
}

interface Props {
  moodboard: Moodboard
  images: MoodboardImage[]
  textElements: MoodboardTextElement[]
  canEdit: boolean
  drawingMode?: 'move' | 'draw' | 'erase'
  penType?: 'pen' | 'marker' | 'pencil' | 'highlighter' | 'spray' | 'watercolor'
  brushSize?: number
  brushColor?: string
  brushOpacity?: number
  brushHardness?: number
  flowRate?: number
  blendMode?: 'source-over' | 'multiply' | 'screen' | 'overlay' | 'soft-light' | 'hard-light' | 'color-dodge' | 'color-burn' | 'difference' | 'exclusion'
  drawingHistory?: ImageData[]
  historyStep?: number
}

interface CanvasSettings {
  canvas_width: number
  canvas_height: number
  canvas_background_color: string
  canvas_background_image?: string
  grid_enabled: boolean
  grid_size: number
  snap_to_grid: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'image-updated': [image: MoodboardImage]
  updateTextElement: [textElement: MoodboardTextElement]
  'update-text-element': [textElement: MoodboardTextElement]
  'delete-element': [elementId: string]
  deleteElement: [elementId: string]
  'image-removed': [elementId: string]
  addImage: [imageData: Partial<MoodboardImage>]
  addTextElement: [textElement: MoodboardTextElement]
  moodboardUpdated: [moodboard: Moodboard]
  'drawing-state-saved': [imageData: ImageData]
}>()

// Canvas state
const canvasElement = ref<HTMLElement>()
const canvasMode = ref<'select' | 'text' | 'image'>('select')
const lastModeChangeTime = ref(0)
const zoomLevel = ref(1)
const showGrid = ref(true)
const snapToGrid = ref(true)
const selectedElements = ref<string[]>([])

// Drawing state
const drawingCanvas = ref<HTMLCanvasElement>()
const isDrawing = ref(false)
const lastDrawPosition = ref<{ x: number, y: number } | null>(null)
const lastDrawTime = ref<number>(0)
const drawingVelocity = ref<number>(0)
const brushAngle = ref<number>(0)

// Selection box for multi-select
const selectionBox = ref({
  visible: false,
  x: 0,
  y: 0,
  width: 0,
  height: 0
})

// Image upload
const showImageUpload = ref(false)
const imageUrl = ref('')

// Watch for changes to showImageUpload
watch(showImageUpload, (newValue: boolean) => {
  
})

// Watch for canvas mode changes
watch(canvasMode, (newMode: string, oldMode: string) => {
  
  // Ensure modal is closed when leaving image mode
  if (oldMode === 'image' && newMode !== 'image') {
    showImageUpload.value = false
  }
})

// Lifecycle hooks
onMounted(() => {
  
  // Ensure modal is closed on mount
  nextTick(() => {
    showImageUpload.value = false
    imageUrl.value = ''
    
  })
})

// Canvas settings
const canvasSettings = computed<CanvasSettings>(() => ({
  canvas_width: props.moodboard.canvas_width || 1920,
  canvas_height: props.moodboard.canvas_height || 1080,
  canvas_background_color: props.moodboard.canvas_background_color || '#FFFFFF',
  canvas_background_image: props.moodboard.canvas_background_image,
  grid_enabled: props.moodboard.grid_enabled ?? true,
  grid_size: props.moodboard.grid_size || 20,
  snap_to_grid: props.moodboard.snap_to_grid ?? true
}))

// API composable
const {
  updateImagePosition: apiUpdateImagePosition,
  createTextElement: apiCreateTextElement,
  updateTextElement: apiUpdateTextElement,
  deleteTextElement: apiDeleteTextElement,
  exportCanvas: apiExportCanvas,
  autoLayoutCanvas: apiAutoLayoutCanvas,
  importImagesToCanvas: apiImportImagesToCanvas
} = useMoodboards()

// Canvas elements
const canvasImages = computed(() => 
  props.images.map((img: MoodboardImage, index: number) => ({
    ...img,
    // Set reasonable default canvas dimensions if not set or too small (likely thumbnails)
    canvas_width: img.canvas_width && img.canvas_width > 250 ? img.canvas_width : 350,
    canvas_height: img.canvas_height && img.canvas_height > 250 ? img.canvas_height : 350,
    // Handle positioning: if position is 0,0 (default/overlapping), use smart defaults
    x_position: (img.x_position !== 0 || img.y_position !== 0) 
      ? img.x_position 
      : 50 + (index % 3) * 370,
    y_position: (img.x_position !== 0 || img.y_position !== 0) 
      ? img.y_position 
      : 50 + Math.floor(index / 3) * 370,
    z_index: img.z_index || (index + 1),
    opacity: img.opacity !== undefined ? img.opacity : 1.0,
    rotation: img.rotation || 0
  }))
)

const canvasTextElements = computed(() => 
  props.textElements.map((text: MoodboardTextElement, index: number) => ({
    ...text,
    // Set default dimensions if not set
    x_position: text.x_position !== undefined ? text.x_position : 50 + (index % 2) * 300,
    y_position: text.y_position !== undefined ? text.y_position : 50 + Math.floor(index / 2) * 80,
    width: text.width || 200,
    height: text.height || 50
  }))
)

// Selected element data
const selectedElementData = computed(() => {
  if (selectedElements.value.length !== 1) return null
  
  const selectedId = selectedElements.value[0]
  return canvasImages.value.find((img: MoodboardImage) => img.id === selectedId) || 
         canvasTextElements.value.find((text: MoodboardTextElement) => text.id === selectedId)
})

// Export options
const exportOptions = [
  { label: 'PNG', click: () => exportCanvas('png') },
  { label: 'JPG', click: () => exportCanvas('jpg') },
  { label: 'PDF', click: () => exportCanvas('pdf') },
  { label: 'SVG', click: () => exportCanvas('svg') }
]

// Font options
const fontOptions = [
  { label: 'Inter', value: 'Inter' },
  { label: 'Helvetica', value: 'Helvetica' },
  { label: 'Arial', value: 'Arial' },
  { label: 'Times New Roman', value: 'Times New Roman' },
  { label: 'Georgia', value: 'Georgia' },
  { label: 'Roboto', value: 'Roboto' },
  { label: 'Open Sans', value: 'Open Sans' },
  { label: 'Lato', value: 'Lato' },
  { label: 'Montserrat', value: 'Montserrat' },
  { label: 'Courier New', value: 'Courier New' }
]

// Font weight options
const fontWeightOptions = [
  { label: 'Thin (100)', value: 100 },
  { label: 'Extra Light (200)', value: 200 },
  { label: 'Light (300)', value: 300 },
  { label: 'Regular (400)', value: 400 },
  { label: 'Medium (500)', value: 500 },
  { label: 'Semi Bold (600)', value: 600 },
  { label: 'Bold (700)', value: 700 },
  { label: 'Extra Bold (800)', value: 800 },
  { label: 'Black (900)', value: 900 }
]

// Text style presets
const textStylePresets = {
  heading: {
    font_size: 32,
    font_weight: 700,
    line_height: 1.2,
    letter_spacing: -0.5
  },
  subheading: {
    font_size: 24,
    font_weight: 600,
    line_height: 1.3,
    letter_spacing: 0
  },
  body: {
    font_size: 16,
    font_weight: 400,
    line_height: 1.5,
    letter_spacing: 0
  },
  caption: {
    font_size: 12,
    font_weight: 400,
    line_height: 1.4,
    letter_spacing: 0.5
  },
  quote: {
    font_size: 18,
    font_weight: 400,
    line_height: 1.6,
    letter_spacing: 0,
    font_family: 'Georgia'
  },
  accent: {
    font_size: 20,
    font_weight: 600,
    line_height: 1.3,
    letter_spacing: 1,
    text_color: '#2563eb'
  }
}

// Methods
function setCanvasMode(mode: typeof canvasMode.value) {
  canvasMode.value = mode
  lastModeChangeTime.value = Date.now()
  // Close the image upload modal when switching away from image mode
  if (mode !== 'image') {
    closeImageModal()
  }
  // Clear selection when switching modes
  selectedElements.value = []
  
  
}

function openImageMode() {
  setCanvasMode('image')
  // Open the modal immediately when clicking the Image button
  showImageUpload.value = true
  
}

function toggleGrid() {
  showGrid.value = !showGrid.value
}

function zoomIn() {
  zoomLevel.value = Math.min(zoomLevel.value + 0.1, 3)
}

function zoomOut() {
  zoomLevel.value = Math.max(zoomLevel.value - 0.1, 0.1)
}

function selectElement(elementId: string, multiSelect = false) {
  if (multiSelect) {
    const index = selectedElements.value.indexOf(elementId)
    if (index > -1) {
      selectedElements.value.splice(index, 1)
    } else {
      selectedElements.value.push(elementId)
    }
  } else {
    selectedElements.value = [elementId]
  }
}

// Auto bring to front when starting to drag an image
function bringImageToFrontOnDrag(imageId: string) {
  const selectedImage = canvasImages.value.find(img => img.id === imageId)
  if (selectedImage) {
    // Get the current highest z-index
    const maxZIndex = Math.max(...canvasImages.value.map(img => img.z_index || 0))
    
    // Only update if this image doesn't already have the highest z-index
    if ((selectedImage.z_index || 0) < maxZIndex) {
      const updatedImage = { ...selectedImage, z_index: maxZIndex + 1 }
      updateImagePosition(updatedImage)
    }
  }
}

function handleCanvasClick(event: MouseEvent) {
  
  
  // Prevent immediate clicks after mode change (give 200ms buffer)
  const timeSinceLastModeChange = Date.now() - lastModeChangeTime.value
  if (timeSinceLastModeChange < 200) {
    
    return
  }
  
  if (canvasMode.value === 'text') {
    addTextElement(event)
  } else if (canvasMode.value === 'image') {
    // Open image upload modal when clicking on canvas in image mode
    
    showImageUpload.value = true
  } else if (canvasMode.value === 'select') {
    // Clear selection if clicking on empty canvas
    if (event.target === canvasElement.value) {
      selectedElements.value = []
    }
  }
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    handleImageUpload({ target: { files } } as any)
  }
}

async function addTextElement(event: MouseEvent) {
  const rect = canvasElement.value!.getBoundingClientRect()
  const x = (event.clientX - rect.left) / zoomLevel.value
  const y = (event.clientY - rect.top) / zoomLevel.value
  
  const textData = {
    content: 'New Text',
    x_position: x,
    y_position: y,
    width: 200,
    height: 50,
    font_family: 'Inter',
    font_size: 16,
    text_color: '#000000',
    is_selected: true,
    z_index: 1,
    opacity: 1
    // Don't include moodboard - it's set by the backend in perform_create
  }
  
  
  
  try {
    const createdTextElement = await apiCreateTextElement(props.moodboard.id, textData) as MoodboardTextElement
    // Only emit if API call was successful and return the created element with proper ID
    emit('addTextElement', createdTextElement)
    canvasMode.value = 'select'
  } catch (error) {
    // Don't emit on error - this prevents adding invalid elements to frontend state
  }
}

async function updateImagePosition(updatedImage: MoodboardImage) {
  try {
    await apiUpdateImagePosition(props.moodboard.id, updatedImage.id, updatedImage)
    emit('image-updated', updatedImage)
  } catch (error) {
    // Silently handle image update errors in production
  }
}

async function updateTextElement(updatedText: MoodboardTextElement) {
  try {
    await apiUpdateTextElement(props.moodboard.id, updatedText.id, updatedText)
    emit('update-text-element', updatedText)
  } catch (error) {
    // Silently handle text element update errors in production
  }
}

async function updateSelectedElement() {
  if (selectedElementData.value) {
    if (isTextElement(selectedElementData.value)) {
      await updateTextElement(selectedElementData.value as MoodboardTextElement)
    } else {
      await updateImagePosition(selectedElementData.value as MoodboardImage)
    }
  }
}

function applyTextStyle(styleName: string) {
  if (selectedElementData.value && isTextElement(selectedElementData.value)) {
    const textElement = selectedElementData.value as MoodboardTextElement
    const preset = textStylePresets[styleName as keyof typeof textStylePresets]
    
    if (preset) {
      // Apply all properties from the preset
      Object.keys(preset).forEach(key => {
        (textElement as any)[key] = (preset as any)[key]
      })
      updateSelectedElement()
    }
  }
}

function isTextElement(element: any): element is MoodboardTextElement {
  return element && 'content' in element
}

function getElementWidth(element: any): number {
  if (isTextElement(element)) {
    return element.width
  } else {
    return element.canvas_width
  }
}

function getElementHeight(element: any): number {
  if (isTextElement(element)) {
    return element.height
  } else {
    return element.canvas_height
  }
}

function updateElementWidth(value: number) {
  if (selectedElementData.value) {
    if (isTextElement(selectedElementData.value)) {
      const updated = { ...selectedElementData.value, width: value }
      emit('updateTextElement', updated)
    } else {
      const updated = { ...selectedElementData.value, canvas_width: value }
      emit('image-updated', updated)
    }
  }
}

function updateElementHeight(value: number) {
  if (selectedElementData.value) {
    if (isTextElement(selectedElementData.value)) {
      const updated = { ...selectedElementData.value, height: value }
      emit('updateTextElement', updated)
    } else {
      const updated = { ...selectedElementData.value, canvas_height: value }
      emit('image-updated', updated)
    }
  }
}

function updateTextProperty(property: string, value: any) {
  if (selectedElementData.value && isTextElement(selectedElementData.value)) {
    const textElement = selectedElementData.value as MoodboardTextElement;
    (textElement as any)[property] = value
    updateSelectedElement()
  }
}

async function deleteElement(elementId: string) {
  try {
    // Check if it's a text element
    const textElement = canvasTextElements.value.find((text: MoodboardTextElement) => text.id === elementId)
    if (textElement) {
      await apiDeleteTextElement(props.moodboard.id, elementId)
      emit('delete-element', elementId)
    } else {
      // It's an image element
      const imageElement = canvasImages.value.find((img: MoodboardImage) => img.id === elementId)
      if (imageElement) {
        emit('image-removed', elementId)
      }
    }
    
    selectedElements.value = selectedElements.value.filter((id: string) => id !== elementId)
  } catch (error) {
    // Silently handle element deletion errors in production
  }
}

async function handleImageUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    try {
      // Create an image using the proper file upload endpoint
      const formData = new FormData()
      formData.append('image_file', file)
      formData.append('title', file.name)
      formData.append('source', 'uploaded')
      formData.append('x_position', '100')
      formData.append('y_position', '100')
      formData.append('canvas_width', '200')
      formData.append('canvas_height', '200')
      formData.append('is_selected', 'true')
      formData.append('z_index', '1')
      formData.append('opacity', '1')

      const config = useRuntimeConfig()
      const csrfToken = useCookie('csrftoken').value
      
      const headers: Record<string, string> = {
        ...useRequestHeaders(['cookie'])
      }
      
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken
      }
      
      const response = await $fetch(`${config.public.apiBase}/moodboards/${props.moodboard.id}/images/`, {
        method: 'POST',
        credentials: 'include',
        headers,
        body: formData
      })

      emit('addImage', response as MoodboardImage)
      closeImageModal()
    } catch (error) {
      // Silently handle file upload errors and close modal
      closeImageModal()
    }
  }
}

async function addImageFromUrl() {
  if (imageUrl.value) {
    try {
      const config = useRuntimeConfig()
      const csrfToken = useCookie('csrftoken').value
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...useRequestHeaders(['cookie'])
      }
      
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken
      }
      
      const response = await $fetch(`${config.public.apiBase}/moodboards/canvas/${props.moodboard.id}/import-image/`, {
        method: 'POST',
        credentials: 'include',
        headers,
        body: {
          image_url: imageUrl.value,
          x_position: 100,
          y_position: 100,
          canvas_width: 200,
          canvas_height: 200
        }
      })

      
      emit('addImage', response as Partial<MoodboardImage>)
      closeImageModal()
    } catch (error) {
      // Silently handle URL import errors and close modal
      closeImageModal()
    }
  }
}

function closeImageModal() {
  showImageUpload.value = false
  imageUrl.value = ''
}

function alignTop() {
  if (selectedElements.value.length < 2) return
  
  const selectedImages = canvasImages.value.filter(img => selectedElements.value.includes(img.id))
  if (selectedImages.length < 2) return
  
  // Find the topmost position
  const topPosition = Math.min(...selectedImages.map(img => img.y_position))
  
  // Update all selected images to align to top
  selectedImages.forEach(img => {
    if (img.y_position !== topPosition) {
      const updatedImage = { ...img, y_position: topPosition }
      updateImagePosition(updatedImage)
    }
  })
}

function alignLeft() {
  if (selectedElements.value.length < 2) return
  
  const selectedImages = canvasImages.value.filter(img => selectedElements.value.includes(img.id))
  if (selectedImages.length < 2) return
  
  // Find the leftmost position
  const leftPosition = Math.min(...selectedImages.map(img => img.x_position))
  
  // Update all selected images to align to left
  selectedImages.forEach(img => {
    if (img.x_position !== leftPosition) {
      const updatedImage = { ...img, x_position: leftPosition }
      updateImagePosition(updatedImage)
    }
  })
}

function distributeHorizontally() {
  if (selectedElements.value.length < 3) return
  
  const selectedImages = canvasImages.value.filter(img => selectedElements.value.includes(img.id))
  if (selectedImages.length < 3) return
  
  // Sort by x position
  selectedImages.sort((a, b) => a.x_position - b.x_position)
  
  const leftmost = selectedImages[0].x_position
  const rightmost = selectedImages[selectedImages.length - 1].x_position
  const totalSpacing = rightmost - leftmost
  const spaceBetween = totalSpacing / (selectedImages.length - 1)
  
  // Update positions for middle elements
  for (let i = 1; i < selectedImages.length - 1; i++) {
    const newX = leftmost + (i * spaceBetween)
    if (selectedImages[i].x_position !== newX) {
      const updatedImage = { ...selectedImages[i], x_position: newX }
      updateImagePosition(updatedImage)
    }
  }
}

// Z-index layering functions
function canBringToFront(): boolean {
  if (selectedElements.value.length !== 1) return false
  const selectedImage = canvasImages.value.find(img => img.id === selectedElements.value[0])
  if (!selectedImage) return false
  
  // Check if this image already has the highest z-index
  const maxZIndex = Math.max(...canvasImages.value.map(img => img.z_index || 0))
  return (selectedImage.z_index || 0) < maxZIndex
}

function canBringForward(): boolean {
  if (selectedElements.value.length !== 1) return false
  const selectedImage = canvasImages.value.find(img => img.id === selectedElements.value[0])
  if (!selectedImage) return false
  
  // Check if there's any image with a higher z-index
  return canvasImages.value.some(img => (img.z_index || 0) > (selectedImage.z_index || 0))
}

function canSendBackward(): boolean {
  if (selectedElements.value.length !== 1) return false
  const selectedImage = canvasImages.value.find(img => img.id === selectedElements.value[0])
  if (!selectedImage) return false
  
  // Check if there's any image with a lower z-index
  return canvasImages.value.some(img => (img.z_index || 0) < (selectedImage.z_index || 0))
}

function canSendToBack(): boolean {
  if (selectedElements.value.length !== 1) return false
  const selectedImage = canvasImages.value.find(img => img.id === selectedElements.value[0])
  if (!selectedImage) return false
  
  // Check if this image already has the lowest z-index
  const minZIndex = Math.min(...canvasImages.value.map(img => img.z_index || 0))
  return (selectedImage.z_index || 0) > minZIndex
}

function bringToFront() {
  if (selectedElements.value.length !== 1) return
  const selectedImage = canvasImages.value.find(img => img.id === selectedElements.value[0])
  if (!selectedImage) return
  
  // Set z-index to highest + 1
  const maxZIndex = Math.max(...canvasImages.value.map(img => img.z_index || 0))
  const updatedImage = { ...selectedImage, z_index: maxZIndex + 1 }
  updateImagePosition(updatedImage)
}

function bringForward() {
  if (selectedElements.value.length !== 1) return
  const selectedImage = canvasImages.value.find(img => img.id === selectedElements.value[0])
  if (!selectedImage) return
  
  const currentZIndex = selectedImage.z_index || 0
  // Find the next higher z-index
  const higherZIndexes = canvasImages.value
    .map(img => img.z_index || 0)
    .filter(z => z > currentZIndex)
    .sort((a, b) => a - b)
  
  if (higherZIndexes.length > 0) {
    const updatedImage = { ...selectedImage, z_index: higherZIndexes[0] + 1 }
    updateImagePosition(updatedImage)
  }
}

function sendBackward() {
  if (selectedElements.value.length !== 1) return
  const selectedImage = canvasImages.value.find(img => img.id === selectedElements.value[0])
  if (!selectedImage) return
  
  const currentZIndex = selectedImage.z_index || 0
  // Find the next lower z-index
  const lowerZIndexes = canvasImages.value
    .map(img => img.z_index || 0)
    .filter(z => z < currentZIndex)
    .sort((a, b) => b - a)
  
  if (lowerZIndexes.length > 0) {
    const updatedImage = { ...selectedImage, z_index: lowerZIndexes[0] - 1 }
    updateImagePosition(updatedImage)
  }
}

function sendToBack() {
  if (selectedElements.value.length !== 1) return
  const selectedImage = canvasImages.value.find(img => img.id === selectedElements.value[0])
  if (!selectedImage) return
  
  // Set z-index to lowest - 1
  const minZIndex = Math.min(...canvasImages.value.map(img => img.z_index || 0))
  const updatedImage = { ...selectedImage, z_index: minZIndex - 1 }
  updateImagePosition(updatedImage)
}

async function exportCanvas(format: string) {
  try {
    await exportCanvasAsImage(format)
  } catch (error) {
    // Export failed silently
  }
}

async function exportCanvasAsImage(format: string) {
  const canvas = canvasElement.value
  if (!canvas) {
    throw new Error('Canvas element not found')
  }

  const exportCanvas = document.createElement('canvas')
  const ctx = exportCanvas.getContext('2d')
  if (!ctx) {
    throw new Error('Could not get canvas context')
  }

  const canvasRect = canvas.getBoundingClientRect()
  const exportWidth = canvasRect.width
  const exportHeight = canvasRect.height
  
  exportCanvas.width = exportWidth
  exportCanvas.height = exportHeight

  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, exportWidth, exportHeight)

  const getActualElementDimensions = (elementId: string) => {
    const element = document.querySelector(`[data-image-id="${elementId}"]`) as HTMLElement
    if (element) {
      const rect = element.getBoundingClientRect()
      const canvasRect = canvas.getBoundingClientRect()
      
      return {
        x: rect.left - canvasRect.left,
        y: rect.top - canvasRect.top,
        width: rect.width,
        height: rect.height
      }
    }
    return null
  }

  const imagePromises = canvasImages.value.map(async (img) => {
    return new Promise<void>((resolve) => {
      if (!img.image_url) {
        resolve()
        return
      }

      const image = new Image()
      
      const tryLoadImage = (useCors: boolean) => {
        if (useCors) {
          image.crossOrigin = 'anonymous'
        } else {
          image.removeAttribute('crossorigin')
        }
        
        image.onload = () => {
          const actualDimensions = getActualElementDimensions(img.id.toString())
          
          let x, y, width, height
          
          if (actualDimensions) {
            x = actualDimensions.x
            y = actualDimensions.y
            width = actualDimensions.width
            height = actualDimensions.height
          } else {
            x = img.x_position || 0
            y = img.y_position || 0
            width = img.canvas_width || 200
            height = img.canvas_height || 200
          }
          
          ctx.save()
          
          if (img.rotation) {
            const centerX = x + width / 2
            const centerY = y + height / 2
            ctx.translate(centerX, centerY)
            ctx.rotate((img.rotation * Math.PI) / 180)
            ctx.translate(-centerX, -centerY)
          }
          
          if (img.opacity !== undefined && img.opacity !== 1) {
            ctx.globalAlpha = img.opacity
          }
          
          try {
            ctx.drawImage(image, x, y, width, height)
          } catch (drawError) {
            // Drawing failed silently
          }
          
          ctx.restore()
          resolve()
        }
        
        image.onerror = () => {
          if (useCors) {
            tryLoadImage(false)
            return
          }
          
          tryFetchProxy()
        }
        
        const tryFetchProxy = async () => {
          try {
            const response = await fetch(imageUrl)
            if (!response.ok) throw new Error(`HTTP ${response.status}`)
            
            const blob = await response.blob()
            const objectUrl = URL.createObjectURL(blob)
            
            const proxyImage = new Image()
            proxyImage.onload = () => {
              const actualDimensions = getActualElementDimensions(img.id.toString())
              
              let x, y, width, height
              
              if (actualDimensions) {
                x = actualDimensions.x
                y = actualDimensions.y
                width = actualDimensions.width
                height = actualDimensions.height
              } else {
                x = img.x_position || 0
                y = img.y_position || 0
                width = img.canvas_width || 200
                height = img.canvas_height || 200
              }
              
              ctx.save()
              
              if (img.rotation) {
                const centerX = x + width / 2
                const centerY = y + height / 2
                ctx.translate(centerX, centerY)
                ctx.rotate((img.rotation * Math.PI) / 180)
                ctx.translate(-centerX, -centerY)
              }
              
              if (img.opacity !== undefined && img.opacity !== 1) {
                ctx.globalAlpha = img.opacity
              }
              
              try {
                ctx.drawImage(proxyImage, x, y, width, height)
              } catch (drawError) {
                // Drawing failed silently
              }
              
              ctx.restore()
              URL.revokeObjectURL(objectUrl)
              resolve()
            }
            
            proxyImage.onerror = () => {
              URL.revokeObjectURL(objectUrl)
              drawPlaceholder()
            }
            
            proxyImage.src = objectUrl
            
          } catch (fetchError) {
            drawPlaceholder()
          }
        }
        
        const drawPlaceholder = () => {
          ctx.save()
          ctx.fillStyle = 'rgba(200, 200, 200, 0.5)'
          const x = (img.x_position || 0)
          const y = (img.y_position || 0)
          const width = (img.canvas_width || 200)
          const height = (img.canvas_height || 200)
          ctx.fillRect(x, y, width, height)
          ctx.restore()
          
          resolve()
        }
        
        let imageUrl = img.image_url
        if (imageUrl.startsWith('/')) {
          const config = useRuntimeConfig()
          imageUrl = `${config.public.apiBase}${imageUrl}`
        }
        
        const separator = imageUrl.includes('?') ? '&' : '?'
        imageUrl += `${separator}_t=${Date.now()}`
        
        image.src = imageUrl
      }
      
      tryLoadImage(true)
    })
  })

  const textPromises = canvasTextElements.value.map(async (textEl) => {
    return new Promise<void>((resolve) => {
      if (!textEl.content || textEl.content.trim() === '') {
        resolve()
        return
      }

      const textElement = document.querySelector(`[data-text-id="${textEl.id}"]`) as HTMLElement
      let x, y, fontSize
      
      if (textElement) {
        const rect = textElement.getBoundingClientRect()
        const canvasRect = canvas.getBoundingClientRect()
        
        x = rect.left - canvasRect.left
        y = rect.top - canvasRect.top + parseFloat(getComputedStyle(textElement).fontSize)
        fontSize = parseFloat(getComputedStyle(textElement).fontSize)
      } else {
        x = textEl.x_position || 0
        y = textEl.y_position || 0
        fontSize = textEl.font_size || 16
      }
      
      ctx.save()
      
      const fontWeight = textEl.font_weight || 'normal'
      const fontFamily = textEl.font_family || 'Arial'
      const textColor = textEl.text_color || '#000000'
      
      ctx.font = `${fontWeight} ${fontSize}px ${fontFamily}`
      ctx.fillStyle = textColor
      ctx.textAlign = (textEl.text_align as CanvasTextAlign) || 'left'
      
      if (textEl.opacity !== undefined && textEl.opacity !== 1) {
        ctx.globalAlpha = textEl.opacity
      }
      
      if (textEl.rotation) {
        ctx.translate(x, y)
        ctx.rotate((textEl.rotation * Math.PI) / 180)
        ctx.fillText(textEl.content, 0, 0)
      } else {
        ctx.fillText(textEl.content, x, y)
      }
      
      ctx.restore()
      resolve()
    })
  })

  await Promise.all([...imagePromises, ...textPromises])

  // Add drawing layer to export if it exists
  if (drawingCanvas.value) {
    const drawingCtx = drawingCanvas.value.getContext('2d')
    if (drawingCtx) {
      const drawingImageData = drawingCtx.getImageData(0, 0, drawingCanvas.value.width, drawingCanvas.value.height)
      
      // Check if there's actually any drawing content
      const hasDrawing = drawingImageData.data.some((value, index) => {
        // Check alpha channel (every 4th value)
        return index % 4 === 3 && value > 0
      })
      
      if (hasDrawing) {
        // Create a temporary canvas for the drawing data
        const tempCanvas = document.createElement('canvas')
        tempCanvas.width = drawingCanvas.value.width
        tempCanvas.height = drawingCanvas.value.height
        const tempCtx = tempCanvas.getContext('2d')
        
        if (tempCtx) {
          tempCtx.putImageData(drawingImageData, 0, 0)
          
          // Draw the drawing layer onto the export canvas
          ctx.drawImage(tempCanvas, 0, 0, exportWidth, exportHeight)
        }
      }
    }
  }

  return new Promise<void>((resolve, reject) => {
    const mimeType = format === 'jpg' ? 'image/jpeg' : 'image/png'
    const quality = format === 'jpg' ? 0.9 : undefined
    
    exportCanvas.toBlob((blob) => {
      if (!blob) {
        reject(new Error('Failed to create blob'))
        return
      }
      
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `moodboard-${props.moodboard.title || 'untitled'}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      resolve()
    }, mimeType, quality)
  })
}

// Drawing Functions
function getCanvasPosition(event: MouseEvent | Touch): { x: number, y: number } {
  if (!drawingCanvas.value) return { x: 0, y: 0 }
  
  const rect = drawingCanvas.value.getBoundingClientRect()
  return {
    x: (event.clientX - rect.left) / zoomLevel.value,
    y: (event.clientY - rect.top) / zoomLevel.value
  }
}

function startDrawing(event: MouseEvent) {
  if (!props.drawingMode || props.drawingMode === 'move') return
  
  isDrawing.value = true
  const pos = getCanvasPosition(event)
  lastDrawPosition.value = pos
  lastDrawTime.value = Date.now()
  drawingVelocity.value = 0
  
  if (props.drawingMode === 'draw') {
    drawDot(pos.x, pos.y)
  }
  
  // Save current state for undo functionality
  saveCurrentDrawingState()
}

function draw(event: MouseEvent) {
  if (!isDrawing.value || !props.drawingMode || props.drawingMode === 'move') return
  if (!drawingCanvas.value || !lastDrawPosition.value) return
  
  const ctx = drawingCanvas.value.getContext('2d')
  if (!ctx) return
  
  const pos = getCanvasPosition(event)
  
  // Calculate pressure simulation based on movement speed
  const currentTime = Date.now()
  const timeDelta = currentTime - lastDrawTime.value
  const distance = Math.sqrt((pos.x - lastDrawPosition.value.x) ** 2 + (pos.y - lastDrawPosition.value.y) ** 2)
  
  if (timeDelta > 0) {
    drawingVelocity.value = distance / timeDelta
    // Simulate pressure: slower movement = more pressure
    const simulatedPressure = Math.max(0.3, Math.min(1.0, 1.0 - (drawingVelocity.value * 0.5)))
    
    // Calculate brush angle based on movement direction
    if (distance > 2) {
      brushAngle.value = Math.atan2(pos.y - lastDrawPosition.value.y, pos.x - lastDrawPosition.value.x)
    }
    
    const penType = props.penType || 'pen'
    const brushSize = (props.brushSize || 5) * simulatedPressure
    const brushColor = props.brushColor || '#000000'
    const brushOpacity = (props.brushOpacity || 1) * simulatedPressure
    const brushHardness = props.brushHardness || 80
    const flowRate = (props.flowRate || 50) / 100
    const blendMode = props.blendMode || 'source-over'
    
    ctx.globalCompositeOperation = props.drawingMode === 'erase' ? 'destination-out' : blendMode
    
    if (props.drawingMode === 'draw') {
      switch (penType) {
        case 'pen':
          drawPen(ctx, lastDrawPosition.value, pos, brushSize, brushColor, brushOpacity, brushHardness, simulatedPressure, blendMode)
          break
        case 'marker':
          drawMarker(ctx, lastDrawPosition.value, pos, brushSize, brushColor, brushOpacity, flowRate, brushAngle.value, blendMode)
          break
        case 'pencil':
          drawPencil(ctx, lastDrawPosition.value, pos, brushSize, brushColor, brushOpacity, brushHardness, simulatedPressure, blendMode)
          break
        case 'highlighter':
          drawHighlighter(ctx, lastDrawPosition.value, pos, brushSize, brushColor, brushOpacity, brushAngle.value, blendMode)
          break
        case 'spray':
          drawSpray(ctx, pos, brushSize, brushColor, brushOpacity, flowRate, simulatedPressure, blendMode)
          break
        case 'watercolor':
          drawWatercolor(ctx, lastDrawPosition.value, pos, brushSize, brushColor, brushOpacity, flowRate, simulatedPressure, blendMode)
          break
      }
    } else if (props.drawingMode === 'erase') {
      drawEraser(ctx, lastDrawPosition.value, pos, brushSize)
    }
  }
  
  lastDrawPosition.value = pos
  lastDrawTime.value = currentTime
}

// Layer initialization is now handled by parent component

function drawPen(ctx: CanvasRenderingContext2D, from: {x: number, y: number}, to: {x: number, y: number}, size: number, color: string, opacity: number, hardness: number, pressure: number = 1, blendMode: string = 'source-over') {
  ctx.save()
  ctx.globalCompositeOperation = blendMode as GlobalCompositeOperation
  ctx.globalAlpha = opacity * pressure
  ctx.strokeStyle = color
  ctx.lineWidth = size * pressure
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  
  // Add slight variation for hardness
  if (hardness < 100) {
    const blur = (100 - hardness) * 0.1 * pressure
    ctx.shadowColor = color
    ctx.shadowBlur = blur
  }
  
  ctx.beginPath()
  ctx.moveTo(from.x, from.y)
  ctx.lineTo(to.x, to.y)
  ctx.stroke()
  ctx.restore()
}

function drawMarker(ctx: CanvasRenderingContext2D, from: {x: number, y: number}, to: {x: number, y: number}, size: number, color: string, opacity: number, flowRate: number, angle: number = 0, blendMode: string = 'source-over') {
  ctx.save()
  ctx.globalCompositeOperation = blendMode as GlobalCompositeOperation
  ctx.globalAlpha = opacity * flowRate
  ctx.strokeStyle = color
  ctx.lineWidth = size
  ctx.lineCap = 'square'
  ctx.lineJoin = 'round'
  
  // Apply brush angle for angled marker effect
  if (angle !== 0) {
    const centerX = (from.x + to.x) / 2
    const centerY = (from.y + to.y) / 2
    ctx.translate(centerX, centerY)
    ctx.rotate(angle + Math.PI / 4) // Add slight angle for marker effect
    ctx.translate(-centerX, -centerY)
  }
  
  // Marker has a slightly streaky appearance
  const gradient = ctx.createLinearGradient(from.x, from.y, to.x, to.y)
  gradient.addColorStop(0, color)
  gradient.addColorStop(0.5, color + '80') // Semi-transparent
  gradient.addColorStop(1, color)
  ctx.strokeStyle = gradient
  
  ctx.beginPath()
  ctx.moveTo(from.x, from.y)
  ctx.lineTo(to.x, to.y)
  ctx.stroke()
  ctx.restore()
}

function drawPencil(ctx: CanvasRenderingContext2D, from: {x: number, y: number}, to: {x: number, y: number}, size: number, color: string, opacity: number, hardness: number, pressure: number = 1, blendMode: string = 'source-over') {
  ctx.save()
  ctx.globalCompositeOperation = blendMode as GlobalCompositeOperation
  
  // Pencil has texture and varying opacity based on pressure
  const distance = Math.sqrt((to.x - from.x) ** 2 + (to.y - from.y) ** 2)
  const steps = Math.max(1, Math.floor(distance / 2))
  
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    const x = from.x + (to.x - from.x) * t
    const y = from.y + (to.y - from.y) * t
    
    // Add texture variation enhanced by pressure
    const variation = (Math.random() - 0.5) * 0.3 * pressure
    const currentOpacity = opacity * pressure * (0.7 + variation)
    const currentSize = size * pressure * (0.8 + variation)
    
    ctx.globalAlpha = currentOpacity
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(x, y, currentSize / 2, 0, Math.PI * 2)
    ctx.fill()
  }
  
  ctx.restore()
}

function drawHighlighter(ctx: CanvasRenderingContext2D, from: {x: number, y: number}, to: {x: number, y: number}, size: number, color: string, opacity: number, angle: number = 0, blendMode: string = 'multiply') {
  ctx.save()
  ctx.globalCompositeOperation = blendMode as GlobalCompositeOperation
  ctx.globalAlpha = opacity
  ctx.strokeStyle = color
  ctx.lineWidth = size
  ctx.lineCap = 'square'
  ctx.lineJoin = 'round'
  
  // Apply angle for realistic highlighter effect
  if (angle !== 0) {
    const centerX = (from.x + to.x) / 2
    const centerY = (from.y + to.y) / 2
    ctx.translate(centerX, centerY)
    ctx.rotate(angle)
    ctx.translate(-centerX, -centerY)
  }
  
  // Highlighter has a flat, wide appearance
  ctx.beginPath()
  ctx.moveTo(from.x, from.y)
  ctx.lineTo(to.x, to.y)
  ctx.stroke()
  ctx.restore()
}

function drawSpray(ctx: CanvasRenderingContext2D, pos: {x: number, y: number}, size: number, color: string, opacity: number, flowRate: number, pressure: number = 1, blendMode: string = 'source-over') {
  ctx.save()
  ctx.globalCompositeOperation = blendMode as GlobalCompositeOperation
  
  // Spray creates multiple small dots, more with higher pressure
  const density = flowRate * 20 * pressure
  const radius = size / 2
  
  for (let i = 0; i < density; i++) {
    const angle = Math.random() * Math.PI * 2
    const distance = Math.random() * radius
    const x = pos.x + Math.cos(angle) * distance
    const y = pos.y + Math.sin(angle) * distance
    const dotSize = Math.random() * 2 * pressure + 0.5
    
    ctx.globalAlpha = opacity * pressure * (Math.random() * 0.5 + 0.5)
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(x, y, dotSize, 0, Math.PI * 2)
    ctx.fill()
  }
  
  ctx.restore()
}

function drawWatercolor(ctx: CanvasRenderingContext2D, from: {x: number, y: number}, to: {x: number, y: number}, size: number, color: string, opacity: number, flowRate: number, pressure: number = 1, blendMode: string = 'multiply') {
  ctx.save()
  ctx.globalCompositeOperation = blendMode as GlobalCompositeOperation
  
  // Watercolor has soft edges and blending, enhanced by pressure
  const effectiveSize = size * pressure
  const gradient = ctx.createRadialGradient(to.x, to.y, 0, to.x, to.y, effectiveSize)
  gradient.addColorStop(0, color)
  gradient.addColorStop(0.7, color + '80')
  gradient.addColorStop(1, color + '00')
  
  ctx.globalAlpha = opacity * flowRate * pressure
  ctx.fillStyle = gradient
  ctx.beginPath()
  ctx.arc(to.x, to.y, effectiveSize, 0, Math.PI * 2)
  ctx.fill()
  
  // Add a connecting stroke
  ctx.globalAlpha = opacity * flowRate * pressure * 0.3
  ctx.strokeStyle = color
  ctx.lineWidth = effectiveSize * 0.6
  ctx.lineCap = 'round'
  ctx.beginPath()
  ctx.moveTo(from.x, from.y)
  ctx.lineTo(to.x, to.y)
  ctx.stroke()
  
  ctx.restore()
}

function drawEraser(ctx: CanvasRenderingContext2D, from: {x: number, y: number}, to: {x: number, y: number}, size: number) {
  ctx.save()
  ctx.globalCompositeOperation = 'destination-out'
  ctx.lineWidth = size
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  
  ctx.beginPath()
  ctx.moveTo(from.x, from.y)
  ctx.lineTo(to.x, to.y)
  ctx.stroke()
  ctx.restore()
}

function stopDrawing() {
  if (isDrawing.value) {
    isDrawing.value = false
    lastDrawPosition.value = null
    saveCurrentDrawingState()
  }
}

function drawDot(x: number, y: number) {
  if (!drawingCanvas.value) return
  
  const ctx = drawingCanvas.value.getContext('2d')
  if (!ctx) return
  
  const penType = props.penType || 'pen'
  const brushSize = props.brushSize || 5
  const brushColor = props.brushColor || '#000000'
  const brushOpacity = props.brushOpacity || 1
  const blendMode = props.blendMode || 'source-over'
  
  ctx.save()
  ctx.globalAlpha = brushOpacity
  ctx.globalCompositeOperation = blendMode as GlobalCompositeOperation
  ctx.fillStyle = brushColor
  
  // Draw based on pen type
  if (penType === 'pen') {
    ctx.beginPath()
    ctx.arc(x, y, brushSize / 2, 0, Math.PI * 2)
    ctx.fill()
  } else if (penType === 'marker') {
    ctx.globalAlpha = brushOpacity * 0.7
    ctx.beginPath()
    ctx.arc(x, y, brushSize / 2, 0, Math.PI * 2)
    ctx.fill()
  } else if (penType === 'pencil') {
    ctx.globalAlpha = brushOpacity * 0.8
    ctx.beginPath()
    ctx.arc(x, y, brushSize / 3, 0, Math.PI * 2)
    ctx.fill()
  } else if (penType === 'highlighter') {
    ctx.globalCompositeOperation = 'multiply'
    ctx.globalAlpha = 0.3
    ctx.beginPath()
    ctx.arc(x, y, brushSize, 0, Math.PI * 2)
    ctx.fill()
  } else if (penType === 'spray') {
    // Spray effect with multiple small dots
    ctx.globalAlpha = brushOpacity * 0.1
    for (let i = 0; i < 20; i++) {
      const sprayX = x + (Math.random() - 0.5) * brushSize
      const sprayY = y + (Math.random() - 0.5) * brushSize
      ctx.beginPath()
      ctx.arc(sprayX, sprayY, 1, 0, Math.PI * 2)
      ctx.fill()
    }
  } else if (penType === 'watercolor') {
    // Watercolor effect with soft edges
    ctx.globalAlpha = brushOpacity * 0.3
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, brushSize / 2)
    gradient.addColorStop(0, brushColor)
    gradient.addColorStop(1, 'transparent')
    ctx.fillStyle = gradient
    ctx.beginPath()
    ctx.arc(x, y, brushSize / 2, 0, Math.PI * 2)
    ctx.fill()
  } else {
    // Default to pen
    ctx.beginPath()
    ctx.arc(x, y, brushSize / 2, 0, Math.PI * 2)
    ctx.fill()
  }
  
  ctx.restore()
}

function saveCurrentDrawingState() {
  if (!drawingCanvas.value) return
  
  const ctx = drawingCanvas.value.getContext('2d')
  if (!ctx) return
  
  const imageData = ctx.getImageData(0, 0, drawingCanvas.value.width, drawingCanvas.value.height)
  emit('drawing-state-saved', imageData)
}

// Touch support for mobile drawing
function handleTouchStart(event: TouchEvent) {
  event.preventDefault()
  if (event.touches.length === 1) {
    const touch = event.touches[0]
    startDrawing(touch as any)
  }
}

function handleTouchMove(event: TouchEvent) {
  event.preventDefault()
  if (event.touches.length === 1) {
    const touch = event.touches[0]
    draw(touch as any)
  }
}

function handleTouchEnd(event: TouchEvent) {
  event.preventDefault()
  stopDrawing()
}

// Watch for undo/redo from parent component
watch(() => props.historyStep, (newStep, oldStep) => {
  if (!drawingCanvas.value || !props.drawingHistory) return
  
  const ctx = drawingCanvas.value.getContext('2d')
  if (!ctx) return
  
  if (newStep !== undefined && newStep >= 0 && newStep < props.drawingHistory.length) {
    const historyItem = props.drawingHistory[newStep]
    ctx.putImageData(historyItem as ImageData, 0, 0)
  } else if (newStep === -1) {
    // Clear canvas
    ctx.clearRect(0, 0, drawingCanvas.value.width, drawingCanvas.value.height)
  }
})

// Watch for clear drawing command (when history is empty and step is -1)
watch(() => [props.drawingHistory?.length, props.historyStep], ([historyLength, step]) => {
  if (!drawingCanvas.value) return
  
  if (historyLength === 0 && step === -1) {
    const ctx = drawingCanvas.value.getContext('2d')
    if (ctx) {
      ctx.clearRect(0, 0, drawingCanvas.value.width, drawingCanvas.value.height)
    }
  }
}, { deep: true })

// Keyboard shortcuts
function handleKeyDown(event: KeyboardEvent) {
  if (event.key === 'Delete' && selectedElements.value.length > 0) {
    selectedElements.value.forEach((id: string) => deleteElement(id))
  }
  if (event.key === 'Escape') {
    selectedElements.value = []
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.moodboard-canvas-wrapper {
  display: contents; /* This makes the wrapper transparent to layout */
}

.moodboard-canvas-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background: #f8fafc;
}

.canvas-toolbar {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  overflow-x: auto;
}

.toolbar-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: fit-content;
}

.toolbar-section h3 {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #6b7280;
  margin: 0;
}

.canvas-wrapper {
  flex: 1;
  overflow: auto;
  position: relative;
  padding: 1rem;
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  min-height: 0;
}

.moodboard-canvas {
  position: relative;
  border: 2px solid #d1d5db;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  transform: scale(var(--zoom-level));
  transform-origin: top left;
  background: white;
  overflow: hidden;
  will-change: transform;
  /* Improve performance for children */
  contain: layout style paint;
  cursor: default;
}

/* Canvas mode cursors */
.moodboard-canvas.mode-select {
  cursor: default;
}

.moodboard-canvas.mode-text {
  cursor: text;
}

/* Visual feedback for text mode - subtle indicator */
.moodboard-canvas.mode-text::after {
  content: '✏️ Click to add text';
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(16, 185, 129, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  pointer-events: none;
  z-index: 100;
  opacity: 0;
  animation: showBriefly 4s ease-in-out;
}

.moodboard-canvas.mode-image {
  cursor: copy;
}

/* Visual feedback for image mode - subtle indicator */
.moodboard-canvas.mode-image::after {
  content: '📷 Click to add image';
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(59, 130, 246, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  pointer-events: none;
  z-index: 100;
  opacity: 0;
  animation: showBriefly 4s ease-in-out;
}

@keyframes fadeInOut {
  0% { opacity: 0; }
  20% { opacity: 0.9; }
  80% { opacity: 0.9; }
  100% { opacity: 0; }
}

@keyframes showBriefly {
  0% { opacity: 0; transform: translateY(-10px); }
  15% { opacity: 0.8; transform: translateY(0); }
  85% { opacity: 0.8; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(-10px); }
}

.grid-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(to right, rgba(0,0,0,0.1) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0,0,0,0.1) 1px, transparent 1px);
  pointer-events: none;
  opacity: 0.3;
}

.selection-box {
  position: absolute;
  border: 2px dashed #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  pointer-events: none;
}

.properties-panel {
  position: absolute;
  right: 1rem;
  top: 1rem;
  width: 300px;
  max-height: calc(100vh - 200px);
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.property-group {
  margin-bottom: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.property-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #374151;
}

.input-row {
  display: flex;
  gap: 0.5rem;
}

.input-row .u-input {
  flex: 1;
}

/* Typography specific styling */
.property-group .grid {
  gap: 0.5rem;
}

.property-group .grid-cols-2 > div {
  display: flex;
  flex-direction: column;
}

.property-group .text-sm {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

/* Color input styling */
.property-group input[type="color"] {
  height: 2.5rem;
  border-radius: 0.375rem;
  border: 1px solid #d1d5db;
  cursor: pointer;
}

/* Quick style buttons */
.property-group .grid .button {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
}

/* Drawing Canvas Styles */
.drawing-canvas {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: auto;
  touch-action: none; /* Prevent scrolling on mobile when drawing */
}

.drawing-canvas:hover {
  opacity: 0.95;
}
</style>
