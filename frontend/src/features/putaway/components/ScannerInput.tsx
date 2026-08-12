import { useState } from 'react'
import { Button } from '../../../components/common/Button'
import type { MobileScanResult } from '../types/putaway'
import { putawayMobileApi } from '../api/putawayMobileApi'

interface Props {
  onScan?: (result: MobileScanResult) => void
  context?: { order_id?: string; task_id?: string }
}

export function ScannerInput({ onScan, context }: Props) {
  const [code, setCode] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [lastResult, setLastResult] = useState<MobileScanResult | null>(null)

  const handleScan = async () => {
    if (!code.trim() || isProcessing) return
    setIsProcessing(true)
    try {
      const result = await putawayMobileApi.scanCode(code, context) as MobileScanResult
      setLastResult(result)
      onScan?.(result)
      setCode('')
    } catch {
      setLastResult(null)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleScan()}
          placeholder="Escanea o escribe un código..."
          className="flex-1 px-4 py-3 text-lg border rounded-lg"
          autoFocus
          disabled={isProcessing}
        />
        <Button onClick={handleScan} disabled={isProcessing || !code.trim()} className="px-6">
          {isProcessing ? '...' : 'Escanear'}
        </Button>
      </div>
      {lastResult && (
        <div className={`text-sm ${lastResult.is_valid ? 'text-green-600' : 'text-red-600'}`}>
          {lastResult.is_valid ? '✓' : '✗'} {lastResult.code} — {lastResult.matched_entity_type}
        </div>
      )}
    </div>
  )
}
