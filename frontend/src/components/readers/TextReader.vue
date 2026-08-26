<script setup lang="ts">
import DOMPurify from 'dompurify'
import { computed, onMounted, ref, watch } from 'vue'

import { getTextContent } from '@/api/client'
import { getLanguageFromPath, getLanguageLabel, highlightCode } from '@/utils/syntaxHighlight'
import ReaderStatus from './ReaderStatus.vue'

const props = defineProps<{ shareId: string; path: string }>()
const content = ref('')
const loading = ref(true)
const error = ref('')
const language = computed(() => getLanguageFromPath(props.path))
const languageLabel = computed(() => language.value ? getLanguageLabel(language.value) : '')
const highlightedContent = computed(() => {
  if (!language.value) return ''
  const result = highlightCode(content.value, language.value)
  return DOMPurify.sanitize(result ?? '', {
    ALLOWED_TAGS: ['span'],
    ALLOWED_ATTR: ['class'],
  })
})

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
  <section v-if="!loading && !error && language" class="code-file-reader">
    <header class="code-file-header">
      <span>{{ languageLabel }}</span>
    </header>
    <!-- highlight.js escapes source text; DOMPurify limits generated markup to token spans. -->
    <pre class="text-reader text-reader--code"><code class="hljs" v-html="highlightedContent"></code></pre>
  </section>
  <pre v-else-if="!loading && !error" class="text-reader">{{ content }}</pre>
</template>
