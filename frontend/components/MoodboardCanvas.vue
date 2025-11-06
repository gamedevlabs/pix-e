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
              title="Select and move elements"
              @click="setCanvasMode('select')"
            >
              Select
            </UButton>
            <UButton
              :variant="canvasMode === 'text' ? 'solid' : 'outline'"
              icon="i-heroicons-document-text"
              title="Add text elements to canvas"
              @click="setCanvasMode('text')"
            >
              Text
            </UButton>
            <UButton
              :variant="canvasMode === 'image' ? 'solid' : 'outline'"
              icon="i-heroicons-photo"
              title="Add images to canvas"
              @click="openImageMode"
            >
              Image
            </UButton>
            <UButton
              :variant="props.drawingMode === 'draw' || props.drawingMode === 'erase' ? 'solid' : 'outline'"
              icon="i-heroicons-pencil"
              color="primary"
              title="Toggle drawing mode"
              @click="toggleDrawMode"
            >
              Draw
            </UButton>
          </UButtonGroup>
        </div>

        <!-- Drawing Controls (shown when Draw mode is active) -->
        <div v-if="props.drawingMode === 'draw' || props.drawingMode === 'erase'" class="drawing-toolbar-expanded">
          <div class="drawing-controls-row">
            <!-- Draw/Erase Toggle -->
            <div class="control-group">
              <span class="control-label">Mode:</span>
              <UButtonGroup size="sm">
                <UButton
                  :variant="props.drawingMode === 'draw' ? 'solid' : 'outline'"
                  color="primary"
                  icon="i-heroicons-pencil-20-solid"
                  @click="setDrawingMode('draw')"
                >
                  Draw
                </UButton>
                <UButton
                  :variant="props.drawingMode === 'erase' ? 'solid' : 'outline'"
                  color="error"
                  icon="i-heroicons-x-circle-20-solid"
                  @click="setDrawingMode('erase')"
                >
                  Erase
                </UButton>
              </UButtonGroup>
            </div>

            <!-- Pen Type (only in draw mode) -->
            <div v-if="props.drawingMode === 'draw'" class="control-group">
              <span class="control-label">Pen Type:</span>
              <UButtonGroup size="sm">
                <UButton
                  :variant="props.penType === 'pen' ? 'solid' : 'outline'"
                  title="Pen"
                  @click="setPenType('pen')"
                >
                  ✏️ Pen
                </UButton>
                <UButton
                  :variant="props.penType === 'marker' ? 'solid' : 'outline'"
                  title="Marker"
                  @click="setPenType('marker')"
                >
                  🖍️ Marker
                </UButton>
                <UButton
                  :variant="props.penType === 'pencil' ? 'solid' : 'outline'"
                  title="Pencil"
                  @click="setPenType('pencil')"
                >
                  ✏️ Pencil
                </UButton>
                <UButton
                  :variant="props.penType === 'highlighter' ? 'solid' : 'outline'"
                  title="Highlighter"
                  @click="setPenType('highlighter')"
                >
                  🖍️ Highlight
                </UButton>
                <UButton
                  :variant="props.penType === 'spray' ? 'solid' : 'outline'"
                  title="Spray"
                  @click="setPenType('spray')"
                >
                  🎨 Spray
                </UButton>
                <UButton
                  :variant="props.penType === 'watercolor' ? 'solid' : 'outline'"
                  title="Watercolor"
                  @click="setPenType('watercolor')"
                >
                  💧 Water
                </UButton>
              </UButtonGroup>
            </div>

            <!-- Brush Size -->
            <div class="control-group brush-control">
              <span class="control-label">Size:</span>
              <input
                :value="props.brushSize"
                type="range"
                :min="getBrushSizeRange().min"
                :max="getBrushSizeRange().max"
                class="range-input-inline"
                @input="updateBrushSize($event)"
              />
              <span class="control-value">{{ props.brushSize }}px</span>
            </div>

            <!-- Brush Color (only in draw mode) -->
            <div v-if="props.drawingMode === 'draw'" class="control-group">
              <span class="control-label">Color:</span>
              <input
                :value="props.brushColor"
                type="color"
                class="color-input-inline"
                @input="updateBrushColor($event)"
              />
            </div>

            <!-- Opacity -->
            <div class="control-group brush-control">
              <span class="control-label">Opacity:</span>
              <input
                :value="props.brushOpacity"
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                class="range-input-inline"
                @input="updateBrushOpacity($event)"
              />
              <span class="control-value">{{ Math.round((props.brushOpacity || 1) * 100) }}%</span>
            </div>

            <!-- Divider -->
            <div class="toolbar-divider"></div>

            <!-- Actions -->
            <div class="control-group">
              <UButtonGroup size="sm">
                <UButton
                  variant="outline"
                  icon="i-heroicons-arrow-uturn-left-20-solid"
                  title="Undo (Ctrl+Z)"
                  :disabled="!canUndo"
                  @click="undoDrawing"
                >
                  Undo
                </UButton>
                <UButton
                  variant="outline"
                  icon="i-heroicons-arrow-uturn-right-20-solid"
                  title="Redo (Ctrl+Y)"
                  :disabled="!canRedo"
                  @click="redoDrawing"
                >
                  Redo
                </UButton>
                <UButton
                  variant="outline"
                  color="error"
                  icon="i-heroicons-trash-20-solid"
                  title="Clear All Drawing"
                  @click="clearDrawing"
                >
                  Clear
                </UButton>
              </UButtonGroup>
            </div>
          </div>
        </div>

        <div class="toolbar-section">
          <h3>View</h3>
          <UButtonGroup>
            <UButton
              :variant="showGrid ? 'solid' : 'outline'"
              icon="i-heroicons-squares-2x2"
              title="Toggle grid overlay"
              @click="toggleGrid"
            >
              Grid
            </UButton>
            <UButton 
              icon="i-heroicons-minus" 
              title="Zoom out"
              @click="zoomOut"
            >
              {{ Math.round(zoomLevel * 100) }}%
            </UButton>
            <UButton 
              icon="i-heroicons-plus" 
              title="Zoom in"
              @click="zoomIn" 
            />
          </UButtonGroup>
        </div>

        <div class="toolbar-section">
          <h3>Layering</h3>
          <UButtonGroup>
            <UButton
              title="Bring to Front"
              icon="i-heroicons-arrow-up-20-solid"
              size="xs"
              :disabled="selectedElements.length !== 1 || !canBringToFront"
              @click="bringToFront"
            >
              Front
            </UButton>
            <UButton
              title="Bring Forward"
              icon="i-heroicons-arrow-up-20-solid"
              size="xs"
              :disabled="selectedElements.length !== 1 || !canBringForward"
              @click="bringForward"
            >
              Forward
            </UButton>
            <UButton
              title="Send Backward"
              icon="i-heroicons-arrow-down-20-solid"
              size="xs"
              :disabled="selectedElements.length !== 1 || !canSendBackward"
              @click="sendBackward"
            >
              Backward
            </UButton>
            <UButton
              title="Send to Back"
              icon="i-heroicons-arrow-down-20-solid"
              size="xs"
              :disabled="selectedElements.length !== 1 || !canSendToBack"
              @click="sendToBack"
            >
              Back
            </UButton>
          </UButtonGroup>
        </div>

        <div class="toolbar-section">
          <h3>Actions</h3>
          <UButtonGroup>
            <UButton
              icon="i-heroicons-check-circle"
              color="primary"
              :loading="isSaving"
              @click="saveCanvas"
            >
              {{ isSaving ? 'Saving...' : 'Save' }}
            </UButton>
            <UDropdownMenu :items="exportMenuItems">
              <UButton icon="i-heroicons-arrow-down-tray" variant="outline" trailing-icon="i-heroicons-chevron-down">
                Export
              </UButton>
              <template #item="{ item }">
                <div class="dropdown-item" @click="item.click">
                  <UIcon :name="item.icon" class="mr-2 w-4 h-4" />
                  <span>{{ item.label }}</span>
                </div>
              </template>
            </UDropdownMenu>
          </UButtonGroup>
        </div>
      </div>

      <!-- Canvas Area -->
      <div
        class="canvas-wrapper"
        :style="{
          '--zoom-level': zoomLevel,
          '--canvas-width': `${canvasSettings.canvas_width}px`,
          '--canvas-height': `${canvasSettings.canvas_height}px`,
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
            'mode-select': canvasMode === 'select',
          }"
          :style="{
            width: `${canvasSettings.canvas_width}px`,
            height: `${canvasSettings.canvas_height}px`,
            backgroundColor: canvasSettings.canvas_background_color,
            backgroundImage: canvasSettings.canvas_background_image
              ? `url(${canvasSettings.canvas_background_image})`
              : 'none',
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
              backgroundSize: `${canvasSettings.grid_size}px ${canvasSettings.grid_size}px`,
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
            @edit="handleImageEdit"
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

          <!-- Drawing Canvas Overlay - Always visible like MS Paint, always below other elements -->
          <canvas
            ref="drawingCanvas"
            class="drawing-canvas"
            :class="{ 'drawing-active': props.drawingMode && props.drawingMode !== 'move' }"
            :width="canvasSettings.canvas_width"
            :height="canvasSettings.canvas_height"
            :style="{
              position: 'absolute',
              top: 0,
              left: 0,
              zIndex: 1,
              pointerEvents:
                props.drawingMode === 'draw' || props.drawingMode === 'erase' ? 'auto' : 'none',
              cursor:
                props.drawingMode === 'draw'
                  ? 'crosshair'
                  : props.drawingMode === 'erase'
                    ? 'grab'
                    : 'default',
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
              height: `${selectionBox.height}px`,
            }"
          />
        </div>
      </div>

      <!-- Properties Panel -->
      <div v-if="selectedElements.length > 0" class="properties-panel" :class="{ collapsed: propertiesPanelCollapsed }">
        <div class="properties-header">
          <h3>Properties</h3>
          <button 
            class="collapse-button" 
            @click="propertiesPanelCollapsed = !propertiesPanelCollapsed"
            :title="propertiesPanelCollapsed ? 'Expand Properties' : 'Collapse Properties'"
          >
            <span v-if="!propertiesPanelCollapsed">✕</span>
            <span v-else>⚙</span>
          </button>
        </div>
        <div v-if="!propertiesPanelCollapsed" class="properties-content">
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
              <USelectMenu
                :model-value="(selectedElementData as MoodboardTextElement).font_family"
                :items="fontOptions"
                value-key="value"
                placeholder="Select font"
                :ui="{ content: 'min-w-fit' }"
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
                <USelectMenu
                  :model-value="(selectedElementData as MoodboardTextElement).font_weight"
                  :items="fontWeightOptions"
                  value-key="value"
                  :ui="{ content: 'min-w-fit' }"
                  @update:model-value="updateTextProperty('font_weight', Number($event))"
                />
              </div>
            </div>

            <!-- Text Alignment -->
            <div class="mb-3">
              <label class="text-sm text-gray-600 mb-1 block">Alignment</label>
              <UButtonGroup class="w-full">
                <UButton
                  :variant="
                    (selectedElementData as MoodboardTextElement).text_align === 'left'
                      ? 'solid'
                      : 'outline'
                  "
                  icon="i-heroicons-bars-3-bottom-left"
                  size="sm"
                  @click="updateTextProperty('text_align', 'left')"
                />
                <UButton
                  :variant="
                    (selectedElementData as MoodboardTextElement).text_align === 'center'
                      ? 'solid'
                      : 'outline'
                  "
                  icon="i-heroicons-bars-3"
                  size="sm"
                  @click="updateTextProperty('text_align', 'center')"
                />
                <UButton
                  :variant="
                    (selectedElementData as MoodboardTextElement).text_align === 'right'
                      ? 'solid'
                      : 'outline'
                  "
                  icon="i-heroicons-bars-3-bottom-right"
                  size="sm"
                  @click="updateTextProperty('text_align', 'right')"
                />
                <UButton
                  :variant="
                    (selectedElementData as MoodboardTextElement).text_align === 'justify'
                      ? 'solid'
                      : 'outline'
                  "
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
                  :model-value="
                    (selectedElementData as MoodboardTextElement).background_color || '#ffffff'
                  "
                  type="color"
                  class="w-16"
                  @update:model-value="updateTextProperty('background_color', $event)"
                />
                <UInput
                  :model-value="
                    (selectedElementData as MoodboardTextElement).background_color || ''
                  "
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
                  :model-value="
                    (selectedElementData as MoodboardTextElement).border_color || '#000000'
                  "
                  type="color"
                  @update:model-value="updateTextProperty('border_color', $event)"
                />
              </div>
            </div>

            <!-- Text Style Presets -->
            <div class="mb-3">
              <label class="text-sm text-gray-600 mb-1 block">Quick Styles</label>
              <div class="grid grid-cols-2 gap-1">
                <UButton size="xs" variant="outline" @click="applyTextStyle('heading')"
                  >Heading</UButton
                >
                <UButton size="xs" variant="outline" @click="applyTextStyle('subheading')"
                  >Subheading</UButton
                >
                <UButton size="xs" variant="outline" @click="applyTextStyle('body')"
                  >Body Text</UButton
                >
                <UButton size="xs" variant="outline" @click="applyTextStyle('caption')"
                  >Caption</UButton
                >
                <UButton size="xs" variant="outline" @click="applyTextStyle('quote')"
                  >Quote</UButton
                >
                <UButton size="xs" variant="outline" @click="applyTextStyle('accent')"
                  >Accent</UButton
                >
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
        <UButton label="Cancel" color="neutral" variant="outline" @click="closeImageModal" />
        <UButton label="Add Image" :disabled="!imageUrl" @click="addImageFromUrl" />
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRuntimeConfig } from '#imports'
import type { MoodboardImage, MoodboardTextElement, Moodboard } from '~/composables/useMoodboards'
import { useMoodboards } from '~/composables/useMoodboards'

