import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useParams,
} from 'react-router-dom'
import { AuthLayout } from '../components/auth/AuthLayout'
import { ProtectedRoute } from '../components/auth/ProtectedRoute'
import { PublicOnlyRoute } from '../components/auth/PublicOnlyRoute'
import { PermissionRoute } from '../components/auth/PermissionRoute'
import { RoleRoute } from '../components/auth/RoleRoute'
import { LogisticsAccessRoute } from '../components/logistics/LogisticsAccessRoute'
import { DashboardLayout } from '../components/layout/DashboardLayout'
import { ResearchSessionProvider } from '../contexts/ResearchSessionContext'
import { ContinuousAuthProvider } from '../contexts/ContinuousAuthProvider'
import { LogisticsAuthorizationProvider } from '../features/logistics-permissions/contexts/LogisticsAuthorizationProvider'
import { LogisticsAccessProvider } from '../features/logistics-me/contexts/LogisticsAccessProvider'
import { LogisticsAccessUnavailablePage } from '../pages/LogisticsAccessUnavailablePage'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import { ContinuousAuthEvaluationDetailPage } from '../features/continuous-auth/pages/ContinuousAuthEvaluationDetailPage'
import { ContinuousAuthEvaluationsPage } from '../features/continuous-auth/pages/ContinuousAuthEvaluationsPage'
import { ContinuousAuthStatusPage } from '../features/continuous-auth/pages/ContinuousAuthStatusPage'
import { ModelStatusPage } from '../features/continuous-auth/pages/ModelStatusPage'
import { ChangePasswordPage } from '../pages/ChangePasswordPage'
import { ClientsPage } from '../pages/ClientsPage'
import { DashboardPage } from '../pages/DashboardPage'
import { ExperimentalSessionDetailPage } from '../pages/ExperimentalSessionDetailPage'
import { ExperimentalSessionsPage } from '../pages/ExperimentalSessionsPage'
import { IncidentsPage } from '../pages/IncidentsPage'
import { InventoryPage } from '../pages/InventoryPage'
import { LoginPage } from '../pages/LoginPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { ParticipantsPage } from '../pages/ParticipantsPage'
import { ProfilePage } from '../pages/ProfilePage'
import { RegisterPage } from '../pages/RegisterPage'
import { ReportsPage } from '../pages/ReportsPage'
import { ResearchPage } from '../pages/ResearchPage'
import { RouteDetailPage } from '../pages/RouteDetailPage'
import { RoutesPage } from '../pages/RoutesPage'
import { SessionsPage } from '../pages/SessionsPage'
import { ShipmentDetailPage } from '../pages/ShipmentDetailPage'
import { ShipmentsPage } from '../pages/ShipmentsPage'
import { UnauthorizedPage } from '../pages/UnauthorizedPage'
import { ProductDetailPage } from '../pages/ProductDetailPage'
import { ProductsPage } from '../pages/ProductsPage'
import { UnitsAndConversionsPage } from '../pages/UnitsAndConversionsPage'
import { BusinessPartnerDetailPage } from '../pages/BusinessPartnerDetailPage'
import { BusinessPartnersPage } from '../pages/BusinessPartnersPage'
import { PurchaseOrdersV2Page } from '../features/purchase-orders/pages/PurchaseOrdersV2Page'
import { PurchaseOrderDetailV2Page } from '../features/purchase-orders/pages/PurchaseOrderDetailV2Page'
import { GeneratePurchaseOrdersWizard } from '../features/purchase-orders/components/GeneratePurchaseOrdersWizard'
import { InboundDockOperationsBoardPage } from '../features/inbound-docks/pages/InboundDockOperationsBoardPage'
import { InboundDockQueuePage } from '../features/inbound-docks/pages/InboundDockQueuePage'
import { WarehouseDockDetailPage } from '../features/inbound-docks/pages/WarehouseDockDetailPage'
import { InboundDockAssignmentDetailPage } from '../features/inbound-docks/pages/InboundDockAssignmentDetailPage'
import { UnloadingOperationWorkspace } from '../features/inbound-docks/pages/UnloadingOperationWorkspace'
import { WarehouseDocksSettingsPage } from '../features/inbound-docks/pages/WarehouseDocksSettingsPage'
import { InboundDockQueueEntryDetailPage } from '../features/inbound-docks/pages/InboundDockQueueEntryDetailPage'
import { DockAssignmentPlanDetailPage } from '../features/inbound-docks/pages/DockAssignmentPlanDetailPage'
import { InboundDockCalendarPage } from '../features/inbound-docks/pages/InboundDockCalendarPage'
import { ReceptionDifferenceCasesPage } from '../features/reception-differences/pages/ReceptionDifferenceCasesPage'
import { CreateReceptionDifferenceCasePage } from '../features/reception-differences/pages/CreateReceptionDifferenceCasePage'
import { ReceptionDifferenceCaseDetailPage } from '../features/reception-differences/pages/ReceptionDifferenceCaseDetailPage'
import ReceptionDifferenceReviewPage from '../features/reception-differences/pages/ReceptionDifferenceReviewPage'
import ReceptionDifferenceApprovalPage from '../features/reception-differences/pages/ReceptionDifferenceApprovalPage'
import ReceptionDifferenceDocumentPage from '../features/reception-differences/pages/ReceptionDifferenceDocumentPage'
import { ReceptionDifferenceHistoryPage } from '../features/reception-differences/pages/ReceptionDifferenceHistoryPage'
import { ReceptionDifferenceIntegrityPage } from '../features/reception-differences/pages/ReceptionDifferenceIntegrityPage'
import { QualityInspectionPlansPage } from '../features/quality-inspection-plans/pages/QualityInspectionPlansPage'
import { CreateQualityInspectionPlanPage } from '../features/quality-inspection-plans/pages/CreateQualityInspectionPlanPage'
import { QualityInspectionPlanDetailPage } from '../features/quality-inspection-plans/pages/QualityInspectionPlanDetailPage'
import { QualityPlanVersionWizardPage } from '../features/quality-inspection-plans/pages/QualityPlanVersionWizardPage'
import { QualityPlanVersionDetailPage } from '../features/quality-inspection-plans/pages/QualityPlanVersionDetailPage'
import { QualityPlanPreviewPage } from '../features/quality-inspection-plans/pages/QualityPlanPreviewPage'
import { QualityPlanVersionComparisonPage } from '../features/quality-inspection-plans/pages/QualityPlanVersionComparisonPage'
import { QualityPlanHistoryPage } from '../features/quality-inspection-plans/pages/QualityPlanHistoryPage'
import { QualityTolerancesPage } from '../features/quality-inspection-plans/pages/QualityTolerancesPage'
import { QualitySamplingPlansPage } from '../features/quality-inspection-plans/pages/QualitySamplingPlansPage'
import { QualityPlanResolutionPage } from '../features/quality-inspection-plans/pages/QualityPlanResolutionPage'
import { QualityQuarantineDashboardPage } from '../features/quarantine/pages/QualityQuarantineDashboardPage'
import { QualityQuarantineCasesPage } from '../features/quarantine/pages/QualityQuarantineCasesPage'
import { QualityInspectionsPage } from '../features/quarantine/pages/QualityInspectionsPage'
import { CreateQualityQuarantinePage } from '../features/quarantine/pages/CreateQualityQuarantinePage'
import { QualityQuarantineDetailPage } from '../features/quarantine/pages/QualityQuarantineDetailPage'
import { QualityInspectionWorkspacePage } from '../features/quarantine/pages/QualityInspectionWorkspacePage'
import { QualityDispositionDecisionPage } from '../features/quarantine/pages/QualityDispositionDecisionPage'
import { QuarantineReleasePage } from '../features/quarantine/pages/QuarantineReleasePage'
import { QuarantineRejectionPage } from '../features/quarantine/pages/QuarantineRejectionPage'
import { QualityNonConformityPage } from '../features/quarantine/pages/QualityNonConformityPage'
import { QualityQuarantineHistoryPage } from '../features/quarantine/pages/QualityQuarantineHistoryPage'
import { QualityQuarantineIntegrityPage } from '../features/quarantine/pages/QualityQuarantineIntegrityPage'
import { QuarantineZonesPage } from '../features/quarantine/pages/QuarantineZonesPage'
import { QualityAvailabilityPage } from '../features/quarantine/pages/QualityAvailabilityPage'
import { QualityInspectionDetailPage } from '../features/quarantine/pages/QualityInspectionDetailPage'
import { PutawayDashboardPage } from '../features/putaway/pages/PutawayDashboardPage'
import { PutawayOrdersPage } from '../features/putaway/pages/PutawayOrdersPage'
import { PutawayOrderDetailPage } from '../features/putaway/pages/PutawayOrderDetailPage'
import { CreatePutawayOrderPage } from '../features/putaway/pages/CreatePutawayOrderPage'
import { PutawayTasksPage } from '../features/putaway/pages/PutawayTasksPage'
import { PutawayTaskDetailPage } from '../features/putaway/pages/PutawayTaskDetailPage'
import { PutawayPlanningPage } from '../features/putaway/pages/PutawayPlanningPage'
import { PutawayExceptionsPage } from '../features/putaway/pages/PutawayExceptionsPage'
import { PutawayExceptionDetailPage } from '../features/putaway/pages/PutawayExceptionDetailPage'
import { PutawayCapacityPage } from '../features/putaway/pages/PutawayCapacityPage'
import { PutawayHistoryPage } from '../features/putaway/pages/PutawayHistoryPage'
import { PutawayIntegrityPage } from '../features/putaway/pages/PutawayIntegrityPage'
import { PutawayMobileWorkspacePage } from '../features/putaway/pages/PutawayMobileWorkspacePage'
import { InventoryStockDashboardPage } from '../features/inventory-balances/pages/InventoryStockDashboardPage'
import { InventoryBalancesPage } from '../features/inventory-balances/pages/InventoryBalancesPage'
import { InventoryProductBalancesPage } from '../features/inventory-balances/pages/InventoryProductBalancesPage'
import { InventoryProductBalanceDetailPage } from '../features/inventory-balances/pages/InventoryProductBalanceDetailPage'
import { InventoryWarehouseBalancesPage } from '../features/inventory-balances/pages/InventoryWarehouseBalancesPage'
import { InventoryWarehouseBalanceDetailPage } from '../features/inventory-balances/pages/InventoryWarehouseBalanceDetailPage'
import { InventoryLocationBalancesPage } from '../features/inventory-balances/pages/InventoryLocationBalancesPage'
import { InventoryLocationBalanceDetailPage } from '../features/inventory-balances/pages/InventoryLocationBalanceDetailPage'
import { InventoryPositionsBalancesPage } from '../features/inventory-balances/pages/InventoryPositionsBalancesPage'
import { InventoryPositionBalanceDetailPage } from '../features/inventory-balances/pages/InventoryPositionBalanceDetailPage'
import { InventoryBalanceFormulasPage } from '../features/inventory-balances/pages/InventoryBalanceFormulasPage'
import { InventoryBalanceFreshnessPage } from '../features/inventory-balances/pages/InventoryBalanceFreshnessPage'
import { InventoryBalanceReconciliationPage } from '../features/inventory-balances/pages/InventoryBalanceReconciliationPage'
import { InventoryBalanceRebuildsPage } from '../features/inventory-balances/pages/InventoryBalanceRebuildsPage'
import { InventoryBalanceCheckpointsPage } from '../features/inventory-balances/pages/InventoryBalanceCheckpointsPage'
import { InventoryBalanceHistoricalPage } from '../features/inventory-balances/pages/InventoryBalanceHistoricalPage'
import { InventoryNegativeBalancesPage } from '../features/inventory-balances/pages/InventoryNegativeBalancesPage'
import { InventoryBalanceAlertsPage } from '../features/inventory-balances/pages/InventoryBalanceAlertsPage'
import { InventoryBalanceExportsPage } from '../features/inventory-balances/pages/InventoryBalanceExportsPage'
import { InventoryLedgerDashboardPage } from '../features/inventory-ledger/pages/InventoryLedgerDashboardPage'
import { InventoryMovementsPage } from '../features/inventory-ledger/pages/InventoryMovementsPage'
import { InventoryMovementDetailPage } from '../features/inventory-ledger/pages/InventoryMovementDetailPage'
import { InventoryKardexPage } from '../features/inventory-ledger/pages/InventoryKardexPage'
import { PreparedInventoryEventsPage } from '../features/inventory-ledger/pages/PreparedInventoryEventsPage'
import { InventoryLedgerPartitionsPage } from '../features/inventory-ledger/pages/InventoryLedgerPartitionsPage'
import { InventoryLedgerPartitionIntegrityPage } from '../features/inventory-ledger/pages/InventoryLedgerPartitionIntegrityPage'
import { InventoryLedgerCheckpointsPage } from '../features/inventory-ledger/pages/InventoryLedgerCheckpointsPage'
import { InventoryLedgerReconciliationPage } from '../features/inventory-ledger/pages/InventoryLedgerReconciliationPage'
import { InventoryKardexExportsPage } from '../features/inventory-ledger/pages/InventoryKardexExportsPage'
import { GateControlDashboardPage } from '../features/gate-control/pages/GateControlDashboardPage'
import { CreateGateCheckInPage } from '../features/gate-control/pages/CreateGateCheckInPage'
import { GateCheckInDetailPage } from '../features/gate-control/pages/GateCheckInDetailPage'
import { WarehouseGatesSettingsPage } from '../features/gate-control/pages/WarehouseGatesSettingsPage'
import { GateVerificationPoliciesPage } from '../features/gate-control/pages/GateVerificationPoliciesPage'
import { ProcurementApprovalsDashboard } from '../features/procurement-approvals/pages/ProcurementApprovalsDashboard'
import { ApprovalInboxPage } from '../features/procurement-approvals/pages/ApprovalInboxPage'
import { ApprovalPoliciesPage } from '../features/procurement-approvals/pages/ApprovalPoliciesPage'
import { ApprovalPolicyCreatePage } from '../features/procurement-approvals/pages/ApprovalPolicyCreatePage'
import { ApprovalPolicyDetailPage } from '../features/procurement-approvals/pages/ApprovalPolicyDetailPage'
import { ApprovalPolicyVersionPage } from '../features/procurement-approvals/pages/ApprovalPolicyVersionPage'
import { ApprovalRequestDetailPage } from '../features/procurement-approvals/pages/ApprovalRequestDetailPage'
import { ApprovalUnavailablePage } from '../features/procurement-approvals/pages/ApprovalUnavailablePage'
import { PurchaseRequisitionsPage } from '../pages/PurchaseRequisitionsPage'
import { QuotationEvaluationsPage } from '../features/supplier-evaluation/pages/QuotationEvaluationsPage'
import { CreateQuotationEvaluationWizard } from '../features/supplier-evaluation/components/CreateQuotationEvaluationWizard'
import { EvaluationDetailPage } from '../features/supplier-evaluation/pages/EvaluationDetailPage'
import { SupplierEvaluationTemplatesPage } from '../features/supplier-evaluation/pages/SupplierEvaluationTemplatesPage'
import { EvaluationTemplateDetailPage } from '../features/supplier-evaluation/pages/EvaluationTemplateDetailPage'
import { EvaluationRubricsPage } from '../features/supplier-evaluation/components/EvaluationRubricsPage'
import { QuotationRoundDetailPage } from '../features/supplier-evaluation/pages/QuotationRoundDetailPage'
import { PurchaseRequisitionFormPage } from '../pages/PurchaseRequisitionFormPage'
import { PurchaseRequisitionDetailPage } from '../pages/PurchaseRequisitionDetailPage'
import { PurchaseRequisitionReviewPage } from '../pages/PurchaseRequisitionReviewPage'
import { CostCentersPage } from '../pages/CostCentersPage'
import { RucIntegrationPage } from '../pages/RucIntegrationPage'
import { VehicleDetailPage } from '../pages/VehicleDetailPage'
import { VehicleMakesPage } from '../pages/VehicleMakesPage'
import { VehicleModelsPage } from '../pages/VehicleModelsPage'
import { VehiclesPage } from '../pages/VehiclesPage'
import { VehicleVerificationConflictsPage } from '../pages/VehicleVerificationConflictsPage'
import { VehicleVerificationRequirementsPage } from '../pages/VehicleVerificationRequirementsPage'
import { VehicleVerificationReviewTasksPage } from '../pages/VehicleVerificationReviewTasksPage'
import { VehicleVerificationsPage } from '../pages/VehicleVerificationsPage'
import { VehicleVerificationSourcesPage } from '../pages/VehicleVerificationSourcesPage'
import { WarehouseDetailPage } from '../pages/WarehouseDetailPage'
import { WarehousesPage } from '../pages/WarehousesPage'
import { OrganizationsPage } from '../pages/OrganizationsPage'
import { BranchesPage } from '../pages/BranchesPage'
import { RolesPage } from '../pages/RolesPage'
import { RoleAssignmentsPage } from '../pages/RoleAssignmentsPage'
import { PermissionsCatalogPage } from '../pages/PermissionsCatalogPage'
import { AuditEventsPage } from '../pages/AuditEventsPage'
import { CompanyProfileSettingsPage } from '../pages/CompanyProfileSettingsPage'
import { DocumentsPage } from '../pages/DocumentsPage'
import { DriversPage } from '../pages/DriversPage'
import { DriverDetailPage } from '../pages/DriverDetailPage'
import { DriverAlertsPage } from '../pages/DriverAlertsPage'
import { DriverLicenseCategoriesPage } from '../pages/DriverLicenseCategoriesPage'
import { FilesRepositoryPage } from '../pages/FilesRepositoryPage'
import { FileUploadPage } from '../pages/FileUploadPage'
import { FileDetailPage } from '../pages/FileDetailPage'
import { FileDeletionRequestsPage } from '../pages/FileDeletionRequestsPage'

