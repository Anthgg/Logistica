import type { RotationComplianceReport } from '../types/putaway'

interface Props {
  report: RotationComplianceReport
}

export function RotationCompliancePanel({ report }: Props) {
  return (
    <div className="p-4 bg-white rounded-lg border space-y-3">
      <h3 className="text-sm font-medium text-gray-700">Cumplimiento de rotación</h3>
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-green-600">{report.fifo_compliant}</div>
          <div className="text-xs text-gray-500">FIFO conforme</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-blue-600">{report.fefo_compliant}</div>
          <div className="text-xs text-gray-500">FEFO conforme</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-red-600">{report.non_compliant}</div>
          <div className="text-xs text-gray-500">No conforme</div>
        </div>
      </div>
      <div className="text-center">
        <span className="text-sm text-gray-500">
          Cumplimiento: {report.compliance_percentage.value}% ({report.total_lines_evaluated} evaluadas)
        </span>
      </div>
      {report.violations.length > 0 && (
        <div className="space-y-1 mt-3">
          <div className="text-sm font-medium text-gray-700">Violaciones</div>
          {report.violations.slice(0, 5).map((v) => (
            <div key={v.line_id} className="text-xs text-gray-600 flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                v.severity === 'critical' ? 'bg-red-500' : v.severity === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
              }`} />
              <span>{v.product.sku} — {v.method} — {v.days_old} días</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