// Type alias for canvas elements that can be either images or text
type CanvasElement = MoodboardImage | MoodboardTextElement

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
  blendMode?:
    | 'source-over'
    | 'multiply'
    | 'screen'
    | 'overlay'
    | 'soft-light'
    | 'hard-light'
    | 'color-dodge'
    | 'color-burn'
    | 'difference'
    | 'exclusion'
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
  moodboardUpdated: [moodboard: Partial<Moodboard>]
  'drawing-state-saved': [imageData: ImageData]
  'image-edit': [image: MoodboardImage]
  'update-drawing-mode': [mode: 'move' | 'draw' | 'erase']
  'update-pen-type': [
    penType: 'pen' | 'marker' | 'pencil' | 'highlighter' | 'spray' | 'watercolor',
  ]
  'update-brush-size': [size: number]
  'update-brush-color': [color: string]
  'update-brush-opacity': [opacity: number]
  'undo-drawing': []
  'redo-drawing': []
  'clear-drawing': []
}>()

// Canvas state
const canvasElement = ref<HTMLElement>()
const canvasMode = ref<'select' | 'text' | 'image'>('select')
const lastModeChangeTime = ref(0)
const zoomLevel = ref(1)
const showGrid = ref(true)
const snapToGrid = ref(true)
const selectedElements = ref<string[]>([])

// Properties panel state
const propertiesPanelCollapsed = ref(false)

// Drawing state
const drawingCanvas = ref<HTMLCanvasElement>()
const isDrawing = ref(false)
const lastDrawPosition = ref<{ x: number; y: number } | null>(null)
const lastDrawTime = ref<number>(0)
const drawingVelocity = ref<number>(0)
const brushAngle = ref<number>(0)

// Selection box for multi-select
const selectionBox = ref({
  visible: false,
  x: 0,
  y: 0,
  width: 0,
  height: 0,
})

// Image upload
const showImageUpload = ref(false)
const imageUrl = ref('')
const isSaving = ref(false)

// Watch for changes to showImageUpload
watch(showImageUpload, (_newValue: boolean) => {})

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
  snap_to_grid: props.moodboard.snap_to_grid ?? true,
}))

// API composable
const {
  updateImagePosition: apiUpdateImagePosition,
  createTextElement: apiCreateTextElement,
  updateTextElement: apiUpdateTextElement,
  deleteTextElement: apiDeleteTextElement,
} = useMoodboards()

// Canvas elements
const canvasImages = computed(() =>
  props.images.map((img: MoodboardImage, index: number) => ({
    ...img,
    // Set reasonable default canvas dimensions if not set or too small (likely thumbnails)
    canvas_width: img.canvas_width && img.canvas_width > 250 ? img.canvas_width : 350,
    canvas_height: img.canvas_height && img.canvas_height > 250 ? img.canvas_height : 350,
    // Handle positioning: if position is 0,0 (default/overlapping), use smart defaults
    x_position:
      img.x_position !== 0 || img.y_position !== 0 ? img.x_position : 50 + (index % 3) * 370,
    y_position:
      img.x_position !== 0 || img.y_position !== 0
        ? img.y_position
        : 50 + Math.floor(index / 3) * 370,
    z_index: img.z_index || index + 1,
    opacity: img.opacity !== undefined ? img.opacity : 1.0,
    rotation: img.rotation || 0,
  })),
)

const canvasTextElements = computed(() =>
  props.textElements.map((text: MoodboardTextElement, index: number) => ({
    ...text,
    // Set default dimensions if not set
    x_position: text.x_position !== undefined ? text.x_position : 50 + (index % 2) * 300,
    y_position: text.y_position !== undefined ? text.y_position : 50 + Math.floor(index / 2) * 80,
    width: text.width || 200,
    height: text.height || 50,
  })),
)

