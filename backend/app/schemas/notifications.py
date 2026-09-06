"""Notification and preference schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    order = "ORDER"
    payment = "PAYMENT"
    buyer = "BUYER"
    ai_alert = "AI_ALERT"
    logistics = "LOGISTICS"
    weather = "WEATHER"
    quality = "QUALITY"
    dispute = "DISPUTE"


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: NotificationType
    title: str
    body: str
    data: dict = Field(default_factory=dict)
    read_at: datetime | None = None
    created_at: datetime


class NotificationPreferences(BaseModel):
    preferences: dict[NotificationType, bool]


class UnreadCountResponse(BaseModel):
    unread_count: int