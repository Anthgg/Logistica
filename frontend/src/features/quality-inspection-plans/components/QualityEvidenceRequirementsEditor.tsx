import React from 'react';

interface QualityEvidenceRequirementsEditorProps {
  evidenceTypes: string[];
  onChange: (types: string[]) => void;
}

const evidenceTypeOptions = [
  { value: 'photography', label: 'Fotografía' },
  { value: 'document', label: 'Documento' },
  { value: 'device_reference', label: 'Referencia de dispositivo' },
  { value: 'certificate', label: 'Certificado' },
  { value: 'label_photo', label: 'Foto de etiqueta' },
  { value: 'packaging_photo', label: 'Foto de empaque' },
  { value: 'temperature_photo', label: 'Foto de temperatura' },
  { value: 'scale_photo', label: 'Foto de báscula' },
  { value: 'sample_reference', label: 'Referencia de muestra' },
  { value: 'comment', label: 'Comentario' },
  { value: 'other', label: 'Otro' },
];

const QualityEvidenceRequirementsEditor: React.FC<QualityEvidenceRequirementsEditorProps> = ({
  evidenceTypes,
  onChange,
}) => {
  const handleToggle = (type: string) => {
    if (evidenceTypes.includes(type)) {
      onChange(evidenceTypes.filter((t) => t !== type));
    } else {
      onChange([...evidenceTypes, type]);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">Tipos de evidencia requeridos</h3>
        <p className="text-sm text-gray-500">
          Se configura el requisito. La evidencia real se capturará durante una inspección futura.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {evidenceTypeOptions.map((option) => (
          <label
            key={option.value}
            className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
              evidenceTypes.includes(option.value)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <input
              type="checkbox"
              checked={evidenceTypes.includes(option.value)}
              onChange={() => handleToggle(option.value)}
              className="h-4 w-4 text-blue-600 rounded"
            />
            <span className="text-sm text-gray-700">{option.label}</span>
          </label>
        ))}
      </div>

      {evidenceTypes.length > 0 && (
        <div className="text-sm text-gray-500">
          {evidenceTypes.length} tipo(s) seleccionado(s)
        </div>
      )}
    </div>
  );
};

export default QualityEvidenceRequirementsEditor;
