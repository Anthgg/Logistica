import { useCallback, useRef, useState } from 'react'
import { formatFileSize } from './file-utils'
import { LogisticsIcon } from '../common/LogisticsIcon'

interface PendingFile {
  file: File
  error: string | null
}

interface Props {
  onFilesSelected: (files: File[]) => void
  accept?: string
  maxFiles?: number
  maxSizeBytes?: number
  disabled?: boolean
  label?: string
  hint?: string
}

export function SecureFileDropzone({
  onFilesSelected,
  accept = '*/*',
  maxFiles = 1,
  maxSizeBytes = 50 * 1024 * 1024,
  disabled = false,
  label = 'Arrastra archivos aquí o haz clic para seleccionar',
  hint,
}: Props) {
  const [isDragging, setIsDragging] = useState(false)
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  const validateFile = useCallback((file: File): string | null => {
    if (file.size > maxSizeBytes) {
      return `Archivo demasiado grande (máximo ${formatFileSize(maxSizeBytes)})`
    }
    if (accept !== '*/*') {
      const acceptedTypes = accept.split(',').map((t) => t.trim())
      const fileMimeType = file.type || 'application/octet-stream'
      const matches = acceptedTypes.some((pattern) => {
        if (pattern.endsWith('/*')) {
          return fileMimeType.startsWith(pattern.slice(0, -1))
        }
        return fileMimeType === pattern
      })
      if (!matches) {
        return `Tipo no permitido: ${fileMimeType}`
      }
    }
    return null
  }, [accept, maxSizeBytes])

  const handleFiles = useCallback((fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return
    const files = Array.from(fileList)
    const validated: PendingFile[] = files.slice(0, maxFiles).map((file) => ({
      file,
      error: validateFile(file),
    }))
    setPendingFiles(validated)
    const validFiles = validated.filter((f) => !f.error).map((f) => f.file)
    if (validFiles.length > 0) {
      onFilesSelected(validFiles)
    }
  }, [maxFiles, onFilesSelected, validateFile])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    if (disabled) return
    handleFiles(e.dataTransfer.files)
  }, [disabled, handleFiles])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled) setIsDragging(true)
  }, [disabled])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      inputRef.current?.click()
    }
  }, [])

  const clearFiles = () => setPendingFiles([])

  return (
    <div className="space-y-3">
      <div
        role="button"
        tabIndex={0}
        aria-label={label}
        onKeyDown={handleKeyDown}
        onClick={() => !disabled && inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-colors ${
          disabled
            ? 'border-slate-200 bg-slate-50 cursor-not-allowed opacity-60'
            : isDragging
              ? 'border-orange-400 bg-orange-50 cursor-pointer'
              : 'border-slate-300 bg-slate-50 cursor-pointer hover:border-slate-400 hover:bg-slate-100'
        }`}
      >
        <svg className="mb-2 h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
        <p className="text-sm font-medium text-slate-700">{label}</p>
        {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={maxFiles > 1}
          disabled={disabled}
          className="sr-only"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {pendingFiles.length > 0 && (
        <ul className="space-y-1" aria-label="Archivos seleccionados">
          {pendingFiles.map((pf, idx) => (
            <li key={idx} className={`flex items-center justify-between rounded-lg border px-3 py-2 text-sm ${pf.error ? 'border-rose-200 bg-rose-50' : 'border-slate-200 bg-white'}`}>
              <div className="flex flex-col">
                <span className="font-medium text-slate-900">{pf.file.name}</span>
                <span className="text-xs text-slate-400">{formatFileSize(pf.file.size)} · {pf.file.type || 'tipo desconocido'}</span>
                {pf.error && <span className="text-xs text-rose-600">{pf.error}</span>}
              </div>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); clearFiles() }}
                className="text-slate-400 hover:text-slate-600"
                aria-label="Quitar archivo"
              >
                <LogisticsIcon name="x" size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}