<template>
  <UModal v-model:open="isOpen" :title="modalTitle" :description="modalDescription" size="lg">
    <template #body>
      <div v-if="moodboard" class="modal-content">
        <!-- Moodboard Preview -->
        <div class="moodboard-preview">
          <div class="preview-image">
            <img
              v-if="moodboard.images?.length"
              :src="getImageUrl(moodboard.images[0]?.image_url)"
              :alt="moodboard.title"
              class="preview-img"
            />
            <div v-else class="preview-placeholder">
              <UIcon name="i-heroicons-photo-20-solid" class="placeholder-icon" />
            </div>
          </div>
          <div class="preview-info">
            <h3 class="preview-title">{{ moodboard.title }}</h3>
            <p v-if="moodboard.description" class="preview-description">
              {{ moodboard.description }}
            </p>
            <div class="preview-meta">
              <span class="meta-item">
                <UIcon name="i-heroicons-photo-20-solid" class="meta-icon" />
                {{ getImageCount(moodboard) }} images
              </span>
              <UBadge
                :color="moodboard.is_public ? 'success' : 'neutral'"
                variant="subtle"
                size="sm"
              >
                {{ moodboard.is_public ? 'Public' : 'Private' }}
              </UBadge>
            </div>
          </div>
        </div>

        <!-- Share Form -->
        <div class="share-form">
          <div class="form-group">
            <label class="form-label">
              <UIcon name="i-heroicons-user-20-solid" class="label-icon" />
              Select User
            </label>
            <USelectMenu
              v-model="selectedUserId"
              :options="userOptions"
              :loading="loadingUsers"
              placeholder="Choose a user to share with..."
              searchable
              class="user-select"
            />
          </div>

          <div class="form-group">
            <label class="form-label">
              <UIcon name="i-heroicons-shield-check-20-solid" class="label-icon" />
              Permission Level
            </label>
            <USelect
              v-model="selectedPermission"
              :options="permissionOptions"
              class="permission-select"
            />
          </div>

          <!-- Permission Description -->
          <div class="permission-description">
            <div class="description-content">
              <UIcon name="i-heroicons-information-circle-20-solid" class="description-icon" />
              <div class="description-text">
                <strong v-if="selectedPermission === 'view'">View Only:</strong>
                <strong v-else-if="selectedPermission === 'edit'">Edit Access:</strong>
                <span v-if="selectedPermission === 'view'">
                  User can view the moodboard but cannot make changes.
                </span>
                <span v-else-if="selectedPermission === 'edit'">
                  User can view and modify the moodboard.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="modal-footer">
        <UButton variant="outline" color="neutral" :disabled="sharing" @click="handleCancel">
          Cancel
        </UButton>
        <UButton
          color="primary"
          :loading="sharing"
          :disabled="!canShare"
          icon="i-heroicons-share-20-solid"
          @click="handleShare"
        >
          Share Moodboard
        </UButton>
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useUsers } from '~/composables/useUsers'
import { useRuntimeConfig } from '#app'

// Types
interface Moodboard {
  id: string
  title: string
  description?: string
  is_public: boolean
  images?: Array<{ image_url: string }>
}

interface LocalUser {
  id: string
  username: string
  email?: string
}

interface Props {
  open: boolean
  moodboard?: Moodboard
}

// Props & Emits
const props = defineProps<Props>()
const emit = defineEmits<{
  'update:open': [value: boolean]
  share: [data: { userId: string; permission: string }]
}>()

// Composables
const { fetchUsers } = useUsers()
const config = useRuntimeConfig()

// State
const users = ref<LocalUser[]>([])
const selectedUserId = ref<string>('')
const selectedPermission = ref<string>('view')
const loadingUsers = ref<boolean>(false)
const sharing = ref<boolean>(false)

// Computed
const isOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value),
})

const modalTitle = computed(() => {
  return props.moodboard ? `Share "${props.moodboard.title}"` : 'Share Moodboard'
})

const modalDescription = computed(() => {
  return 'Give another user access to view or edit this moodboard'
})

const userOptions = computed(() => {
  return users.value.map((user) => ({
    value: user.id,
    label: user.username,
  }))
})

const permissionOptions = computed(() => [
  { value: 'view', label: 'View Only' },
  { value: 'edit', label: 'Edit Access' },
])

const canShare = computed(() => {
  return selectedUserId.value && selectedPermission.value && !sharing.value
})

