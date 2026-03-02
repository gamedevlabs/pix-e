<script setup lang="ts">
import { ref, watch } from 'vue'
import { useProjectDataProvider, useAuthentication } from '~/studyMock'

const provider = useProjectDataProvider()
const authentication = useAuthentication()
const projectHandler = useProjectHandler()

// Controlled by the layout (Study button + first-open auto-open)
const open = useState<boolean>('studyOverlayOpen', () => false)
const phase = useState<'setup' | 'running' | 'paused' | 'finished'>('studyPhase', () => 'setup')
const isRunning = useState<boolean>('studyRunning', () => false)

// ─── Session helpers ──────────────────────────────────────────────────────────
const participantId = ref('')

function refreshMeta() {
  if (!import.meta.client) return
  participantId.value = provider.getParticipantId()
}

if (import.meta.client) {
  refreshMeta()
}

watch(phase, () => refreshMeta())

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
}

function onParticipantChange(v: string) {
  participantId.value = v
  provider.setParticipantId(v)
}

async function onStartStudy() {
  await onResetSession(true)
  projectHandler.unselectProject()
  await authentication.logout()
  phase.value = 'running'
  isRunning.value = true
  open.value = false
  await navigateTo('/')
}

function onResumeStudy() {
  phase.value = 'running'
  isRunning.value = true
  open.value = false
}

async function onRestartStudy() {
  await provider.resetState()
  if (import.meta.client) {
    window.location.href = window.location.origin
    location.reload()
  }
}

async function onEndStudy() {
  isRunning.value = false
  await onExport()
  phase.value = 'finished'
  open.value = true
}

function onContinueExploring() {
  // Allow the participant to keep using the app after we've shown the "finished" state.
  // We only expose this action in the finished phase to ensure export happened first.
  open.value = false
}
</script>

<template>
  <ClientOnly>
    <teleport to="body">
      <div v-if="open" class="fixed inset-0 z-100">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" />

        <div class="absolute inset-0 flex items-center justify-center p-6">
          <div class="w-full max-w-sm">
            <div
              class="rounded-xl ring-2 ring-primary-500/60 shadow-2xl overflow-hidden bg-white dark:bg-gray-900"
            >
              <!-- Header -->
              <div class="px-5 py-3 bg-primary-600 dark:bg-primary-700 flex items-center gap-2">
                <UIcon name="i-lucide-flask-conical" class="size-4 text-white/90" />
                <span class="text-base font-bold text-white tracking-wide">Study Mode</span>
              </div>

              <!-- Body -->
              <div class="px-5 py-4 space-y-4">
                <!-- SETUP PHASE -->
                <div v-if="phase === 'setup'" class="space-y-4">
                  <UFormField
                    label="Participant ID"
                    name="participantId"
                    hint="Found on your study sheet"
                    class="w-full"
                  >
                    <UInput
                      :model-value="participantId"
                      placeholder="e.g. P01"
                      class="w-full font-mono"
                      @update:model-value="onParticipantChange"
                    />
                  </UFormField>

                  <UButton
                    size="md"
                    color="primary"
                    variant="solid"
                    icon="i-lucide-play"
                    class="w-full justify-center"
                    @click="onStartStudy"
                  >
                    Start study
                  </UButton>
                </div>

                <!-- PAUSED PHASE -->
                <div v-else-if="phase === 'paused'" class="space-y-3">
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    Study paused — participant
                    <span class="font-mono font-semibold text-gray-700 dark:text-gray-200">{{
                      participantId || '—'
                    }}</span>
                  </p>

                  <div class="flex flex-col gap-2">
                    <UButton
                      size="md"
                      color="primary"
                      variant="solid"
                      icon="i-lucide-play"
                      class="w-full justify-center"
                      @click="onResumeStudy"
                    >
                      Continue
                    </UButton>
                    <UButton
                      size="md"
                      color="neutral"
                      variant="soft"
                      icon="i-lucide-rotate-ccw"
                      class="w-full justify-center"
                      @click="onRestartStudy"
                    >
                      Reset & restart
                    </UButton>
                    <UButton
                      size="sm"
                      color="error"
                      variant="solid"
                      icon="i-lucide-flag"
                      class="w-full justify-center"
                      @click="onEndStudy"
                    >
                      End study & download data
                    </UButton>
                  </div>
                </div>

                <!-- FINISHED PHASE -->
                <div v-else-if="phase === 'finished'" class="space-y-4">
                  <div
                    class="flex items-start gap-3 p-3 rounded-lg bg-success-50 dark:bg-success-900/20 border border-success-200 dark:border-success-800/50"
                  >
                    <UIcon
                      name="i-lucide-check-circle"
                      class="size-5 text-success-500 mt-0.5 shrink-0"
                    />
                    <div>
                      <p class="text-sm font-semibold text-success-700 dark:text-success-400">
                        Study complete!
                      </p>
                      <p class="text-xs text-success-600 dark:text-success-500 mt-0.5">
                        Data downloaded. Please send the file to the facilitator.
                      </p>
                    </div>
                  </div>

                  <div class="flex flex-col gap-2">
                    <UButton
                      size="md"
                      color="primary"
                      variant="soft"
                      icon="i-lucide-download"
                      class="w-full justify-center"
                      @click="onExport"
                    >
                      Download again
                    </UButton>

                    <UButton
                      size="md"
                      color="neutral"
                      variant="soft"
                      icon="i-lucide-rotate-ccw"
                      class="w-full justify-center"
                      @click="onRestartStudy"
                    >
                      Reset & restart
                    </UButton>

                    <UButton
                      size="sm"
                      color="neutral"
                      variant="solid"
                      icon="i-lucide-arrow-right"
                      class="w-full justify-center"
                      @click="onContinueExploring"
                    >
                      Continue Exploring
                    </UButton>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </teleport>
  </ClientOnly>
</template>
