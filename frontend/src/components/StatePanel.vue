<script setup lang="ts">
import { AlertCircle, FolderOpen, RefreshCw } from '@lucide/vue'

withDefaults(
  defineProps<{
    kind?: 'empty' | 'error'
    title: string
    message: string
    retryable?: boolean
  }>(),
  { kind: 'empty', retryable: false },
)

defineEmits<{ retry: [] }>()
</script>

<template>
  <section class="state-panel" role="status">
    <span class="state-icon">
      <AlertCircle v-if="kind === 'error'" :size="27" />
      <FolderOpen v-else :size="27" />
    </span>
    <h2>{{ title }}</h2>
    <p>{{ message }}</p>
    <button v-if="retryable" class="button button--secondary" type="button" @click="$emit('retry')">
      <RefreshCw :size="16" />
      重新加载
    </button>
  </section>
</template>
