<script setup lang="ts">
import type { MovieScript } from '~/utils/movie-script-evaluator'

const props = defineProps<{
  files: MovieScript[]
}>()

const emit = defineEmits<{
  (e: 'delete' | 'select', fileId: number): void
}>()

function handleCheckboxChange(file: MovieScript) {
  // Handle checkbox change logic here
  if (file.id) {
    emit('select', file.id)
  }
}
</script>

<template>
  <div class="w-full">
    <ul v-if="props.files.length > 0" class="list-none p-0 m-0">
      <li v-for="file in props.files" :key="file.id" class="flex items-center gap-2 py-1.5">
        <svg xmlns="http://www.w3.org/2000/svg" width="0.75em" height="1em" viewBox="0 0 384 512">
          <!-- Icon from File Icons by John Gardner - https://github.com/file-icons/icons/blob/master/LICENSE.md -->
          <path fill="currentColor" d="M288 32H0v448h384V128zm64 416H32V64h224l96 96z" />
        </svg>
        <span> {{ file.title }} </span>
        <span v-if="file.created_at" class="ml-auto text-sm text-gray-500">
          uploaded on: {{ new Date(file.created_at).toLocaleDateString() }}
        </span>
        <input
          type="radio"
          :name="'movie-script'"
          :value="file.id"
          class="ml-2"
          @change="handleCheckboxChange(file)"
        />
        <button
          v-if="file.id"
          class="ml-2 text-red-500 hover:text-red-700"
          :title="'Are you sure to delete the file?'"
          @click="emit('delete', file.id)"
        >
          ×
        </button>
      </li>
    </ul>
  </div>
</template>
