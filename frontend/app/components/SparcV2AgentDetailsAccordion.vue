<script setup lang="ts">
const props = defineProps<{
  agentDetails: AgentExecutionDetail[]
}>()

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

function formatAgentName(name: string): string {
  // Format agent names for display
  // e.g., "player_experience_v2" -> "Player Experience"
  return name
    .replace('_v2', '')
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function getAgentIcon(name: string): string {
  if (name === 'router') return 'i-heroicons-arrow-path-rounded-square'
  if (name === 'synthesis') return 'i-heroicons-chart-bar'
  return 'i-heroicons-cube'
}

// Sort agents: router first, then aspects, then synthesis
const sortedAgents = computed(() => {
  const agents = [...props.agentDetails]
  return agents.sort((a, b) => {
    if (a.agent_name === 'router') return -1
    if (b.agent_name === 'router') return 1
    if (a.agent_name === 'synthesis') return 1
    if (b.agent_name === 'synthesis') return -1
    return a.agent_name.localeCompare(b.agent_name)
  })
})

const items = computed(() =>
  sortedAgents.value.map((agent) => ({
    label: formatAgentName(agent.agent_name),
    icon: getAgentIcon(agent.agent_name),
    defaultOpen: false,
    slot: agent.agent_name,
  })),
)
</script>

<template>
  <div>
    <UAccordion :items="items" variant="soft">
      <template v-for="agent in sortedAgents" :key="agent.agent_name" #[agent.agent_name]>
        <div class="text-sm space-y-2 pb-2">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <span class="text-neutral-400">Execution Time:</span>
              <span class="ml-2">{{ formatDuration(agent.execution_time_ms) }}</span>
            </div>
            <div>
              <span class="text-neutral-400">Total Tokens:</span>
              <span class="ml-2">{{ agent.total_tokens.toLocaleString() }}</span>
            </div>
            <div>
              <span class="text-neutral-400">Prompt Tokens:</span>
              <span class="ml-2">{{ agent.prompt_tokens.toLocaleString() }}</span>
            </div>
            <div>
              <span class="text-neutral-400">Completion Tokens:</span>
              <span class="ml-2">{{ agent.completion_tokens.toLocaleString() }}</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-neutral-400">Status:</span>
            <UBadge
              :color="agent.success ? 'success' : 'error'"
              :label="agent.success ? 'Success' : 'Failed'"
              size="xs"
            />
          </div>
        </div>
      </template>
    </UAccordion>
  </div>
</template>