// Selected element data
const selectedElementData = computed(() => {
  if (selectedElements.value.length !== 1) return null

  const selectedId = selectedElements.value[0]
  return (
    canvasImages.value.find((img: MoodboardImage) => img.id === selectedId) ||
    canvasTextElements.value.find((text: MoodboardTextElement) => text.id === selectedId)
  )
})

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
  { label: 'Courier New', value: 'Courier New' },
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
  { label: 'Black (900)', value: 900 },
]

// Text style presets
const textStylePresets = {
  heading: {
    font_size: 32,
    font_weight: 700,
    line_height: 1.2,
    letter_spacing: -0.5,
  },
  subheading: {
    font_size: 24,
    font_weight: 600,
    line_height: 1.3,
    letter_spacing: 0,
  },
  body: {
    font_size: 16,
    font_weight: 400,
    line_height: 1.5,
    letter_spacing: 0,
  },
  caption: {
    font_size: 12,
    font_weight: 400,
    line_height: 1.4,
    letter_spacing: 0.5,
  },
  quote: {
    font_size: 18,
    font_weight: 400,
    line_height: 1.6,
    letter_spacing: 0,
    font_family: 'Georgia',
  },
  accent: {
    font_size: 20,
    font_weight: 600,
    line_height: 1.3,
    letter_spacing: 1,
    text_color: '#2563eb',
  },
}

// Methods
function setCanvasMode(mode: typeof canvasMode.value) {
  canvasMode.value = mode
  lastModeChangeTime.value = Date.now()
  
  // Reset drawing mode to 'move' when switching to any canvas mode
  if (props.drawingMode && props.drawingMode !== 'move') {
    emit('update-drawing-mode', 'move')
  }
  
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

// Drawing control functions
function toggleDrawMode() {
  // If not in draw/erase mode, activate draw mode
  // If already in draw/erase mode, go back to move mode
  if (props.drawingMode === 'move') {
    // Activate draw mode and set canvas mode to select
    canvasMode.value = 'select'
    emit('update-drawing-mode', 'draw')
  } else {
    // Deactivate draw mode
    emit('update-drawing-mode', 'move')
  }
}

function setDrawingMode(mode: 'move' | 'draw' | 'erase') {
  // When enabling draw or erase mode, ensure canvas mode is select
  if (mode !== 'move') {
    canvasMode.value = 'select'
  }
  emit('update-drawing-mode', mode)
}

function setPenType(penType: 'pen' | 'marker' | 'pencil' | 'highlighter' | 'spray' | 'watercolor') {
  emit('update-pen-type', penType)
}

function getBrushSizeRange() {
  const penType = props.penType || 'pen'
  const ranges: Record<string, { min: number; max: number }> = {
    pen: { min: 1, max: 20 },
    marker: { min: 5, max: 50 },
    pencil: { min: 1, max: 10 },
    highlighter: { min: 10, max: 60 },
    spray: { min: 5, max: 40 },
    watercolor: { min: 10, max: 80 },
  }
  return ranges[penType] || { min: 1, max: 50 }
}

function updateBrushSize(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update-brush-size', Number(target.value))
}

function updateBrushColor(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update-brush-color', target.value)
}

function updateBrushOpacity(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update-brush-opacity', Number(target.value))
}

function undoDrawing() {
  emit('undo-drawing')
}

function redoDrawing() {
  emit('redo-drawing')
}

function clearDrawing() {
  emit('clear-drawing')
}

// Computed properties for undo/redo
const canUndo = computed(() => {
  return (props.historyStep || 0) > 0
})

const canRedo = computed(() => {
  return (props.historyStep || 0) < (props.drawingHistory?.length || 0) - 1
})

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
  const selectedImage = canvasImages.value.find((img) => img.id === imageId)
  if (selectedImage) {
    // Get the current highest z-index
    const maxZIndex = Math.max(...canvasImages.value.map((img) => img.z_index || 0))

    // Only update if this image doesn't already have the highest z-index
    if ((selectedImage.z_index || 0) < maxZIndex) {
      const updatedImage = { ...selectedImage, z_index: maxZIndex + 1 }
      updateImagePosition(updatedImage)
    }
  }
}

// Handle image edit
function handleImageEdit(image: MoodboardImage) {
  emit('image-edit', image)
}

function handleCanvasClick(event: MouseEvent) {
  // Don't handle canvas clicks when in draw/erase mode
  if (props.drawingMode && props.drawingMode !== 'move') {
    return
  }

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
    // Create a proper event-like object for the file upload handler
    const fileUploadEvent = new Event('change')
    Object.defineProperty(fileUploadEvent, 'target', {
      value: { files },
      writable: false,
    })
    handleImageUpload(fileUploadEvent)
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
    opacity: 1,
    // Don't include moodboard - it's set by the backend in perform_create
  }

  try {
    const createdTextElement = (await apiCreateTextElement(
      props.moodboard.id,
      textData,
    )) as MoodboardTextElement
    // Only emit if API call was successful and return the created element with proper ID
    emit('addTextElement', createdTextElement)
    canvasMode.value = 'select'
  } catch {
    // Don't emit on error - this prevents adding invalid elements to frontend state
  }
}

async function updateImagePosition(updatedImage: MoodboardImage) {
  try {
    await apiUpdateImagePosition(props.moodboard.id, updatedImage.id, updatedImage)
    emit('image-updated', updatedImage)
  } catch {
    // Silently handle image update errors in production
  }
}

async function updateTextElement(updatedText: MoodboardTextElement) {
  try {
    await apiUpdateTextElement(props.moodboard.id, updatedText.id, updatedText)
    emit('update-text-element', updatedText)
  } catch {
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
      Object.keys(preset).forEach((key) => {
        const typedKey = key as keyof typeof preset
        ;(textElement as unknown as Record<string, unknown>)[key] = preset[typedKey]
      })
      updateSelectedElement()
    }
  }
}

function isTextElement(element: CanvasElement): element is MoodboardTextElement {
  return element && 'content' in element
}

function getElementWidth(element: CanvasElement): number {
  if (isTextElement(element)) {
    return element.width
  } else {
    return element.canvas_width
  }
}

function getElementHeight(element: CanvasElement): number {
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

function updateTextProperty(property: keyof MoodboardTextElement, value: unknown) {
  if (selectedElementData.value && isTextElement(selectedElementData.value)) {
    const textElement = selectedElementData.value as MoodboardTextElement
    ;(textElement as unknown as Record<string, unknown>)[property] = value
    updateSelectedElement()
  }
}

async function deleteElement(elementId: string) {
  try {
    // Check if it's a text element
    const textElement = canvasTextElements.value.find(
      (text: MoodboardTextElement) => text.id === elementId,
    )
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
  } catch {
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
        ...useRequestHeaders(['cookie']),
      }

      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken
      }

      const response = await $fetch(
        `${config.public.apiBase}/moodboards/${props.moodboard.id}/images/`,
        {
          method: 'POST',
          credentials: 'include',
          headers,
          body: formData,
        },
      )

      emit('addImage', response as MoodboardImage)
      closeImageModal()
    } catch {
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
        ...useRequestHeaders(['cookie']),
      }

      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken
      }

      const response = await $fetch(
        `${config.public.apiBase}/moodboards/canvas/${props.moodboard.id}/import-image/`,
        {
          method: 'POST',
          credentials: 'include',
          headers,
          body: {
            image_url: imageUrl.value,
            x_position: 100,
            y_position: 100,
            canvas_width: 200,
            canvas_height: 200,
          },
        },
      )

      emit('addImage', response as Partial<MoodboardImage>)
      closeImageModal()
    } catch {
      // Silently handle URL import errors and close modal
      closeImageModal()
    }
  }
}

function closeImageModal() {
  showImageUpload.value = false
  imageUrl.value = ''
}

// Z-index layering functions (as computed properties for reactivity)
// Simplified: Enable layering buttons when exactly 1 element is selected and there are 2+ total elements
const canBringToFront = computed((): boolean => {
  if (selectedElements.value.length !== 1) return false
  const totalElements = canvasImages.value.length + canvasTextElements.value.length
  return totalElements >= 2
})

const canBringForward = computed((): boolean => {
  if (selectedElements.value.length !== 1) return false
  const totalElements = canvasImages.value.length + canvasTextElements.value.length
  return totalElements >= 2
})

const canSendBackward = computed((): boolean => {
  if (selectedElements.value.length !== 1) return false
  const totalElements = canvasImages.value.length + canvasTextElements.value.length
  return totalElements >= 2
})

const canSendToBack = computed((): boolean => {
  if (selectedElements.value.length !== 1) return false
  const totalElements = canvasImages.value.length + canvasTextElements.value.length
  return totalElements >= 2
})

