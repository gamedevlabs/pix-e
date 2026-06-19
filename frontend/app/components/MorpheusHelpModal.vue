<script setup lang="ts">
const open = defineModel<boolean>({ default: false })
</script>

<template>
  <UModal v-model:open="open" title="Morpheus (TUM CIT) — API Key Guide" class="max-w-lg w-full">
    <template #body>
      <div class="space-y-4 text-sm">
        <p>
          <a href="https://morpheus.cit.tum.de" target="_blank" class="text-primary underline"
            >Morpheus</a
          >
          is the TUM CIT LLM cluster. It provides free, privacy-respecting access to open-source
          LLMs for students and staff.
        </p>

        <div class="bg-muted p-3 rounded-lg space-y-1">
          <p class="font-semibold">Step 1: Log in to Morpheus</p>
          <p>
            Go to
            <a href="https://morpheus.cit.tum.de" target="_blank" class="text-primary underline"
              >morpheus.cit.tum.de</a
            >
            and log in with your <b>CIT / RBG account</b> (the same credentials you use for CIT
            computer pools and other TUM CIT services).
          </p>
        </div>

        <div class="bg-muted p-3 rounded-lg space-y-1">
          <p class="font-semibold">Step 2: Find your API Key</p>
          <p>Once logged in:</p>
          <ul class="list-disc pl-5 space-y-1">
            <li>Click on your <b>avatar / profile icon</b> (top-right corner).</li>
            <li>Go to <b>Settings</b> → <b>Account</b>.</li>
            <li>Scroll down to the <b>API Keys</b> section.</li>
            <li>Click <b>"Create API Key"</b> (or copy the existing one).</li>
            <li>
              Copy the key — it starts with <code class="text-xs bg-muted px-1 rounded">sk-</code>.
            </li>
          </ul>
        </div>

        <div class="bg-muted p-3 rounded-lg space-y-1">
          <p class="font-semibold">Step 3: Add the key to pix:e</p>
          <p>Paste the key into the API Key field above.</p>
          <p class="text-dimmed text-xs">
            The base URL (<code class="text-xs bg-muted px-1 rounded"
              >https://morpheus.cit.tum.de/api</code
            >) is automatically configured — you don't need to enter it.
          </p>
        </div>

        <div class="bg-muted p-3 rounded-lg space-y-1">
          <p class="font-semibold">Available Models</p>
          <p>
            pix:e will automatically discover the available models from the Morpheus API. The
            currently supported models include:
          </p>
          <ul class="list-disc pl-5 space-y-0.5 text-xs">
            <li><b>ministral-3</b> — 14B params, 32K context (lightweight, European)</li>
            <li><b>gemma-4</b> — 31B params, 64K context (vision, thinking, coding)</li>
            <li><b>qwen-35-35b</b> — 35B params (general tasks)</li>
            <li><b>qwen-35-35b-coding</b> — 35B params (coding-optimised)</li>
          </ul>
        </div>

        <p class="text-xs text-dimmed">
          For questions or support:
          <a href="mailto:support@ito.cit.tum.de" class="text-primary underline"
            >support@ito.cit.tum.de</a
          >
        </p>
      </div>
    </template>
  </UModal>
</template>
