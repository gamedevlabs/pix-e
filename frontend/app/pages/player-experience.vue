<script setup lang="ts">
// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
// ============================================================================

import * as z from 'zod'
// import type { FormSubmitEvent } from '@nuxt/ui'
import { usePxExport } from '~/composables/usePxExport'
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Player Experience',
    icon: 'i-lucide-chart-no-axes-gantt',
    navGroup: 'main',
    navOrder: 3,
    showInNav: true,
  },
})

const { exportPxData, importPxData } = usePxExport()
const { downloadJson } = useDownloadJson()

const MAX_FILE_SIZE = 8 * 1024 * 1024
const ACCEPTED_FILE_FORMATS = ['application/json']

const formatBytes = (bytes: number, decimals = 2) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

const schema = z.object({
  file: z
    .instanceof(File, {
      message: 'Please provide a JSON file.',
    })
    .refine((file) => file.size <= MAX_FILE_SIZE, {
      message: `The file size is too large. Please choose a file smaller than ${formatBytes(MAX_FILE_SIZE)}.`,
    })
    .refine((file) => ACCEPTED_FILE_FORMATS.includes(file.type), {
      message: 'Please upload a valid file (JSON).',
    }),
})

type schema = z.output<typeof schema>

const state = reactive<Partial<schema>>({
  file: undefined,
})

// event: FormSubmitEvent<schema>
async function onSubmit() {
  if (!state.file) return

  const file = state.file
  const text = await file.text()
  const json = JSON.parse(text)

  console.log(json)

  await importPxData(json)
}

async function onClickExportCurrentData() {
  const pxdata = await exportPxData()

  if (!pxdata) return

  downloadJson(pxdata)
}
</script>

<template>
  <UContainer class="py-10 space-y-10">
    <!-- Hero Section -->
    <section class="text-center">
      <h1 class="text-4xl font-bold mb-4">Welcome to the player experience section of pix:e 🎉</h1>
      <p class="text-gray-500 dark:text-gray-400 mb-6">Plan experiences for your players.</p>
    </section>

    <!-- Cards Section -->
    <section class="grid grid-cols-1 sm:grid-cols-2 gap-6">
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/pxcharts"> Charts </NuxtLink>
          </h2>
        </template>
        <p>Charts contain multiple nodes and model nodes in a graph structure.</p>
      </UCard>
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/pxnodes"> Nodes </NuxtLink>
          </h2>
        </template>
        <p>
          A Px Node provides formal information about what the player should experience during that
          part of gameplay.
        </p>
      </UCard>
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/pxcomponents"> Components </NuxtLink>
          </h2>
        </template>
        <p>
          You can attach components to nodes based on component definitions and assign values to
          them.
        </p>
      </UCard>
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/pxcomponentdefinitions"> Component Definitions </NuxtLink>
          </h2>
        </template>
        <p>
          Component definitions allow you to create definitions. Based on these definitions, you can
          add components to nodes and specify values.
        </p>
      </UCard>
    </section>

    <section class="center">
      <UForm :schema="schema" :state="state" @submit="onSubmit">
        <UFormField name="file">
          <UFileUpload
            v-model="state.file"
            accept="application/json"
            label="Import PX data here"
            :dropzone="true"
            description="JSON File (Max. 8MB)"
            class="w-96 min-h-48"
          />
        </UFormField>

        <UButton type="submit" color="primary" label="Submit" />
      </UForm>
    </section>
    <UButton @click="onClickExportCurrentData"> Export your current data as a JSON. </UButton>
  </UContainer>
</template>

<style scoped></style>
