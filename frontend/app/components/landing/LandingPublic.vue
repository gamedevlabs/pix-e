<script setup lang="ts">
import LandingFeatureHighlightCard from '~/components/landing/LandingFeatureHighlightCard.vue'
import LandingStandaloneModuleCard from '~/components/landing/LandingStandaloneModuleCard.vue'

const router = useRouter()

interface PublicModule {
  id: string
  label: string
  description: string
  icon: string
  to: string
}

const standaloneModules: PublicModule[] = [
  {
    id: 'movie-script',
    label: 'Movie Script Evaluator',
    description:
      'Evaluate movie scripts through LLMs based on available assets for virtual production.',
    icon: 'i-lucide-film',
    to: '/movie-script-evaluator',
  },
]

const featureHighlights = [
  {
    icon: 'i-lucide-landmark',
    iconBgClass: 'bg-secondary-500/10',
    iconColorClass: 'text-secondary-500',
    title: 'Experience Pillars',
    description: 'Map design decisions to validated player experience dimensions.',
  },
  {
    icon: 'i-lucide-book-open',
    iconBgClass: 'bg-success-500/10',
    iconColorClass: 'text-success-600 dark:text-success-400',
    title: 'Player Expectations',
    description: 'Define what players expect from your game and track how your design meets it.',
  },
  {
    icon: 'i-lucide-chart-no-axes-gantt',
    iconBgClass: 'bg-primary/10',
    iconColorClass: 'text-primary',
    title: 'Player Experience',
    description: 'Evaluate and iterate on the overall experience your game delivers.',
  },
  {
    icon: 'i-lucide-film',
    iconBgClass: 'bg-secondary-500/10',
    iconColorClass: 'text-secondary-500',
    title: 'Script Evaluator',
    description: 'Evaluate narrative scripts via LLMs for virtual production readiness.',
  },
]
</script>

<template>
  <div class="space-y-14">
    <!-- Hero -->
    <section class="text-center space-y-5 max-w-2xl mx-auto pt-6">
      <div class="flex justify-center">
        <img src="/favicon.png" alt="pix:e logo" class="size-14 rounded-xl" />
      </div>

      <h1
        class="text-4xl xl:text-5xl font-bold tracking-tight text-gray-900 dark:text-gray-50 leading-tight"
      >
        Improve your player's experience<br />
        <span class="text-primary">with pix:e</span>
      </h1>

      <p class="text-base text-gray-500 dark:text-gray-400 max-w-lg mx-auto leading-relaxed">
        <span class="text-primary font-semibold">pix:e</span> helps you design, evaluate, and
        iterate on your game's player experience using research-backed methods.
      </p>

      <div class="flex flex-wrap items-center justify-center gap-3 pt-1">
        <UButton
          label="Get Started"
          icon="i-lucide-user-plus"
          color="primary"
          size="xl"
          @click="router.push('/login')"
        />
        <UButton
          label="Sign in"
          icon="i-lucide-log-in"
          color="neutral"
          variant="outline"
          size="xl"
          @click="router.push('/login')"
        />
      </div>
    </section>

    <!-- Feature highlights -->
    <section class="space-y-6 max-w-5xl mx-auto">
      <div class="text-center space-y-1">
        <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">What's inside</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Tools to cover the full player experience design cycle
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <LandingFeatureHighlightCard
          v-for="feature in featureHighlights"
          :key="feature.title"
          :icon="feature.icon"
          :title="feature.title"
          :description="feature.description"
          :icon-bg-class="feature.iconBgClass"
          :icon-color-class="feature.iconColorClass"
        />
      </div>
    </section>

    <!-- Standalone modules (available without login) -->
    <section class="space-y-5 max-w-5xl mx-auto">
      <div class="flex items-center gap-3">
        <div class="h-6 w-1 rounded-full bg-secondary-500" />
        <div>
          <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">Try without an account</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            These tools are available immediately — no login required
          </p>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <LandingStandaloneModuleCard
          v-for="module in standaloneModules"
          :key="module.id"
          :icon="module.icon"
          :label="module.label"
          :description="module.description"
          :to="module.to"
          tag-label="No login needed"
        />
      </div>
    </section>

    <!-- Bottom sign-up nudge -->
    <section class="max-w-5xl mx-auto">
      <UCard
        class="border border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900"
        :ui="{ body: 'px-6 py-6' }"
      >
        <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div class="space-y-1 text-center sm:text-left">
            <p class="font-semibold text-gray-900 dark:text-gray-100">
              Create an account to get started
            </p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Sign up to manage projects and access all tools.
            </p>
          </div>
          <div class="flex gap-3 shrink-0">
            <UButton
              label="Create account"
              icon="i-lucide-user-plus"
              color="primary"
              size="md"
              @click="router.push('/login')"
            />
            <UButton
              label="Sign in"
              icon="i-lucide-log-in"
              color="neutral"
              variant="outline"
              size="md"
              @click="router.push('/login')"
            />
          </div>
        </div>
      </UCard>
    </section>
  </div>
</template>
