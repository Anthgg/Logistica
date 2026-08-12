import React, { useState } from 'react';
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery';
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions';
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map';
import { getCsrfToken } from '../../../api/api-client';
import { Button } from '../../../components/common/Button';
import { Input } from '../../../components/common/Input';
import type {
  QualityTolerance,
  CreateQualityToleranceRequest,
  UnitOfMeasureSummary,
} from '../types/quality-inspection-plans';

interface QualityTolerancePreviewProps {
  tolerance: QualityTolerance | null;
}

const QualityTolerancePreview: React.FC<QualityTolerancePreviewProps> = ({ tolerance }) => {
  if (!tolerance) return null;

  const renderVisualRepresentation = () => {
    if (!tolerance.min_value || !tolerance.max_value || !tolerance.target_value) {
      return <div className="text-sm text-gray-500">Sin valores definidos</div>;
    }

    const min = parseFloat(tolerance.min_value);
    const max = parseFloat(tolerance.max_value);
    const target = parseFloat(tolerance.target_value);
    const range = max - min;
    const targetPosition = range > 0 ? ((target - min) / range) * 100 : 50;

    return (
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-gray-600">
          <span>Mín: {tolerance.min_value}</span>
          <span>Objetivo: {tolerance.target_value}</span>
          <span>Máx: {tolerance.max_value}</span>
        </div>
        <div className="relative h-4 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="absolute h-full bg-green-500 opacity-30"
            style={{
              left: 0,
              right: 0,
            }}
          />
          {tolerance.lower_deviation && tolerance.upper_deviation && (
            <div
              className="absolute h-full bg-yellow-500 opacity-30"
              style={{
                left: `${Math.max(0, targetPosition - (parseFloat(tolerance.upper_deviation) / range) * 100)}%`,
                width: `${((parseFloat(tolerance.upper_deviation) + parseFloat(tolerance.lower_deviation)) / range) * 100}%`,
              }}
            />
          )}
          <div
            className="absolute w-1 h-full bg-blue-600"
            style={{ left: `${targetPosition}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-500">
          <span>{tolerance.unit_name || 'N/A'}</span>
          <span>Escala: {tolerance.decimal_scale}</span>
          <span>Redondeo: {tolerance.rounding_mode}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      <h4 className="text-sm font-medium text-gray-700 mb-2">Vista previa de tolerancia</h4>
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Código:</span>
          <span className="text-sm font-medium">{tolerance.code}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Nombre:</span>
          <span className="text-sm">{tolerance.name}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Tipo:</span>
          <span className="text-sm capitalize">{tolerance.tolerance_type}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Dimensión:</span>
          <span className="text-sm capitalize">{tolerance.dimension}</span>
        </div>
        {renderVisualRepresentation()}
      </div>
    </div>
  );
};

const QualityTolerancesPage: React.FC = () => {
  const { hasPermission } = useLogisticsPermissions();
  const [showForm, setShowForm] = useState(false);
  const [editingTolerance, setEditingTolerance] = useState<QualityTolerance | null>(null);
  const [selectedTolerance, setSelectedTolerance] = useState<QualityTolerance | null>(null);
  const [formData, setFormData] = useState<any>({
    code: '',
    name: '',
    description: '',
    tolerance_type: 'absolute',
    dimension: 'quality',
    target_value: '',
    min_value: '',
    max_value: '',
    lower_deviation: '',
    upper_deviation: '',
    lower_percentage: '',
    upper_percentage: '',
    unit_id: '',
    inclusivity: 'inclusive',
    decimal_scale: '2',
    rounding_mode: 'round',
    valid_from: '',
    valid_until: '',
    status: 'active',
  });

  const { data: tolerances, isLoading, refetch } = useQuery<QualityTolerance[]>(
    ['quality-inspection-plans', 'tolerances'],
    '/logistics/quality-inspection-plans/tolerances/',
  );

  const { data: units } = useQuery<UnitOfMeasureSummary[]>(
    ['quality-inspection-plans', 'units'],
    '/logistics/quality-inspection-plans/units/',
  );

  const createMutation = useMutation<CreateQualityToleranceRequest, QualityTolerance>(
    async (input) => {
      // Dummy fetch
      return input as unknown as QualityTolerance;
    },
    {
      onSuccess: () => {
        void refetch();
        setShowForm(false);
        resetForm();
      },
    }
  );

  const updateMutation = useMutation<Partial<CreateQualityToleranceRequest>, QualityTolerance>(
    async (input) => {
      return input as unknown as QualityTolerance;
    },
    {
      onSuccess: () => {
        void refetch();
        setShowForm(false);
        setEditingTolerance(null);
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
        setEditingTolerance(null);
      },
    }
  );

  const resetForm = () => {
    setFormData({
      code: '',
      name: '',
      description: '',
      tolerance_type: 'absolute',
      dimension: 'quality',
      target_value: '',
      min_value: '',
      max_value: '',
      lower_deviation: '',
      upper_deviation: '',
      lower_percentage: '',
      upper_percentage: '',
      unit_id: '',
      inclusivity: 'inclusive',
      decimal_scale: '2',
      rounding_mode: 'round',
      valid_from: '',
      valid_until: '',
      status: 'active',
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const csrfToken = await getCsrfToken();
    if (editingTolerance) {
      updateMutation.mutate({ ...formData, csrf_token: csrfToken });
    } else {
      createMutation.mutate({ ...formData, csrf_token: csrfToken });
    }
  };

  const handleEdit = (tolerance: QualityTolerance) => {
    setEditingTolerance(tolerance);
    setFormData({
      code: tolerance.code,
      name: tolerance.name,
      description: tolerance.description || '',
      tolerance_type: tolerance.tolerance_type,
      dimension: tolerance.dimension,
      target_value: tolerance.target_value || '',
      min_value: tolerance.min_value || '',
      max_value: tolerance.max_value || '',
      lower_deviation: tolerance.lower_deviation || '',
      upper_deviation: tolerance.upper_deviation || '',
      lower_percentage: tolerance.lower_percentage || '',
      upper_percentage: tolerance.upper_percentage || '',
      unit_id: tolerance.unit_id || '',
      inclusivity: tolerance.inclusivity,
      decimal_scale: tolerance.decimal_scale || '2',
      rounding_mode: tolerance.rounding_mode || 'round',
      valid_from: tolerance.valid_from || '',
      valid_until: tolerance.valid_until || '',
      status: tolerance.status,
    });
    setSelectedTolerance(tolerance);
    setShowForm(true);
  };

  const handleDelete = async () => {
    if (editingTolerance && window.confirm('¿Está seguro de eliminar esta tolerancia?')) {
      const csrfToken = await getCsrfToken();
      deleteMutation.mutate({ csrf_token: csrfToken } as any);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData((prev: any) => ({ ...prev, [field]: value }));
  };

  if (!hasPermission(LOGISTICS_PERMISSIONS.quarantine.recordControlResult)) {
    return (
      <div className="p-4 text-center text-gray-500">
        No tiene permisos para acceder a esta sección
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Tolerancias de calidad</h1>
        <Button
          onClick={() => {
            resetForm();
            setEditingTolerance(null);
            setSelectedTolerance(null);
            setShowForm(true);
          }}
        >
          Nueva tolerancia
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
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dimensión</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Objetivo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mín</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Máx</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unidad</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {tolerances?.map((tolerance) => (
                <tr key={tolerance.tolerance_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{tolerance.code}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{tolerance.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 capitalize">{tolerance.tolerance_type}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 capitalize">{tolerance.dimension}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{tolerance.target_value || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{tolerance.min_value || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{tolerance.max_value || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{tolerance.unit_name || '-'}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      tolerance.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {tolerance.status === 'ACTIVE' ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <Button
                      variant="secondary"
                      size="small"
                      onClick={() => handleEdit(tolerance)}
                    >
                      Editar
                    </Button>
                  </td>
                </tr>
              ))}
              {(!tolerances || tolerances.length === 0) && (
                <tr>
                  <td colSpan={10} className="px-4 py-8 text-center text-gray-500">
                    No hay tolerancias configuradas
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
                {editingTolerance ? 'Editar tolerancia' : 'Nueva tolerancia'}
              </h2>
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Código</label>
                    <Input label=""
                      value={formData.code}
                      onChange={(e) => handleChange('code', e.target.value)}
                      placeholder="Ej: TOL-001"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                    <Input label=""
                      value={formData.name}
                      onChange={(e) => handleChange('name', e.target.value)}
                      placeholder="Nombre de la tolerancia"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
                    <Input label=""
                      value={formData.description}
                      onChange={(e) => handleChange('description', e.target.value)}
                      placeholder="Descripción opcional"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                    <select
                      value={formData.tolerance_type}
                      onChange={(e) => handleChange('tolerance_type', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="absolute">Absoluto</option>
                      <option value="relative">Relativo</option>
                      <option value="percentage">Porcentaje</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Dimensión</label>
                    <select
                      value={formData.dimension}
                      onChange={(e) => handleChange('dimension', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="quality">Calidad</option>
                      <option value="weight">Peso</option>
                      <option value="dimensions">Dimensiones</option>
                      <option value="temperature">Temperatura</option>
                      <option value="time">Tiempo</option>
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
                        <option key={unit.unit_id} value={unit.unit_id}>
                          {unit.name} ({unit.symbol})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Valor objetivo</label>
                    <Input label=""
                      value={formData.target_value}
                      onChange={(e) => handleChange('target_value', e.target.value)}
                      placeholder="Ej: 100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Valor mínimo</label>
                    <Input label=""
                      value={formData.min_value}
                      onChange={(e) => handleChange('min_value', e.target.value)}
                      placeholder="Ej: 90"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Valor máximo</label>
                    <Input label=""
                      value={formData.max_value}
                      onChange={(e) => handleChange('max_value', e.target.value)}
                      placeholder="Ej: 110"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Desviación inferior</label>
                    <Input label=""
                      value={formData.lower_deviation}
                      onChange={(e) => handleChange('lower_deviation', e.target.value)}
                      placeholder="Ej: 5"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Desviación superior</label>
                    <Input label=""
                      value={formData.upper_deviation}
                      onChange={(e) => handleChange('upper_deviation', e.target.value)}
                      placeholder="Ej: 5"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Porcentaje inferior (%)</label>
                    <Input label=""
                      value={formData.lower_percentage}
                      onChange={(e) => handleChange('lower_percentage', e.target.value)}
                      placeholder="Ej: 10"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Porcentaje superior (%)</label>
                    <Input label=""
                      value={formData.upper_percentage}
                      onChange={(e) => handleChange('upper_percentage', e.target.value)}
                      placeholder="Ej: 10"
                    />
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-4 gap-4 mt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Inclusividad</label>
                  <select
                    value={formData.inclusivity}
                    onChange={(e) => handleChange('inclusivity', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="inclusive">Inclusivo</option>
                    <option value="exclusive">Exclusivo</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Escala decimal</label>
                  <Input label=""
                    value={formData.decimal_scale}
                    onChange={(e) => handleChange('decimal_scale', e.target.value)}
                    placeholder="2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Modo de redondeo</label>
                  <select
                    value={formData.rounding_mode}
                    onChange={(e) => handleChange('rounding_mode', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="round">Redondear</option>
                    <option value="floor">Truncar</option>
                    <option value="ceil">Redondear hacia arriba</option>
                  </select>
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
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Válido desde</label>
                  <Input label=""
                    type="date"
                    value={formData.valid_from}
                    onChange={(e) => handleChange('valid_from', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Válido hasta</label>
                  <Input label=""
                    type="date"
                    value={formData.valid_until}
                    onChange={(e) => handleChange('valid_until', e.target.value)}
                  />
                </div>
              </div>

              <div className="mt-6">
                <QualityTolerancePreview tolerance={selectedTolerance} />
              </div>

              <div className="flex justify-end gap-3 mt-6">
                {editingTolerance && (
                  <Button variant="danger" onClick={handleDelete}>
                    Eliminar
                  </Button>
                )}
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowForm(false);
                    setEditingTolerance(null);
                    setSelectedTolerance(null);
                  }}
                >
                  Cancelar
                </Button>
                <Button onClick={handleSubmit}>
                  {editingTolerance ? 'Guardar cambios' : 'Crear tolerancia'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QualityTolerancesPage;

export { QualityTolerancesPage }
