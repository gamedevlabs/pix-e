import type { SelectItem } from '@nuxt/ui'
import { defineStore } from 'pinia'

export const useLLM = defineStore('llm', () => {
  const llm_models = ref([
    {
      label: 'Google Gemini',
      value: 'gemini',
      icon: 'i-simple-icons-googlegemini',
    },
    {
      label: 'ChatGPT (GPT-4)',
      value: 'openai',
      icon: 'i-simple-icons-openai',
    },
    {
      label: 'Local Model (Ollama)',
      value: 'ollama',
      icon: 'i-simple-icons-ollama',
    },
  ] satisfies SelectItem[])
  const active_llm = ref(llm_models.value[0]?.value)
  const llm_icon = computed(
    () => llm_models.value.find((item) => item.value === active_llm.value)?.icon,
  )
  return {
    llm_models,
    active_llm,
    llm_icon,
  }
})
