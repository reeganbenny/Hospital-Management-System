<template>
  <div>
    <!-- Tabs Header -->
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item" v-for="tab in tabs" :key="tab.value">
        <button
          class="nav-link"
          :class="{ active: modelValue === tab.value }"
          @click="$emit('update:modelValue', tab.value)"
        >
          {{ tab.label }}
        </button>
      </li>
    </ul>

    <!-- Tabs Content -->
    <div>
      <slot />
    </div>
  </div>
</template>

<script>
export default {
  props: {
    tabs: Array,
    modelValue: String
  }
};
</script>