from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enum matching Stripe statuses"""
    ACTIVE = "active"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    UNPAID = "unpaid"


class SubscriptionTier(str, enum.Enum):
    """Subscription tier/plan types"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Stripe subscription details
    stripe_subscription_id = Column(String, unique=True, nullable=True, index=True)
    stripe_price_id = Column(String, nullable=True)
    stripe_product_id = Column(String, nullable=True)
    
    # Subscription info
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.INCOMPLETE, nullable=False)
    
    # Dates
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier='{self.tier}', status='{self.status}')>"