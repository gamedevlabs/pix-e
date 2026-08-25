<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import LandingStandaloneModuleCard from '~/components/landing/LandingStandaloneModuleCard.vue'
import ProjectImporter from '~/components/ProjectImporter.vue'
import ProjectDiffModal from '~/components/ProjectDiffModal.vue'
import { exportFileName, useDataTransfer } from '~/composables/useDataTransfer'
import { useProjectDiff, type ProjectDiff } from '~/composables/useProjectDiff'

interface ProjectCard {
  id: number
  label: string
  description?: string
  icon?: string
  initials?: string
  updatedAt?: string
}

interface StandaloneModule {
  id: string
  label: string
  description: string
  icon: string
  to: string
}

defineProps<{
  username: string
}>()

const router = useRouter()
const { projects, switchProject, deleteProject, fetchProjects } = useProjectHandler()
const { exportProject, importProject, overwriteProject } = useDataTransfer()
const { downloadJson } = useDownloadJson()
const { computeDiff, buildMergedPayload } = useProjectDiff()
const { error: errorToast } = usePixeToast()

const open = ref(false)

type Payload = Record<string, unknown> & { project?: { id?: number; name?: string } }

// Diff-viewer state (shared by both import entry points).
const diffOpen = ref(false)
const diffFileName = ref('')
const diff = ref<ProjectDiff | null>(null)
let flowFileData: Payload | null = null
let flowDbData: Payload | null = null
let flowTargetId: number | null = null

// Hidden picker used by the card-menu "Import".
const cardFileInput = ref<HTMLInputElement | null>(null)
let cardRequireId: number | null = null

function findMatchingProject(fileData: Payload) {
  const list = projects?.value ?? []
  const fid = fileData.project?.id
  if (fid != null) {
    const byId = list.find((p) => p.id === fid)
    if (byId) return byId
  }
  // Old files without an id fall back to matching by name.
  if (fid == null) {
    const byName = list.find((p) => p.name === fileData.project?.name)
    if (byName) return byName
  }
  return undefined
}

async function startImportFlow(file: File, requireProjectId?: number) {
  let fileData: Payload
  try {
    fileData = JSON.parse(await file.text())
  } catch {
    errorToast('Could not read the file. Please choose a valid project JSON export.')
    return
  }
  if (!fileData || fileData.version !== 1 || !fileData.project) {
    errorToast('This file is not a valid pix:e project export.')
    return
  }

  // Card-menu pre-check: the file must belong to the clicked card's project.
  if (requireProjectId != null && fileData.project.id !== requireProjectId) {
    errorToast(
      "This file belongs to a different project and can't be imported here. " +
        'Use this card’s own export, or the Import button on the project overview.',
    )
    return
  }

  const match = findMatchingProject(fileData)
  if (!match) {
    // No match → keep the existing behavior: import as a brand-new project.
    await importProject(fileData)
    await fetchProjects()
    return
  }

  const dbData = (await exportProject(String(match.id))) as Payload | undefined
  if (!dbData) return

  flowFileData = fileData
  flowDbData = dbData
  flowTargetId = match.id
  diff.value = computeDiff(fileData, dbData)
  diffFileName.value = file.name
  diffOpen.value = true
}

async function onDiffApply(ticks: Set<string>) {
  if (!flowFileData || !flowDbData || flowTargetId == null) return
  const merged = buildMergedPayload(flowFileData, flowDbData, ticks)
  try {
    await overwriteProject(String(flowTargetId), merged)
    diffOpen.value = false
    await fetchProjects()
  } catch {
    // Toast already shown; keep the modal open so the user can retry/cancel.
  }
}

async function onOverviewFilePicked(file: File) {
  open.value = false
  await startImportFlow(file)
}

async function exportProjectToFile(projectId: number) {
  const data = (await exportProject(String(projectId))) as Payload | undefined
  if (!data) return
  downloadJson(data, exportFileName(data.project?.name ?? 'project'))
}

function triggerCardImport(projectId: number) {
  cardRequireId = projectId
  cardFileInput.value?.click()
}

async function onCardFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = '' // allow re-picking the same file
  if (!file || cardRequireId == null) return
  await startImportFlow(file, cardRequireId)
  cardRequireId = null
}

const getInitials = (name: string): string =>
  name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

// Project cards sorted by most recently edited.
const projectCards = computed<ProjectCard[]>(() => {
  const list = (projects?.value ?? []).slice().sort((a, b) => {
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  })

  return list.map((p) => ({
    id: p.id,
    label: p.name,
    description: p.description || undefined,
    icon: p.icon || undefined,
    initials: getInitials(p.name),
    updatedAt: p.updated_at,
  }))
})

