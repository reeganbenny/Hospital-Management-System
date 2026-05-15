<script setup>
defineProps({
  title: String,
  value: [String, Number],
  accent: String,
  icon: String
})
</script>

<template>
  <div class="stat-card">
    <div>
      <p class="stat-card-title">{{ title }}</p>
      <p class="stat-card-value">{{ value }}</p>
    </div>
    <div class="stat-card-icon" :class="accent || 'stat-card-icon-default'">
      <i v-if="icon" :class="icon"></i>
      <slot v-else />
    </div>
  </div>
</template>
