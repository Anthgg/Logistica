"""Vehicle Ownership & Carrier Assignment Application Service (Phase 027)."""

from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.partners.models import BusinessPartnerModel, BusinessPartnerRoleModel
from app.modules.logistics.vehicles.domain.errors.exceptions import (
    VehicleCarrierBlockedError,
    VehicleCarrierRoleRequiredError,
    VehicleNotFoundError,
)
from app.modules.logistics.vehicles.infrastructure.persistence.models import (
    VehicleCarrierAssignmentModel,
    VehicleModel,
    VehicleOwnershipAssignmentModel,
)


class VehicleOwnershipCarrierService:
    def __init__(self, db: Session):
        self.db = db

    def assign_owner(
        self,
        vehicle_id: UUID,
        organization_id: UUID,
        owner_type: str,  # INTERNAL_ORGANIZATION or BUSINESS_PARTNER
        actor_id: UUID,
        owner_business_partner_id: Optional[UUID] = None,
        ownership_type: str = "OWNED",
        contract_reference: Optional[str] = None,
    ) -> VehicleOwnershipAssignmentModel:
        vehicle = self.db.scalars(
            select(VehicleModel).where(
                and_(VehicleModel.id == vehicle_id, VehicleModel.organization_id == organization_id)
            )
        ).first()

        if not vehicle:
            raise VehicleNotFoundError(str(vehicle_id))

        if owner_type == "BUSINESS_PARTNER" and owner_business_partner_id:
            bp = self.db.scalars(
                select(BusinessPartnerModel).where(
                    and_(
                        BusinessPartnerModel.id == owner_business_partner_id,
                        BusinessPartnerModel.organization_id == organization_id,
                    )
                )
            ).first()
            if not bp:
                raise HTTPException(status_code=404, detail="Socio de negocio propietario no encontrado.")

        # Supersede existing owner assignment
        self.db.execute(
            update(VehicleOwnershipAssignmentModel)
            .where(
                and_(
                    VehicleOwnershipAssignmentModel.vehicle_id == vehicle_id,
                    VehicleOwnershipAssignmentModel.status == "CURRENT",
                )
            )
            .values(status="SUPERSEDED", valid_until=utc_now())
        )

        assignment = VehicleOwnershipAssignmentModel(
            id=uuid4(),
            vehicle_id=vehicle_id,
            owner_type=owner_type,
            owner_organization_id=organization_id if owner_type == "INTERNAL_ORGANIZATION" else None,
            owner_business_partner_id=owner_business_partner_id if owner_type == "BUSINESS_PARTNER" else None,
            ownership_type=ownership_type,
            contract_reference=contract_reference,
            valid_from=utc_now(),
            status="CURRENT",
            created_by=actor_id,
        )
        self.db.add(assignment)
        self.db.commit()

        vehicle.current_owner_assignment_id = assignment.id
        vehicle.ownership_type = ownership_type
        self.db.commit()

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle.owner_assigned",
                severity="medium",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="vehicle_ownership_assignment",
                resource_id=str(assignment.id),
            ),
        )

        return assignment

    def assign_carrier(
        self,
        vehicle_id: UUID,
        organization_id: UUID,
        carrier_business_partner_id: UUID,
        actor_id: UUID,
        assignment_type: str = "OWN_FLEET",
        authorization_reference: Optional[str] = None,
    ) -> VehicleCarrierAssignmentModel:
        vehicle = self.db.scalars(
            select(VehicleModel).where(
                and_(VehicleModel.id == vehicle_id, VehicleModel.organization_id == organization_id)
            )
        ).first()

        if not vehicle:
            raise VehicleNotFoundError(str(vehicle_id))

        # Check BusinessPartner CARRIER role
        partner = self.db.scalars(
            select(BusinessPartnerModel).where(
                and_(
                    BusinessPartnerModel.id == carrier_business_partner_id,
                    BusinessPartnerModel.organization_id == organization_id,
                )
            )
        ).first()

        if not partner:
            raise HTTPException(status_code=404, detail="Transportista no encontrado.")

        if partner.status == "BLOCKED":
            raise VehicleCarrierBlockedError(str(partner.id))

        carrier_role = self.db.scalars(
            select(BusinessPartnerRoleModel).where(
                and_(
                    BusinessPartnerRoleModel.business_partner_id == partner.id,
                    BusinessPartnerRoleModel.role_type == "CARRIER",
                    BusinessPartnerRoleModel.status == "ACTIVE",
                )
            )
        ).first()

        if not carrier_role:
            raise VehicleCarrierRoleRequiredError(str(partner.id))

        # Supersede existing carrier assignment
        self.db.execute(
            update(VehicleCarrierAssignmentModel)
            .where(
                and_(
                    VehicleCarrierAssignmentModel.vehicle_id == vehicle_id,
                    VehicleCarrierAssignmentModel.status == "CURRENT",
                )
            )
            .values(status="SUPERSEDED", valid_until=utc_now())
        )

        assignment = VehicleCarrierAssignmentModel(
            id=uuid4(),
            vehicle_id=vehicle_id,
            carrier_business_partner_id=partner.id,
            carrier_role_id=carrier_role.id,
            assignment_type=assignment_type,
            authorization_reference=authorization_reference,
            valid_from=utc_now(),
            status="CURRENT",
            created_by=actor_id,
        )
        self.db.add(assignment)
        self.db.commit()

        vehicle.current_carrier_assignment_id = assignment.id
        self.db.commit()

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle.carrier_assigned",
                severity="high",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="vehicle_carrier_assignment",
                resource_id=str(assignment.id),
            ),
        )

        return assignment
