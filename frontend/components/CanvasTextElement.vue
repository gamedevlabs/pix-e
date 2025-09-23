<template>
  <div
    class="canvas-text-element"
    :class="{ selected }"
    :data-text-id="textElement.id"
    :style="{
      left: `${textElement.x_position}px`,
      top: `${textElement.y_position}px`,
      width: `${textElement.width}px`,
      height: `${textElement.height}px`,
      transform: `rotate(${textElement.rotation}deg)`,
      zIndex: textElement.z_index,
      opacity: textElement.opacity,
      fontFamily: textElement.font_family,
      fontSize: `${textElement.font_size}px`,
      fontWeight: textElement.font_weight,
      textAlign: textElement.text_align,
      lineHeight: textElement.line_height,
      letterSpacing: `${textElement.letter_spacing}px`,
      color: textElement.text_color,
      backgroundColor: textElement.background_color || 'transparent',
      borderColor: textElement.border_color || 'transparent',
      borderWidth: `${textElement.border_width}px`,
      borderStyle: textElement.border_width > 0 ? 'solid' : 'none'
    }"
    @mousedown="handleMouseDown"
    @click="handleClick"
  >
    <div
      v-if="!isEditing"
      class="text-content"
      @dblclick="startEditing"
    >
      {{ textElement.content }}
    </div>
    
    <!-- Simple text editing -->
    <div v-else class="text-editing-container">
      <div class="text-editing-toolbar">
        <span class="editing-hint">Double-click to edit • Enter to save • Esc to cancel</span>
        <button title="Save" class="save-button" @click="finishEditing">
          ✓
        </button>
        <button title="Cancel" class="cancel-button" @click="cancelEditing">
          ✕
        </button>
      </div>
      <textarea
        ref="textInput"
        v-model="editingContent"
        class="text-editor"
        placeholder="Enter your text..."
        @blur="finishEditing"
        @keydown.enter.exact="finishEditing"
        @keydown.escape="cancelEditing"
      />
    </div>
    
    <!-- Selection handles -->
    <div v-if="selected && !isEditing" class="selection-handles">
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
      v-if="selected && !isEditing"
      class="delete-button"
      title="Delete"
      @click.stop="handleDelete"
    >
      ×
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onUnmounted } from 'vue'
import type { MoodboardTextElement } from '~/composables/useMoodboards'

interface Props {
  textElement: MoodboardTextElement
  selected: boolean
  zoomLevel: number
  snapToGrid: boolean
  gridSize: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  select: [textId: string, multiSelect?: boolean]
  update: [textElement: MoodboardTextElement]
  delete: [textId: string]
}>()

const textInput = ref<HTMLTextAreaElement>()
const isEditing = ref(false)
const editingContent = ref('')
const isDragging = ref(false)
const isResizing = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const resizeHandle = ref<string>('')
const originalBounds = ref({ x: 0, y: 0, width: 0, height: 0 })

function handleClick(event: MouseEvent) {
  event.stopPropagation()
  emit('select', props.textElement.id, event.ctrlKey || event.metaKey)
}

