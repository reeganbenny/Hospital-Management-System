<script setup>
defineProps({
  modelValue: String,
  placeholder: String
})

defineEmits(['update:modelValue'])
</script>

<template>
  <input
    type="text"
    class="form-control"
    :placeholder="placeholder"
    :value="modelValue"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>
