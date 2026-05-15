<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary'
  },
  size: {
    type: String,
    default: 'default'
  }
})
</script>

<template>
  <button
    type="button"
    class="btn"
    :class="{
      'btn-primary': variant === 'default' || variant === 'primary',
      'btn-outline-primary': variant === 'outline',
      'btn-outline-secondary': variant === 'ghost',
      'btn-sm': size === 'sm',
      'btn-lg': size === 'lg'
    }"
  >
    <slot />
  </button>
</template>
