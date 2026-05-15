<template>
  <div class="card shadow-sm">
    <div v-if="$slots.header" class="card-header bg-transparent border-bottom py-3">
      <slot name="header" />
    </div>
    <div class="card-body">
      <slot />
    </div>
  </div>
</template>
