"""Product identifiers & barcode rendering application service for Phase 023."""

import io
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select, update
from sqlalchemy.orm import Session
import qrcode

from app.modules.logistics.products.gtin_validator import ProductIdentifierValidator
from app.modules.logistics.products.models import ProductIdentifierModel, ProductModel


class ProductIdentifierService:
    def __init__(self, db: Session):
        self.db = db

    def add_identifier(
        self,
        organization_id: UUID,
        product_id: UUID,
        identifier_type: str,
        value: str,
        is_primary: bool = False,
        symbology: Optional[str] = None,
        issuer: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> ProductIdentifierModel:
        product = self.db.get(ProductModel, product_id)
        if not product or product.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        # Validate GTIN or internal barcode
        is_valid, norm_val, ver_status, err_msg = ProductIdentifierValidator.validate_gtin(identifier_type, value)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

        # Check uniqueness per org
        stmt = select(ProductIdentifierModel).where(
            ProductIdentifierModel.organization_id == organization_id,
            ProductIdentifierModel.normalized_value == norm_val,
        )
        if self.db.scalar(stmt):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Identifier value '{value}' is already assigned to another product in this organization.",
            )

        if is_primary:
            # Demote existing primary identifiers of same type
            self.db.execute(
                update(ProductIdentifierModel)
                .where(
                    ProductIdentifierModel.product_id == product_id,
                    ProductIdentifierModel.identifier_type == identifier_type,
                )
                .values(is_primary=False)
            )

        ident = ProductIdentifierModel(
            organization_id=organization_id,
            product_id=product_id,
            identifier_type=identifier_type,
            value=value.strip(),
            normalized_value=norm_val,
            symbology=symbology or "CODE128",
            issuer=issuer,
            is_primary=is_primary,
            status="ACTIVE",
            verified_status=ver_status,
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(ident)
        self.db.commit()
        self.db.refresh(ident)
        return ident

    def render_barcode_png(self, identifier_id: UUID) -> Response:
        ident = self.db.get(ProductIdentifierModel, identifier_id)
        if not ident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Identifier not found.")

        # Generate QR barcode representation
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(ident.normalized_value)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return Response(content=buf.getvalue(), media_type="image/png")

    def list_identifiers(self, product_id: UUID) -> List[ProductIdentifierModel]:
        stmt = select(ProductIdentifierModel).where(
            ProductIdentifierModel.product_id == product_id
        ).order_by(ProductIdentifierModel.is_primary.desc())
        return list(self.db.scalars(stmt).all())
