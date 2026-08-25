<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { DiffEntry, DiffSection, ProjectDiff } from '~/composables/useProjectDiff'

const props = defineProps<{
  open: boolean
  fileName: string
  diff: ProjectDiff | null
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'apply', ticks: Set<string>): void
  (e: 'cancel'): void
}>()

const META_KEY = 'project:meta'
const key = (collection: string, id: string) => `${collection}:${id}`

// Ticked change ids (collection:id, plus project:meta). Reactive via reassignment.
const ticks = ref<Set<string>>(new Set())
const expanded = ref<Set<string>>(new Set())
const collapsedSections = reactive<Record<string, boolean>>({})
const metaCollapsed = ref(true)

const changeable = (e: DiffEntry) => e.status !== 'unchanged'

function resetTicks() {
  const t = new Set<string>()
  if (props.diff) {
    for (const s of props.diff.sections)
      for (const e of s.entries) if (changeable(e)) t.add(key(s.key, e.id))
    if (props.diff.metadata.status !== 'unchanged') t.add(META_KEY)
  }
  ticks.value = t
}

watch(
  () => props.diff,
  () => resetTicks(),
  { immediate: true },
)

function setTick(k: string, on: boolean) {
  const t = new Set(ticks.value)
  if (on) t.add(k)
  else t.delete(k)
  ticks.value = t
}

// Section tri-state over its changeable children.
function sectionState(s: DiffSection): 'all' | 'none' | 'some' {
  const kids = s.entries.filter(changeable)
  if (!kids.length) return 'none'
  const on = kids.filter((e) => ticks.value.has(key(s.key, e.id))).length
  if (on === 0) return 'none'
  if (on === kids.length) return 'all'
  return 'some'
}

function toggleSection(s: DiffSection, on: boolean) {
  const t = new Set(ticks.value)
  for (const e of s.entries)
    if (changeable(e)) {
      if (on) t.add(key(s.key, e.id))
      else t.delete(key(s.key, e.id))
    }
  ticks.value = t
}

function setAll(on: boolean) {
  if (!props.diff) return
  const t = new Set<string>()
  if (on) {
    for (const s of props.diff.sections)
      for (const e of s.entries) if (changeable(e)) t.add(key(s.key, e.id))
    if (props.diff.metadata.status !== 'unchanged') t.add(META_KEY)
  }
  ticks.value = t
}

function toggleExpand(k: string) {
  const e = new Set(expanded.value)
  if (e.has(k)) e.delete(k)
  else e.add(k)
  expanded.value = e
}

const hasChanges = computed(() => {
  const c = props.diff?.counts
  return !!c && (c.new || c.modified || c.deleted)
})

