<template>
  <component
    :is="as"
    class="animate-pulse rounded-md bg-surface-800/50 light:bg-surface-200/80"
    :class="className"
  />
</template>

<script setup>
defineProps({
  as: { type: String, default: 'div' },
  className: { type: String, default: '' },
})
</script>
