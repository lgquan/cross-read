import { createRouter, createWebHistory } from 'vue-router'

import BrowseView from '@/views/BrowseView.vue'
import HomeView from '@/views/HomeView.vue'
import PreviewView from '@/views/PreviewView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/browse/:shareId', name: 'browse', component: BrowseView },
    { path: '/preview/:shareId', name: 'preview', component: PreviewView },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

export default router