const standaloneModules: StandaloneModule[] = [
  {
    id: 'movie-script',
    label: 'Movie Script Evaluator',
    description:
      'Evaluate movie scripts through LLMs based on available assets for virtual production.',
    icon: 'i-lucide-film',
    to: '/movie-script-evaluator',
  },
]

const getProjectMenuItems = (projectId: number): DropdownMenuItem[][] => [
  [
    {
      label: 'Edit',
      icon: 'i-lucide-pencil',
      onSelect: () => router.push(`/settings?id=${projectId}`),
    },
    {
      label: 'Duplicate',
      icon: 'i-lucide-copy',
      onSelect: () => router.push(`/create?duplicate=${projectId}`),
      disabled: true,
    },
  ],
  [
    {
      label: 'Export',
      icon: 'i-lucide-download',
      onSelect: () => exportProjectToFile(projectId),
    },
    {
      label: 'Import',
      icon: 'i-lucide-upload',
      onSelect: () => triggerCardImport(projectId),
    },
  ],
  [
    {
      label: 'Delete',
      icon: 'i-lucide-trash',
      color: 'error' as const,
      onSelect: async () => {
        if (confirm('Are you sure you want to delete this project?')) {
          await deleteProject(projectId)
        }
      },
    },
  ],
]

// Ignore clicks that originated on the project's dropdown menu trigger.
const handleProjectClick = async (projectId: number, event?: MouseEvent) => {
  if (event?.target && (event.target as HTMLElement).closest('.project-menu-button')) return
  await switchProject(projectId)
}

</script>

<template>
  <div class="max-w-7xl mx-auto space-y-12">
    <!-- Header -->
    <div
      class="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-6"
    >
      <div class="space-y-1">
        <h1 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">Projects</h1>
        <p class="text-gray-500 dark:text-gray-400">
          Welcome back, {{ username }}. Select a project to continue.
        </p>
      </div>

      <div class="flex gap-3">
        <UModal
          v-model:open="open"
          title="Import Project"
          description="Drag and drop a json file or search in file browser."
        >
          <UButton label="Import Project" icon="i-lucide-import" color="primary" size="md" />

          <template #body>
            <ProjectImporter @file-picked="onOverviewFilePicked" />
          </template>
        </UModal>

        <UButton
          label="New Project"
          icon="i-lucide-plus"
          color="primary"
          size="md"
          @click="router.push('/create')"
        />
      </div>
    </div>

    <!-- Projects -->
    <div class="space-y-6">
      <div
        v-if="projectCards.length === 0"
        class="flex flex-col items-center justify-center gap-4 py-20 text-center border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-xl"
      >
        <div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-full">
          <UIcon name="i-lucide-folder-open" class="size-8 text-gray-400" />
        </div>
        <div class="max-w-md space-y-1">
          <h3 class="font-semibold text-gray-900 dark:text-white">No projects yet</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Create your first project to get started with pix:e's player experience tools.
          </p>
        </div>

        <UButton
          label="Create Project"
          icon="i-lucide-plus"
          color="primary"
          variant="solid"
          @click="router.push('/create')"
        />
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <LandingProjectCard
          v-for="project in projectCards"
          :id="project.id"
          :key="project.id"
          :label="project.label"
          :description="project.description"
          :icon="project.icon"
          :initials="project.initials"
          :updated-at="project.updatedAt"
          :menu-items="getProjectMenuItems(project.id)"
          @click="handleProjectClick(project.id, $event)"
        />
      </div>
    </div>

    <!-- Standalone modules -->
    <div class="space-y-6 pt-2">
      <div class="flex items-center gap-3">
        <div class="h-6 w-1 rounded-full bg-secondary-500" />
        <div>
          <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">Additional Modules</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Standalone tools that work independently from your projects
          </p>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <LandingStandaloneModuleCard
          v-for="module in standaloneModules"
          :key="module.id"
          :icon="module.icon"
          :label="module.label"
          :description="module.description"
          :to="module.to"
        />
      </div>
    </div>

    <!-- Hidden picker for the card-menu "Import" (with per-card pre-check) -->
    <input
      ref="cardFileInput"
      type="file"
      accept="application/json"
      class="hidden"
      @change="onCardFileChange"
    />

    <!-- Shared diff viewer for imports that match an existing project -->
    <ProjectDiffModal
      v-model:open="diffOpen"
      :file-name="diffFileName"
      :diff="diff"
      @apply="onDiffApply"
    />
  </div>
</template>
