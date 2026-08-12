import React, { useState } from 'react';
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery';
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions';
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map';
import { getCsrfToken } from '../../../api/api-client';
import { Button } from '../../../components/common/Button';
import { Input } from '../../../components/common/Input';
import type {
  QualitySamplingPlan,
  CreateQualitySamplingPlanRequest,
  UnitOfMeasureSummary,
} from '../types/quality-inspection-plans';

interface QualitySampleSizePreviewPanelProps {
  formData: any;
}

const QualitySampleSizePreviewPanel: React.FC<QualitySampleSizePreviewPanelProps> = ({ formData }) => {
  const [populationSize, setPopulationSize] = useState<string>('');

  const calculateSampleSize = () => {
    if (!populationSize || populationSize === '') return null;
    const popSize = parseInt(populationSize, 10);
    if (isNaN(popSize) || popSize <= 0) return null;

    let sampleSize = 0;

    if (formData.sampling_method === 'fixed') {
      sampleSize = parseInt(formData.fixed_sample_size || '0', 10);
    } else if (formData.sampling_method === 'percentage') {
      const percentage = parseFloat(formData.sampling_percentage || '0');
      sampleSize = Math.ceil((popSize * percentage) / 100);
    } else if (formData.sampling_method === 'min_max') {
      const percentage = parseFloat(formData.sampling_percentage || '0');
      const min = parseInt(formData.min_sample_size || '0', 10);
      const max = parseInt(formData.max_sample_size || '0', 10);
      sampleSize = Math.ceil((popSize * percentage) / 100);
      if (sampleSize < min) sampleSize = min;
      if (sampleSize > max) sampleSize = max;
    }

    return sampleSize;
  };

  const calculatedSize = calculateSampleSize();

  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-gray-700">Vista previa de tamaño de muestra</h4>
        <span className="text-xs text-gray-400 bg-yellow-50 px-2 py-1 rounded">
          Cálculo orientativo. No selecciona unidades físicas.
        </span>
      </div>
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Tamaño de población:</label>
          <Input
            label="Tamaño de población:"
            value={populationSize}
            onChange={(e) => setPopulationSize(e.target.value)}
            placeholder="Ej: 1000"
            className="w-32"
          />
        </div>
        {calculatedSize !== null && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Muestra calculada:</span>
            <span className="text-lg font-semibold text-blue-600">{calculatedSize}</span>
            <span className="text-sm text-gray-500">unidades</span>
          </div>
        )}
        <div className="text-xs text-gray-500">
          Método: {formData.sampling_method === 'fixed' ? 'Fijo' :
            formData.sampling_method === 'percentage' ? 'Porcentaje' :
            'Mín-Máx'}
        </div>
      </div>
    </div>
  );
};

