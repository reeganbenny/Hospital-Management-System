<template>
  <div v-if="active === value">
    <slot />
  </div>
</template>

<script>
export default {
  props: {
    active: String,
    value: String
  }
};
</script>