const exportMenuItems = computed(() => [
  {
    label: 'Export as PNG',
    icon: 'i-heroicons-photo',
    click: () => exportCanvas('png'),
  },
  {
    label: 'Export as JPEG',
    icon: 'i-heroicons-photo',
    click: () => exportCanvas('jpg'),
  },
  {
    label: 'Export as PDF',
    icon: 'i-heroicons-document',
    click: () => exportCanvas('pdf'),
  },
])

function bringToFront() {
  if (selectedElements.value.length !== 1) return
  
  // Get all z-indexes from both images and text elements
  const allZIndexes = [
    ...canvasImages.value.map((img) => img.z_index || 0),
    ...canvasTextElements.value.map((txt) => txt.z_index || 0)
  ]
  const maxZIndex = Math.max(...allZIndexes)
  
  // Check if it's an image
  const selectedImage = canvasImages.value.find((img) => img.id === selectedElements.value[0])
  if (selectedImage) {
    const updatedImage = { ...selectedImage, z_index: maxZIndex + 1 }
    updateImagePosition(updatedImage)
    return
  }
  
  // Check if it's a text element
  const selectedText = canvasTextElements.value.find((txt) => txt.id === selectedElements.value[0])
  if (selectedText) {
    const updatedText = { ...selectedText, z_index: maxZIndex + 1 }
    updateTextElement(updatedText)
  }
}

function bringForward() {
  if (selectedElements.value.length !== 1) return
  
  // Check if it's an image
  const selectedImage = canvasImages.value.find((img) => img.id === selectedElements.value[0])
  if (selectedImage) {
    const currentZIndex = selectedImage.z_index || 0
    // Find the next higher z-index from all elements
    const allZIndexes = [
      ...canvasImages.value.map((img) => img.z_index || 0),
      ...canvasTextElements.value.map((txt) => txt.z_index || 0)
    ]
    const higherZIndexes = allZIndexes
      .filter((z) => z > currentZIndex)
      .sort((a, b) => a - b)

    if (higherZIndexes.length > 0) {
      const updatedImage = { ...selectedImage, z_index: higherZIndexes[0] + 1 }
      updateImagePosition(updatedImage)
    }
    return
  }
  
  // Check if it's a text element
  const selectedText = canvasTextElements.value.find((txt) => txt.id === selectedElements.value[0])
  if (selectedText) {
    const currentZIndex = selectedText.z_index || 0
    // Find the next higher z-index from all elements
    const allZIndexes = [
      ...canvasImages.value.map((img) => img.z_index || 0),
      ...canvasTextElements.value.map((txt) => txt.z_index || 0)
    ]
    const higherZIndexes = allZIndexes
      .filter((z) => z > currentZIndex)
      .sort((a, b) => a - b)

    if (higherZIndexes.length > 0) {
      const updatedText = { ...selectedText, z_index: higherZIndexes[0] + 1 }
      updateTextElement(updatedText)
    }
  }
}

function sendBackward() {
  if (selectedElements.value.length !== 1) return
  
  // Check if it's an image
  const selectedImage = canvasImages.value.find((img) => img.id === selectedElements.value[0])
  if (selectedImage) {
    const currentZIndex = selectedImage.z_index || 0
    // Find the next lower z-index from all elements
    const allZIndexes = [
      ...canvasImages.value.map((img) => img.z_index || 0),
      ...canvasTextElements.value.map((txt) => txt.z_index || 0)
    ]
    const lowerZIndexes = allZIndexes
      .filter((z) => z < currentZIndex)
      .sort((a, b) => b - a)

    if (lowerZIndexes.length > 0) {
      const updatedImage = { ...selectedImage, z_index: lowerZIndexes[0] - 1 }
      updateImagePosition(updatedImage)
    }
    return
  }
  
  // Check if it's a text element
  const selectedText = canvasTextElements.value.find((txt) => txt.id === selectedElements.value[0])
  if (selectedText) {
    const currentZIndex = selectedText.z_index || 0
    // Find the next lower z-index from all elements
    const allZIndexes = [
      ...canvasImages.value.map((img) => img.z_index || 0),
      ...canvasTextElements.value.map((txt) => txt.z_index || 0)
    ]
    const lowerZIndexes = allZIndexes
      .filter((z) => z < currentZIndex)
      .sort((a, b) => b - a)

    if (lowerZIndexes.length > 0) {
      const updatedText = { ...selectedText, z_index: lowerZIndexes[0] - 1 }
      updateTextElement(updatedText)
    }
  }
}

function sendToBack() {
  if (selectedElements.value.length !== 1) return
  
  // Get all z-indexes from both images and text elements
  const allZIndexes = [
    ...canvasImages.value.map((img) => img.z_index || 0),
    ...canvasTextElements.value.map((txt) => txt.z_index || 0)
  ]
  const minZIndex = Math.min(...allZIndexes)
  
  // Check if it's an image
  const selectedImage = canvasImages.value.find((img) => img.id === selectedElements.value[0])
  if (selectedImage) {
    const updatedImage = { ...selectedImage, z_index: minZIndex - 1 }
    updateImagePosition(updatedImage)
    return
  }
  
  // Check if it's a text element
  const selectedText = canvasTextElements.value.find((txt) => txt.id === selectedElements.value[0])
  if (selectedText) {
    const updatedText = { ...selectedText, z_index: minZIndex - 1 }
    updateTextElement(updatedText)
  }
}

// Save canvas function
async function saveCanvas() {
  if (isSaving.value) return
  
  const toast = useToast()
  isSaving.value = true

  try {
    const savePromises: Promise<unknown>[] = []
    let drawingDataUrl = ''
    let failedSaves = 0
    
    // Count items to save
    const totalItems = canvasTextElements.value.length + canvasImages.value.length
    
    // 1. Save all text elements (to ensure any unsaved changes are persisted)
    for (const textElement of canvasTextElements.value) {
      const savePromise = apiUpdateTextElement(
        props.moodboard.id,
        textElement.id,
        textElement
      ).catch((error) => {
        console.error(`Failed to save text element ${textElement.id}:`, error)
        failedSaves++
        // Continue with other saves even if one fails
        return null
      })
      savePromises.push(savePromise)
    }
    
    // 2. Save all images (to ensure any unsaved position/size changes are persisted)
    for (const image of canvasImages.value) {
      const savePromise = apiUpdateImagePosition(
        props.moodboard.id,
        image.id,
        {
          x_position: image.x_position,
          y_position: image.y_position,
          canvas_width: image.canvas_width,
          canvas_height: image.canvas_height,
          rotation: image.rotation,
          z_index: image.z_index,
          opacity: image.opacity,
        }
      ).catch((error) => {
        console.error(`Failed to save image ${image.id}:`, error)
        failedSaves++
        // Continue with other saves even if one fails
        return null
      })
      savePromises.push(savePromise)
    }
    
    // 3. Convert drawing canvas to base64 image
    const canvas = drawingCanvas.value
    if (canvas) {
      // Check if canvas has any drawings (not completely blank)
      const ctx = canvas.getContext('2d')
      if (ctx) {
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        const data = imageData.data
        let hasDrawing = false
        
        // Check if any pixel is not transparent
        for (let i = 3; i < data.length; i += 4) {
          if (data[i] > 0) { // Check alpha channel
            hasDrawing = true
            break
          }
        }
        
        // Only save if there are actual drawings
        if (hasDrawing) {
          drawingDataUrl = canvas.toDataURL('image/png')
          // Also emit for history tracking
          emit('drawing-state-saved', imageData)
        }
      }
    }

    // Wait for all text and image saves to complete
    await Promise.all(savePromises)

    // 4. Save moodboard with drawing layer (wait for this to complete too)
    if (props.moodboard) {
      await new Promise<void>((resolve) => {
        emit('moodboardUpdated', {
          ...props.moodboard,
          canvas_drawing_layer: drawingDataUrl
        })
        // Give the parent component time to save
        setTimeout(() => resolve(), 500)
      })
    }

    // Show appropriate success/warning message
    if (failedSaves === 0) {
      toast.add({
        title: 'Saved Successfully',
        description: `All canvas content saved (${totalItems} items + drawings)`,
        color: 'success',
        icon: 'i-heroicons-check-circle',
      })
    } else {
      toast.add({
        title: 'Partially Saved',
        description: `Saved ${totalItems - failedSaves}/${totalItems} items. ${failedSaves} failed - please try again.`,
        color: 'warning',
        icon: 'i-heroicons-exclamation-triangle',
      })
    }
  } catch (error) {
    console.error('Error saving canvas:', error)
    toast.add({
      title: 'Save Failed',
      description: 'Failed to save canvas. Please try again.',
      color: 'error',
      icon: 'i-heroicons-exclamation-circle',
    })
  } finally {
    isSaving.value = false
  }
}

