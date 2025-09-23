<template>
  <div
    class="canvas-image-element"
    :class="{ 
      selected, 
      dragging: isDragging, 
      resizing: isResizing,
      rotating: isRotating
    }"
    :style="elementStyle"
    :data-image-id="image.id"
    @mousedown="handleMouseDown"
    @click="handleClick"
  >
    <img
      :src="getFullImageUrl(image.image_url)"
      :alt="image.title"
      class="element-image"
      draggable="false"
      @load="handleImageLoad"
    />
    
    <!-- Selection handles -->
    <div v-if="selected" class="selection-handles">
      <div class="handle handle-nw" @mousedown="handleResize($event, 'nw')"/>
      <div class="handle handle-ne" @mousedown="handleResize($event, 'ne')"/>
      <div class="handle handle-sw" @mousedown="handleResize($event, 'sw')"/>
      <div class="handle handle-se" @mousedown="handleResize($event, 'se')"/>
      <div class="handle handle-n" @mousedown="handleResize($event, 'n')"/>
      <div class="handle handle-s" @mousedown="handleResize($event, 's')"/>
      <div class="handle handle-w" @mousedown="handleResize($event, 'w')"/>
      <div class="handle handle-e" @mousedown="handleResize($event, 'e')"/>
    </div>

    <!-- Delete button -->
    <button 
      v-if="selected"
      class="delete-button"
      title="Delete"
      @click.stop="handleDelete"
    >
      ×
    </button>

    <!-- Rotation handle -->
    <div 
      v-if="selected"
      class="rotation-handle"
      @mousedown="handleRotationStart"
    >
      ↻
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { MoodboardImage } from '~/composables/useMoodboards'

interface Props {
  image: MoodboardImage
  selected: boolean
  zoomLevel: number
  snapToGrid: boolean
  gridSize: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  select: [imageId: string, multiSelect?: boolean]
  update: [image: MoodboardImage]
  delete: [imageId: string]
  dragStart: [imageId: string]
}>()

const isDragging = ref(false)
const isResizing = ref(false)
const isRotating = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const resizeHandle = ref<string>('')
const originalBounds = ref({ x: 0, y: 0, width: 0, height: 0 })

// Local state for smooth visual updates during interactions
const localPosition = ref({ x: 0, y: 0 })
const localSize = ref({ width: 0, height: 0 })
const localRotation = ref(0)
const rotationStarted = ref(false) // Track if we've actually started rotating

// Computed style that uses local state during interactions, props otherwise
const elementStyle = computed(() => ({
  left: `${isDragging.value || isResizing.value ? localPosition.value.x : props.image.x_position}px`,
  top: `${isDragging.value || isResizing.value ? localPosition.value.y : props.image.y_position}px`,
  width: `${isDragging.value || isResizing.value ? localSize.value.width : props.image.canvas_width}px`,
  height: `${isDragging.value || isResizing.value ? localSize.value.height : props.image.canvas_height}px`,
  transform: `rotate(${isRotating.value ? localRotation.value : (props.image.rotation || 0)}deg)`,
  // Give dragged/resized images temporary highest z-index for better UX
  zIndex: isDragging.value || isResizing.value || isRotating.value ? 9999 : props.image.z_index,
  opacity: props.image.opacity
}))

// Get runtime config for API base URL
const config = useRuntimeConfig()

