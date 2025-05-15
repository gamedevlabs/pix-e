<script setup lang="ts">
import { ref } from 'vue'
import { useAuthentication } from '~/composables/useAuthentication'

const username = ref('')
const password = ref('')
const userId = ref<number | null>(null)
const error = ref('')
const authentication = useAuthentication()
const user = ref('')
await useFetch<{ id: number; username: string }>('http://localhost:8000/accounts/me/', {
  credentials: 'include',
  headers: useRequestHeaders(['cookie']),
})
  .then((data) => {
    if (data.data.value) {
      user.value = data.data.value.username
    } else {
      user.value = ''
    }
  })
  .catch(() => {
    user.value = ''
  })
</script>

<template>
  <div class="max-w-md mx-auto mt-10 p-4 border rounded shadow space-y-4">
    <h1 class="text-2xl font-bold">Login Test</h1>

    <UInput v-model="username" placeholder="Username" color="primary" class="w-full" />
    <UInput
      v-model="password"
      type="password"
      placeholder="Password"
      color="primary"
      class="w-full"
    />

    <div class="flex gap-2">
      <UButton color="primary" @click="authentication.login(username, password)"> Login </UButton>
      <UButton color="secondary" @click="authentication.register(username, password)">
        Register
      </UButton>
      <UButton color="success" @click="authentication.checkAuth"> Check Auth </UButton>
      <UButton color="error" @click="authentication.logout"> Logout </UButton>
    </div>

    <div>
      <p v-if="userId !== null" class="text-green-600">Logged in as id: {{ userId }}</p>
      <p v-else class="text-red-600">{{ error }}</p>
      <p v-if="user" class="text-gray-600">Current user: {{ user }}</p>
    </div>
  </div>
</template>