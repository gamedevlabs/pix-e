<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
})

const route = useRoute()
const id = route.params.id as string

const { currentProject } = useProjectHandler()

const {
  checking: checkingPropagation,
  report: propagationReport,
  checkPropagation,
  clearReport: dismissPropagation,
} = useChangePropagation()

async function handleDelete() {
  await navigateTo('/pxnodes')
}

async function handleDescriptionChanged(payload: {
  nodeId: string
  oldDescription: string
  newDescription: string
}) {
  if (!currentProject.value?.id) return
  await checkPropagation({
    projectId: currentProject.value.id,
    nodeId: payload.nodeId,
    oldDescription: payload.oldDescription,
    newDescription: payload.newDescription,
  })
}
</script>

<template>
  <div class="p-8">
    <PxNodeCard
      :node-id="id"
      :visualization-style="'detailed'"
      @delete="handleDelete"
      @description-changed="handleDescriptionChanged"
    />

    <!-- Change Propagation loading -->
    <UCard v-if="checkingPropagation" class="mt-6">
      <div class="flex items-center gap-3 text-sm text-neutral-500">
        <UIcon name="i-lucide-loader-circle" class="animate-spin" />
        Checking for affected nodes...
      </div>
    </UCard>

    <!-- Change Propagation results -->
    <UCard v-else-if="propagationReport" class="mt-6">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-git-branch" class="text-primary" />
            <span class="font-semibold">Change Propagation</span>
          </div>
          <UButton variant="ghost" size="xs" icon="i-lucide-x" @click="dismissPropagation">
            Dismiss
          </UButton>
        </div>
      </template>

      <div
        v-if="propagationReport.findings.length === 0"
        class="text-sm text-neutral-500"
      >
        No other nodes are affected by this change.
      </div>

      <div v-else class="space-y-3">
        <p class="text-sm text-neutral-500 mb-3">
          {{ propagationReport.findings.length }}
          {{ propagationReport.findings.length === 1 ? 'node' : 'nodes' }} may need updating:
        </p>
        <div
          v-for="finding in propagationReport.findings"
          :key="finding.affected_node_id"
          class="rounded-lg bg-neutral-50 p-4 dark:bg-neutral-800"
        >
          <div class="mb-2 flex items-center justify-between">
            <span class="font-medium">{{ finding.affected_node_name }}</span>
            <UBadge color="neutral" variant="soft" size="xs">
              {{ Math.round(finding.confidence * 100) }}% confidence
            </UBadge>
          </div>
          <p class="mb-2 text-sm text-neutral-600 dark:text-neutral-400">
            {{ finding.reason }}
          </p>
          <div class="flex items-start gap-2">
            <UIcon name="i-lucide-lightbulb" class="mt-0.5 shrink-0 text-amber-500" size="sm" />
            <p class="text-sm text-amber-700 dark:text-amber-400">
              {{ finding.suggested_action }}
            </p>
          </div>
        </div>
      </div>
    </UCard>

    <UButton to="/pxnodes" class="my-4">← Back to all Nodes</UButton>
  </div>
</template>

<style scoped></style>