function handleMouseDown(event: MouseEvent) {
  if (isEditing.value) return
  
  if (event.target === event.currentTarget || (event.target as Element).classList.contains('text-content')) {
    isDragging.value = true
    dragStart.value = { x: event.clientX, y: event.clientY }
    originalBounds.value = {
      x: props.textElement.x_position,
      y: props.textElement.y_position,
      width: props.textElement.width,
      height: props.textElement.height
    }
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

  const updatedText: MoodboardTextElement = {
    ...props.textElement,
    x_position: Math.max(0, newX),
    y_position: Math.max(0, newY)
  }

  emit('update', updatedText)
}

function handleDragEnd() {
  isDragging.value = false
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', handleDragEnd)
}

function handleResize(event: MouseEvent, handle: string) {
  event.stopPropagation()
  isResizing.value = true
  resizeHandle.value = handle
  dragStart.value = { x: event.clientX, y: event.clientY }
  originalBounds.value = {
    x: props.textElement.x_position,
    y: props.textElement.y_position,
    width: props.textElement.width,
    height: props.textElement.height
  }
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
      newBounds.width = Math.max(50, originalBounds.value.width - deltaX)
      newBounds.height = Math.max(20, originalBounds.value.height - deltaY)
      newBounds.x = originalBounds.value.x + (originalBounds.value.width - newBounds.width)
      newBounds.y = originalBounds.value.y + (originalBounds.value.height - newBounds.height)
      break
    case 'ne':
      newBounds.width = Math.max(50, originalBounds.value.width + deltaX)
      newBounds.height = Math.max(20, originalBounds.value.height - deltaY)
      newBounds.y = originalBounds.value.y + (originalBounds.value.height - newBounds.height)
      break
    case 'sw':
      newBounds.width = Math.max(50, originalBounds.value.width - deltaX)
      newBounds.height = Math.max(20, originalBounds.value.height + deltaY)
      newBounds.x = originalBounds.value.x + (originalBounds.value.width - newBounds.width)
      break
    case 'se':
      newBounds.width = Math.max(50, originalBounds.value.width + deltaX)
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
      newBounds.width = Math.max(50, originalBounds.value.width - deltaX)
      newBounds.x = originalBounds.value.x + (originalBounds.value.width - newBounds.width)
      break
    case 'e':
      newBounds.width = Math.max(50, originalBounds.value.width + deltaX)
      break
  }

  const updatedText: MoodboardTextElement = {
    ...props.textElement,
    x_position: newBounds.x,
    y_position: newBounds.y,
    width: newBounds.width,
    height: newBounds.height
  }

  emit('update', updatedText)
}

function handleResizeEnd() {
  isResizing.value = false
  resizeHandle.value = ''
  document.removeEventListener('mousemove', handleResizeMove)
  document.removeEventListener('mouseup', handleResizeEnd)
}

function startEditing() {
  if (!props.selected) return
  
  isEditing.value = true
  editingContent.value = props.textElement.content
  
  nextTick(() => {
    if (textInput.value) {
      textInput.value.focus()
      textInput.value.select()
    }
  })
}

function finishEditing() {
  if (!isEditing.value) return
  
  const updatedText: MoodboardTextElement = {
    ...props.textElement,
    content: editingContent.value.trim() || 'New Text'
  }
  
  emit('update', updatedText)
  isEditing.value = false
}

function cancelEditing() {
  isEditing.value = false
  editingContent.value = ''
}

function handleDelete() {
  emit('delete', props.textElement.id)
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', handleDragEnd)
  document.removeEventListener('mousemove', handleResizeMove)
  document.removeEventListener('mouseup', handleResizeEnd)
})
</script>

<style scoped>
.canvas-text-element {
  position: absolute;
  cursor: move;
  border: 2px solid transparent;
  transition: border-color 0.2s ease;
  padding: 4px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  word-wrap: break-word;
  overflow: hidden;
}

.canvas-text-element:hover {
  border-color: #3b82f6;
}

.canvas-text-element.selected {
  border-color: #3b82f6;
}

.text-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  user-select: none;
  word-break: break-word;
  white-space: pre-wrap;
}

.text-editor {
  width: 100%;
  height: 100%;
  border: none;
  outline: none;
  background: transparent;
  font: inherit;
  color: inherit;
  text-align: inherit;
  line-height: inherit;
  letter-spacing: inherit;
  resize: none;
  padding: 0;
  margin: 0;
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

.delete-button:hover {
  background: #dc2626;
}

/* Text editing styles */
.text-editing-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.text-editing-toolbar {
  position: absolute;
  top: -40px;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 4px 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  font-size: 12px;
  min-width: 300px;
}

.editing-hint {
  color: #6b7280;
  font-size: 11px;
  flex: 1;
}

.save-button, .cancel-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  margin-left: 4px;
  font-size: 12px;
  font-weight: bold;
}

.save-button {
  color: #059669;
}

.save-button:hover {
  background: #d1fae5;
}

.cancel-button {
  color: #dc2626;
}

.cancel-button:hover {
  background: #fee2e2;
}
</style>
