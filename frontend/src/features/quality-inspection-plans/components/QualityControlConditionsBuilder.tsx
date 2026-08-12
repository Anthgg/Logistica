import React, { useState } from 'react';
import { useMutation } from '../../inbound-docks/hooks/useQuery';
import { getCsrfToken, apiRequest } from '../../../api/api-client';
import { Button } from '../../../components/common/Button';
import { Input } from '../../../components/common/Input';
import type { QualityControlCondition } from '../types/quality-inspection-plans';

interface QualityControlConditionsBuilderProps {
  controlId: string;
  conditions: QualityControlCondition[];
  onRefresh: () => void;
}

const QualityControlConditionsBuilder: React.FC<QualityControlConditionsBuilderProps> = ({
  controlId,
  conditions,
  onRefresh,
}) => {
  const [showForm, setShowForm] = useState(false);
  const [editingCondition, setEditingCondition] = useState<QualityControlCondition | null>(null);
  const EMPTY_CONDITION = {
    condition_field: '',
    operator: 'EQUALS',
    value: '',
    display_order: '0',
  };
  const [formData, setFormData] = useState(EMPTY_CONDITION);

  const operators = [
    { value: 'EQUALS', label: 'Igual a' },
    { value: 'NOT_EQUALS', label: 'No igual a' },
    { value: 'IN_LIST', label: 'En lista' },
    { value: 'NOT_IN_LIST', label: 'No en lista' },
    { value: 'GREATER_THAN', label: 'Mayor que' },
    { value: 'LESS_THAN', label: 'Menor que' },
    { value: 'GREATER_THAN_OR_EQUALS', label: 'Mayor o igual que' },
    { value: 'LESS_THAN_OR_EQUALS', label: 'Menor o igual que' },
    { value: 'CONTAINS', label: 'Contiene' },
    { value: 'NOT_CONTAINS', label: 'No contiene' },
    { value: 'STARTS_WITH', label: 'Comienza con' },
    { value: 'ENDS_WITH', label: 'Termina con' },
    { value: 'IS_EMPTY', label: 'Está vacío' },
    { value: 'IS_NOT_EMPTY', label: 'No está vacío' },
    { value: 'BETWEEN', label: 'Entre' },
    { value: 'NOT_BETWEEN', label: 'No entre' },
  ];

  const createMutation = useMutation<any, QualityControlCondition>(
    async (input) => {
      const csrf = await getCsrfToken();
      return apiRequest({
        path: '/logistics/quality/conditions',
        method: 'POST',
        body: input,
        headers: { 'X-CSRF-Token': csrf }
      });
    },
    {
      onSuccess: () => {
        onRefresh();
        setShowForm(false);
        setFormData(EMPTY_CONDITION);
      },
    }
  );

  const updateMutation = useMutation<any, QualityControlCondition>(
    async (input) => {
      const csrf = await getCsrfToken();
      return apiRequest({
        path: editingCondition ? `/logistics/quality/conditions/${editingCondition.condition_id}` : '/logistics/quality/conditions',
        method: 'PUT',
        body: input,
        headers: { 'X-CSRF-Token': csrf }
      });
    },
    {
      onSuccess: () => {
        onRefresh();
        setShowForm(false);
        setEditingCondition(null);
      },
    }
  );

  const deleteMutation = useMutation<{ condition_id: string }, void>(
    async (input) => {
      const csrf = await getCsrfToken();
      return apiRequest({
        path: `/api/quality-inspection-plans/conditions/${input.condition_id}/`,
        method: 'DELETE',
        headers: { 'X-CSRF-Token': csrf }
      });
    },
    {
      onSuccess: () => {
        onRefresh();
        setShowForm(false);
        setEditingCondition(null);
      },
    }
  );

  const resetForm = () => {
    setFormData({
      condition_field: '',
      operator: 'EQUALS',
      value: '',
      display_order: '0',
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editingCondition) {
      updateMutation.mutate({ ...formData });
    } else {
      createMutation.mutate({ ...formData, control_id: controlId });
    }
  };

  const handleEdit = (condition: QualityControlCondition) => {
    setEditingCondition(condition);
    setFormData({
      condition_field: condition.condition_field,
      operator: condition.operator,
      value: condition.value || '',
      display_order: condition.display_order?.toString() || '0',
    });
    setShowForm(true);
  };

  const handleDelete = async () => {
    if (editingCondition && window.confirm('¿Está seguro de eliminar esta condición?')) {
      deleteMutation.mutate({ condition_id: editingCondition.condition_id });
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const getOperatorLabel = (operator: string) => {
    return operators.find((op) => op.value === operator)?.label || operator;
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">Condiciones del control</h3>
        <Button
          onClick={() => {
            resetForm();
            setEditingCondition(null);
            setShowForm(true);
          }}
        >
          Nueva condición
        </Button>
      </div>

      <div className="space-y-3">
        {conditions.map((condition) => (
          <div
            key={condition.condition_id}
            className="border rounded-lg p-4 flex justify-between items-start hover:bg-gray-50"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">#{condition.display_order}</span>
                <span className="font-medium text-gray-900">{condition.condition_field}</span>
                <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded">
                  {getOperatorLabel(condition.operator)}
                </span>
                {condition.value && (
                  <span className="text-gray-700">{condition.value}</span>
                )}
              </div>
            </div>
            <Button
              variant="secondary"
              size="small"
              onClick={() => handleEdit(condition)}
            >
              Editar
            </Button>
          </div>
        ))}
        {conditions.length === 0 && (
          <div className="text-center py-8 text-gray-500 border rounded-lg">
            No hay condiciones configuradas para este control
          </div>
        )}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                {editingCondition ? 'Editar condición' : 'Nueva condición'}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Input
                    label="Campo de condición"
                    value={formData.condition_field}
                    onChange={(e: any) => handleChange('condition_field', e.target.value)}
                    placeholder="Ej: supplier_type"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Operador</label>
                  <select
                    value={formData.operator}
                    onChange={(e: any) => handleChange('operator', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    {operators.map((op) => (
                      <option key={op.value} value={op.value}>{op.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <Input
                    label="Valor"
                    value={formData.value}
                    onChange={(e: any) => handleChange('value', e.target.value)}
                    placeholder="Valor de la condición"
                  />
                </div>

                <div>
                  <Input
                    label="Orden de visualización"
                    type="number"
                    value={formData.display_order}
                    onChange={(e: any) => handleChange('display_order', e.target.value)}
                    placeholder="0"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  {editingCondition && (
                    <Button type="button" variant="danger" onClick={handleDelete}>
                      Eliminar
                    </Button>
                  )}
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      setShowForm(false);
                      setEditingCondition(null);
                    }}
                  >
                    Cancelar
                  </Button>
                  <Button type="submit">
                    {editingCondition ? 'Guardar cambios' : 'Crear condición'}
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

export default QualityControlConditionsBuilder;