function getFullImageUrl(url: string): string {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${config.public.apiBase}${url}`
}

function handleClick(event: MouseEvent) {
  event.stopPropagation()
  emit('select', props.image.id, event.ctrlKey || event.metaKey)
}

function handleMouseDown(event: MouseEvent) {
  if (event.target === event.currentTarget || (event.target as Element).classList.contains('element-image')) {
    // First, ensure this image is selected (this will trigger auto bring-to-front)
    if (!props.selected) {
      emit('select', props.image.id, event.ctrlKey || event.metaKey)
    }
    
    // Emit drag start event to bring image to front
    emit('dragStart', props.image.id)
    
    isDragging.value = true
    dragStart.value = { x: event.clientX, y: event.clientY }
    originalBounds.value = {
      x: props.image.x_position,
      y: props.image.y_position,
      width: props.image.canvas_width,
      height: props.image.canvas_height
    }
    // Initialize local state
    localPosition.value = { x: props.image.x_position, y: props.image.y_position }
    localSize.value = { width: props.image.canvas_width, height: props.image.canvas_height }
    
    document.addEventListener('mousemove', handleDrag)
    document.addEventListener('mouseup', handleDragEnd)
    event.preventDefault()
  }
}

function handleDrag(event: MouseEvent) {
  if (!isDragging.value) return

  const deltaX = (event.clientX - dragStart.value.x) / props.zoomLevel
  const deltaY = (event.clientY - dragStart.value.y) / props.zoomLevel

  let newX = originalBounds.value.x + deltaX
  let newY = originalBounds.value.y + deltaY

  // Snap to grid if enabled
  if (props.snapToGrid) {
    newX = Math.round(newX / props.gridSize) * props.gridSize
    newY = Math.round(newY / props.gridSize) * props.gridSize
  }

  // Update local state for smooth visual feedback
  localPosition.value = {
    x: Math.max(0, newX),
    y: Math.max(0, newY)
  }

  // Don't emit updates during dragging - only update visually
}

function handleDragEnd() {
  if (!isDragging.value) return
  
  isDragging.value = false
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', handleDragEnd)

  // Now emit the final update with the local position
  const updatedImage: MoodboardImage = {
    ...props.image,
    x_position: localPosition.value.x,
    y_position: localPosition.value.y
  }

  emit('update', updatedImage)
}

function handleResize(event: MouseEvent, handle: string) {
  event.stopPropagation()
  isResizing.value = true
  resizeHandle.value = handle
  dragStart.value = { x: event.clientX, y: event.clientY }
  originalBounds.value = {
    x: props.image.x_position,
    y: props.image.y_position,
    width: props.image.canvas_width,
    height: props.image.canvas_height
  }
  // Initialize local state
  localPosition.value = { x: props.image.x_position, y: props.image.y_position }
  localSize.value = { width: props.image.canvas_width, height: props.image.canvas_height }
  
  document.addEventListener('mousemove', handleResizeMove)
  document.addEventListener('mouseup', handleResizeEnd)
  event.preventDefault()
}

function handleResizeMove(event: MouseEvent) {
  if (!isResizing.value) return

  const deltaX = (event.clientX - dragStart.value.x) / props.zoomLevel
  const deltaY = (event.clientY - dragStart.value.y) / props.zoomLevel

  const newBounds = { ...originalBounds.value }

  switch (resizeHandle.value) {
    case 'nw':
      newBounds.width = Math.max(20, originalBounds.value.width - deltaX)
      newBounds.height = Math.max(20, originalBounds.value.height - deltaY)
      newBounds.x = originalBounds.value.x + (originalBounds.value.width - newBounds.width)
      newBounds.y = originalBounds.value.y + (originalBounds.value.height - newBounds.height)
      break
    case 'ne':
      newBounds.width = Math.max(20, originalBounds.value.width + deltaX)
      newBounds.height = Math.max(20, originalBounds.value.height - deltaY)
      newBounds.y = originalBounds.value.y + (originalBounds.value.height - newBounds.height)
      break
    case 'sw':
      newBounds.width = Math.max(20, originalBounds.value.width - deltaX)
      newBounds.height = Math.max(20, originalBounds.value.height + deltaY)
      newBounds.x = originalBounds.value.x + (originalBounds.value.width - newBounds.width)
      break
    case 'se':
      newBounds.width = Math.max(20, originalBounds.value.width + deltaX)
      newBounds.height = Math.max(20, originalBounds.value.height + deltaY)
      break
    case 'n':
      newBounds.height = Math.max(20, originalBounds.value.height - deltaY)
      newBounds.y = originalBounds.value.y + (originalBounds.value.height - newBounds.height)
      break
    case 's':
      newBounds.height = Math.max(20, originalBounds.value.height + deltaY)
      break
    case 'w':
      newBounds.width = Math.max(20, originalBounds.value.width - deltaX)
      newBounds.x = originalBounds.value.x + (originalBounds.value.width - newBounds.width)
      break
    case 'e':
      newBounds.width = Math.max(20, originalBounds.value.width + deltaX)
      break
  }

  // Update local state for smooth visual feedback
  localPosition.value = { x: newBounds.x, y: newBounds.y }
  localSize.value = { width: newBounds.width, height: newBounds.height }

  // Don't emit updates during resizing - only update visually
}

function handleResizeEnd() {
  if (!isResizing.value) return
  
  isResizing.value = false
  resizeHandle.value = ''
  document.removeEventListener('mousemove', handleResizeMove)
  document.removeEventListener('mouseup', handleResizeEnd)

  // Now emit the final update with the local state
  const updatedImage: MoodboardImage = {
    ...props.image,
    x_position: localPosition.value.x,
    y_position: localPosition.value.y,
    canvas_width: localSize.value.width,
    canvas_height: localSize.value.height
  }

  emit('update', updatedImage)
}

function handleRotationStart(event: MouseEvent) {
  event.stopPropagation()
  event.preventDefault()

  
  // Set rotating state immediately
  isRotating.value = true
  rotationStarted.value = false // Reset the actual rotation started flag
  
  // Simple approach: just store mouse start position and current rotation
  const currentRotation = props.image.rotation || 0
  


  
  dragStart.value = { x: event.clientX, y: event.clientY }
  originalBounds.value = { x: 0, y: 0, width: 0, height: currentRotation } // Store rotation in height field
  localRotation.value = currentRotation
  
  // Add event listeners to document to ensure they work even if mouse leaves element
  document.addEventListener('mousemove', handleRotationMove, { passive: false })
  document.addEventListener('mouseup', handleRotationEnd, { passive: false })
  

}

function handleRotationMove(event: MouseEvent) {
  if (!isRotating.value) {

    return
  }
  
  event.preventDefault()
  event.stopPropagation()
  

  
  // Check if we've moved enough to start rotating (prevent accidental clicks)
  const deltaX = event.clientX - dragStart.value.x
  const deltaY = event.clientY - dragStart.value.y
  const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)
  
  if (!rotationStarted.value && distance < 5) {

    return // Need at least 5px movement to start rotating
  }
  
  if (!rotationStarted.value) {
    rotationStarted.value = true

  }
  
  // Simple rotation: horizontal movement = rotation change
  const rotationSpeed = 2 // 2 degrees per pixel for more responsive feel
  
  let newRotation = originalBounds.value.height + (deltaX * rotationSpeed) // height field stores initial rotation
  
  // Normalize rotation to 0-360 range
  newRotation = ((newRotation % 360) + 360) % 360
  
  // Snap to 15-degree increments if shift is held
  if (event.shiftKey) {
    newRotation = Math.round(newRotation / 15) * 15
  }
  

  localRotation.value = newRotation
}

function handleRotationEnd() {

  
  if (!isRotating.value) return
  

  
  isRotating.value = false
  rotationStarted.value = false
  document.removeEventListener('mousemove', handleRotationMove)
  document.removeEventListener('mouseup', handleRotationEnd)
  
  // Only emit if rotation actually changed significantly
  const rotationChange = Math.abs(localRotation.value - (props.image.rotation || 0))
  if (rotationChange > 1) { // At least 1 degree change
    // Emit the final rotation
    const updatedImage: MoodboardImage = {
      ...props.image,
      rotation: localRotation.value
    }
    

    emit('update', updatedImage)
  } else {

  }
}

function handleDelete() {
  emit('delete', props.image.id)
}

function handleImageLoad(event: Event) {
  const img = event.target as HTMLImageElement
  
  // If canvas dimensions are small (like 200x200 thumbnails) but actual image is larger, 
  // auto-resize to a reasonable size based on the actual image
  if (props.image.canvas_width <= 250 || props.image.canvas_height <= 250) {
    const aspectRatio = img.naturalWidth / img.naturalHeight
    const idealWidth = Math.min(400, Math.max(300, img.naturalWidth * 0.6))
    const idealHeight = idealWidth / aspectRatio
    
    const updatedImage: MoodboardImage = {
      ...props.image,
      canvas_width: idealWidth,
      canvas_height: idealHeight
    }
    
    emit('update', updatedImage)
  }
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', handleDragEnd)
  document.removeEventListener('mousemove', handleResizeMove)
  document.removeEventListener('mouseup', handleResizeEnd)
  document.removeEventListener('mousemove', handleRotationMove)
  document.removeEventListener('mouseup', handleRotationEnd)
})
</script>

<style scoped>
.canvas-image-element {
  position: absolute;
  cursor: move;
  border: 2px solid transparent;
  transition: border-color 0.2s ease;
  user-select: none;
  will-change: transform, left, top, width, height;
}

.canvas-image-element:hover {
  border-color: #3b82f6;
}

.canvas-image-element.selected {
  border-color: #3b82f6;
}

.canvas-image-element.dragging {
  cursor: grabbing !important;
  z-index: 9999 !important;
  border-color: #10b981 !important;
}

.canvas-image-element.resizing {
  border-color: #f59e0b !important;
}

.canvas-image-element.rotating {
  border-color: #8b5cf6 !important;
  cursor: grab;
}

.element-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
  user-select: none;
  pointer-events: none;
  will-change: transform;
}

.selection-handles {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  pointer-events: none;
}

.handle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #3b82f6;
  border: 1px solid white;
  border-radius: 2px;
  pointer-events: all;
}

.handle-nw { top: 0; left: 0; cursor: nw-resize; }
.handle-ne { top: 0; right: 0; cursor: ne-resize; }
.handle-sw { bottom: 0; left: 0; cursor: sw-resize; }
.handle-se { bottom: 0; right: 0; cursor: se-resize; }
.handle-n { top: 0; left: 50%; transform: translateX(-50%); cursor: n-resize; }
.handle-s { bottom: 0; left: 50%; transform: translateX(-50%); cursor: s-resize; }
.handle-w { top: 50%; left: 0; transform: translateY(-50%); cursor: w-resize; }
.handle-e { top: 50%; right: 0; transform: translateY(-50%); cursor: e-resize; }

.delete-button {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 20px;
  height: 20px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rotation-handle {
  position: absolute;
  top: -25px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 20px;
  background: #8b5cf6;
  color: white;
  border-radius: 50%;
  cursor: grab;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: all;
  transition: background-color 0.2s ease;
}

.rotation-handle:hover {
  background: #7c3aed;
  cursor: grabbing;
}
</style>
