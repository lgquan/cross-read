import type { DirectoryResponse, SearchResponse, ShareListResponse } from '@/types/files'

const API_BASE = '/api/v1'

export class ApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
  ) {
    super(message)
  }
}

async function request<T>(url: string): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    let message = '请求失败，请稍后重试'
    let code = 'request_failed'
    try {
      const body = (await response.json()) as {
        error?: { code?: string; message?: string }
      }
      message = body.error?.message ?? message
      code = body.error?.code ?? code
    } catch {
      // Keep the stable fallback when the response is not JSON.
    }
    throw new ApiError(message, code, response.status)
  }

  return (await response.json()) as T
}

export function getShares(): Promise<ShareListResponse> {
  return request<ShareListResponse>('/shares')
}

export function getEntries(shareId: string, path: string): Promise<DirectoryResponse> {
  const query = new URLSearchParams()
  if (path) query.set('path', path)
  const suffix = query.size > 0 ? `?${query.toString()}` : ''
  return request<DirectoryResponse>(`/shares/${encodeURIComponent(shareId)}/entries${suffix}`)
}

export function searchEntries(shareId: string, path: string, query: string): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query })
  if (path) params.set('path', path)
  return request<SearchResponse>(
    `/shares/${encodeURIComponent(shareId)}/search?${params.toString()}`,
  )
}

function fileUrl(endpoint: 'content' | 'media', shareId: string, path: string): string {
  const query = new URLSearchParams({ path })
  return `${API_BASE}/shares/${encodeURIComponent(shareId)}/${endpoint}?${query.toString()}`
}

export function getContentUrl(shareId: string, path: string): string {
  return fileUrl('content', shareId, path)
}

export function getMediaUrl(shareId: string, path: string): string {
  return fileUrl('media', shareId, path)
}

export async function getTextContent(shareId: string, path: string): Promise<string> {
  const response = await fetch(getContentUrl(shareId, path), {
    headers: { Accept: 'text/plain, text/markdown' },
  })
  if (!response.ok) {
    throw new ApiError('无法读取文件内容', 'content_failed', response.status)
  }
  return response.text()
}
