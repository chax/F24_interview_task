export type FileEntry = {
  id: number
  name: string
  created: string
  modified: string
  parent_id: number | null
  path: string
}

export type EntryKind = 'folder' | 'file'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

const BASE = '/api'

function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.set(key, String(value))
  }
  const query = search.toString()
  return query ? `?${query}` : ''
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(res.status, body?.detail ?? res.statusText)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export function listFolders(parentId: number | null): Promise<FileEntry[]> {
  return request(`/folders${buildQuery({ parent_id: parentId ?? undefined })}`)
}

export function listFiles(parentId: number | null): Promise<FileEntry[]> {
  return request(`/files${buildQuery({ parent_id: parentId ?? undefined })}`)
}

export function createFolder(name: string, parentId: number | null): Promise<FileEntry> {
  return request(`/folders/create${buildQuery({ name, parent_id: parentId ?? undefined })}`, {
    method: 'POST',
  })
}

export function createFile(name: string, parentId: number | null): Promise<FileEntry> {
  return request(`/files/create${buildQuery({ name, parent_id: parentId ?? undefined })}`, {
    method: 'POST',
  })
}

export function renameEntry(kind: EntryKind, fileId: number, name: string): Promise<FileEntry> {
  const path = kind === 'folder' ? '/folders/rename' : '/files/rename'
  return request(`${path}${buildQuery({ file_id: fileId, name })}`, { method: 'POST' })
}

export function deleteEntry(kind: EntryKind, fileId: number, recursive = false): Promise<void> {
  const path = kind === 'folder' ? '/folders/delete' : '/files/delete'
  return request(`${path}${buildQuery({ file_id: fileId, recursive })}`, { method: 'DELETE' })
}

export function searchFiles(startsWith: string, parentId: number | null): Promise<string[]> {
  return request(`/files/search${buildQuery({ starts_with: startsWith, parent_id: parentId ?? undefined })}`)
}

export function getFilesByName(fileName: string, parentId: number | null): Promise<FileEntry[]> {
  return request(`/files/get_by_name${buildQuery({ file_name: fileName, parent_id: parentId ?? undefined })}`)
}
