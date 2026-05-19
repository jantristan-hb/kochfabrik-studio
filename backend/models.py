"""US-002 — SQLAlchemy 2 Schema (EPIC-001 Persistenz).

app_user · customer (Kundennummer 100001-A) · offer (Angebotsnummer +
voller Angebot-State JSONB) · chat_message (S2-Nutzung) · seq_counter
(atomare Nummern, US-003).
"""
from datetime import datetime

from sqlalchemy import (BigInteger, DateTime, ForeignKey, Integer,
                        String, Text, func)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                            relationship)


class Base(DeclarativeBase):
    pass


class AppUser(Base):
    __tablename__ = "app_user"
    email: Mapped[str] = mapped_column(String(320), primary_key=True)
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())


class Customer(Base):
    __tablename__ = "customer"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True,
                                    autoincrement=True)
    kundennummer: Mapped[str] = mapped_column(String(32), unique=True,
                                              index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    owner_email: Mapped[str] = mapped_column(
        ForeignKey("app_user.email"), index=True)
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    offers: Mapped[list["Offer"]] = relationship(back_populates="customer")


class Offer(Base):
    __tablename__ = "offer"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True,
                                    autoincrement=True)
    angebotsnummer: Mapped[str] = mapped_column(String(32), unique=True,
                                                index=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customer.id"), index=True)
    owner_email: Mapped[str] = mapped_column(
        ForeignKey("app_user.email"), index=True)
    state: Mapped[dict] = mapped_column(JSONB)        # volles Angebot-JSON
    status: Mapped[str] = mapped_column(String(16), default="draft")
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now())
    customer: Mapped["Customer"] = relationship(back_populates="offers")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="offer", cascade="all, delete-orphan")


class ChatMessage(Base):                              # S2-Nutzung
    __tablename__ = "chat_message"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True,
                                    autoincrement=True)
    offer_id: Mapped[int] = mapped_column(
        ForeignKey("offer.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))     # me|bot
    content: Mapped[str] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    offer: Mapped["Offer"] = relationship(back_populates="messages")


class SeqCounter(Base):
    __tablename__ = "seq_counter"
    name: Mapped[str] = mapped_column(String(32), primary_key=True)
    value: Mapped[int] = mapped_column(Integer, default=0)