const QualitySamplingPlansPage: React.FC = () => {
  const { hasPermission } = useLogisticsPermissions();
  const [showForm, setShowForm] = useState(false);
  const [editingPlan, setEditingPlan] = useState<QualitySamplingPlan | null>(null);
  const [formData, setFormData] = useState<any>({
    code: '',
    name: '',
    description: '',
    sampling_type: 'random',
    sampling_method: 'fixed',
    fixed_sample_size: '',
    sampling_percentage: '',
    min_sample_size: '',
    max_sample_size: '',
    unit_id: '',
    status: 'active',
  });

  const { data: plans, isLoading, refetch } = useQuery<QualitySamplingPlan[]>(
    ['quality-inspection-plans', 'sampling-plans'],
    '/logistics/quality-inspection-plans/sampling-plans/',
  );

  const { data: units } = useQuery<UnitOfMeasureSummary[]>(
    ['quality-inspection-plans', 'units'],
    '/logistics/quality-inspection-plans/units/',
  );

  const createMutation = useMutation<CreateQualitySamplingPlanRequest, QualitySamplingPlan>(
    async (input) => {
      return input as unknown as QualitySamplingPlan;
    },
    {
      onSuccess: () => {
        void refetch();
        setShowForm(false);
        resetForm();
      },
    }
  );

  const updateMutation = useMutation<Partial<CreateQualitySamplingPlanRequest>, QualitySamplingPlan>(
    async (input) => {
      return input as unknown as QualitySamplingPlan;
    },
    {
      onSuccess: () => {
        void refetch();
        setShowForm(false);
        setEditingPlan(null);
        resetForm();
      },
    }
  );

  const deleteMutation = useMutation<void, void>(
    async () => {
      // Dummy
    },
    {
      onSuccess: () => {
        void refetch();
        setEditingPlan(null);
      },
    }
  );

  const resetForm = () => {
    setFormData({
      code: '',
      name: '',
      description: '',
      sampling_type: 'FIXED',
      sample_unit: 'UNITS',
      fixed_quantity: '',
      percentage: '',
      minimum: '',
      maximum: '',
      rounding_mode: 'HALF_UP',
      selection_method: 'RANDOM',
    } as any);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const csrfToken = await getCsrfToken();
    if (editingPlan) {
      updateMutation.mutate({ ...formData, csrf_token: csrfToken });
    } else {
      createMutation.mutate({ ...formData, csrf_token: csrfToken });
    }
  };

  const handleEdit = (plan: QualitySamplingPlan) => {
    setEditingPlan(plan);
    setFormData({
      code: plan.code,
      name: plan.name,
      description: plan.description || '',
      sampling_type: plan.sampling_type,
      sample_unit: plan.sample_unit,
      fixed_quantity: plan.fixed_quantity || '',
      percentage: plan.percentage || '',
      minimum: plan.minimum || '',
      maximum: plan.maximum || '',
      rounding_mode: plan.rounding_mode,
      selection_method: plan.selection_method,
    } as any);
    setShowForm(true);
  };

  const handleDelete = async () => {
    if (editingPlan && window.confirm('¿Está seguro de eliminar este plan de muestreo?')) {
      const csrfToken = await getCsrfToken();
      deleteMutation.mutate({ csrf_token: csrfToken } as any);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData((prev: any) => ({ ...prev, [field]: value }));
  };

  if (!hasPermission(LOGISTICS_PERMISSIONS.qualitySamplingPlans.create)) {
    return (
      <div className="p-4 text-center text-gray-500">
        No tiene permisos para acceder a esta sección
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Planes de muestreo</h1>
        <Button
          onClick={() => {
            resetForm();
            setEditingPlan(null);
            setShowForm(true);
          }}
        >
          Nuevo plan
        </Button>
      </div>

      {isLoading ? (
        <div className="text-center py-8 text-gray-500">Cargando...</div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unidad</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fijo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Porcentaje</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mín</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Máx</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Método</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {plans?.map((plan) => (
                <tr key={plan.sampling_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{plan.code}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{plan.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 capitalize">{plan.sampling_type}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{plan.sample_unit || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{plan.fixed_quantity || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{plan.percentage || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{plan.minimum || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{plan.maximum || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 capitalize">{plan.selection_method}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      plan.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {plan.status === 'ACTIVE' ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <Button
                      variant="secondary"
                      size="small"
                      onClick={() => handleEdit(plan)}
                    >
                      Editar
                    </Button>
                  </td>
                </tr>
              ))}
              {(!plans || plans.length === 0) && (
                <tr>
                  <td colSpan={11} className="px-4 py-8 text-center text-gray-500">
                    No hay planes de muestreo configurados
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                {editingPlan ? 'Editar plan de muestreo' : 'Nuevo plan de muestreo'}
              </h2>
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Código</label>
                    <Input
                      label=""
                      value={formData.code}
                      onChange={(e) => handleChange('code', e.target.value)}
                      placeholder="Ej: SMP-001"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                    <Input
                      label=""
                      value={formData.name}
                      onChange={(e) => handleChange('name', e.target.value)}
                      placeholder="Nombre del plan"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
                    <Input
                      label=""
                      value={formData.description}
                      onChange={(e) => handleChange('description', e.target.value)}
                      placeholder="Descripción opcional"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de muestreo</label>
                    <select
                      value={formData.sampling_type}
                      onChange={(e) => handleChange('sampling_type', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="random">Aleatorio</option>
                      <option value="systematic">Sistemático</option>
                      <option value="stratified">Estratificado</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Unidad</label>
                    <select
                      value={formData.unit_id}
                      onChange={(e) => handleChange('unit_id', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="">Seleccionar unidad</option>
                      {units?.map((unit) => (
                        <option key={unit.unit_id} value={unit.unit_id}>{unit.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Método de muestreo</label>
                    <select
                      value={formData.sampling_method}
                      onChange={(e) => handleChange('sampling_method', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="fixed">Fijo</option>
                      <option value="percentage">Porcentaje</option>
                      <option value="min_max">Mín-Máx</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tamaño fijo</label>
                    <Input label=""
                      value={formData.fixed_sample_size}
                      onChange={(e) => handleChange('fixed_sample_size', e.target.value)}
                      placeholder="Ej: 50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Porcentaje (%)</label>
                    <Input label=""
                      value={formData.sampling_percentage}
                      onChange={(e) => handleChange('sampling_percentage', e.target.value)}
                      placeholder="Ej: 10"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Mínimo</label>
                    <Input label=""
                      value={formData.min_sample_size}
                      onChange={(e) => handleChange('min_sample_size', e.target.value)}
                      placeholder="Ej: 5"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Máximo</label>
                    <Input label=""
                      value={formData.max_sample_size}
                      onChange={(e) => handleChange('max_sample_size', e.target.value)}
                      placeholder="Ej: 100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                    <select
                      value={formData.status}
                      onChange={(e) => handleChange('status', e.target.value as 'active' | 'inactive')}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="active">Activo</option>
                      <option value="inactive">Inactivo</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <QualitySampleSizePreviewPanel formData={formData} />
              </div>

              <div className="flex justify-end gap-3 mt-6">
                {editingPlan && (
                  <Button variant="danger" onClick={handleDelete}>
                    Eliminar
                  </Button>
                )}
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowForm(false);
                    setEditingPlan(null);
                  }}
                >
                  Cancelar
                </Button>
                <Button onClick={handleSubmit}>
                  {editingPlan ? 'Guardar cambios' : 'Crear plan'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QualitySamplingPlansPage;

export { QualitySamplingPlansPage }
