import { readonly, useState } from '#imports'

export const useWorkflowSlideover = () => {
  const isOpen = useState<boolean>('workflow-slideover-open', () => false)

  const open = () => {
    isOpen.value = true
  }

  const close = () => {
    isOpen.value = false
  }

  const toggle = () => {
    isOpen.value = !isOpen.value
  }

  return {
    isOpen: readonly(isOpen),
    open,
    close,
    toggle,
  }
}
