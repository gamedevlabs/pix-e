<script setup lang="ts">

const props = defineProps({
    assets: {
        type: Array,
        default: () => []
    },
    loading: {
        type: Boolean,
        default: false,
    },
}); 


</script>

<template>
    <UTable :data="assets" :loading="loading" class="flex-1" />
</template>