// Methods
function getImageUrl(url?: string): string {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${config.public.apiUrl}${url.startsWith('/') ? '' : '/'}${url}`
}

function getImageCount(moodboard: Moodboard): number {
  return moodboard.images?.length || 0
}

async function loadUsers() {
  if (users.value.length > 0) return

  loadingUsers.value = true
  try {
    const result = await fetchUsers()
    if (result && Array.isArray(result)) {
      users.value = result.map((user: { id: number; username: string; email?: string }) => ({
        id: String(user.id),
        username: user.username,
        email: user.email,
      }))
    }
  } catch {
    // Handle error silently for production
  } finally {
    loadingUsers.value = false
  }
}

function handleCancel() {
  isOpen.value = false
  resetForm()
}

function handleShare() {
  if (!canShare.value) return

  sharing.value = true
  emit('share', {
    userId: selectedUserId.value,
    permission: selectedPermission.value,
  })
}

function resetForm() {
  selectedUserId.value = ''
  selectedPermission.value = 'view'
  sharing.value = false
}

// Watchers
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      loadUsers()
    } else {
      resetForm()
    }
  },
)

watch(
  () => props.open,
  (isOpen, wasOpen) => {
    if (wasOpen && !isOpen && sharing.value) {
      sharing.value = false
    }
  },
)
</script>

<style scoped>
.modal-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 0.5rem 0;
}

/* Moodboard Preview */
.moodboard-preview {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 0.875rem;
  border: 1px solid rgb(226 232 240);
  transition: all 0.2s ease;
}

.dark .moodboard-preview {
  background: linear-gradient(135deg, rgb(30 41 59) 0%, rgb(15 23 42) 100%);
  border-color: rgb(51 65 85);
}

.preview-image {
  flex-shrink: 0;
  width: 4.5rem;
  height: 4.5rem;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 0.625rem;
  border: 1px solid rgb(226 232 240);
  transition: transform 0.2s ease;
}

.preview-img:hover {
  transform: scale(1.02);
}

.dark .preview-img {
  border-color: rgb(51 65 85);
}

.preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
  border-radius: 0.625rem;
  color: rgb(107 114 128);
}

.dark .preview-placeholder {
  background: linear-gradient(135deg, rgb(51 65 85) 0%, rgb(30 41 59) 100%);
  color: rgb(156 163 175);
}

.placeholder-icon {
  width: 1.5rem;
  height: 1.5rem;
}

.preview-info {
  flex: 1;
  min-width: 0;
}

.preview-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: rgb(17 24 39);
  margin: 0 0 0.375rem 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dark .preview-title {
  color: rgb(243 244 246);
}

.preview-description {
  color: rgb(107 114 128);
  font-size: 0.875rem;
  margin: 0 0 0.875rem 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.dark .preview-description {
  color: rgb(156 163 175);
}

.preview-meta {
  display: flex;
  align-items: center;
  gap: 0.875rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  color: rgb(107 114 128);
  font-size: 0.875rem;
  font-weight: 500;
}

.dark .meta-item {
  color: rgb(156 163 175);
}

.meta-icon {
  width: 0.875rem;
  height: 0.875rem;
}

/* Share Form */
.share-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: rgb(55 65 81);
}

.dark .form-label {
  color: rgb(209 213 219);
}

.label-icon {
  width: 1rem;
  height: 1rem;
  color: rgb(107 114 128);
}

.dark .label-icon {
  color: rgb(156 163 175);
}

.user-select,
.permission-select {
  width: 100%;
}

/* Permission Description */
.permission-description {
  padding: 1.125rem;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 1px solid rgb(191 219 254);
  border-radius: 0.625rem;
}

.dark .permission-description {
  background: linear-gradient(135deg, rgb(30 58 138 / 0.1) 0%, rgb(30 64 175 / 0.05) 100%);
  border-color: rgb(59 130 246 / 0.3);
}

.description-content {
  display: flex;
  gap: 0.875rem;
}

.description-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: rgb(59 130 246);
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.description-text {
  font-size: 0.875rem;
  color: rgb(55 65 81);
  line-height: 1.5;
}

.dark .description-text {
  color: rgb(209 213 219);
}

.description-text strong {
  color: rgb(59 130 246);
  font-weight: 600;
}

/* Modal Footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.875rem;
  padding-top: 1.25rem;
}

/* Responsive */
@media (max-width: 640px) {
  .moodboard-preview {
    flex-direction: column;
    gap: 0.875rem;
  }

  .preview-image {
    width: 100%;
    height: 8rem;
  }

  .modal-footer {
    flex-direction: column-reverse;
    gap: 0.625rem;
  }

  .modal-footer button {
    width: 100%;
  }
}
</style>