function fmt(v: unknown): string {
  if (v === null || v === undefined || v === '') return '∅'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

const badge: Record<string, { text: string; class: string }> = {
  new: { text: 'NEW', class: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' },
  modified: {
    text: 'MOD',
    class: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  },
  deleted: { text: 'DEL', class: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300' },
  unchanged: {
    text: '=',
    class: 'bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500',
  },
}

function onApply() {
  emit('apply', ticks.value)
}
function onCancel() {
  emit('cancel')
  emit('update:open', false)
}
</script>

<template>
  <UModal
    :open="open"
    :title="`Import — ${fileName}`"
    :ui="{ content: 'max-w-3xl' }"
    @update:open="emit('update:open', $event)"
  >
    <template #content>
      <div v-if="diff" class="flex flex-col max-h-[80vh]">
        <!-- Header -->
        <div class="px-5 pt-4 pb-3 border-b border-gray-200 dark:border-gray-800">
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-file-braces-corner" class="size-4 text-gray-400" />
            <h2 class="font-semibold text-gray-900 dark:text-white truncate">{{ fileName }}</h2>
          </div>

          <button
            class="mt-2 flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            @click="metaCollapsed = !metaCollapsed"
          >
            <UIcon :name="metaCollapsed ? 'i-lucide-chevron-right' : 'i-lucide-chevron-down'" class="size-3" />
            Project &amp; Metadata
          </button>
          <div v-if="!metaCollapsed" class="mt-2 pl-4 text-xs space-y-1">
            <div class="text-gray-600 dark:text-gray-300">
              <span class="font-medium">{{ diff.metadata.name }}</span>
            </div>
            <label
              v-if="diff.metadata.status !== 'unchanged'"
              class="flex items-center gap-2 cursor-pointer"
            >
              <input
                type="checkbox"
                class="accent-primary-500"
                :checked="ticks.has(META_KEY)"
                @change="setTick(META_KEY, ($event.target as HTMLInputElement).checked)"
              />
              <span class="text-amber-600 dark:text-amber-400">Update project metadata</span>
            </label>
            <span v-else class="text-gray-400">Metadata unchanged</span>
            <ul v-if="diff.metadata.changes.length" class="pl-5 text-gray-500 space-y-0.5">
              <li v-for="c in diff.metadata.changes" :key="c.field">
                {{ c.field }}: <span class="text-red-500">{{ fmt(c.old) }}</span> →
                <span class="text-green-600 dark:text-green-400">{{ fmt(c.new) }}</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto px-2 py-2">
          <div v-for="s in diff.sections" :key="s.key" class="mb-1">
            <div
              class="flex items-center gap-2 px-3 py-1.5 rounded hover:bg-gray-50 dark:hover:bg-gray-800/50"
            >
              <input
                type="checkbox"
                class="accent-primary-500"
                :disabled="s.changeCount === 0"
                :checked="sectionState(s) === 'all'"
                :indeterminate.prop="sectionState(s) === 'some'"
                @change="toggleSection(s, ($event.target as HTMLInputElement).checked)"
              />
              <button
                class="flex items-center gap-1 flex-1 text-left text-sm font-medium text-gray-800 dark:text-gray-100"
                @click="collapsedSections[s.key] = !collapsedSections[s.key]"
              >
                <UIcon
                  :name="collapsedSections[s.key] ? 'i-lucide-chevron-right' : 'i-lucide-chevron-down'"
                  class="size-3.5 text-gray-400"
                />
                {{ s.label }}
                <span class="text-xs font-normal text-gray-400">
                  ({{ s.changeCount ? `${s.changeCount} change${s.changeCount > 1 ? 's' : ''}` : 'no changes' }})
                </span>
              </button>
            </div>

            <div v-if="!collapsedSections[s.key]" class="pl-6">
              <div v-for="e in s.entries" :key="e.id">
                <div
                  class="flex items-center gap-2 px-3 py-1 rounded text-sm hover:bg-gray-50 dark:hover:bg-gray-800/40"
                >
                  <input
                    type="checkbox"
                    class="accent-primary-500"
                    :disabled="!changeable(e)"
                    :checked="ticks.has(key(s.key, e.id))"
                    @change="setTick(key(s.key, e.id), ($event.target as HTMLInputElement).checked)"
                  />
                  <span
                    class="inline-block min-w-[2.4rem] text-center px-1 py-0.5 rounded text-[10px] font-bold"
                    :class="badge[e.status].class"
                  >
                    {{ badge[e.status].text }}
                  </span>
                  <span class="flex-1 truncate text-gray-700 dark:text-gray-200">{{ e.name }}</span>
                  <button
                    v-if="e.status === 'modified' && e.changes.length"
                    class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    @click="toggleExpand(key(s.key, e.id))"
                  >
                    <UIcon
                      :name="expanded.has(key(s.key, e.id)) ? 'i-lucide-chevron-up' : 'i-lucide-list'"
                      class="size-3.5"
                    />
                  </button>
                </div>
                <ul
                  v-if="e.status === 'modified' && expanded.has(key(s.key, e.id))"
                  class="pl-14 pb-1 text-xs text-gray-500 space-y-0.5"
                >
                  <li v-for="c in e.changes" :key="c.field">
                    {{ c.field }}: <span class="text-red-500">{{ fmt(c.old) }}</span> →
                    <span class="text-green-600 dark:text-green-400">{{ fmt(c.new) }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Toolbar -->
        <div
          class="flex items-center gap-3 px-5 py-2 border-t border-gray-200 dark:border-gray-800 text-xs"
        >
          <UButton size="xs" color="neutral" variant="ghost" @click="setAll(true)">All</UButton>
          <UButton size="xs" color="neutral" variant="ghost" @click="setAll(false)">None</UButton>
          <div class="flex-1" />
          <template v-if="hasChanges">
            <span v-if="diff.counts.new" class="font-bold text-green-600 dark:text-green-400"
              >{{ diff.counts.new }} new</span
            >
            <span v-if="diff.counts.modified" class="font-bold text-amber-600 dark:text-amber-400"
              >{{ diff.counts.modified }} modified</span
            >
            <span v-if="diff.counts.deleted" class="font-bold text-red-600 dark:text-red-400"
              >{{ diff.counts.deleted }} removed</span
            >
          </template>
          <span v-else class="text-gray-400">No changes</span>
        </div>

        <!-- Footer -->
        <div
          class="flex justify-end gap-2 px-5 py-3 border-t border-gray-200 dark:border-gray-800"
        >
          <UButton color="neutral" variant="soft" @click="onCancel">Cancel</UButton>
          <UButton color="success" @click="onApply">Apply</UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
