<script setup lang="ts">
import { ChevronRight, FolderOpen } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { getShares } from '@/api/client'
import StatePanel from '@/components/StatePanel.vue'
import type { ShareSummary } from '@/types/files'

const shares = ref<ShareSummary[]>([])
const loading = ref(true)
const error = ref('')

async function loadShares() {
  loading.value = true
  error.value = ''
  try {
    shares.value = (await getShares()).items
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '无法连接到 Cross Read 服务'
  } finally {
    loading.value = false
  }
}

onMounted(loadShares)
</script>

<template>
  <section class="hero">
    <p class="eyebrow">你的私人阅读空间</p>
    <h1>从这里开始阅读</h1>
    <p class="hero-copy">选择电脑上已经开放的资料库。所有内容保持原位，只通过局域网读取。</p>
  </section>

  <section class="content-section" aria-labelledby="library-heading">
    <div class="section-heading">
      <div>
        <h2 id="library-heading">资料库</h2>
        <p>{{ loading ? '正在连接电脑…' : `${shares.length} 个共享目录` }}</p>
      </div>
    </div>

    <div v-if="loading" class="library-grid" aria-label="正在加载">
      <div v-for="index in 2" :key="index" class="library-card skeleton-card"></div>
    </div>

    <StatePanel
      v-else-if="error"
      kind="error"
      title="暂时无法连接"
      :message="error"
      retryable
      @retry="loadShares"
    />

    <StatePanel
      v-else-if="shares.length === 0"
      title="还没有资料库"
      message="请先在电脑端配置至少一个共享目录。"
    />

    <div v-else class="library-grid">
      <RouterLink
        v-for="share in shares"
        :key="share.id"
        class="library-card"
        :to="{ name: 'browse', params: { shareId: share.id } }"
      >
        <span class="library-icon"><FolderOpen :size="28" :stroke-width="1.7" /></span>
        <span class="library-copy">
          <strong>{{ share.name }}</strong>
          <small>浏览这个资料库</small>
        </span>
        <ChevronRight class="card-chevron" :size="20" aria-hidden="true" />
      </RouterLink>
    </div>
  </section>
</template>
