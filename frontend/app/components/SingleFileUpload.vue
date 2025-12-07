<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'

const props = defineProps<{
  maxFileSize: number
  acceptedFileTypes: string[]
  onSubmit: (event: FormSubmitEvent<any>) => void

  // for image files
  minDimensions?: { width: number; height: number }
  maxDimensions?: { width: number; height: number }
}>()

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
      message: 'Please select a file.'
    })
    .refine((file) => file.size <= props.maxFileSize, {
      message: `The file is too large. Please choose a file smaller than ${formatBytes(props.maxFileSize)}.`
    })
    .refine((file) => props.acceptedFileTypes.includes(file.type), {
      message: `Please upload a valid file (${props.acceptedFileTypes.join(', ')}).`
    })
    .refine(
      (file) =>
        new Promise((resolve) => {
          const reader = new FileReader()
          reader.onload = (e) => {

            if (!file.type.startsWith('image/')) {
              // If not an image, skip dimension check
              resolve(true)
              return
            }
            const img = new Image()
            img.onload = () => {
              const meetsDimensions =
                img.width >= (props.minDimensions?.width ?? 0) &&
                img.height >= (props.minDimensions?.height ?? 0) &&
                img.width <= (props.maxDimensions?.width ?? Infinity) &&
                img.height <= (props.maxDimensions?.height ?? Infinity)
              resolve(meetsDimensions)
            }
            img.src = e.target?.result as string
          }
          reader.readAsDataURL(file)
        }),
      {
        message: `The image dimensions are invalid. Please upload an image between ${props.minDimensions?.width ?? 0}x${props.minDimensions?.height ?? 0} and ${props.maxDimensions?.width ?? Infinity}x${props.maxDimensions?.height ?? Infinity} pixels.`
      }
    )
})

type schema = z.output<typeof schema>

const state = reactive<Partial<schema>>({
  file: undefined
})

async function onSubmit(event: FormSubmitEvent<schema>) {
  console.log(event.data)
}
</script>

<template>
  <UForm :schema="schema" :state="state" class="space-y-4 w-96" @submit="onSubmit">
    <UFormField name="file" label="File" :description="`Max file size: ${formatBytes(props.maxFileSize)}`">
      <UFileUpload v-model="state.file" :accept="props.acceptedFileTypes.join(',')" class="min-h-48" />
    </UFormField>

    <UButton type="submit" label="Submit" color="neutral" />
  </UForm>
</template>
