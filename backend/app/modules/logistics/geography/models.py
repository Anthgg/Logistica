"""SQLAlchemy models for canonical Peruvian geographic administrative divisions (UBIGEO)."""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class GeoDepartment(Base):
    """First-level administrative division: 25 Departments of Peru."""

    __tablename__ = "geo_departments"

    code: Mapped[str] = mapped_column(String(2), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    provinces: Mapped[list["GeoProvince"]] = relationship(
        back_populates="department", cascade="all, delete-orphan", passive_deletes=True
    )
    districts: Mapped[list["GeoDistrict"]] = relationship(
        back_populates="department", cascade="all, delete-orphan", passive_deletes=True
    )


class GeoProvince(Base):
    """Second-level administrative division: 196 Provinces of Peru."""

    __tablename__ = "geo_provinces"

    code: Mapped[str] = mapped_column(String(4), primary_key=True)
    department_code: Mapped[str] = mapped_column(
        String(2),
        ForeignKey("geo_departments.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    department: Mapped["GeoDepartment"] = relationship(back_populates="provinces")
    districts: Mapped[list["GeoDistrict"]] = relationship(
        back_populates="province", cascade="all, delete-orphan", passive_deletes=True
    )


class GeoDistrict(Base):
    """Third-level administrative division: Districts (canonical 6-digit UBIGEO)."""

    __tablename__ = "geo_districts"

    code: Mapped[str] = mapped_column(String(6), primary_key=True)
    province_code: Mapped[str] = mapped_column(
        String(4),
        ForeignKey("geo_provinces.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_code: Mapped[str] = mapped_column(
        String(2),
        ForeignKey("geo_departments.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    province: Mapped["GeoProvince"] = relationship(back_populates="districts")
    department: Mapped["GeoDepartment"] = relationship(back_populates="districts")
