<script setup>
defineProps({
  variant: String
})
</script>

<template>
  <span class="badge border" :class="$attrs.class">
    <slot />
  </span>
</template>
