<script setup>
import { ref, computed } from 'vue'

// HelpDesk Form functions:
// default: don't show user request form
const showRequestForm = ref(false)

// form variables
const requestType = ref('')
const formDescription = ref('')
const userContact = ref('')
const requestTitle = ref('')

const requestTypeOptions = [
  { label: 'Bug Report', value: 'Bug Report' },
  { label: 'Help Request', value: 'Help Request' },
  { label: 'Feature Request', value: 'Feature Request' },
]

// showing success/error pop-ups
const toast = useToast()

// session logging
const attachLogs = ref(true)
const { getLogs, addLog } = useSessionLog()

// open / close logic for the form
function openRequestForm() {
  // log form opening
  addLog('info', 'helpdesk_form_opened')
  showRequestForm.value = true
}

function closeRequestForm() {
  showRequestForm.value = false
  resetRequestForm()
}

const isRequestFormOpen = computed({
  get: () => showRequestForm.value,
  set: (isOpen) => {
    showRequestForm.value = isOpen

    if (!isOpen) {
      resetRequestForm()
    }
  },
})

function resetRequestForm() {
  requestType.value = ''
  formDescription.value = ''
  userContact.value = ''
  requestTitle.value = ''
  attachLogs.value = true
}

// check if contact details are needed
const contactDetailsRequired = computed(() => {
  return requestType.value === 'Help Request'
})

const checkRequestForm = computed(() => {
  return (
    requestType.value &&
    formDescription.value.trim().length > 0 &&
    requestTitle.value.trim().length > 0 &&
    (!contactDetailsRequired.value || userContact.value.trim().length > 0)
  )
})

// sending request
async function submitRequestForm() {
  // log form submit
  addLog('info', 'helpdesk_form_submit_clicked', {
    type: requestType.value,
    hasContact: userContact.value.trim().length > 0,
  })

  if (!checkRequestForm.value) {
    toast.add({
      title: 'Submission failed',
      description: 'Please fill out all mandatory fields.',
      color: 'error',
    })
    return
  }

  try {
    await $fetch('/api/helpdesk/tickets/', {
      baseURL: useRuntimeConfig().public.apiBase,
      method: 'POST',
      credentials: 'include',
      body: {
        type: requestType.value,
        title: requestTitle.value,
        description: formDescription.value,
        contact: userContact.value,
        logs: requestType.value === 'Bug Report' && attachLogs.value ? getLogs() : null,
      },
    })

    closeRequestForm()
    toast.add({
      title: 'Success',
      description: 'Submitted your request successfully.',
      color: 'success',
    })
  } catch (error) {
    console.error('Failed to submit helpdesk request', error)

    if (error?.data?.error === 'Helpdesk is not configured') {
      toast.add({
        title: 'Helpdesk Not Configured',
        description: 'The helpdesk GitHub token is missing.',
        color: 'error',
      })
    }
  }
}
</script>

<template>
  <UModal
    v-model:open="isRequestFormOpen"
    :ui="{
      content: 'w-[calc(100vw-2rem)] max-w-3xl max-h-[85dvh]',
      body: 'space-y-4 overflow-y-auto',
      footer: 'justify-end',
    }"
  >
    <UButton
      class="w-fit"
      label="Contact Us"
      icon="i-lucide-message-circle"
      color="neutral"
      variant="soft"
      size="sm"
      block
      @click="openRequestForm"
    />

    <template #title>
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-mail" class="text-primary" />
        <span>Contact Us - Request Form</span>
      </div>
    </template>

    <template #body>
      <UFormField label="Please provide a short request title." required>
        <UInput
          v-model="requestTitle"
          class="w-full"
          maxlength="120"
          placeholder="Enter title..."
        />
      </UFormField>

      <UFormField label="What type of request would you like to send us?" required>
        <USelect
          v-model="requestType"
          class="w-full"
          :items="requestTypeOptions"
          value-key="value"
          label-key="label"
          placeholder="Select request type..."
        />
      </UFormField>

      <UCheckbox
        v-if="requestType === 'Bug Report'"
        v-model="attachLogs"
        label="Attach session logs?"
      />

      <UFormField
        label="Please provide us with as much information as possible about your request."
        required
      >
        <UTextarea
          v-model="formDescription"
          class="w-full"
          maxlength="5000"
          placeholder="Enter your request..."
          :rows="6"
        />
      </UFormField>

      <UFormField
        label="How can we contact you? (e.g., e-mail, discord handle, ...)"
        :required="contactDetailsRequired"
      >
        <UInput
          v-model="userContact"
          class="w-full"
          maxlength="255"
          :placeholder="
            contactDetailsRequired
              ? 'Enter your contact data...'
              : 'Enter your contact data... (optional)'
          "
        />
      </UFormField>

      <p class="text-xs text-error italic">Fields marked with an asterisk (*) are mandatory.</p>
    </template>

    <template #footer>
      <UButton label="Cancel" color="neutral" variant="ghost" @click="closeRequestForm" />

      <UButton
        label="Send"
        color="primary"
        :disabled="!checkRequestForm"
        @click="submitRequestForm"
      />
    </template>
  </UModal>
</template>
