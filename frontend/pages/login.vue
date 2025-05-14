<script setup lang="ts">
import { ref } from 'vue'

const username = ref('')
const password = ref('')
const userId = ref<number | null>(null)
const error = ref('')

const user = ref('')
await useFetch<{id: number, username: string}>('http://localhost:8000/accounts/me/', {
  credentials: 'include',
  headers: useRequestHeaders(['cookie']),
}).then(data => {
  if (data.data.value) {
    user.value = data.data.value.username
  } else {
    user.value = ''
  }
}).catch(() => {
  user.value = ''
})

const register = async () => {
  error.value = ''
  try {
    await $fetch('http://localhost:8000/accounts/register/', {
      method: 'POST',
      body: { username: username.value, password: password.value },
      credentials: 'include',
    })
    await login()
  } catch {
    error.value = 'Registration failed.'
  }
}

const login = async () => {
  error.value = ''
  try {
    await $fetch('http://localhost:8000/accounts/login/', {
      method: 'POST',
      body: { username: username.value, password: password.value },
      credentials: 'include',
    })
    await checkAuth()
  } catch {
    error.value = 'Login failed.'
  }
}

const checkAuth = async () => {
  try {
    const res = await $fetch<{ id: number }>('http://localhost:8000/accounts/me/', {
      credentials: 'include',
    })
    userId.value = res.id
  } catch {
    error.value = 'Not logged in'
    userId.value = null
  }
}

const logout = async () => {
  error.value = ''
  const csrftoken = useCookie('csrftoken', {readonly : true}).value
  try {
    await $fetch('http://localhost:8000/accounts/logout/', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'X-CSRFToken': csrftoken ?? '',
      } as HeadersInit
    })
    userId.value = null
  } catch {
    error.value = 'Logout failed.'
  }
}
</script>

<template>
  <div class="max-w-md mx-auto mt-10 p-4 border rounded shadow space-y-4">
    <h1 class="text-2xl font-bold">Login Test</h1>

    <UInput v-model="username" placeholder="Username" color="primary" class="w-full"/>
    <UInput v-model="password" type="password" placeholder="Password" color="primary" class="w-full"/>

    <div class="flex gap-2">
      <UButton color="primary" @click="login">
        Login
      </UButton>
      <UButton color="secondary" @click="register">
        Register
      </UButton>
      <UButton color="success" @click="checkAuth">
        Check Auth
      </UButton>
      <UButton color="error" @click="logout">
        Logout
      </UButton>
    </div>

    <div>
      <p v-if="userId !== null" class="text-green-600">Logged in as id: {{ userId }}</p>
      <p v-else class="text-red-600">{{ error }}</p>
      <p v-if="user" class="text-gray-600">Current user: {{ user }}</p>
    </div>
  </div>
</template>