import { useState, useRef, useEffect, useCallback } from 'react'
import type {
  QualityPlanListQuery,
  QualityInspectionPlanStatus,
  QualityInspectionPlanFamily,
} from '../types/quality-inspection-plans'

interface QualityPlanSearchFiltersProps {
  filters: QualityPlanListQuery
  onChange: (filters: QualityPlanListQuery) => void
}

const STATUS_OPTIONS: { value: QualityInspectionPlanStatus; label: string }[] = [
  { value: 'DRAFT', label: 'Borrador' },
  { value: 'VALIDATED', label: 'Validado' },
  { value: 'SCHEDULED', label: 'Programado' },
  { value: 'ACTIVE', label: 'Activo' },
  { value: 'RETIRED', label: 'Retirado' },
  { value: 'ARCHIVED', label: 'Archivado' },
]

const FAMILY_OPTIONS: { value: QualityInspectionPlanFamily; label: string }[] = [
  { value: 'GENERAL', label: 'General' },
  { value: 'PRODUCT', label: 'Producto' },
  { value: 'CATEGORY', label: 'Categoría' },
  { value: 'WAREHOUSE', label: 'Bodega' },
  { value: 'SUPPLIER', label: 'Proveedor' },
  { value: 'TEMPERATURE', label: 'Temperatura' },
  { value: 'HAZMAT', label: 'Material peligroso' },
]

export function QualityPlanSearchFilters({ filters, onChange }: QualityPlanSearchFiltersProps) {
  const [search, setSearch] = useState(filters.search ?? '')

  const handleChange = useCallback(
    (partial: Partial<QualityPlanListQuery>) => {
      onChange({ ...filters, ...partial, page: 1 })
    },
    [filters, onChange],
  )

  const handleSearchSubmit = useCallback(() => {
    handleChange({ search: search || undefined })
  }, [search, handleChange])

  const hasActiveFilters = Boolean(
    filters.status || filters.family || filters.has_conflicts !== undefined ||
    filters.has_packaging !== undefined || filters.has_weight !== undefined ||
    filters.has_temperature !== undefined || filters.has_certificates !== undefined ||
    filters.has_sampling !== undefined || filters.created_by ||
    (filters as any).valid_from || (filters as any).valid_until || filters.search,
  )

  const clearAll = useCallback(() => {
    setSearch('')
    onChange({ page: 1, page_size: filters.page_size })
  }, [onChange, filters.page_size])

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearchSubmit()}
            placeholder="Buscar planes por código, nombre o descripción…"
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 pr-9 text-xs text-slate-800 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={handleSearchSubmit}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
        </div>
        {hasActiveFilters && (
          <button
            type="button"
            onClick={clearAll}
            className="whitespace-nowrap rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600 hover:bg-slate-50"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <MultiSelectDropdown
          label="Estado"
          options={STATUS_OPTIONS}
          selected={filters.status ? (Array.isArray(filters.status) ? filters.status : [filters.status]) : []}
          onChange={(status) => handleChange({ status: status.length > 0 ? (status.length === 1 ? status[0] as QualityInspectionPlanStatus : status as QualityInspectionPlanStatus[]) : undefined })}
        />
        <MultiSelectDropdown
          label="Familia"
          options={FAMILY_OPTIONS}
          selected={filters.family ? (Array.isArray(filters.family) ? filters.family : [filters.family]) : []}
          onChange={(family) => handleChange({ family: family.length > 0 ? (family.length === 1 ? family[0] as QualityInspectionPlanFamily : family as QualityInspectionPlanFamily[]) : undefined })}
        />
        <BooleanFilter
          label="Con conflictos"
          value={filters.has_conflicts}
          onChange={(v) => handleChange({ has_conflicts: v })}
        />
        <BooleanFilter
          label="Embalaje"
          value={filters.has_packaging}
          onChange={(v) => handleChange({ has_packaging: v })}
        />
        <BooleanFilter
          label="Peso"
          value={filters.has_weight}
          onChange={(v) => handleChange({ has_weight: v })}
        />
        <BooleanFilter
          label="Temperatura"
          value={filters.has_temperature}
          onChange={(v) => handleChange({ has_temperature: v })}
        />
        <BooleanFilter
          label="Certificados"
          value={filters.has_certificates}
          onChange={(v) => handleChange({ has_certificates: v })}
        />
        <BooleanFilter
          label="Muestreo"
          value={filters.has_sampling}
          onChange={(v) => handleChange({ has_sampling: v })}
        />
      </div>

      <div className="flex flex-wrap items-end gap-2">
        <div className="space-y-1">
          <label className="block text-[10px] font-semibold uppercase text-slate-400">Vigencia desde</label>
          <input
            type="date"
            value={(filters as any).valid_from ?? ''}
            onChange={(e) => handleChange({ valid_from: e.target.value || undefined } as any)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-800 focus:border-indigo-500 focus:outline-none"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-[10px] font-semibold uppercase text-slate-400">Vigencia hasta</label>
          <input
            type="date"
            value={(filters as any).valid_until ?? ''}
            onChange={(e) => handleChange({ valid_until: e.target.value || undefined } as any)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-800 focus:border-indigo-500 focus:outline-none"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-[10px] font-semibold uppercase text-slate-400">Creado por</label>
          <input
            type="text"
            value={filters.created_by ?? ''}
            onChange={(e) => handleChange({ created_by: e.target.value || undefined })}
            placeholder="ID del usuario"
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none"
          />
        </div>
      </div>
    </div>
  )
}

interface MultiSelectDropdownProps {
  label: string
  options: { value: string; label: string }[]
  selected: string[]
  onChange: (selected: string[]) => void
}

function MultiSelectDropdown({ label, options, selected, onChange }: MultiSelectDropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const toggle = useCallback(
    (value: string) => {
      const next = selected.includes(value)
        ? selected.filter((v) => v !== value)
        : [...selected, value]
      onChange(next)
    },
    [selected, onChange],
  )

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs transition-colors ${
          selected.length > 0
            ? 'border-indigo-300 bg-indigo-50 text-indigo-700'
            : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
        }`}
      >
        {label}
        {selected.length > 0 && (
          <span className="rounded-full bg-indigo-600 px-1.5 py-0.5 text-[10px] font-bold text-white">
            {selected.length}
          </span>
        )}
        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute z-50 mt-1 w-48 rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
          {options.map((opt) => (
            <label
              key={opt.value}
              className="flex cursor-pointer items-center gap-2 px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-50"
            >
              <input
                type="checkbox"
                checked={selected.includes(opt.value)}
                onChange={() => toggle(opt.value)}
                className="h-3.5 w-3.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              {opt.label}
            </label>
          ))}
        </div>
      )}
    </div>
  )
}

interface BooleanFilterProps {
  label: string
  value: boolean | undefined
  onChange: (value: boolean | undefined) => void
}

function BooleanFilter({ label, value, onChange }: BooleanFilterProps) {
  return (
    <button
      type="button"
      onClick={() => {
        if (value === undefined) onChange(true)
        else if (value === true) onChange(false)
        else onChange(undefined)
      }}
      className={`rounded-lg border px-3 py-1.5 text-xs transition-colors ${
        value === true
          ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
          : value === false
            ? 'border-rose-300 bg-rose-50 text-rose-700'
            : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
      }`}
    >
      {label}
      {value === true && ' (Sí)'}
      {value === false && ' (No)'}
    </button>
  )
}
