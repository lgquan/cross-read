<script setup lang="ts">
import { AlertCircle, LoaderCircle } from '@lucide/vue'

defineProps<{
  loading?: boolean
  error?: string
}>()
</script>

<template>
  <div v-if="loading || error" class="reader-status" role="status">
    <LoaderCircle v-if="loading" class="spin" :size="25" />
    <AlertCircle v-else :size="25" />
    <p>{{ loading ? '正在打开文件…' : error }}</p>
  </div>
</template>
