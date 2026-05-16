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

// showing success/error pop ups
const toast = useToast()

// open / close logic for the form
function openRequestForm() {
  showRequestForm.value = true
}

function closeRequestForm() {
  showRequestForm.value = false
  resetRequestForm()
}

function resetRequestForm() {
  requestType.value = ''
  formDescription.value = ''
  userContact.value = ''
  requestTitle.value = ''
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

  <Teleport to="body">
    <!-- User Request Pop Up -->
    <div v-if="showRequestForm" class="modal">
      <div class="modal-content">
        <div class="flex items-center gap-2 mb-3 pb-4 border-b">
          <UIcon name="i-lucide-mail" class="text-primary" />
          <h2 class="text-lg font-semibold">Contact Us - Request Form</h2>
        </div>

        <div class="form-body">
          <!-- Request title -->
          <p class="text-sm mb-1">
            Please provide a short request title.<span class="text-red-500">*</span>
          </p>
          <input
            v-model="requestTitle"
            class="input mb-4"
            maxlength="120"
            placeholder="Enter title..."
          />

          <!-- Request type dropdown -->
          <p class="text-sm mb-1">
            What type of request would you like to send us? <span class="text-red-500">*</span>
          </p>
          <select v-model="requestType" class="input mb-4">
            <option disabled value="">Select request type...</option>
            <option>Bug Report</option>
            <option>Help Request</option>
            <option>Feature Request</option>
          </select>

          <!-- Request description -->
          <p class="text-sm mb-1">
            Please provide us with as much information as possible about your request.<span
              class="text-red-500"
              >*</span
            >
          </p>
          <textarea
            v-model="formDescription"
            maxlength="5000"
            placeholder="Enter your request..."
            class="textarea mb-4"
          />

          <!-- optional email -->
          <p class="text-sm mb-1">
            How can we contact you? (e.g., e-mail, discord handle, ...)
            <span v-if="contactDetailsRequired" class="text-red-500">*</span>
          </p>
          <input
            v-model="userContact"
            maxlength="255"
            :placeholder="
              contactDetailsRequired
                ? 'Enter your contact data...'
                : 'Enter your contact data... (optional)'
            "
            class="input mb-4"
          />

          <!-- info message -->
          <p class="text-xs text-red-500 italic mb-3">
            Fields marked with a red asterisk (*) are mandatory.
          </p>
        </div>

        <!-- Sending / Cancel Buttons -->
        <div class="actions">
          <UButton
            label="Send"
            color="primary"
            :disabled="!checkRequestForm"
            @click="submitRequestForm"
          />

          <UButton label="Cancel" color="neutral" @click="closeRequestForm" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style>
/* screen overlay settings of request form */
.modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);

  display: flex;
  align-items: center;
  justify-content: center;

  z-index: 50;
}

/* main request form */
.modal-content {
  background: var(--ui-color-neutral-50);
  color: var(--ui-color-neutral-900);

  width: 60%;
  max-width: 800px;
  height: 85%;
  max-height: 900px;

  border-radius: 12px;
  padding: 20px;

  display: flex;
  flex-direction: column;

  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.dark .modal-content {
  background: var(--ui-color-neutral-800);
  color: var(--ui-color-neutral-50);
}

/* scrollable area */
.form-body {
  flex: 1;
  overflow: auto;

  display: flex;
  flex-direction: column;
  gap: 12px;

  margin-top: 10px;

  padding-right: 12px;
  padding-left: 12px;
}

/* bottom action bar */
.actions {
  margin-top: auto;
  display: flex;
  gap: 8px;
}

/* input styling */
.input,
.textarea {
  width: 100%;
  padding: 8px;
  font-size: 14px;

  background: white;
  color: var(--ui-color-neutral-900);
  border: 1px solid var(--ui-color-neutral-300);
  border-radius: 6px;
}

.dark .input,
.dark .textarea {
  background: var(--ui-color-neutral-900);
  color: var(--ui-color-neutral-50);
  border-color: var(--ui-color-neutral-700);
}
</style>