async function exportCanvas(format: string) {
  try {
    if (format === 'pdf') {
      await exportCanvasAsPDF()
    } else {
      await exportCanvasAsImage(format)
    }
  } catch (error) {
    console.error('Export failed:', error)
    // Export failed silently
  }
}

async function exportCanvasAsImage(format: string) {
  const canvas = canvasElement.value
  if (!canvas) {
    throw new Error('Canvas element not found')
  }
  
  const wrapper = canvas.parentElement
  if (!wrapper) {
    throw new Error('Canvas wrapper not found')
  }

  const exportCanvas = document.createElement('canvas')
  const ctx = exportCanvas.getContext('2d')
  if (!ctx) {
    throw new Error('Could not get canvas context')
  }

  // Export the ENTIRE canvas, not just visible area
  // Get the full canvas dimensions
  const canvasWidth = canvas.offsetWidth
  const canvasHeight = canvas.offsetHeight
  
  // Set export dimensions to the full canvas size (at current zoom level)
  const exportWidth = Math.round(canvasWidth * zoomLevel.value)
  const exportHeight = Math.round(canvasHeight * zoomLevel.value)

  exportCanvas.width = exportWidth
  exportCanvas.height = exportHeight
  
  // Source coordinates cover the entire canvas
  const sourceX = 0
  const sourceY = 0
  const sourceWidth = canvasWidth
  const sourceHeight = canvasHeight

  ctx.fillStyle = props.moodboard.canvas_background_color || '#ffffff'
  ctx.fillRect(0, 0, exportWidth, exportHeight)
  
  // Draw background image if exists (entire background)
  if (props.moodboard.canvas_background_image) {
    try {
      const bgImage = new Image()
      bgImage.crossOrigin = 'anonymous'
      await new Promise<void>((resolve, reject) => {
        bgImage.onload = () => {
          // Draw the entire background
          ctx.drawImage(
            bgImage,
            0, 0, canvasWidth, canvasHeight,  // source: full canvas
            0, 0, exportWidth, exportHeight  // destination: full export canvas
          )
          resolve()
        }
        bgImage.onerror = () => resolve() // Continue even if background fails
        bgImage.src = props.moodboard.canvas_background_image!
      })
    } catch {
      // Continue without background
    }
  }
  
  // Draw grid if enabled (only in visible area)
  if (showGrid.value) {
    const gridSize = canvasSettings.value.grid_size * zoomLevel.value
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)'
    ctx.lineWidth = 1
    
    // Calculate grid starting points based on visible offset
    const gridStartX = (sourceX * zoomLevel.value) % gridSize
    const gridStartY = (sourceY * zoomLevel.value) % gridSize
    
    // Draw vertical lines
    for (let x = gridStartX; x <= exportWidth; x += gridSize) {
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, exportHeight)
      ctx.stroke()
    }
    
    // Draw horizontal lines
    for (let y = gridStartY; y <= exportHeight; y += gridSize) {
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(exportWidth, y)
      ctx.stroke()
    }
  }

  // Draw background image if exists (only the visible portion)
  if (props.moodboard.canvas_background_image) {
    try {
      const bgImage = new Image()
      bgImage.crossOrigin = 'anonymous'
      await new Promise<void>((resolve, reject) => {
        bgImage.onload = () => {
          // Draw only the visible portion of the background
          ctx.drawImage(
            bgImage,
            sourceX, sourceY, sourceWidth, sourceHeight,  // source: visible area
            0, 0, exportWidth, exportHeight  // destination: full export canvas
          )
          resolve()
        }
        bgImage.onerror = () => resolve() // Continue even if background fails
        bgImage.src = props.moodboard.canvas_background_image!
      })
    } catch {
      // Continue without background
    }
  }

  // Calculate scale to convert from stored positions to export size
  const scale = zoomLevel.value

  const getActualElementDimensions = (elementId: string) => {
    // Get the element from data and scale by zoom level (no scroll offset needed for full canvas export)
    const imageElement = canvasImages.value.find((img) => img.id.toString() === elementId)
    
    if (imageElement) {
      return {
        x: (imageElement.x_position || 0) * scale,
        y: (imageElement.y_position || 0) * scale,
        width: (imageElement.canvas_width || 200) * scale,
        height: (imageElement.canvas_height || 200) * scale,
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
          } catch {
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
              } catch {
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
          } catch {
            drawPlaceholder()
          }
        }

        const drawPlaceholder = () => {
          ctx.save()
          ctx.fillStyle = 'rgba(200, 200, 200, 0.5)'
          const x = (img.x_position || 0) * scale
          const y = (img.y_position || 0) * scale
          const width = (img.canvas_width || 200) * scale
          const height = (img.canvas_height || 200) * scale
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

      // Use stored positions and dimensions scaled by zoom level
      const x = (textEl.x_position || 0) * scale
      const y = (textEl.y_position || 0) * scale
      const width = (textEl.width || 200) * scale
      const height = (textEl.height || 50) * scale
      const fontSize = (textEl.font_size || 16) * scale
      const fontWeight = textEl.font_weight || 400
      const fontFamily = textEl.font_family || 'Arial'
      const textColor = textEl.text_color || '#000000'
      const lineHeight = textEl.line_height || 1.4
      const letterSpacing = (textEl.letter_spacing || 0) * scale
      const textAlign = textEl.text_align || 'left'
      const backgroundColor = textEl.background_color
      const borderColor = textEl.border_color
      const borderWidth = (textEl.border_width || 0) * scale

      ctx.save()

      // Apply rotation if needed
      if (textEl.rotation) {
        const centerX = x + width / 2
        const centerY = y + height / 2
        ctx.translate(centerX, centerY)
        ctx.rotate((textEl.rotation * Math.PI) / 180)
        ctx.translate(-centerX, -centerY)
      }

      // Apply opacity
      if (textEl.opacity !== undefined && textEl.opacity !== 1) {
        ctx.globalAlpha = textEl.opacity
      }

      // Draw background if specified
      if (backgroundColor && backgroundColor.trim() !== '') {
        ctx.fillStyle = backgroundColor
        ctx.fillRect(x, y, width, height)
      }

      // Draw border if specified
      if (borderWidth > 0 && borderColor && borderColor.trim() !== '') {
        ctx.strokeStyle = borderColor
        ctx.lineWidth = borderWidth
        ctx.strokeRect(x, y, width, height)
      }

      // Set up text rendering
      ctx.font = `${fontWeight} ${fontSize}px ${fontFamily}`
      ctx.fillStyle = textColor

      // Handle letter spacing (if supported)
      if ('letterSpacing' in ctx) {
        (ctx as any).letterSpacing = `${letterSpacing}px`
      }

      // Calculate padding (8px like the component)
      const padding = 8 * scale

      // Split text into lines based on content (handle \n) and word wrapping
      const lines: string[] = []
      const paragraphs = textEl.content.split('\n')
      
      for (const paragraph of paragraphs) {
        if (paragraph.trim() === '') {
          lines.push('')
          continue
        }

        // Word wrap within available width
        const words = paragraph.split(' ')
        let currentLine = ''

        for (const word of words) {
          const testLine = currentLine ? `${currentLine} ${word}` : word
          const metrics = ctx.measureText(testLine)
          const testWidth = metrics.width + (testLine.length - 1) * letterSpacing

          if (testWidth > width - padding * 2 && currentLine !== '') {
            lines.push(currentLine)
            currentLine = word
          } else {
            currentLine = testLine
          }
        }

        if (currentLine) {
          lines.push(currentLine)
        }
      }

      // Calculate line positions
      const lineHeightPx = fontSize * lineHeight
      let currentY = y + padding + fontSize // Start position (top padding + font size for baseline)

      // Draw each line
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i]
        
        if (line.trim() === '') {
          currentY += lineHeightPx
          continue
        }

        let lineX = x + padding

        // Apply text alignment
        if (textAlign === 'center') {
          const metrics = ctx.measureText(line)
          const lineWidth = metrics.width + (line.length - 1) * letterSpacing
          lineX = x + (width - lineWidth) / 2
        } else if (textAlign === 'right') {
          const metrics = ctx.measureText(line)
          const lineWidth = metrics.width + (line.length - 1) * letterSpacing
          lineX = x + width - lineWidth - padding
        } else if (textAlign === 'justify' && i < lines.length - 1) {
          // For justify, draw with default spacing (simplified - full justify is complex)
          lineX = x + padding
        }

        // Break if we exceed the text box height
        if (currentY > y + height - padding) {
          break
        }

        // Draw the text line
        if (letterSpacing > 0.5) {
          // Manual letter spacing for better control
          let charX = lineX
          for (const char of line) {
            ctx.fillText(char, charX, currentY)
            charX += ctx.measureText(char).width + letterSpacing
          }
        } else {
          ctx.fillText(line, lineX, currentY)
        }

        currentY += lineHeightPx
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
      const drawingImageData = drawingCtx.getImageData(
        0,
        0,
        drawingCanvas.value.width,
        drawingCanvas.value.height,
      )

      // Check if there's actually any drawing content
      const hasDrawing = drawingImageData.data.some((value, index) => {
        // Check alpha channel (every 4th value)
        return index % 4 === 3 && value > 0
      })

      if (hasDrawing) {
        // Draw only the visible portion of the drawing canvas
        // Source: the visible area in the full-size drawing canvas
        // Destination: the entire export canvas
        
        ctx.save()
        ctx.drawImage(
          drawingCanvas.value,
          sourceX, sourceY, sourceWidth, sourceHeight,  // source: visible area in logical coords
          0, 0, exportWidth, exportHeight  // destination: full export canvas
        )
        ctx.restore()
      }
    }
  }

  return new Promise<void>((resolve, reject) => {
    const mimeType = format === 'jpg' ? 'image/jpeg' : 'image/png'
    const quality = format === 'jpg' ? 0.9 : undefined

    exportCanvas.toBlob(
      (blob) => {
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
      },
      mimeType,
      quality,
    )
  })
}

