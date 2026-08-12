import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { InstitutionalDocumentPreview } from './InstitutionalDocumentPreview'
import { companyProfileApi } from '../../api/company-profile-api'

vi.mock('../../api/company-profile-api', () => ({
  companyProfileApi: {
    listAddresses: vi.fn(),
    listSigners: vi.fn(),
    getPreviewDocumentBlobUrl: vi.fn(),
  },
}))

const mockAddresses = [
  {
    id: 'addr-1',
    branch_id: 'branch-100',
    label: 'Sede Central',
    branch_name: 'Almacén Central',
    address_line: 'Av. Argentina 1234',
    district: 'Callao',
    department: 'Callao',
    country_code: 'PE',
    is_primary: true,
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'addr-2',
    branch_id: 'branch-200',
    label: 'Sede Sur',
    branch_name: 'Depósito Lurín',
    address_line: 'Km 38 Panamericana Sur',
    district: 'Lurín',
    department: 'Lima',
    country_code: 'PE',
    is_primary: false,
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

const mockSigners = [
  {
    id: 'signer-1',
    full_name: 'Ing. Carlos Mendoza',
    job_title: 'Jefe de Operaciones',
    department: 'Logística',
    signature_level: 'HEAD',
    status: 'ACTIVE' as const,
    has_signature_image: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'signer-2',
    full_name: 'Dra. María Ramos',
    job_title: 'Representante Legal',
    department: 'Legal',
    signature_level: 'DIRECTOR',
    status: 'ACTIVE' as const,
    has_signature_image: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

describe('InstitutionalDocumentPreview Component (Fase 021)', () => {
  const mockedApi = vi.mocked(companyProfileApi)

  beforeEach(() => {
    vi.clearAllMocks()
    mockedApi.listAddresses.mockResolvedValue(mockAddresses as any)
    mockedApi.listSigners.mockResolvedValue({
      items: mockSigners as any,
      page: 1,
      page_size: 100,
      total: 2,
      total_pages: 1,
    })
    mockedApi.getPreviewDocumentBlobUrl.mockResolvedValue('blob:http://localhost:3000/mock-pdf-url')
  })

  it('renderiza título, explicaciones de resolución automática y carga sedes y firmantes', async () => {
    render(<InstitutionalDocumentPreview />)

    expect(
      screen.getByText('Motor de Vista Previa Institucional (Fase 021)'),
    ).toBeInTheDocument()
    expect(screen.getByText('Sede opcional:')).toBeInTheDocument()
    expect(screen.getByText('Firmante opcional:')).toBeInTheDocument()

    // Espera que las opciones de sedes y firmantes se carguen
    await waitFor(() => {
      expect(mockedApi.listAddresses).toHaveBeenCalled()
      expect(mockedApi.listSigners).toHaveBeenCalled()
    })

    const branchSelect = screen.getByLabelText(/Sede Operativa/i)
    expect(branchSelect).toBeInTheDocument()
    expect(screen.getByText(/Resolución Automática — Sede Principal Activa/i)).toBeInTheDocument()

    const signerSelect = screen.getByLabelText(/Firmante Institucional/i)
    expect(signerSelect).toBeInTheDocument()
    expect(screen.getByText(/Resolución Automática — Según Políticas de Firma/i)).toBeInTheDocument()
  })

  it('permite cambiar el tipo de documento y muestra la descripción correspondiente', async () => {
    const user = userEvent.setup()
    render(<InstitutionalDocumentPreview />)

    await waitFor(() => expect(mockedApi.listAddresses).toHaveBeenCalled())

    const docSelect = screen.getByLabelText(/Tipo de Comprobante \/ Documento/i)
    await user.selectOptions(docSelect, 'CPV')

    expect(screen.getAllByText(/Constancia de Peso y Volumen/i).length).toBeGreaterThanOrEqual(1)
    expect(
      screen.getByText(
        /Comprobante de ingreso y registro de garita con verificación de chofer, placa, precinto/i,
      ),
    ).toBeInTheDocument()
  })

  it('permite cargar datos de ejemplo en el editor de variables dinámicas', async () => {
    const user = userEvent.setup()
    render(<InstitutionalDocumentPreview />)

    await waitFor(() => expect(mockedApi.listAddresses).toHaveBeenCalled())

    const loadSampleButton = screen.getByRole('button', { name: /Cargar datos de ejemplo/i })
    await user.click(loadSampleButton)

    // El editor se abre y se formatea el JSON
    const textarea = screen.getByPlaceholderText(/po_number/i) as HTMLTextAreaElement
    expect(textarea).toBeInTheDocument()
    expect(textarea.value).toContain('DISTRIBUIDORA LOGÍSTICA S.A.C.')
    expect(screen.getByText(/JSON válido \(5 campos configurados\)/i)).toBeInTheDocument()
  })

  it('valida la sintaxis del JSON y muestra mensaje de error si está mal formado', async () => {
    const user = userEvent.setup()
    render(<InstitutionalDocumentPreview />)

    await waitFor(() => expect(mockedApi.listAddresses).toHaveBeenCalled())

    // Abrir editor
    const toggleEditor = screen.getByRole('button', { name: /Variables Dinámicas/i })
    await user.click(toggleEditor)

    const textarea = screen.getByPlaceholderText(/po_number/i)
    fireEvent.change(textarea, { target: { value: '{ bad_json: ' } })

    expect(screen.getByText(/Sintaxis JSON inválida|Expected property name/i)).toBeInTheDocument()

    // El botón de generar queda deshabilitado o bloqueado
    const generateBtn = screen.getByRole('button', { name: /Generar vista previa en PDF/i })
    expect(generateBtn).toBeDisabled()
  })

  it('llama a getPreviewDocumentBlobUrl con branch_id y signer_id null al usar resolución automática', async () => {
    const user = userEvent.setup()
    render(<InstitutionalDocumentPreview />)

    await waitFor(() => expect(mockedApi.listAddresses).toHaveBeenCalled())

    const generateBtn = screen.getByRole('button', { name: /Generar vista previa en PDF/i })
    await user.click(generateBtn)

    await waitFor(() => {
      expect(mockedApi.getPreviewDocumentBlobUrl).toHaveBeenCalledWith({
        doc_type_code: 'AREC',
        branch_id: null,
        signer_id: null,
        custom_data: {},
      })
    })

    // Se abre el visor modal
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText(/Vista Previa Institucional — Acta Recepción/i)).toBeInTheDocument()
  })

  it('envía sede específica, firmante específico y custom_data cuando el usuario los selecciona', async () => {
    const user = userEvent.setup()
    render(<InstitutionalDocumentPreview />)

    await waitFor(() => expect(mockedApi.listAddresses).toHaveBeenCalled())

    // Seleccionar sede Sur
    const branchSelect = screen.getByLabelText(/Sede Operativa/i)
    await user.selectOptions(branchSelect, 'branch-200')

    // Seleccionar firmante 2
    const signerSelect = screen.getByLabelText(/Firmante Institucional/i)
    await user.selectOptions(signerSelect, 'signer-2')

    // Cargar datos de ejemplo
    const loadSampleButton = screen.getByRole('button', { name: /Cargar datos de ejemplo/i })
    await user.click(loadSampleButton)

    // Generar vista previa
    const generateBtn = screen.getByRole('button', { name: /Generar vista previa en PDF/i })
    await user.click(generateBtn)

    await waitFor(() => {
      expect(mockedApi.getPreviewDocumentBlobUrl).toHaveBeenCalledWith({
        doc_type_code: 'AREC',
        branch_id: 'branch-200',
        signer_id: 'signer-2',
        custom_data: expect.objectContaining({
          supplier_name: 'DISTRIBUIDORA LOGÍSTICA S.A.C.',
          reference: 'GUIA-REMITENTE-001-9872',
        }),
      })
    })
  })
})
