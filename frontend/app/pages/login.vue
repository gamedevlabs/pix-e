<script setup lang="ts">
import type { FormError } from '@nuxt/ui'
import type { WorkflowInstance } from '~/mock_data/mock_workflow'

// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
definePageMeta({
  pageConfig: {
    type: 'public',
    showSidebar: false,
    title: 'Login',
  },
})
// ============================================================================

const state = reactive({ username: '', password: '' })
const authentication = useAuthentication()
const show = ref(false)

const { loadForUser, toggleSubstep } = useProjectWorkflow()
const projectWorkflow = useProjectWorkflow()

const overallProgress = computed(() => projectWorkflow.getProgress.value || 0)
const activeWorkflowTitle = computed(() => {
  const list = (projectWorkflow.workflows?.value || []) as WorkflowInstance[]
  const activeId = projectWorkflow.activeWorkflowId?.value
  const w = list.find((x) => x.id === activeId)
  return w?.meta?.title || 'Getting Started'
})

onMounted(async () => {
  await loadForUser()
  // Opening the login page counts as completing the first substep
  await toggleSubstep('user-onb-1', 'user-onb-1-1')
})

const validate = (state: { username: string; password: string }): FormError[] => {
  const errors = []
  if (!state.username) errors.push({ name: 'username', message: 'Required' })
  if (!state.password) errors.push({ name: 'password', message: 'Required' })
  return errors
}

const toast = useToast()

async function handleLogin() {
  const success = await authentication.login(state.username, state.password)
  if (success) {
    // Mark the final login substep complete (preceding substeps are auto-completed by toggleSubstep)
    await toggleSubstep('user-onb-1', 'user-onb-1-2')
    toast.add({
      title: 'Login Successful',
      description: `Welcome Back ${state.username}`,
      color: 'success',
    })
  } else {
    state.password = ''
    toast.add({ title: 'Login Failed', description: 'Invalid credentials.', color: 'error' })
  }
}

async function handleRegistration() {
  if (validate(state).length > 0) {
    toast.add({
      title: 'Registration Failed',
      description: 'Please fill in all fields.',
      color: 'error',
    })
    return
  }
  const success = await authentication.register(state.username, state.password)
  if (success) {
    // Mark the final login substep complete (preceding substeps are auto-completed by toggleSubstep)
    await toggleSubstep('user-onb-1', 'user-onb-1-2')
    toast.add({
      title: 'Registration Successful',
      description: `Welcome ${state.username}`,
      color: 'success',
    })
  } else {
    toast.add({
      title: 'Registration Failed',
      description: 'Username already exists.',
      color: 'error',
    })
  }
}
</script>

<template>
  <div class="items-center justify-center flex-col flex">

    <!-- Workflow button fixed bottom-left -->
    <div class="fixed left-4 bottom-4 z-40 w-72 max-w-[calc(100vw-2rem)]">
      <WorkflowSlideOverButton :title="activeWorkflowTitle" :progress="overallProgress" />
    </div>
    <WorkflowSlideover />

    <h1 class="text-2xl font-bold mb-4">Login</h1>
    <UForm :validate="validate" :state="state" class="space-y-4 w-60">
      <UFormField label="Username" name="username" size="lg" required>
        <UInput v-model="state.username" class="w-full" />
      </UFormField>

      <UFormField label="Password" name="password" size="lg" required>
        <UInput v-model="state.password" :type="show ? 'text' : 'password'" class="w-full">
          <template #trailing>
            <UButton
              color="neutral"
              variant="link"
              size="xs"
              :icon="show ? 'i-lucide-eye-off' : 'i-lucide-eye'"
              :aria-label="show ? 'Hide password' : 'Show password'"
              :aria-pressed="show"
              aria-controls="password"
              @click="show = !show"
            />
          </template>
        </UInput>
      </UFormField>

      <div class="flex items-center gap-2 justify-between">
        <UButton
          color="success"
          type="submit"
          label="Login"
          variant="subtle"
          class="w-full justify-center"
          @click="handleLogin"
        />
        <UButton
          color="info"
          type="submit"
          label="Register"
          variant="subtle"
          class="w-full justify-center"
          @click="handleRegistration"
        />
      </div>
    </UForm>
  </div>
</template>
