import React, { useState } from 'react';
import { apiRequest, getCsrfToken } from '../../../api/api-client';
import { Button } from '../../../components/common/Button';
import { Input } from '../../../components/common/Input';
import { useMutation } from '../../inbound-docks/hooks/useQuery';
import type { QualityCertificateRequirement } from '../types/quality-inspection-plans';

interface QualityCertificateRequirementsEditorProps {
  versionId: string;
  requirements: QualityCertificateRequirement[];
  onRefresh: () => void;
}

const QualityCertificateRequirementsEditor: React.FC<QualityCertificateRequirementsEditorProps> = ({
  versionId,
  requirements,
  onRefresh,
}) => {
  const [showForm, setShowForm] = useState(false);
  const [editingRequirement, setEditingRequirement] = useState<QualityCertificateRequirement | null>(null);
  
  const EMPTY_FORM = {
    code: '',
    name: '',
    description: '',
    document_type_id: '',
    accepted_types: [] as string[],
    required: true,
    issuer_pattern: '',
    issue_date_required: true,
    expiration_required: false,
    minimum_validity_days: '',
    reference_number_required: false,
    file_required: true,
    metadata_validation: '',
    external_validation: '',
    instructions: '',
  };

  const [formData, setFormData] = useState(EMPTY_FORM);

  const createMutation = useMutation<any, QualityCertificateRequirement>(
    async (input) => {
      const csrf = await getCsrfToken();
      return apiRequest({
        path: '/api/quality-inspection-plans/certificate-requirements/',
        method: 'POST',
        body: input,
        headers: { 'X-CSRF-Token': csrf }
      });
    },
    {
      onSuccess: () => {
        onRefresh();
        setShowForm(false);
        setFormData(EMPTY_FORM);
      },
    }
  );

  const updateMutation = useMutation<any, QualityCertificateRequirement>(
    async (input) => {
      const csrf = await getCsrfToken();
      return apiRequest({
        path: `/api/quality-inspection-plans/certificate-requirements/${editingRequirement?.requirement_id}/`,
        method: 'PUT',
        body: input,
        headers: { 'X-CSRF-Token': csrf }
      });
    },
    {
      onSuccess: () => {
        onRefresh();
        setShowForm(false);
        setEditingRequirement(null);
      },
    }
  );

  const deleteMutation = useMutation<{ requirement_id: string }, void>(
    async (input) => {
      const csrf = await getCsrfToken();
      return apiRequest({
        path: `/api/quality-inspection-plans/certificate-requirements/${input.requirement_id}/`,
        method: 'DELETE',
        headers: { 'X-CSRF-Token': csrf }
      });
    },
    {
      onSuccess: () => {
        onRefresh();
        setShowForm(false);
        setEditingRequirement(null);
      },
    }
  );

  const resetForm = () => {
    setFormData(EMPTY_FORM);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editingRequirement) {
      updateMutation.mutate({ ...formData });
    } else {
      createMutation.mutate({ ...formData, version_id: versionId });
    }
  };

  const handleEdit = (requirement: QualityCertificateRequirement) => {
    setEditingRequirement(requirement);
    setFormData({
      code: requirement.code,
      name: requirement.name,
      description: requirement.description || '',
      document_type_id: requirement.document_type_id || '',
      accepted_types: requirement.accepted_types || [],
      required: requirement.required,
      issuer_pattern: requirement.issuer_pattern || '',
      issue_date_required: requirement.issue_date_required,
      expiration_required: requirement.expiration_required,
      minimum_validity_days: requirement.minimum_validity_days?.toString() || '',
      reference_number_required: requirement.reference_number_required,
      file_required: requirement.file_required,
      metadata_validation: requirement.metadata_validation || '',
      external_validation: requirement.external_validation || '',
      instructions: requirement.instructions || '',
    });
    setShowForm(true);
  };

  const handleDelete = async () => {
    if (editingRequirement && window.confirm('¿Está seguro de eliminar este requisito?')) {
      deleteMutation.mutate({ requirement_id: editingRequirement.requirement_id });
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: String(value) }));
  };

  const handleToggleItem = (field: string, item: string, checked: boolean) => {
    setFormData((prev: any) => ({
      ...prev,
      [field]: checked 
        ? [...prev[field], item] 
        : prev[field].filter((i: string) => i !== item)
    }));
  };

  const acceptedTypeOptions = [
    { value: 'pdf', label: 'PDF' },
    { value: 'image', label: 'Imagen' },
    { value: 'document', label: 'Documento' },
    { value: 'spreadsheet', label: 'Hoja de cálculo' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">Requisitos de certificados</h3>
        <Button
          onClick={() => {
            resetForm();
            setEditingRequirement(null);
            setShowForm(true);
          }}
        >
          Nuevo requisito
        </Button>
      </div>

      <div className="space-y-3">
        {requirements.map((req) => (
          <div
            key={req.requirement_id}
            className="border rounded-lg p-4 flex justify-between items-start hover:bg-gray-50"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900">{req.name}</span>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">{req.document_type_id}</span>
                {req.required && (
                  <span className="px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded-full">
                    Requerido
                  </span>
                )}
              </div>
              {req.description && (
                <p className="text-sm text-gray-500">{req.description}</p>
              )}
              <div className="flex gap-4 text-xs text-gray-500">
                <span>Tipos aceptados: {req.accepted_types?.join(', ') || 'N/A'}</span>
                {req.issuer_pattern && <span>Emisor: {req.issuer_pattern}</span>}
              </div>
            </div>
            <Button
              variant="secondary"
              size="small"
              onClick={() => handleEdit(req)}
            >
              Editar
            </Button>
          </div>
        ))}
        {requirements.length === 0 && (
          <div className="text-center py-8 text-gray-500 border rounded-lg">
            No hay requisitos de certificados configurados
          </div>
        )}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                {editingRequirement ? 'Editar requisito' : 'Nuevo requisito'}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Input
                      label="Código"
                      value={formData.code}
                      onChange={(e: any) => handleChange('code', e.target.value)}
                      placeholder="Ej: CERT-001"
                    />
                  </div>
                  <div>
                    <Input
                      label="Nombre"
                      value={formData.name}
                      onChange={(e: any) => handleChange('name', e.target.value)}
                      placeholder="Nombre del requisito"
                    />
                  </div>
                </div>

                <div>
                  <Input
                    label="Descripción"
                    value={formData.description}
                    onChange={(e: any) => handleChange('description', e.target.value)}
                    placeholder="Descripción del requisito"
                  />
                </div>

                <div>
                  <Input
                    label="Tipo de documento"
                    value={formData.document_type_id}
                    onChange={(e: any) => handleChange('document_type_id', e.target.value)}
                    placeholder="ID del tipo de documento"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Tipos aceptados</label>
                  <div className="flex flex-wrap gap-2">
                    {acceptedTypeOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => handleToggleItem('accepted_types', option.value, !formData.accepted_types.includes(option.value))}
                        className={`px-3 py-1 rounded-full text-sm border ${
                          formData.accepted_types.includes(option.value)
                            ? 'bg-blue-100 border-blue-500 text-blue-800'
                            : 'bg-gray-100 border-gray-300 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="required"
                      checked={formData.required}
                      onChange={(e) => handleChange('required', e.target.checked)}
                      className="h-4 w-4 text-blue-600"
                    />
                    <label htmlFor="required" className="text-sm text-gray-700">Requerido</label>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="file_required"
                      checked={formData.file_required}
                      onChange={(e: any) => handleChange('file_required', e.target.checked)}
                      className="h-4 w-4 text-blue-600"
                    />
                    <label htmlFor="file_required" className="text-sm text-gray-700">Archivo requerido</label>
                  </div>
                </div>

                <div>
                  <Input
                    label="Patrón de emisor"
                    value={formData.issuer_pattern}
                    onChange={(e: any) => handleChange('issuer_pattern', e.target.value)}
                    placeholder="Ej: ISO.*"
                  />
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="issue_date_required"
                      checked={formData.issue_date_required}
                      onChange={(e) => handleChange('issue_date_required', e.target.checked)}
                      className="h-4 w-4 text-blue-600"
                    />
                    <label htmlFor="issue_date_required" className="text-sm text-gray-700">Fecha emisión requerida</label>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="expiration_required"
                      checked={formData.expiration_required}
                      onChange={(e) => handleChange('expiration_required', e.target.checked)}
                      className="h-4 w-4 text-blue-600"
                    />
                    <label htmlFor="expiration_required" className="text-sm text-gray-700">Expiración requerida</label>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="reference_number_required"
                      checked={formData.reference_number_required}
                      onChange={(e) => handleChange('reference_number_required', e.target.checked)}
                      className="h-4 w-4 text-blue-600"
                    />
                    <label htmlFor="reference_number_required" className="text-sm text-gray-700">Nº referencia requerido</label>
                  </div>
                </div>

                <div>
                  <Input
                    label="Días mínimos de validez"
                    type="number"
                    value={formData.minimum_validity_days}
                    onChange={(e: any) => handleChange('minimum_validity_days', e.target.value)}
                    placeholder="Ej: 30"
                  />
                </div>

                <div>
                  <Input
                    label="Validación de metadatos"
                    value={formData.metadata_validation}
                    onChange={(e: any) => handleChange('metadata_validation', e.target.value)}
                    placeholder="Expresión de validación"
                  />
                </div>

                <div>
                  <Input
                    label="Validación externa"
                    value={formData.external_validation}
                    onChange={(e: any) => handleChange('external_validation', e.target.value)}
                    placeholder="URL o servicio de validación"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Instrucciones</label>
                  <textarea
                    value={formData.instructions}
                    onChange={(e: any) => handleChange('instructions', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    rows={3}
                    placeholder="Instrucciones para el proveedor"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  {editingRequirement && (
                    <Button type="button" variant="danger" onClick={handleDelete}>
                      Eliminar
                    </Button>
                  )}
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      setShowForm(false);
                      setEditingRequirement(null);
                    }}
                  >
                    Cancelar
                  </Button>
                  <Button type="submit">
                    {editingRequirement ? 'Guardar cambios' : 'Crear requisito'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QualityCertificateRequirementsEditor;
