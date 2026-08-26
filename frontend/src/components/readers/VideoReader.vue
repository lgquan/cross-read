<script setup lang="ts">
import { computed, ref } from 'vue'

import { getMediaUrl } from '@/api/client'

const props = defineProps<{ shareId: string; path: string }>()
const playbackError = ref('')
const mediaUrl = computed(() => getMediaUrl(props.shareId, props.path))
</script>

<template>
  <div class="video-reader">
    <video
      :src="mediaUrl"
      controls
      playsinline
      preload="metadata"
      @error="playbackError = 'Safari 无法播放这个视频，文件内部编码可能不兼容。建议使用 H.264 + AAC。'"
    >
      当前浏览器不支持 HTML5 视频播放。
    </video>
    <p v-if="playbackError" class="reader-error">{{ playbackError }}</p>
  </div>
</template>