async function exportCanvasAsPDF() {
  // Import jsPDF dynamically
  const { jsPDF } = await import('jspdf')
  
  const canvas = canvasElement.value
  if (!canvas) {
    throw new Error('Canvas element not found')
  }
  
  const wrapper = canvas.parentElement
  if (!wrapper) {
    throw new Error('Canvas wrapper not found')
  }

  // Export the ENTIRE canvas, not just visible area
  // Get the full canvas dimensions
  const canvasWidth = canvas.offsetWidth
  const canvasHeight = canvas.offsetHeight
  
  // Create a temporary canvas for export
  const tempCanvas = document.createElement('canvas')
  const exportWidth = Math.round(canvasWidth * zoomLevel.value)
  const exportHeight = Math.round(canvasHeight * zoomLevel.value)
  
  tempCanvas.width = exportWidth
  tempCanvas.height = exportHeight
  
  const ctx = tempCanvas.getContext('2d')
  if (!ctx) {
    throw new Error('Could not get canvas context')
  }

  // Source coordinates cover the entire canvas
  const sourceX = 0
  const sourceY = 0
  const sourceWidth = canvasWidth
  const sourceHeight = canvasHeight
  
  // Fill with background color
  ctx.fillStyle = props.moodboard.canvas_background_color || '#ffffff'
  ctx.fillRect(0, 0, exportWidth, exportHeight)
  
  // Draw background image if exists (entire background)
  if (props.moodboard.canvas_background_image) {
    try {
      const bgImage = new Image()
      bgImage.crossOrigin = 'anonymous'
      await new Promise<void>((resolve, reject) => {
        bgImage.onload = () => {
          ctx.drawImage(
            bgImage,
            0, 0, canvasWidth, canvasHeight,
            0, 0, exportWidth, exportHeight
          )
          resolve()
        }
        bgImage.onerror = () => resolve()
        bgImage.src = props.moodboard.canvas_background_image!
      })
    } catch {
      // Continue without background
    }
  }

  // Draw grid if enabled
  if (showGrid.value) {
    const gridSize = canvasSettings.value.grid_size * zoomLevel.value
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)'
    ctx.lineWidth = 1
    
    // Draw vertical lines
    for (let x = 0; x <= exportWidth; x += gridSize) {
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, exportHeight)
      ctx.stroke()
    }
    
    // Draw horizontal lines
    for (let y = 0; y <= exportHeight; y += gridSize) {
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(exportWidth, y)
      ctx.stroke()
    }
  }

  const scale = zoomLevel.value

  const getActualElementDimensions = (elementId: string) => {
    const imageElement = canvasImages.value.find((img) => img.id.toString() === elementId)
    
    if (imageElement) {
      return {
        x: (imageElement.x_position || 0) * scale,
        y: (imageElement.y_position || 0) * scale,
        width: (imageElement.canvas_width || 200) * scale,
        height: (imageElement.canvas_height || 200) * scale,
      }
    }
    return null
  }

  // Draw images
  const imagePromises = canvasImages.value.map(async (img) => {
    return new Promise<void>((resolve) => {
      if (!img.image_url) {
        resolve()
        return
      }

      const image = new Image()
      image.crossOrigin = 'anonymous'
      
      image.onload = () => {
        const actualDimensions = getActualElementDimensions(img.id.toString())
        const x = actualDimensions?.x || (img.x_position || 0)
        const y = actualDimensions?.y || (img.y_position || 0)
        const width = actualDimensions?.width || (img.canvas_width || 200)
        const height = actualDimensions?.height || (img.canvas_height || 200)

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
        } catch {
          // Drawing failed
        }

        ctx.restore()
        resolve()
      }

      image.onerror = () => {
        // Draw placeholder
        ctx.save()
        ctx.fillStyle = 'rgba(200, 200, 200, 0.5)'
        const x = (img.x_position || 0) * scale
        const y = (img.y_position || 0) * scale
        const width = (img.canvas_width || 200) * scale
        const height = (img.canvas_height || 200) * scale
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
    })
  })

  // Draw text elements
  const textPromises = canvasTextElements.value.map(async (textEl) => {
    return new Promise<void>((resolve) => {
      if (!textEl.content || textEl.content.trim() === '') {
        resolve()
        return
      }

      // Use stored positions and dimensions scaled by zoom level
      const x = (textEl.x_position || 0) * scale
      const y = (textEl.y_position || 0) * scale
      const width = (textEl.width || 200) * scale
      const height = (textEl.height || 50) * scale
      const fontSize = (textEl.font_size || 16) * scale
      const fontWeight = textEl.font_weight || 400
      const fontFamily = textEl.font_family || 'Arial'
      const textColor = textEl.text_color || '#000000'
      const lineHeight = textEl.line_height || 1.4
      const letterSpacing = (textEl.letter_spacing || 0) * scale
      const textAlign = textEl.text_align || 'left'
      const backgroundColor = textEl.background_color
      const borderColor = textEl.border_color
      const borderWidth = (textEl.border_width || 0) * scale

      ctx.save()

      // Apply rotation if needed
      if (textEl.rotation) {
        const centerX = x + width / 2
        const centerY = y + height / 2
        ctx.translate(centerX, centerY)
        ctx.rotate((textEl.rotation * Math.PI) / 180)
        ctx.translate(-centerX, -centerY)
      }

      // Apply opacity
      if (textEl.opacity !== undefined && textEl.opacity !== 1) {
        ctx.globalAlpha = textEl.opacity
      }

      // Draw background if specified
      if (backgroundColor && backgroundColor.trim() !== '') {
        ctx.fillStyle = backgroundColor
        ctx.fillRect(x, y, width, height)
      }

      // Draw border if specified
      if (borderWidth > 0 && borderColor && borderColor.trim() !== '') {
        ctx.strokeStyle = borderColor
        ctx.lineWidth = borderWidth
        ctx.strokeRect(x, y, width, height)
      }

      // Set up text rendering
      ctx.font = `${fontWeight} ${fontSize}px ${fontFamily}`
      ctx.fillStyle = textColor

      // Handle letter spacing (if supported)
      if ('letterSpacing' in ctx) {
        (ctx as any).letterSpacing = `${letterSpacing}px`
      }

      // Calculate padding (8px like the component)
      const padding = 8 * scale

      // Split text into lines based on content (handle \n) and word wrapping
      const lines: string[] = []
      const paragraphs = textEl.content.split('\n')
      
      for (const paragraph of paragraphs) {
        if (paragraph.trim() === '') {
          lines.push('')
          continue
        }

        // Word wrap within available width
        const words = paragraph.split(' ')
        let currentLine = ''

        for (const word of words) {
          const testLine = currentLine ? `${currentLine} ${word}` : word
          const metrics = ctx.measureText(testLine)
          const testWidth = metrics.width + (testLine.length - 1) * letterSpacing

          if (testWidth > width - padding * 2 && currentLine !== '') {
            lines.push(currentLine)
            currentLine = word
          } else {
            currentLine = testLine
          }
        }

        if (currentLine) {
          lines.push(currentLine)
        }
      }

      // Calculate line positions
      const lineHeightPx = fontSize * lineHeight
      let currentY = y + padding + fontSize // Start position (top padding + font size for baseline)

      // Draw each line
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i]
        
        if (line.trim() === '') {
          currentY += lineHeightPx
          continue
        }

        let lineX = x + padding

        // Apply text alignment
        if (textAlign === 'center') {
          const metrics = ctx.measureText(line)
          const lineWidth = metrics.width + (line.length - 1) * letterSpacing
          lineX = x + (width - lineWidth) / 2
        } else if (textAlign === 'right') {
          const metrics = ctx.measureText(line)
          const lineWidth = metrics.width + (line.length - 1) * letterSpacing
          lineX = x + width - lineWidth - padding
        } else if (textAlign === 'justify' && i < lines.length - 1) {
          // For justify, draw with default spacing (simplified - full justify is complex)
          lineX = x + padding
        }

        // Break if we exceed the text box height
        if (currentY > y + height - padding) {
          break
        }

        // Draw the text line
        if (letterSpacing > 0.5) {
          // Manual letter spacing for better control
          let charX = lineX
          for (const char of line) {
            ctx.fillText(char, charX, currentY)
            charX += ctx.measureText(char).width + letterSpacing
          }
        } else {
          ctx.fillText(line, lineX, currentY)
        }

        currentY += lineHeightPx
      }

      ctx.restore()
      resolve()
    })
  })

  await Promise.all([...imagePromises, ...textPromises])

  // Add drawing layer if it exists
  if (drawingCanvas.value) {
    const drawingCtx = drawingCanvas.value.getContext('2d')
    if (drawingCtx) {
      const drawingImageData = drawingCtx.getImageData(
        0, 0,
        drawingCanvas.value.width,
        drawingCanvas.value.height,
      )

      const hasDrawing = drawingImageData.data.some((value, index) => {
        return index % 4 === 3 && value > 0
      })

      if (hasDrawing) {
        ctx.save()
        ctx.drawImage(
          drawingCanvas.value,
          sourceX, sourceY, sourceWidth, sourceHeight,
          0, 0, exportWidth, exportHeight
        )
        ctx.restore()
      }
    }
  }

  // Convert canvas to data URL
  const imgData = tempCanvas.toDataURL('image/jpeg', 0.95)
  
  // Calculate PDF dimensions (A4 or custom based on aspect ratio)
  const imgWidth = exportWidth
  const imgHeight = exportHeight
  const aspectRatio = imgWidth / imgHeight
  
  // Use landscape or portrait based on aspect ratio
  const orientation = aspectRatio > 1 ? 'landscape' : 'portrait'
  
  // Create PDF
  const pdf = new jsPDF({
    orientation,
    unit: 'mm',
    format: 'a4'
  })
  
  // Get PDF dimensions
  const pdfWidth = pdf.internal.pageSize.getWidth()
  const pdfHeight = pdf.internal.pageSize.getHeight()
  
  // Calculate dimensions to fit image in PDF while maintaining aspect ratio
  let finalWidth = pdfWidth
  let finalHeight = pdfWidth / aspectRatio
  
  if (finalHeight > pdfHeight) {
    finalHeight = pdfHeight
    finalWidth = pdfHeight * aspectRatio
  }
  
  // Center the image
  const x = (pdfWidth - finalWidth) / 2
  const y = (pdfHeight - finalHeight) / 2
  
  pdf.addImage(imgData, 'JPEG', x, y, finalWidth, finalHeight)
  
  // Save the PDF
  pdf.save(`moodboard-${props.moodboard.title || 'untitled'}.pdf`)
}

