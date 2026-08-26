<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { getTextContent } from '@/api/client'
import ReaderStatus from './ReaderStatus.vue'

const props = defineProps<{ shareId: string; path: string }>()
const content = ref('')
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    content.value = await getTextContent(props.shareId, props.path)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '无法读取文本文件'
  } finally {
    loading.value = false
  }
}

watch(() => [props.shareId, props.path], load)
onMounted(load)
</script>

<template>
  <ReaderStatus :loading="loading" :error="error" />
  <pre v-if="!loading && !error" class="text-reader">{{ content }}</pre>
</template>
