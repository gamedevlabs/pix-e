<script setup lang="ts">
const authentication = useAuthentication()
const llmStore = useLLM()
const router = useRouter()
const apiKeysOpen = ref(false)

const dropdownItems = computed(() => [
  [
    {
      label: authentication.user.value?.username || 'User',
      icon: 'i-lucide-user',
      type: 'label' as const,
    },
  ],
  [
    {
      label: 'Logout',
      icon: 'i-lucide-log-out',
      onSelect: async (e: Event | undefined) => {
        e?.preventDefault?.()
        await authentication.logout()
      },
    },
  ],
])
</script>

<template>
  <UHeader class="px-0" :ui="{ container: 'sm:px-2 lg:px-4' }">
    <template #left>
      <NuxtLink to="/" class="flex items-center gap-2 no-underline" aria-label="Home">
        <NuxtImg src="/favicon.png" alt="Logo" class="h-10 w-auto object-contain" />
        <h1 class="text-xl font-bold">pix:e</h1>
      </NuxtLink>
    </template>

    <template #right>
      <UColorModeSwitch />

      <UButton
        v-if="!authentication.isLoggedIn.value"
        label="Login"
        color="primary"
        variant="subtle"
        @click="router.push('login')"
      />
      <div v-else class="flex items-center gap-2">
        <UButton
          icon="i-lucide-key-round"
          color="neutral"
          variant="ghost"
          title="API Keys"
          @click="apiKeysOpen = true"
        />
        <USelect
          v-model="llmStore.activeModel"
          :items="llmStore.models"
          value-key="value"
          :icon="llmStore.activeModelIcon"
          class="w-48"
        />
        <UDropdownMenu :items="dropdownItems">
          <!-- Wrap so the whole avatar surface is clickable -->
          <div>
            <UAvatar avatar="i-lucide-user" :alt="authentication.user.value?.username" />
          </div>
        </UDropdownMenu>
      </div>
    </template>
  </UHeader>

  <SettingsOverlay v-model:open="apiKeysOpen" />
</template>
