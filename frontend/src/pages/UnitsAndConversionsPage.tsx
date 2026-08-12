import { useCallback, useEffect, useState } from 'react'
import { unitsConversionsApi } from '../api/units-conversions-api'
import { Alert } from '../components/common/Alert'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import { StatusBadge } from '../components/common/StatusBadge'
import { UnitConversionSimulatorPanel } from '../components/units/UnitConversionSimulatorPanel'
import type { PaginatedResponse } from '../types/logistics-resources'
import type { UnitConversionRule, UnitOfMeasure } from '../types/units-conversions'
import { getErrorMessage } from '../utils/errors'

type UnitsTab = 'units' | 'conversions' | 'simulator'

export function UnitsAndConversionsPage() {
  const [activeTab, setActiveTab] = useState<UnitsTab>('units')
  const [unitsData, setUnitsData] = useState<PaginatedResponse<UnitOfMeasure>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [rulesData, setRulesData] = useState<PaginatedResponse<UnitConversionRule>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      if (activeTab === 'units') {
        setUnitsData(await unitsConversionsApi.listUnits())
      } else if (activeTab === 'conversions') {
        setRulesData(await unitsConversionsApi.listConversionRules())
      }
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [activeTab])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const unitColumns: TableColumn<UnitOfMeasure>[] = [
    {
      key: 'code',
      label: 'Código / Símbolo',
      render: (row) => (
        <div className="table-primary">
          <strong>{row.name}</strong>
          <small className="font-mono text-blue-700 font-bold">{row.symbol} ({row.code})</small>
        </div>
      ),
    },
    {
      key: 'dimension',
      label: 'Dimensión',
      render: (row) => (
        <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded font-bold text-slate-700">
          {row.dimension}
        </span>
      ),
    },
    {
      key: 'scope',
      label: 'Scope',
      render: (row) => row.scope,
    },
    {
      key: 'precision',
      label: 'Precisión Decimal',
      render: (row) => `${row.decimal_precision} decimales`,
    },
    {
      key: 'status',
      label: 'Estado',
      render: (row) => (
        <StatusBadge value={row.status.toLowerCase()}>{row.status}</StatusBadge>
      ),
    },
  ]

  const ruleColumns: TableColumn<UnitConversionRule>[] = [
    {
      key: 'equivalence',
      label: 'Equivalencia Direccionada',
      render: (row) => (
        <span className="font-mono font-bold text-blue-800 text-xs">
          1 {row.source_unit_code} = {row.multiplier} {row.target_unit_code}
        </span>
      ),
    },
    {
      key: 'scope',
      label: 'Scope',
      render: (row) => row.scope,
    },
    {
      key: 'rounding',
      label: 'Política de Redondeo',
      render: (row) => (
        <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">
          {row.rounding_policy}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Estado',
      render: (row) => (
        <StatusBadge value={row.status.toLowerCase()}>{row.status}</StatusBadge>
      ),
    },
  ]

  return (
    <div className="page">
      <PageHeader
        eyebrow="Motor autoritativo de conversiones logísticas"
        title="Unidades de Medida y Conversiones"
        description="Catálogo maestro de unidades de medida, reglas de equivalencia exacta y motor de simulación backend."
      />

      {error && <Alert variant="error">{error}</Alert>}

      <section className="panel operations-section space-y-4">
        <div className="tabs border-b border-slate-200 pb-2 flex items-center gap-2">
          {[
            { id: 'units', label: 'Catálogo de Unidades' },
            { id: 'conversions', label: 'Reglas de Conversión' },
            { id: 'simulator', label: 'Simulador Autoritativo' },
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                activeTab === t.id
                  ? 'bg-blue-700 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
              onClick={() => setActiveTab(t.id as UnitsTab)}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="pt-2">
          {activeTab === 'units' && (
            <div className="space-y-3">
              {isLoading ? (
                <div className="loading-panel">
                  <span className="spinner" />
                  <p>Cargando unidades de medida…</p>
                </div>
              ) : (
                <>
                  <OperationsTable rows={unitsData.items} columns={unitColumns} getRowKey={(row) => row.id} />
                  <Pagination
                    page={unitsData.page}
                    totalPages={unitsData.total_pages}
                    total={unitsData.total}
                    onPageChange={() => {}}
                  />
                </>
              )}
            </div>
          )}

          {activeTab === 'conversions' && (
            <div className="space-y-3">
              {isLoading ? (
                <div className="loading-panel">
                  <span className="spinner" />
                  <p>Cargando reglas de conversión…</p>
                </div>
              ) : (
                <>
                  <OperationsTable rows={rulesData.items} columns={ruleColumns} getRowKey={(row) => row.id} />
                  <Pagination
                    page={rulesData.page}
                    totalPages={rulesData.total_pages}
                    total={rulesData.total}
                    onPageChange={() => {}}
                  />
                </>
              )}
            </div>
          )}

          {activeTab === 'simulator' && <UnitConversionSimulatorPanel />}
        </div>
      </section>
    </div>
  )
}
