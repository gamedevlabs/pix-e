<script setup lang="ts">
import {useDataTransfer} from "~/composables/useDataTransfer";

const { downloadJson } = useDownloadJson()
const { exportProject } = useDataTransfer()
const { currentProjectId } = useProjectHandler()

async function onClickExportCurrentData() {
  if (!currentProjectId.value) {
    console.error("No project selected")
    return;
  }

  const pxdata = await exportProject(currentProjectId.value.toString())

  if (!pxdata) return

  downloadJson(pxdata)
}
</script>

<template>
  <div>
    <UButton icon="i-lucide-file-braces-corner" @click="onClickExportCurrentData">
      Export project
    </UButton>
  </div>
</template>

<style scoped></style>
