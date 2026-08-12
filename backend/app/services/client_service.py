from math import ceil
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.models.client import Client
from app.models.user import User
from app.repositories.client_repository import ClientRepository
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.schemas.common import PaginatedResponse
from app.services.audit_service import AuditService


class ClientService:
    def __init__(self) -> None:
        self.repository = ClientRepository()
        self.audit = AuditService()

    def list(
        self,
        database: Session,
        *,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_order: str,
        is_active: bool | None,
    ) -> PaginatedResponse[ClientRead]:
        if sort_by not in self.repository.SORT_FIELDS:
            raise ApplicationError("INVALID_SORT_FIELD", "Campo de orden no permitido.", 422)
        items, total = self.repository.list(
            database,
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            is_active=is_active,
        )
        return PaginatedResponse(
            items=[ClientRead.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        )

    def get(self, database: Session, client_id: UUID) -> Client:
        client = self.repository.get(database, client_id)
        if not client:
            raise ApplicationError("CLIENT_NOT_FOUND", "El cliente no existe.", 404)
        return client

    def create(self, database: Session, data: ClientCreate, user: User) -> Client:
        if self.repository.get_by_document(database, data.document_number):
            raise ApplicationError(
                "CLIENT_DOCUMENT_ALREADY_EXISTS",
                "Ya existe un cliente con ese documento.",
                409,
            )
        client = Client(**data.model_dump())
        database.add(client)
        try:
            database.flush()
        except IntegrityError as exc:
            database.rollback()
            raise ApplicationError(
                "CLIENT_DOCUMENT_ALREADY_EXISTS",
                "Ya existe un cliente con ese documento.",
                409,
            ) from exc
        self.audit.record(
            database,
            "CLIENT_CREATED",
            user_id=user.id,
            resource_type="client",
            resource_id=str(client.id),
        )
        database.commit()
        database.refresh(client)
        return client

    def update(
        self, database: Session, client_id: UUID, data: ClientUpdate
    ) -> Client:
        client = self.get(database, client_id)
        changes = data.model_dump(exclude_unset=True)
        document_number = changes.get("document_number")
        if document_number:
            duplicate = self.repository.get_by_document(database, str(document_number))
            if duplicate and duplicate.id != client.id:
                raise ApplicationError(
                    "CLIENT_DOCUMENT_ALREADY_EXISTS",
                    "Ya existe un cliente con ese documento.",
                    409,
                )
        for field, value in changes.items():
            setattr(client, field, value)
        try:
            database.commit()
        except IntegrityError as exc:
            database.rollback()
            raise ApplicationError(
                "CLIENT_DOCUMENT_ALREADY_EXISTS",
                "Ya existe un cliente con ese documento.",
                409,
            ) from exc
        database.refresh(client)
        return client

    def delete(self, database: Session, client_id: UUID) -> bool:
        client = self.get(database, client_id)
        if self.repository.has_shipments(database, client_id):
            client.is_active = False
            database.commit()
            return False
        database.delete(client)
        database.commit()
        return True
