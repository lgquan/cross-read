<script setup lang="ts">
import { ChevronLeft, ChevronRight, Home, Search, X } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getEntries } from '@/api/client'
import FileKindIcon from '@/components/FileKindIcon.vue'
import StatePanel from '@/components/StatePanel.vue'
import type { DirectoryResponse, FileEntry } from '@/types/files'
import { formatFileSize, formatModifiedAt } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const data = ref<DirectoryResponse | null>(null)
const loading = ref(true)
const error = ref('')
const search = ref('')

const shareId = computed(() => String(route.params.shareId))
const currentPath = computed(() => (typeof route.query.path === 'string' ? route.query.path : ''))
const pathParts = computed(() => currentPath.value.split('/').filter(Boolean))
const visibleItems = computed(() => {
  const query = search.value.trim().toLocaleLowerCase()
  if (!query) return data.value?.items ?? []
  return (data.value?.items ?? []).filter((item) => item.name.toLocaleLowerCase().includes(query))
})

function pathAt(index: number): string {
  return pathParts.value.slice(0, index + 1).join('/')
}

function goToPath(path: string) {
  void router.push({ name: 'browse', params: { shareId: shareId.value }, query: path ? { path } : {} })
}

function goUp() {
  if (pathParts.value.length === 0) {
    void router.push({ name: 'home' })
    return
  }
  goToPath(pathParts.value.slice(0, -1).join('/'))
}

function openEntry(entry: FileEntry) {
  if (entry.is_directory) {
    goToPath(entry.path)
    return
  }
  void router.push({
    name: 'preview',
    params: { shareId: shareId.value },
    query: { path: entry.path, kind: entry.kind },
  })
}

async function loadEntries() {
  loading.value = true
  error.value = ''
  search.value = ''
  try {
    data.value = await getEntries(shareId.value, currentPath.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '无法打开这个文件夹'
  } finally {
    loading.value = false
  }
}

watch([shareId, currentPath], loadEntries)
onMounted(loadEntries)
</script>

<template>
  <section class="browse-header">
    <button class="icon-button back-button" type="button" aria-label="返回上一级" @click="goUp">
      <ChevronLeft :size="23" />
    </button>
    <div class="browse-title">
      <p class="eyebrow">{{ data?.share.name ?? '资料库' }}</p>
      <h1>{{ pathParts[pathParts.length - 1] ?? data?.share.name ?? '正在加载' }}</h1>
    </div>
  </section>

  <nav v-if="data" class="breadcrumbs" aria-label="当前位置">
    <button type="button" title="资料库根目录" @click="goToPath('')">
      <Home :size="15" />
    </button>
    <template v-for="(part, index) in pathParts" :key="pathAt(index)">
      <ChevronRight :size="14" aria-hidden="true" />
      <button type="button" @click="goToPath(pathAt(index))">{{ part }}</button>
    </template>
  </nav>

  <label v-if="data && data.items.length > 0" class="search-field">
    <Search :size="18" aria-hidden="true" />
    <input v-model="search" type="search" placeholder="筛选当前文件夹" autocomplete="off" />
    <button v-if="search" type="button" aria-label="清除筛选" @click="search = ''">
      <X :size="16" />
    </button>
  </label>

  <div v-if="loading" class="file-list" aria-label="正在加载">
    <div v-for="index in 5" :key="index" class="file-row skeleton-row"></div>
  </div>

  <StatePanel
    v-else-if="error"
    kind="error"
    title="无法打开文件夹"
    :message="error"
    retryable
    @retry="loadEntries"
  />

  <StatePanel
    v-else-if="data?.items.length === 0"
    title="这里还没有文件"
    message="这个文件夹是空的。"
  />

  <StatePanel
    v-else-if="visibleItems.length === 0"
    title="没有匹配的文件"
    message="换一个关键词试试。"
  />

  <section v-else class="file-list" aria-label="文件列表">
    <button
      v-for="entry in visibleItems"
      :key="entry.path"
      class="file-row"
      type="button"
      @click="openEntry(entry)"
    >
      <FileKindIcon :kind="entry.kind" />
      <span class="file-copy">
        <strong>{{ entry.name }}</strong>
        <small>
          {{ formatFileSize(entry.size) }}
          <span aria-hidden="true"> · </span>
          {{ formatModifiedAt(entry.modified_at) }}
        </small>
      </span>
      <ChevronRight class="row-chevron" :size="18" aria-hidden="true" />
    </button>
  </section>
</template>
