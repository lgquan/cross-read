<script setup lang="ts">
import {
  File,
  FileCode2,
  FileImage,
  FileText,
  FileType2,
  Film,
  Folder,
} from '@lucide/vue'
import { computed } from 'vue'

import type { FileKind } from '@/types/files'

const props = defineProps<{ kind: FileKind }>()

const icon = computed(() => {
  const icons = {
    directory: Folder,
    markdown: FileCode2,
    pdf: FileText,
    docx: FileType2,
    image: FileImage,
    text: FileText,
    video: Film,
    unsupported: File,
  }
  return icons[props.kind]
})
</script>

<template>
  <span class="file-icon" :class="`file-icon--${kind}`" aria-hidden="true">
    <component :is="icon" :size="23" :stroke-width="1.8" />
  </span>
</template>
