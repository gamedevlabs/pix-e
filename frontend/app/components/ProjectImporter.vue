<script setup lang="ts">
import * as z from "zod";

type schema = z.output<typeof schema>

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

  //await importPxData(json)
}
</script>

<template>
  <div>
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
  </div>
</template>

<style scoped>

</style>