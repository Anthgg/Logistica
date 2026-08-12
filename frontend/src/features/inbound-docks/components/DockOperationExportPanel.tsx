import { useState } from 'react'
import { Button } from '../../../components/common/Button'
import { SectionPanel } from './ui/Primitives'
import { DockOperationExportDialog } from './dialogs/DockOperationExportDialog'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

export function DockOperationExportPanel({
  defaultWarehouseId,
  defaultDockIds,
  defaultDateFrom,
  defaultDateTo,
}: {
  defaultWarehouseId?: string
  defaultDockIds?: string[]
  defaultDateFrom?: string
  defaultDateTo?: string
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canExport = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.export)
  const [open, setOpen] = useState(false)
  return (
    <SectionPanel
      title="Exportación operativa"
      description="CSV, XLSX o PDF operativo. No incluye productos recibidos."
      actions={
        <Button
          type="button"
          variant="primary"
          onClick={() => setOpen(true)}
          disabled={!canExport}
        >
          Nueva exportación
        </Button>
      }
    >
      <p className="text-xs text-slate-600">
        La exportación se ejecutará como un job en el backend. Recibirás un enlace con caducidad para la descarga.
        No se incluyen productos recibidos, lotes, series ni diferencias.
      </p>
      <DockOperationExportDialog
        open={open}
        onOpenChange={setOpen}
        defaultWarehouseId={defaultWarehouseId}
        defaultDockIds={defaultDockIds}
        defaultDateFrom={defaultDateFrom}
        defaultDateTo={defaultDateTo}
      />
    </SectionPanel>
  )
}
