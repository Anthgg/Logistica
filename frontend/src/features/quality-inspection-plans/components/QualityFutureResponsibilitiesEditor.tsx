import React from 'react';

interface QualityFutureResponsibilitiesEditorProps {
  responsibilities: string[];
  onChange: (roles: string[]) => void;
}

const responsibilityOptions = [
  { value: 'quality_operator', label: 'Operador de calidad' },
  { value: 'quality_supervisor', label: 'Supervisor de calidad' },
  { value: 'reception_operator', label: 'Operador de recepción' },
  { value: 'warehouse_supervisor', label: 'Supervisor de almacén' },
  { value: 'document_reviewer', label: 'Revisor de documentos' },
  { value: 'security_reviewer', label: 'Revisor de seguridad' },
  { value: 'other', label: 'Otro' },
];

const QualityFutureResponsibilitiesEditor: React.FC<QualityFutureResponsibilitiesEditorProps> = ({
  responsibilities,
  onChange,
}) => {
  const handleToggle = (role: string) => {
    if (responsibilities.includes(role)) {
      onChange(responsibilities.filter((r) => r !== role));
    } else {
      onChange([...responsibilities, role]);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">Roles futuros</h3>
        <p className="text-sm text-gray-500">
          Seleccione los roles que tendrán responsabilidad en futuras inspecciones.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {responsibilityOptions.map((option) => (
          <label
            key={option.value}
            className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
              responsibilities.includes(option.value)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <input
              type="checkbox"
              checked={responsibilities.includes(option.value)}
              onChange={() => handleToggle(option.value)}
              className="h-4 w-4 text-blue-600 rounded"
            />
            <span className="text-sm text-gray-700">{option.label}</span>
          </label>
        ))}
      </div>

      {responsibilities.length > 0 && (
        <div className="text-sm text-gray-500">
          {responsibilities.length} rol(es) seleccionado(s)
        </div>
      )}
    </div>
  );
};

export default QualityFutureResponsibilitiesEditor;
