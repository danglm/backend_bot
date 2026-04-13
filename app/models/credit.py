from sqlalchemy import Column, Integer, String, Float, Date, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
import enum

class CreditStatus(str, enum.Enum):
    ACTIVE = "active" ## Đang vay
    PAID = "paid" ## Đã tất toán khoản vay
    CANCELLED = "cancelled" ## Đã hủy hợp đồng
    BAD_DEBT = "bad_debt" ## Nợ xấu (Blacklist)

class CreditCustomer(Base):
    __tablename__ = "credit_customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_name = Column(String)
    customer_name = Column(String)
    contact_info = Column(String)  # telegram_username / contact_info
    total_credit_limit = Column(Float)
    remaining_credit_limit = Column(Float)
    total_principal_outstanding = Column(Float)

    credits = relationship("Credit", back_populates="customer")

class Credit(Base):
    __tablename__ = "credits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("credit_customers.id"))

    contract_id = Column(String)  # contract_id / contract_code
    loan_type = Column(String)  # Collateral / Unsecured
    initial_principal = Column(Float)
    start_date = Column(Date)
    due_date = Column(Date)  # due_date / maturity_date
    interest_start_date = Column(Date)
    monthly_interest_rate = Column(Float)
    monthly_interest_amount = Column(Float)
    total_principal_paid = Column(Float)
    remaining_principal = Column(Float)
    notes = Column(String)
    send_message_arise = Column(Boolean, default=False)
    message_content = Column(String)
    credit_status = Column(String)
    interest_debt = Column(Float, default=0.0)
    last_interest_charged_date = Column(Date, nullable=True)

    customer = relationship("CreditCustomer", back_populates="credits")

class CreditInterest(Base):
    __tablename__ = "credit_interests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(String)
    interest_payment_date = Column(Date)
    payment_time = Column(DateTime)
    interest_amount = Column(Float)