// Drawing Functions
function getCanvasPosition(event: MouseEvent | Touch): { x: number; y: number } {
  if (!drawingCanvas.value) return { x: 0, y: 0 }

  const rect = drawingCanvas.value.getBoundingClientRect()
  return {
    x: (event.clientX - rect.left) / zoomLevel.value,
    y: (event.clientY - rect.top) / zoomLevel.value,
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
  const distance = Math.sqrt(
    (pos.x - lastDrawPosition.value.x) ** 2 + (pos.y - lastDrawPosition.value.y) ** 2,
  )

  if (timeDelta > 0) {
    drawingVelocity.value = distance / timeDelta
    // Simulate pressure: slower movement = more pressure
    const simulatedPressure = Math.max(0.3, Math.min(1.0, 1.0 - drawingVelocity.value * 0.5))

    // Calculate brush angle based on movement direction
    if (distance > 2) {
      brushAngle.value = Math.atan2(
        pos.y - lastDrawPosition.value.y,
        pos.x - lastDrawPosition.value.x,
      )
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
          drawPen(
            ctx,
            lastDrawPosition.value,
            pos,
            brushSize,
            brushColor,
            brushOpacity,
            brushHardness,
            simulatedPressure,
            blendMode,
          )
          break
        case 'marker':
          drawMarker(
            ctx,
            lastDrawPosition.value,
            pos,
            brushSize,
            brushColor,
            brushOpacity,
            flowRate,
            brushAngle.value,
            blendMode,
          )
          break
        case 'pencil':
          drawPencil(
            ctx,
            lastDrawPosition.value,
            pos,
            brushSize,
            brushColor,
            brushOpacity,
            brushHardness,
            simulatedPressure,
            blendMode,
          )
          break
        case 'highlighter':
          drawHighlighter(
            ctx,
            lastDrawPosition.value,
            pos,
            brushSize,
            brushColor,
            brushOpacity,
            brushAngle.value,
            blendMode,
          )
          break
        case 'spray':
          drawSpray(
            ctx,
            pos,
            brushSize,
            brushColor,
            brushOpacity,
            flowRate,
            simulatedPressure,
            blendMode,
          )
          break
        case 'watercolor':
          drawWatercolor(
            ctx,
            lastDrawPosition.value,
            pos,
            brushSize,
            brushColor,
            brushOpacity,
            flowRate,
            simulatedPressure,
            blendMode,
          )
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

function drawPen(
  ctx: CanvasRenderingContext2D,
  from: { x: number; y: number },
  to: { x: number; y: number },
  size: number,
  color: string,
  opacity: number,
  hardness: number,
  pressure: number = 1,
  blendMode: string = 'source-over',
) {
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

function drawMarker(
  ctx: CanvasRenderingContext2D,
  from: { x: number; y: number },
  to: { x: number; y: number },
  size: number,
  color: string,
  opacity: number,
  flowRate: number,
  angle: number = 0,
  blendMode: string = 'source-over',
) {
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

function drawPencil(
  ctx: CanvasRenderingContext2D,
  from: { x: number; y: number },
  to: { x: number; y: number },
  size: number,
  color: string,
  opacity: number,
  hardness: number,
  pressure: number = 1,
  blendMode: string = 'source-over',
) {
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

function drawHighlighter(
  ctx: CanvasRenderingContext2D,
  from: { x: number; y: number },
  to: { x: number; y: number },
  size: number,
  color: string,
  opacity: number,
  angle: number = 0,
  blendMode: string = 'multiply',
) {
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

function drawSpray(
  ctx: CanvasRenderingContext2D,
  pos: { x: number; y: number },
  size: number,
  color: string,
  opacity: number,
  flowRate: number,
  pressure: number = 1,
  blendMode: string = 'source-over',
) {
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

function drawWatercolor(
  ctx: CanvasRenderingContext2D,
  from: { x: number; y: number },
  to: { x: number; y: number },
  size: number,
  color: string,
  opacity: number,
  flowRate: number,
  pressure: number = 1,
  blendMode: string = 'multiply',
) {
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

function drawEraser(
  ctx: CanvasRenderingContext2D,
  from: { x: number; y: number },
  to: { x: number; y: number },
  size: number,
) {
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
    // Convert touch to mouse-like event
    const mouseEvent = {
      clientX: touch.clientX,
      clientY: touch.clientY,
      preventDefault: () => {},
      stopPropagation: () => {},
    } as MouseEvent
    startDrawing(mouseEvent)
  }
}

function handleTouchMove(event: TouchEvent) {
  event.preventDefault()
  if (event.touches.length === 1) {
    const touch = event.touches[0]
    // Convert touch to mouse-like event
    const mouseEvent = {
      clientX: touch.clientX,
      clientY: touch.clientY,
      preventDefault: () => {},
      stopPropagation: () => {},
    } as MouseEvent
    draw(mouseEvent)
  }
}

function handleTouchEnd(event: TouchEvent) {
  event.preventDefault()
  stopDrawing()
}

// Watch for undo/redo from parent component
watch(
  () => props.historyStep,
  (newStep, _oldStep) => {
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
  },
)

// Watch for clear drawing command (when history is empty and step is -1)
watch(
  () => [props.drawingHistory?.length, props.historyStep],
  ([historyLength, step]) => {
    if (!drawingCanvas.value) return

    if (historyLength === 0 && step === -1) {
      const ctx = drawingCanvas.value.getContext('2d')
      if (ctx) {
        ctx.clearRect(0, 0, drawingCanvas.value.width, drawingCanvas.value.height)
      }
    }
  },
  { deep: true },
)

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
  
  // Restore drawing layer if it exists
  restoreDrawingLayer()
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
})

// Watch for moodboard changes to restore drawing layer
watch(
  () => props.moodboard?.canvas_drawing_layer,
  () => {
    restoreDrawingLayer()
  }
)

// Function to restore drawing layer from saved data
async function restoreDrawingLayer() {
  await nextTick() // Ensure canvas is mounted
  
  if (!drawingCanvas.value || !props.moodboard?.canvas_drawing_layer) return
  
  const ctx = drawingCanvas.value.getContext('2d')
  if (!ctx) return
  
  // Load the image from base64
  const img = new Image()
  img.onload = () => {
    // Clear canvas first
    ctx.clearRect(0, 0, drawingCanvas.value!.width, drawingCanvas.value!.height)
    // Draw the saved image
    ctx.drawImage(img, 0, 0)
  }
  img.src = props.moodboard.canvas_drawing_layer
}
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
  flex-wrap: wrap;
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

/* Draw controls styling */
.drawing-toolbar-expanded {
  width: 100%;
  background: linear-gradient(to bottom, #f9fafb, #f3f4f6);
  border-top: 1px solid #e5e7eb;
  border-bottom: 2px solid #d1d5db;
  padding: 0.875rem 1.25rem;
  margin-top: 0;
  grid-column: 1 / -1;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
}

.drawing-controls-row {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.control-group.brush-control {
  background: white;
  padding: 0.375rem 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.control-label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #4b5563;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.control-value {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #1f2937;
  min-width: 40px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.toolbar-divider {
  width: 1px;
  height: 32px;
  background: linear-gradient(to bottom, transparent, #d1d5db 20%, #d1d5db 80%, transparent);
  margin: 0 0.5rem;
}

.range-input-inline {
  width: 100px;
  height: 6px;
  background: linear-gradient(to right, #e5e7eb, #cbd5e1);
  border-radius: 3px;
  outline: none;
  appearance: none;
  cursor: pointer;
  transition: background 0.2s;
}

.range-input-inline:hover {
  background: linear-gradient(to right, #cbd5e1, #94a3b8);
}

.range-input-inline::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s, box-shadow 0.2s;
}

.range-input-inline::-webkit-slider-thumb:hover {
  transform: scale(1.15);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

.range-input-inline::-moz-range-thumb {
  width: 16px;
  height: 16px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border-radius: 50%;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s, box-shadow 0.2s;
}

.range-input-inline::-moz-range-thumb:hover {
  transform: scale(1.15);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

.color-input-inline {
  width: 40px;
  height: 40px;
  border: 2px solid #d1d5db;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.color-input-inline:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);
  transform: scale(1.05);
}

.ml-auto {
  margin-left: auto;
}

/* Legacy draw controls styling (can be removed if not used elsewhere) */
.draw-controls {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.control-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
}

.brush-settings {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 0.375rem;
  border: 1px solid #e5e7eb;
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.setting-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: #374151;
  min-width: 50px;
}

.range-input {
  width: 80px;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  outline: none;
  appearance: none;
  cursor: pointer;
}

.range-input::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 12px;
  background: #3b82f6;
  border-radius: 50%;
  cursor: pointer;
}

.range-input::-moz-range-thumb {
  width: 12px;
  height: 12px;
  background: #3b82f6;
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.color-input {
  width: 32px;
  height: 32px;
  border: 1px solid #e5e7eb;
  border-radius: 0.25rem;
  cursor: pointer;
}

.setting-value {
  font-size: 0.7rem;
  font-weight: 500;
  color: #6b7280;
  min-width: 35px;
}

.drawing-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding-top: 0.5rem;
  border-top: 1px solid #e5e7eb;
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
  content: '✏️ Click anywhere to add text';
  position: absolute;
  top: 20px;
  right: 20px;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  pointer-events: none;
  z-index: 100;
  opacity: 0;
  animation: showBriefly 4s ease-in-out;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  border: 2px solid white;
}

.moodboard-canvas.mode-image {
  cursor: copy;
}

/* Visual feedback for image mode - subtle indicator */
.moodboard-canvas.mode-image::after {
  content: '📷 Click anywhere to add image';
  position: absolute;
  top: 20px;
  right: 20px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  pointer-events: none;
  z-index: 100;
  opacity: 0;
  animation: showBriefly 4s ease-in-out;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  border: 2px solid white;
}

@keyframes fadeInOut {
  0% {
    opacity: 0;
  }
  20% {
    opacity: 0.9;
  }
  80% {
    opacity: 0.9;
  }
  100% {
    opacity: 0;
  }
}

@keyframes showBriefly {
  0% {
    opacity: 0;
    transform: translateY(-10px);
  }
  15% {
    opacity: 0.8;
    transform: translateY(0);
  }
  85% {
    opacity: 0.8;
    transform: translateY(0);
  }
  100% {
    opacity: 0;
    transform: translateY(-10px);
  }
}

.grid-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(to right, rgba(0, 0, 0, 0.1) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0, 0, 0, 0.1) 1px, transparent 1px);
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
  position: fixed;
  right: 1.5rem;
  top: 50%;
  transform: translateY(-50%);
  width: 320px;
  max-height: calc(100vh - 100px);
  background: linear-gradient(to bottom, #ffffff, #fafbfc);
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 0;
  overflow: visible;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12), 0 4px 8px rgba(0, 0, 0, 0.08);
  z-index: 1000;
  transition: all 0.3s ease;
  clip-path: none;
}

.properties-panel:hover {
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15), 0 5px 10px rgba(0, 0, 0, 0.1);
}

.properties-panel.collapsed {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  top: auto;
  bottom: 2rem;
  transform: none;
}

.properties-panel.collapsed:hover {
  transform: scale(1.1);
}

.properties-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border-bottom: 2px solid #e5e7eb;
  border-radius: 12px 12px 0 0;
  overflow: hidden;
}

.properties-panel.collapsed .properties-header {
  padding: 0;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  height: 60px;
  border-bottom: none;
  justify-content: center;
}

.properties-panel.collapsed .properties-header h3 {
  display: none;
}

.collapse-button {
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 16px;
  font-weight: bold;
}

.collapse-button:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.properties-panel.collapsed .collapse-button {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  font-size: 24px;
  border: none;
  background: transparent;
}

.properties-content {
  padding: 1.25rem;
  max-height: calc(100vh - 180px);
  overflow-y: auto;
  overflow-x: visible;
  position: relative;
  z-index: 1;
  background: linear-gradient(to bottom, #ffffff, #fafbfc);
  border-radius: 0 0 12px 12px;
}

.properties-panel h3 {
  font-size: 1.125rem;
  font-weight: 700;
  margin: 0;
  color: white;
}

/* Responsive adjustments for smaller screens */
@media (max-width: 768px) {
  .properties-panel {
    width: 280px;
    right: 1rem;
  }
  
  .properties-panel.collapsed {
    width: 50px;
    height: 50px;
    right: 1rem;
    bottom: 1rem;
  }
}

@media (max-height: 700px) {
  .properties-panel {
    max-height: calc(100vh - 80px);
  }
  
  .properties-content {
    max-height: calc(100vh - 160px);
  }
}

.property-group {
  margin-bottom: 1.25rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.property-group:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.property-group label {
  display: block;
  font-size: 0.8125rem;
  font-weight: 600;
  margin-bottom: 0.625rem;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-row {
  display: flex;
  gap: 0.75rem;
}

.input-row .u-input {
  flex: 1;
}

/* Typography specific styling */
.property-group .grid {
  gap: 0.75rem;
}

.property-group .grid-cols-2 > div {
  display: flex;
  flex-direction: column;
}

.property-group .text-sm {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 0.375rem;
  text-transform: none;
  letter-spacing: normal;
}

/* Color input styling */
.property-group input[type='color'] {
  height: 2.75rem;
  border-radius: 0.5rem;
  border: 2px solid #d1d5db;
  cursor: pointer;
  transition: all 0.2s ease;
}

.property-group input[type='color']:hover {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Quick style buttons */
.property-group .grid .button {
  font-size: 0.75rem;
  padding: 0.375rem 0.75rem;
  font-weight: 600;
  transition: all 0.15s ease;
}

/* Ensure dropdowns appear above everything */
.property-group :deep(.ui-select-menu),
.property-group :deep([data-headlessui-state]) {
  z-index: 9999 !important;
}

/* Ensure dropdown text doesn't get clipped */
.property-group :deep(.ui-select-menu-item),
.property-group :deep([role="option"]) {
  white-space: nowrap;
  overflow: visible;
}

/* Drawing Canvas Styles */
.drawing-canvas {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: auto;
  touch-action: none; /* Prevent scrolling on mobile when drawing */
  transition: opacity 0.15s ease;
  /* Always visible, acts as the background drawing layer like MS Paint */
}

/* Subtle visual feedback when drawing mode is active */
.drawing-canvas.drawing-active {
  /* Slight highlight to show drawing mode is active */
  filter: brightness(1.02);
}

/* When not in drawing mode, slightly reduce opacity to emphasize it's background */
.drawing-canvas:not(.drawing-active) {
  opacity: 0.98;
}
</style>
