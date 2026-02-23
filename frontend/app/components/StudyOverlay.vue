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
      <!-- Backdrop: stronger blur + darker overlay to clearly separate from app -->
      <div
        class="absolute inset-0 bg-black/60 backdrop-blur-sm"
        @click.self="phase === 'finished' ? (open = false) : null"
      />

      <!-- Centered modal -->
      <div class="absolute inset-0 flex items-center justify-center p-6">
        <div class="w-full max-w-lg">
          <UCard
            class="ring-2 ring-primary-500/60 shadow-2xl"
            :ui="{
              header: 'px-6 py-4 bg-primary-600 dark:bg-primary-700 rounded-t-xl',
              body: 'px-6 py-5',
              footer: 'px-6 py-4 border-t border-default/60',
            }"
          >
            <template #header>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <UIcon name="i-lucide-flask-conical" class="size-5 text-white/90" />
                  <span class="text-lg font-bold text-white tracking-wide">Study Mode</span>
                  <UBadge color="warning" variant="solid" size="sm">MOCK</UBadge>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-white/70 font-mono">{{ statusText }}</span>
                  <UButton
                    v-if="phase === 'finished'"
                    size="xs"
                    variant="ghost"
                    color="neutral"
                    icon="i-lucide-x"
                    class="text-white/80 hover:text-white hover:bg-white/10"
                    @click="open = false"
                  />
                </div>
              </div>
            </template>

            <div class="space-y-5">
              <!-- SETUP PHASE -->
              <div v-if="phase === 'setup'" class="space-y-5">
                <p class="text-sm leading-relaxed text-gray-600 dark:text-gray-300">
                  Configure the study session, then start it. Starting will
                  <span class="font-semibold text-gray-800 dark:text-gray-100"
                    >reset local data</span
                  >, unselect any project, and log out so the participant starts fresh.
                </p>

                <UFormField
                  label="Participant ID"
                  name="participantId"
                  size="lg"
                  hint="Stored locally in your browser"
                  class="w-full"
                >
                  <UInput
                    :model-value="participantId"
                    placeholder="e.g. P01"
                    size="lg"
                    class="w-full font-mono"
                    @update:model-value="onParticipantChange"
                  />
                </UFormField>

                <div class="flex flex-wrap gap-3 pt-1">
                  <UButton
                    size="md"
                    color="warning"
                    variant="soft"
                    icon="i-lucide-rotate-ccw"
                    @click="onResetSession(true)"
                  >
                    Reset session
                  </UButton>
                  <UButton
                    size="md"
                    color="primary"
                    variant="solid"
                    icon="i-lucide-play"
                    @click="onStartStudy"
                  >
                    Start study
                  </UButton>
                </div>

                <!-- Facilitator section -->
                <div class="pt-4 border-t border-default/50 space-y-3">
                  <p
                    class="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500"
                  >
                    Facilitator tools
                  </p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">
                    Import or export session data between participants.
                  </p>
                  <div class="flex flex-wrap gap-2">
                    <UButton
                      size="sm"
                      color="neutral"
                      variant="soft"
                      icon="i-lucide-download"
                      @click="onExport"
                    >
                      Export session
                    </UButton>
                    <UButton
                      size="sm"
                      color="neutral"
                      variant="soft"
                      icon="i-lucide-upload"
                      as="label"
                    >
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

              <!-- FINISHED PHASE -->
              <div v-else-if="phase === 'finished'" class="space-y-5">
                <div
                  class="flex items-start gap-3 p-4 rounded-lg bg-success-50 dark:bg-success-900/20 border border-success-200 dark:border-success-800/50"
                >
                  <UIcon
                    name="i-lucide-check-circle"
                    class="size-5 text-success-500 mt-0.5 shrink-0"
                  />
                  <div>
                    <p class="text-sm font-semibold text-success-700 dark:text-success-400">
                      Study finished
                    </p>
                    <p class="text-sm text-success-600 dark:text-success-500 mt-0.5">
                      Export the captured session data before closing.
                    </p>
                  </div>
                </div>

                <div class="flex flex-wrap gap-3">
                  <UButton
                    size="md"
                    color="neutral"
                    variant="soft"
                    icon="i-lucide-download"
                    @click="onExport"
                  >
                    Export session
                  </UButton>
                  <UButton
                    size="md"
                    color="warning"
                    variant="soft"
                    icon="i-lucide-rotate-ccw"
                    @click="onResetSession(true)"
                  >
                    Reset session
                  </UButton>
                  <UButton
                    size="md"
                    color="primary"
                    variant="solid"
                    icon="i-lucide-x"
                    @click="open = false"
                  >
                    Close
                  </UButton>
                </div>
              </div>
            </div>

            <template #footer>
              <div class="flex items-center justify-between">
                <div class="text-xs text-gray-400 dark:text-gray-500">
                  Storage key:
                  <code class="font-mono bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-xs"
                    >pixe.study.v1</code
                  >
                </div>
                <UButton
                  v-if="phase === 'running'"
                  size="sm"
                  color="neutral"
                  variant="soft"
                  icon="i-lucide-flag"
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
