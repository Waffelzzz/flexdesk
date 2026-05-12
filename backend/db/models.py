from __future__ import annotations

from datetime import date, datetime, time
from typing import List, Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    func,
    inspect
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    def to_dict(self) -> dict[str, Any]:
        """
        Универсальный метод для преобразования модели в словарь.
        """
        data = {}
        for column in inspect(self).mapper.column_attrs:
            key = column.key
            value = getattr(self, key)

            if isinstance(value, datetime):
                value = value.isoformat()

            data[key] = value

        return data


class Organization(Base):
    __tablename__ = "organizations"

    organization_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    admin_id: Mapped[int | None] = mapped_column(index=True)
    name: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    contact_info: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    time_gap: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="интервал / gap в минутах (например: 60 = 1 час)"
    )

    granular_step: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="шаг сетки расписания в минутах"
    )
    is_enable: Mapped[bool] = mapped_column(Boolean, default=True, index=True, comment="организация активна")

    services: Mapped[List["Service"]] = relationship(back_populates="organization")
    templates: Mapped[List["Template"]] = relationship(back_populates="organization")


class Service(Base):
    __tablename__ = "services"

    service_pk: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), index=True)
    name: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    service_group: Mapped[str | None] = mapped_column(String)

    organization: Mapped[Organization] = relationship(back_populates="services")
    service_masters: Mapped[List["ServiceMaster"]] = relationship(back_populates="service")


class ServiceMaster(Base):
    __tablename__ = "service_masters"

    service_master_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.service_pk"), index=True)
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.master_id"), index=True)
    price: Mapped[int | None] = mapped_column()
    price_grp: Mapped[int | None] = mapped_column()
    day_start: Mapped[date | None] = mapped_column(Date)
    day_finish: Mapped[date | None] = mapped_column(Date)
    is_enable: Mapped[bool] = mapped_column(default=True)
    duration: Mapped[int | None] = mapped_column()  # минуты?
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), index=True)

    service: Mapped[Service] = relationship(back_populates="service_masters")
    master: Mapped["Master"] = relationship(back_populates="service_masters")
    organization: Mapped[Organization] = relationship()


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str | None] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    middle_name: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(25))
    login: Mapped[str | None] = mapped_column(String(64))
    password: Mapped[str | None] = mapped_column(String(255))
    is_enable: Mapped[bool] = mapped_column(default=True)
    comments: Mapped[str | None] = mapped_column(Text)


class Client(Base):
    __tablename__ = "clients"

    client_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.account_id"), index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), index=True)

    account: Mapped[Account] = relationship()
    organization: Mapped[Organization] = relationship()
    bookings: Mapped[List["Booking"]] = relationship(back_populates="client")


class Manager(Base):
    __tablename__ = "managers"

    managers_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.account_id"), index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), index=True)

    account: Mapped[Account] = relationship()
    organization: Mapped[Organization] = relationship()


class Master(Base):
    __tablename__ = "masters"

    master_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.account_id"), index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), index=True)
    specialization: Mapped[str | None] = mapped_column()  # исправлена опечатка specialiation
    grade: Mapped[str | None] = mapped_column()

    account: Mapped[Account] = relationship()
    organization: Mapped[Organization] = relationship()
    service_masters: Mapped[List[ServiceMaster]] = relationship(back_populates="master")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="master")


class Booking(Base):
    __tablename__ = "booking"
    __table_args__ = (
        Index("ix_booking_master_dt", "booking_dt", "master_id"),
        Index("ix_booking_client", "client_id"),
        Index("ix_booking_organization", "organization_id"),
    )

    booking_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.client_id"), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("service_masters.service_master_id"), index=True)
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.master_id"), index=True)
    booking_dt: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str | None] = mapped_column(String(30))
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), index=True)

    client: Mapped[Client] = relationship(back_populates="bookings")
    service_master: Mapped[ServiceMaster] = relationship()
    master: Mapped[Master] = relationship(back_populates="bookings")
    organization: Mapped[Organization] = relationship()
    review: Mapped["Review"] = relationship(back_populates="booking", uselist=False)


class Review(Base):
    __tablename__ = "reviews"

    review_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("booking.booking_id"), index=True, unique=True)  # 1:1
    rating: Mapped[int | None] = mapped_column(SmallInteger)
    comment: Mapped[str | None] = mapped_column(Text)
    date: Mapped[date | None] = mapped_column(Date)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), index=True)

    booking: Mapped[Booking] = relationship(back_populates="review")
    organization: Mapped[Organization] = relationship()


class Template(Base):
    __tablename__ = "templates"

    template_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_name: Mapped[str | None] = mapped_column()
    week_day: Mapped[int | None] = mapped_column(SmallInteger)  # 0-6 или 1-7 ?
    time_from: Mapped[time | None] = mapped_column(Time)
    time_to: Mapped[time | None] = mapped_column(Time)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), index=True)

    organization: Mapped[Organization] = relationship(back_populates="templates")
    schedulers: Mapped[List["Scheduler"]] = relationship(back_populates="template")


class Scheduler(Base):
    __tablename__ = "schedulers"

    scheduler_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.master_id"), index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.template_id"), index=True)

    master: Mapped[Master] = relationship()
    template: Mapped[Template] = relationship(back_populates="schedulers")


class ClientArchive(Base):
    __tablename__ = "client_archive"

    client_archive_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.client_id"), index=True)
    service_master_id: Mapped[int] = mapped_column(ForeignKey("service_masters.service_master_id"), index=True)
    visit_start_dt: Mapped[datetime | None] = mapped_column(DateTime)  # исправлено имя visit_start_db → visit_start_dt
    visit_end_dt: Mapped[datetime | None] = mapped_column(DateTime)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), index=True)


class MasterArchive(Base):
    __tablename__ = "masters_archive"

    master_archive_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.master_id"), index=True)
    released_hours: Mapped[float | None] = mapped_column(Numeric)
    released_amount: Mapped[float | None] = mapped_column(Numeric)
    cheats_hours: Mapped[float | None] = mapped_column(Numeric)
    booking_count: Mapped[int | None] = mapped_column()
    work_day: Mapped[date | None] = mapped_column(Date)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), index=True)


class OrganizationArchive(Base):
    __tablename__ = "organization_archive"

    organization_archive_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    revenue: Mapped[float | None] = mapped_column(Numeric)
    booking_count: Mapped[int | None] = mapped_column()
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), index=True)
    work_period: Mapped[date | None] = mapped_column(Date)