function LegacyPurchaseOrderDetailRedirect() {
  const { purchaseOrderId } = useParams<{ purchaseOrderId: string }>()
  return (
    <Navigate
      to={
        purchaseOrderId
          ? `/logistics/purchasing/purchase-orders/${purchaseOrderId}`
          : '/logistics/purchasing/purchase-orders'
      }
      replace
    />
  )
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicOnlyRoute />}>
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route
            element={
              <ResearchSessionProvider>
                <ContinuousAuthProvider>
                  <LogisticsAccessProvider>
                    <LogisticsAuthorizationProvider>
                      <DashboardLayout />
                    </LogisticsAuthorizationProvider>
                  </LogisticsAccessProvider>
                </ContinuousAuthProvider>
              </ResearchSessionProvider>
            }
          >
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/shipments" element={<ShipmentsPage />} />
            <Route path="/shipments/:shipmentId" element={<ShipmentDetailPage />} />
            {/* Ruta canónica de almacenes: /logistics/warehouses.
                /warehouses queda como redirect de compatibilidad. */}
            <Route
              path="/warehouses"
              element={<Navigate to="/logistics/warehouses" replace />}
            />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/routes" element={<RoutesPage />} />
            <Route path="/routes/:routeId" element={<RouteDetailPage />} />
            <Route path="/incidents" element={<IncidentsPage />} />
            <Route element={<PermissionRoute permission="viewReports" />}>
              <Route path="/reports" element={<ReportsPage />} />
            </Route>
            <Route path="/research" element={<ResearchPage />} />
            <Route element={<RoleRoute roles={['admin', 'supervisor']} />}>
              <Route path="/research/participants" element={<ParticipantsPage />} />
            </Route>
            <Route element={<RoleRoute roles={['admin', 'supervisor']} />}>
              <Route path="/research/sessions" element={<ExperimentalSessionsPage />} />
              <Route path="/research/sessions/:sessionId" element={<ExperimentalSessionDetailPage />} />
            </Route>
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/sessions" element={<SessionsPage />} />
            <Route
              path="/security/continuous-auth"
              element={<ContinuousAuthStatusPage />}
            />
            <Route element={<RoleRoute roles={['admin', 'supervisor']} />}>
              <Route
                path="/admin/continuous-auth/evaluations"
                element={<ContinuousAuthEvaluationsPage />}
              />
              <Route
                path="/admin/continuous-auth/evaluations/:evaluationId"
                element={<ContinuousAuthEvaluationDetailPage />}
              />
              <Route
                path="/admin/models/status"
                element={<ModelStatusPage />}
              />
            </Route>
            <Route
              path="/change-password"
              element={<ChangePasswordPage />}
            />
            <Route
              path="/security"
              element={
                <Navigate to="/security/continuous-auth" replace />
              }
            />
            <Route element={<LogisticsAccessRoute />}>
              <Route path="/logistics" element={<Navigate to="/logistics/warehouses" replace />} />
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.warehouses.read}
                  />
                }
              >
                <Route path="/logistics/warehouses" element={<WarehousesPage />} />
                <Route
                  path="/logistics/settings/warehouses"
                  element={<WarehousesPage />}
                />
                <Route
                  path="/logistics/settings/warehouses/:warehouseId"
                  element={<WarehouseDetailPage />}
                />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.organizations.read}
                  />
                }
              >
                <Route path="/logistics/organizations" element={<OrganizationsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.branches.read}
                  />
                }
              >
                <Route path="/logistics/branches" element={<BranchesPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.roles.read}
                  />
                }
              >
                <Route path="/logistics/roles" element={<RolesPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.roleAssignments.read}
                  />
                }
              >
                <Route path="/logistics/role-assignments" element={<RoleAssignmentsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.documents.read}
                  />
                }
              >
                <Route path="/logistics/documents" element={<DocumentsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.companySettings.read}
                  />
                }
              >
                <Route path="/logistics/company-profile" element={<CompanyProfileSettingsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.catalog.read}
                  />
                }
              >
                <Route path="/logistics/products" element={<ProductsPage />} />
                <Route path="/logistics/products/:productId" element={<ProductDetailPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.units.read}
                  />
                }
              >
                <Route path="/logistics/units" element={<UnitsAndConversionsPage />} />
                <Route path="/logistics/unit-conversions" element={<UnitsAndConversionsPage />} />
                <Route path="/logistics/unit-conversions/simulator" element={<UnitsAndConversionsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.partners.read}
                  />
                }
              >
                <Route path="/logistics/business-partners" element={<BusinessPartnersPage />} />
                <Route path="/logistics/suppliers" element={<BusinessPartnersPage />} />
                <Route path="/logistics/customers" element={<BusinessPartnersPage />} />
                <Route path="/logistics/carriers" element={<BusinessPartnersPage />} />
                <Route path="/logistics/business-partners/:partnerId" element={<BusinessPartnerDetailPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.purchaseOrders.read}
                  />
                }
              >
                <Route path="/logistics/purchase-orders" element={<Navigate to="/logistics/purchasing/purchase-orders" replace />} />
                <Route path="/logistics/purchase-orders/:purchaseOrderId" element={<LegacyPurchaseOrderDetailRedirect />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.rucIntegration.read}
                  />
                }
              >
                <Route path="/logistics/ruc" element={<RucIntegrationPage />} />
                <Route path="/logistics/ruc/lookup" element={<RucIntegrationPage />} />
                <Route path="/logistics/ruc/datasets" element={<RucIntegrationPage />} />
                <Route path="/logistics/ruc/imports" element={<RucIntegrationPage />} />
                <Route path="/logistics/ruc/assisted-verifications" element={<RucIntegrationPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.vehicleVerifications.read}
                  />
                }
              >
                <Route
                  path="/logistics/integrations/vehicle-verifications"
                  element={<VehicleVerificationsPage />}
                />
                <Route
                  path="/logistics/integrations/vehicle-verifications/sources"
                  element={<VehicleVerificationSourcesPage />}
                />
                <Route
                  path="/logistics/integrations/vehicle-verifications/conflicts"
                  element={<VehicleVerificationConflictsPage />}
                />
                <Route
                  path="/logistics/integrations/vehicle-verifications/review-tasks"
                  element={<VehicleVerificationReviewTasksPage />}
                />
                <Route
                  path="/logistics/integrations/vehicle-verifications/requirements"
                  element={<VehicleVerificationRequirementsPage />}
                />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.vehicles.read}
                  />
                }
              >
                <Route path="/logistics/vehicles" element={<VehiclesPage />} />
                <Route path="/logistics/vehicles/new" element={<VehiclesPage />} />
                <Route path="/logistics/vehicles/:vehicleId" element={<VehicleDetailPage />} />
                <Route path="/logistics/vehicles/:vehicleId/edit" element={<VehicleDetailPage />} />
                <Route path="/logistics/vehicles/:vehicleId/documents" element={<VehicleDetailPage />} />
                <Route path="/logistics/vehicles/:vehicleId/versions" element={<VehicleDetailPage />} />
                <Route path="/logistics/vehicles/:vehicleId/history" element={<VehicleDetailPage />} />
                <Route path="/logistics/vehicle-makes" element={<VehicleMakesPage />} />
                <Route path="/logistics/vehicle-models" element={<VehicleModelsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.purchaseRequisitions.read}
                  />
                }
              >
                <Route path="/logistics/purchasing/requisitions" element={<PurchaseRequisitionsPage />} />
                <Route path="/logistics/purchasing/requisitions/new" element={<PurchaseRequisitionFormPage />} />
                <Route path="/logistics/purchasing/requisitions/:requisitionId" element={<PurchaseRequisitionDetailPage />} />
                <Route path="/logistics/purchasing/requisitions/:requisitionId/edit" element={<PurchaseRequisitionFormPage />} />
                <Route path="/logistics/purchasing/requisitions/:requisitionId/revisions" element={<PurchaseRequisitionDetailPage />} />
                <Route path="/logistics/purchasing/requisitions/:requisitionId/history" element={<PurchaseRequisitionDetailPage />} />
                <Route path="/logistics/purchasing/requisitions/mine" element={<PurchaseRequisitionsPage />} />
                <Route path="/logistics/purchasing/requisitions/review" element={<PurchaseRequisitionReviewPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.supplierEvaluations.view}
                  />
                }
              >
                <Route path="/logistics/purchasing/evaluations" element={<QuotationEvaluationsPage />} />
                <Route path="/logistics/purchasing/evaluations/new" element={<CreateQuotationEvaluationWizard />} />
                <Route path="/logistics/purchasing/evaluations/:evaluationId" element={<EvaluationDetailPage />} />
                <Route path="/logistics/purchasing/evaluations/:evaluationId/decision" element={<EvaluationDetailPage initialTab="decision" />} />
                <Route path="/logistics/purchasing/evaluation-templates" element={<SupplierEvaluationTemplatesPage />} />
                <Route path="/logistics/purchasing/evaluation-templates/:templateId" element={<EvaluationTemplateDetailPage />} />
                <Route path="/logistics/purchasing/evaluation-rubrics" element={<EvaluationRubricsPage />} />
                <Route path="/logistics/purchasing/quotations/:roundId" element={<QuotationRoundDetailPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.purchaseOrdersV2.view}
                  />
                }
              >
                <Route path="/logistics/purchasing/purchase-orders" element={<PurchaseOrdersV2Page />} />
                <Route path="/logistics/purchasing/purchase-orders/generate" element={<GeneratePurchaseOrdersWizard />} />
                <Route path="/logistics/purchasing/purchase-orders/:purchaseOrderId" element={<PurchaseOrderDetailV2Page />} />
                <Route path="/logistics/purchasing/purchase-orders/:purchaseOrderId/edit" element={<PurchaseOrderDetailV2Page section="edit" />} />
                <Route path="/logistics/purchasing/purchase-orders/:purchaseOrderId/revisions" element={<PurchaseOrderDetailV2Page section="revisions" />} />
                <Route path="/logistics/purchasing/purchase-orders/:purchaseOrderId/schedules" element={<PurchaseOrderDetailV2Page section="schedules" />} />
                <Route path="/logistics/purchasing/purchase-orders/:purchaseOrderId/dispatch" element={<PurchaseOrderDetailV2Page section="dispatch" />} />
                <Route path="/logistics/purchasing/purchase-orders/:purchaseOrderId/document" element={<PurchaseOrderDetailV2Page section="document" />} />
                <Route path="/logistics/purchasing/purchase-orders/:purchaseOrderId/history" element={<PurchaseOrderDetailV2Page section="history" />} />
                <Route path="/logistics/purchasing/purchase-orders/:purchaseOrderId/amendments" element={<PurchaseOrderDetailV2Page section="amendments" />} />
                <Route path="/logistics/purchasing/purchase-orders/:purchaseOrderId/approval" element={<PurchaseOrderDetailV2Page section="approval" />} />
                <Route path="/logistics/purchasing/purchase-orders/:purchaseOrderId/approval-chain" element={<PurchaseOrderDetailV2Page section="approval-chain" />} />
                <Route path="/logistics/purchasing/purchase-orders/:purchaseOrderId/approval-seal" element={<PurchaseOrderDetailV2Page section="approval-seal" />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.inboundDocks.view}
                  />
                }
              >
                <Route path="/logistics/inbound/docks" element={<InboundDockOperationsBoardPage />} />
                <Route path="/logistics/inbound/docks/board" element={<InboundDockOperationsBoardPage />} />
                <Route path="/logistics/inbound/docks/queue" element={<InboundDockQueuePage />} />
                <Route path="/logistics/inbound/docks/queue/:entryId" element={<InboundDockQueueEntryDetailPage />} />
                <Route path="/logistics/inbound/dock-assignment-plans/:planId" element={<DockAssignmentPlanDetailPage />} />
                <Route path="/logistics/inbound/docks/calendar" element={<InboundDockCalendarPage />} />
                <Route path="/logistics/inbound/docks/:dockId" element={<WarehouseDockDetailPage />} />
                <Route path="/logistics/inbound/dock-assignments/:assignmentId" element={<InboundDockAssignmentDetailPage />} />
                <Route path="/logistics/inbound/dock-assignments/:assignmentId/history" element={<InboundDockAssignmentDetailPage />} />
                <Route path="/logistics/inbound/dock-assignments/:assignmentId/metrics" element={<InboundDockAssignmentDetailPage />} />
                <Route path="/logistics/inbound/unloading/:operationId" element={<UnloadingOperationWorkspace />} />
                <Route path="/logistics/inbound/unloading/:operationId/history" element={<UnloadingOperationWorkspace />} />
                <Route path="/logistics/inbound/unloading/:operationId/metrics" element={<UnloadingOperationWorkspace />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.receptionDifferences.view}
                  />
                }
              >
                <Route path="/logistics/inbound/reception-differences" element={<ReceptionDifferenceCasesPage />} />
                <Route path="/logistics/inbound/reception-differences/new" element={<CreateReceptionDifferenceCasePage />} />
                <Route path="/logistics/inbound/reception-differences/:caseId" element={<ReceptionDifferenceCaseDetailPage />} />
                <Route path="/logistics/inbound/reception-differences/:caseId/edit" element={<ReceptionDifferenceCaseDetailPage section="edit" />} />
                <Route path="/logistics/inbound/reception-differences/:caseId/review" element={<ReceptionDifferenceReviewPage />} />
                <Route path="/logistics/inbound/reception-differences/:caseId/approval" element={<ReceptionDifferenceApprovalPage />} />
                <Route path="/logistics/inbound/reception-differences/:caseId/document" element={<ReceptionDifferenceDocumentPage />} />
                <Route path="/logistics/inbound/reception-differences/:caseId/history" element={<ReceptionDifferenceHistoryPage />} />
                <Route path="/logistics/inbound/reception-differences/:caseId/integrity" element={<ReceptionDifferenceIntegrityPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.qualityInspectionPlans.read}
                  />
                }
              >
                <Route path="/logistics/quality/plans" element={<QualityInspectionPlansPage />} />
                <Route path="/logistics/quality/plans/new" element={<CreateQualityInspectionPlanPage />} />
                <Route path="/logistics/quality/plans/:planId" element={<QualityInspectionPlanDetailPage />} />
                <Route path="/logistics/quality/plans/:planId/versions/new" element={<QualityPlanVersionWizardPage />} />
                <Route path="/logistics/quality/plans/:planId/versions/:versionId" element={<QualityPlanVersionDetailPage />} />
                <Route path="/logistics/quality/plans/:planId/versions/:versionId/edit" element={<QualityPlanVersionWizardPage />} />
                <Route path="/logistics/quality/plans/:planId/versions/:versionId/preview" element={<QualityPlanPreviewPage />} />
                <Route path="/logistics/quality/plans/:planId/versions/:versionId/compare" element={<QualityPlanVersionComparisonPage />} />
                <Route path="/logistics/quality/plans/:planId/history" element={<QualityPlanHistoryPage />} />
                <Route path="/logistics/quality/tolerances" element={<QualityTolerancesPage />} />
                <Route path="/logistics/quality/sampling-plans" element={<QualitySamplingPlansPage />} />
                <Route path="/logistics/quality/plan-resolution" element={<QualityPlanResolutionPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.inventoryLedger.view}
                  />
                }
              >
                <Route path="/logistics/inventory/ledger" element={<InventoryLedgerDashboardPage />} />
                <Route path="/logistics/inventory/ledger/movements" element={<InventoryMovementsPage />} />
                <Route path="/logistics/inventory/ledger/movements/:movementId" element={<InventoryMovementDetailPage />} />
                <Route path="/logistics/inventory/ledger/kardex" element={<InventoryKardexPage />} />
                <Route path="/logistics/inventory/ledger/prepared-events" element={<PreparedInventoryEventsPage />} />
                <Route path="/logistics/inventory/ledger/partitions" element={<InventoryLedgerPartitionsPage />} />
                <Route path="/logistics/inventory/ledger/partitions/:partitionId" element={<InventoryLedgerPartitionIntegrityPage />} />
                <Route path="/logistics/inventory/ledger/checkpoints" element={<InventoryLedgerCheckpointsPage />} />
                <Route path="/logistics/inventory/ledger/reconciliation" element={<InventoryLedgerReconciliationPage />} />
                <Route path="/logistics/inventory/ledger/exports" element={<InventoryKardexExportsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.inventoryLedger.view}
                  />
                }
              >
                <Route path="/logistics/inventory/stock" element={<InventoryStockDashboardPage />} />
                <Route path="/logistics/inventory/stock/products" element={<InventoryProductBalancesPage />} />
                <Route path="/logistics/inventory/stock/products/:productId" element={<InventoryProductBalanceDetailPage />} />
                <Route path="/logistics/inventory/stock/warehouses" element={<InventoryWarehouseBalancesPage />} />
                <Route path="/logistics/inventory/stock/warehouses/:warehouseId" element={<InventoryWarehouseBalanceDetailPage />} />
                <Route path="/logistics/inventory/stock/locations" element={<InventoryLocationBalancesPage />} />
                <Route path="/logistics/inventory/stock/locations/:locationId" element={<InventoryLocationBalanceDetailPage />} />
                <Route path="/logistics/inventory/stock/positions" element={<InventoryPositionsBalancesPage />} />
                <Route path="/logistics/inventory/stock/positions/:positionId" element={<InventoryPositionBalanceDetailPage />} />
                <Route path="/logistics/inventory/stock/list" element={<InventoryBalancesPage />} />
                <Route path="/logistics/inventory/stock/formulas" element={<InventoryBalanceFormulasPage />} />
                <Route path="/logistics/inventory/stock/freshness" element={<InventoryBalanceFreshnessPage />} />
                <Route path="/logistics/inventory/stock/reconciliation" element={<InventoryBalanceReconciliationPage />} />
                <Route path="/logistics/inventory/stock/rebuilds" element={<InventoryBalanceRebuildsPage />} />
                <Route path="/logistics/inventory/stock/checkpoints" element={<InventoryBalanceCheckpointsPage />} />
                <Route path="/logistics/inventory/stock/history" element={<InventoryBalanceHistoricalPage />} />
                <Route path="/logistics/inventory/stock/negatives" element={<InventoryNegativeBalancesPage />} />
                <Route path="/logistics/inventory/stock/alerts" element={<InventoryBalanceAlertsPage />} />
                <Route path="/logistics/inventory/stock/exports" element={<InventoryBalanceExportsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.putaway.view}
                  />
                }
              >
                <Route path="/logistics/putaway" element={<PutawayDashboardPage />} />
                <Route path="/logistics/putaway/orders" element={<PutawayOrdersPage />} />
                <Route path="/logistics/putaway/orders/new" element={<CreatePutawayOrderPage />} />
                <Route path="/logistics/putaway/orders/:orderId" element={<PutawayOrderDetailPage />} />
                <Route path="/logistics/putaway/orders/:orderId/edit" element={<PutawayOrderDetailPage />} />
                <Route path="/logistics/putaway/orders/:orderId/plan" element={<PutawayPlanningPage />} />
                <Route path="/logistics/putaway/orders/:orderId/history" element={<PutawayHistoryPage />} />
                <Route path="/logistics/putaway/orders/:orderId/integrity" element={<PutawayIntegrityPage />} />
                <Route path="/logistics/putaway/tasks" element={<PutawayTasksPage />} />
                <Route path="/logistics/putaway/tasks/:taskId" element={<PutawayTaskDetailPage />} />
                <Route path="/logistics/putaway/exceptions" element={<PutawayExceptionsPage />} />
                <Route path="/logistics/putaway/exceptions/:exceptionId" element={<PutawayExceptionDetailPage />} />
                <Route path="/logistics/putaway/capacity" element={<PutawayCapacityPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.putaway.mobileAccess}
                  />
                }
              >
                <Route path="/logistics/putaway/mobile" element={<PutawayMobileWorkspacePage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.quarantine.view}
                  />
                }
              >
                <Route path="/logistics/quality/quarantine" element={<QualityQuarantineDashboardPage />} />
                <Route path="/logistics/quality/quarantine/cases" element={<QualityQuarantineCasesPage />} />
                <Route path="/logistics/quality/quarantine/new" element={<CreateQualityQuarantinePage />} />
                <Route path="/logistics/quality/quarantine/:caseId" element={<QualityQuarantineDetailPage />} />
                <Route path="/logistics/quality/quarantine/:caseId/inspection" element={<QualityInspectionWorkspacePage />} />
                <Route path="/logistics/quality/quarantine/:caseId/decision" element={<QualityDispositionDecisionPage />} />
                <Route path="/logistics/quality/quarantine/:caseId/release" element={<QuarantineReleasePage />} />
                <Route path="/logistics/quality/quarantine/:caseId/rejection" element={<QuarantineRejectionPage />} />
                <Route path="/logistics/quality/quarantine/:caseId/document" element={<QualityNonConformityPage />} />
                <Route path="/logistics/quality/quarantine/:caseId/history" element={<QualityQuarantineHistoryPage />} />
                <Route path="/logistics/quality/quarantine/:caseId/integrity" element={<QualityQuarantineIntegrityPage />} />
                <Route path="/logistics/quality/inspections" element={<QualityInspectionsPage />} />
                <Route path="/logistics/quality/inspections/:inspectionId" element={<QualityInspectionDetailPage />} />
                <Route path="/logistics/quality/quarantine-zones" element={<QuarantineZonesPage />} />
                <Route path="/logistics/quality/availability" element={<QualityAvailabilityPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.inboundDocks.manageDocks}
                  />
                }
              >
                <Route path="/logistics/inbound/docks/settings" element={<WarehouseDocksSettingsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.gateControl.view}
                  />
                }
              >
                <Route path="/logistics/inbound/gate-control" element={<GateControlDashboardPage />} />
                <Route path="/logistics/inbound/gate-control/queue" element={<GateControlDashboardPage />} />
                <Route path="/logistics/inbound/gate-control/check-ins/new" element={<CreateGateCheckInPage />} />
                <Route path="/logistics/inbound/gate-control/check-ins/:checkInId" element={<GateCheckInDetailPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.gateControl.manageGates}
                  />
                }
              >
                <Route path="/logistics/inbound/gate-control/gates" element={<WarehouseGatesSettingsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.gateControl.managePolicies}
                  />
                }
              >
                <Route path="/logistics/inbound/gate-control/policies" element={<GateVerificationPoliciesPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    anyOf={[
                      LOGISTICS_PERMISSIONS.procurementApprovals.view,
                      LOGISTICS_PERMISSIONS.purchaseOrdersV2.approveTransitional,
                    ]}
                  />
                }
              >
                <Route path="/logistics/purchasing/approvals" element={<ProcurementApprovalsDashboard />} />
                <Route path="/logistics/purchasing/approvals/inbox" element={<ApprovalInboxPage />} />
                <Route
                  path="/logistics/purchasing/approvals/created-by-me"
                  element={
                    <ApprovalUnavailablePage
                      title="Solicitudes creadas por mí"
                      description="El OpenAPI 0.9.1 no publica un listado de solicitudes por creador."
                    />
                  }
                />
                <Route path="/logistics/purchasing/approvals/:requestId" element={<ApprovalRequestDetailPage />} />
                <Route path="/logistics/purchasing/approvals/:requestId/history" element={<ApprovalRequestDetailPage section="history" />} />
                <Route path="/logistics/purchasing/approvals/:requestId/integrity" element={<ApprovalRequestDetailPage section="integrity" />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    anyOf={[
                      LOGISTICS_PERMISSIONS.procurementApprovals.policiesRead,
                      LOGISTICS_PERMISSIONS.procurementApprovals.policiesCreate,
                      LOGISTICS_PERMISSIONS.procurementApprovals.policiesUpdate,
                      LOGISTICS_PERMISSIONS.procurementApprovals.policiesActivate,
                    ]}
                  />
                }
              >
                <Route path="/logistics/purchasing/approval-policies" element={<ApprovalPoliciesPage />} />
                <Route path="/logistics/purchasing/approval-policies/new" element={<ApprovalPolicyCreatePage />} />
                <Route path="/logistics/purchasing/approval-policies/:policyId" element={<ApprovalPolicyDetailPage />} />
                <Route path="/logistics/purchasing/approval-policies/:policyId/versions" element={<ApprovalPolicyDetailPage section="versions" />} />
                <Route path="/logistics/purchasing/approval-policy-versions/:versionId" element={<ApprovalPolicyVersionPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={
                      LOGISTICS_PERMISSIONS.procurementApprovals.manageDelegations
                    }
                  />
                }
              >
                <Route
                  path="/logistics/purchasing/approval-delegations"
                  element={
                    <ApprovalUnavailablePage
                      title="Delegaciones de aprobación"
                      description="El backend actual no publica operaciones de delegación."
                    />
                  }
                />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.costCenters.read}
                  />
                }
              >
                <Route path="/logistics/catalog/cost-centers" element={<CostCentersPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.drivers.read}
                  />
                }
              >
                <Route path="/logistics/drivers" element={<DriversPage />} />
                <Route path="/logistics/drivers/new" element={<DriversPage />} />
                <Route path="/logistics/drivers/:driverId" element={<DriverDetailPage />} />
                <Route path="/logistics/drivers/:driverId/edit" element={<DriverDetailPage />} />
                <Route path="/logistics/drivers/:driverId/licenses" element={<DriverDetailPage />} />
                <Route path="/logistics/drivers/:driverId/documents" element={<DriverDetailPage />} />
                <Route path="/logistics/drivers/:driverId/versions" element={<DriverDetailPage />} />
                <Route path="/logistics/drivers/:driverId/history" element={<DriverDetailPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.drivers.read}
                  />
                }
              >
                <Route path="/logistics/driver-license-categories" element={<DriverLicenseCategoriesPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.drivers.read}
                  />
                }
              >
                <Route path="/logistics/alerts/drivers" element={<DriverAlertsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.files.read}
                  />
                }
              >
                <Route path="/logistics/files" element={<FilesRepositoryPage />} />
                <Route path="/logistics/files/upload" element={<FileUploadPage />} />
                <Route path="/logistics/files/:fileId" element={<FileDetailPage />} />
                <Route path="/logistics/files/:fileId/versions" element={<FileDetailPage />} />
                <Route path="/logistics/files/:fileId/evidence" element={<FileDetailPage />} />
                <Route path="/logistics/files/:fileId/access" element={<FileDetailPage />} />
                <Route path="/logistics/files/:fileId/history" element={<FileDetailPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.files.read}
                  />
                }
              >
                <Route path="/logistics/evidence" element={<Navigate to="/logistics/files" replace />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.files.read}
                  />
                }
              >
                <Route path="/logistics/file-deletion-requests" element={<FileDeletionRequestsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.audit.read}
                  />
                }
              >
                <Route path="/logistics/audit-events" element={<AuditEventsPage />} />
              </Route>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.permissions.read}
                  />
                }
              >
                <Route path="/logistics/permissions" element={<PermissionsCatalogPage />} />
              </Route>
            </Route>
          </Route>
        </Route>

        <Route path="/logistics/unavailable" element={<LogisticsAccessUnavailablePage />} />

        <Route path="/unauthorized" element={<UnauthorizedPage />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
