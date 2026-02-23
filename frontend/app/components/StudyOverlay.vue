<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useProjectDataProvider, useAuthentication } from '~/studyMock'

const provider = useProjectDataProvider()
const authentication = useAuthentication()
const projectHandler = useProjectHandler()

const open = useState<boolean>('studyOverlayOpen', () => false)
const phase = ref<'setup' | 'running' | 'finished'>('setup')

const participantId = ref('')
const lastSavedAt = ref<string | null>(null)

function refreshMeta() {
  if (!import.meta.client) return
  participantId.value = provider.getParticipantId()
  lastSavedAt.value = provider.getLastSavedAt()
}

if (import.meta.client) {
  refreshMeta()
}

watch(open, (v) => {
  if (v) refreshMeta()
})

async function hardRefresh() {
  try {
    await navigateTo(useRoute().fullPath)
  } catch {
    // ignore
  }
}

async function onResetSession(keepParticipantId = true) {
  const pid = participantId.value
  await provider.resetState()
  if (keepParticipantId) provider.setParticipantId(pid)
  refreshMeta()
  await hardRefresh()
}

function download(filename: string, content: string) {
  if (!import.meta.client) return
  const blob = new Blob([content], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

async function onExport() {
  const stateJson = await provider.exportState()
  const exported = {
    schemaVersion: 1,
    participantId: participantId.value,
    timestamp: new Date().toISOString(),
    state: JSON.parse(stateJson),
  }
  download(
    `pixe-study-${participantId.value || 'participant'}-${Date.now()}.json`,
    JSON.stringify(exported, null, 2),
  )
  refreshMeta()
}

async function onImportFile(file?: File | null) {
  if (!file) return
  const txt = await file.text()
  let parsed: unknown
  try {
    parsed = JSON.parse(txt)
  } catch {
    throw new Error('Invalid JSON file')
  }

  if (!parsed || typeof parsed !== 'object') throw new Error('Invalid import format')

  // Narrow to a record so we can safely access fields and validate their types.
  const parsedObj = parsed as Record<string, unknown>

  if (parsedObj.schemaVersion !== 1) throw new Error('Unsupported schemaVersion')
  if (!('state' in parsedObj)) throw new Error('Missing state')

  await provider.importState(JSON.stringify(parsedObj.state))
  if (typeof parsedObj.participantId === 'string') {
    provider.setParticipantId(parsedObj.participantId)
  }
  refreshMeta()
  await hardRefresh()
}

function onParticipantChange(v: string) {
  participantId.value = v
  provider.setParticipantId(v)
  refreshMeta()
}

async function onStartStudy() {
  // Full fresh-start feel: clear local session + clear selected project + log out.
  await onResetSession(true)
  projectHandler.unselectProject()
  await authentication.logout()
  phase.value = 'running'
  open.value = false
  await navigateTo('/')
}

function onFinishStudy() {
  phase.value = 'finished'
  open.value = true
}

const statusText = computed(() => {
  return lastSavedAt.value
    ? `Autosaved ✓ ${new Date(lastSavedAt.value).toLocaleTimeString()}`
    : 'Autosave pending…'
})
</script>

<template>
  <teleport to="body">
    <div v-if="open" class="fixed inset-0 z-100">
      <!-- Backdrop blocks interaction (only dismissable once finished) -->
      <div
        class="absolute inset-0 bg-black/40"
        @click.self="phase === 'finished' ? (open = false) : null"
      />

      <!-- Centered modal -->
      <div class="absolute inset-0 flex items-center justify-center p-4">
        <div class="w-105 max-w-[calc(100vw-2rem)]">
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <div class="font-medium">Study Mode</div>
                <div class="flex items-center gap-2">
                  <UBadge color="success" variant="subtle">MOCK</UBadge>
                  <UButton
                    v-if="phase === 'finished'"
                    size="xs"
                    variant="ghost"
                    color="neutral"
                    icon="i-lucide-x"
                    @click="open = false"
                  />
                </div>
              </div>
              <div class="mt-1 text-xs text-gray-500">{{ statusText }}</div>
            </template>

            <div class="space-y-4">
              <div v-if="phase === 'setup'">
                <div class="text-sm text-gray-600 dark:text-gray-300">
                  Configure the study, then start it. Starting will reset local data, unselect any
                  project, and log out.
                </div>

                <UFormField
                  label="Participant ID"
                  name="participantId"
                  size="lg"
                  hint="Stored locally in your browser"
                >
                  <UInput
                    :model-value="participantId"
                    placeholder="e.g. P01"
                    @update:model-value="onParticipantChange"
                  />
                </UFormField>

                <div class="flex flex-wrap gap-2">
                  <UButton size="xs" color="warning" variant="soft" @click="onResetSession(true)"
                    >Reset session</UButton
                  >
                  <UButton size="xs" color="primary" variant="solid" @click="onStartStudy"
                    >Start study</UButton
                  >
                </div>

                <div class="pt-2 border-t border-default/50">
                  <div class="text-xs text-gray-500 mb-2">
                    Import/export is usually used by the facilitator.
                  </div>
                  <div class="flex flex-wrap gap-2">
                    <UButton size="xs" color="neutral" variant="soft" @click="onExport"
                      >Export session</UButton
                    >
                    <UButton size="xs" color="neutral" variant="soft" as="label">
                      Import session
                      <input
                        type="file"
                        accept="application/json"
                        class="hidden"
                        @change="
                          (e: Event) => onImportFile((e.target as HTMLInputElement)?.files?.[0])
                        "
                      />
                    </UButton>
                  </div>
                </div>
              </div>

              <div v-else-if="phase === 'finished'">
                <div class="text-sm text-gray-600 dark:text-gray-300">
                  Study finished. Export the captured session data.
                </div>

                <div class="flex flex-wrap gap-2">
                  <UButton size="xs" color="neutral" variant="soft" @click="onExport"
                    >Export session</UButton
                  >
                  <UButton size="xs" color="warning" variant="soft" @click="onResetSession(true)"
                    >Reset session</UButton
                  >
                  <UButton size="xs" color="primary" variant="solid" @click="open = false"
                    >Close</UButton
                  >
                </div>
              </div>
            </div>

            <template #footer>
              <div class="flex items-center justify-between">
                <div class="text-xs text-gray-500">Storage key: <code>pixe.study.v1</code></div>
                <!-- Facilitator-only: show Finish button while running -->
                <UButton
                  v-if="phase === 'running'"
                  size="xs"
                  color="neutral"
                  variant="soft"
                  @click="onFinishStudy"
                >
                  Finish study
                </UButton>
              </div>
            </template>
          </UCard>
        </div>
      </div>
    </div>
  </teleport>
</template>
