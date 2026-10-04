from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class ReportPeriod(BaseModel):
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def validate_order(self) -> "ReportPeriod":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("report boundaries must include a timezone")
        return self


class DonorReceipt(BaseModel):
    receipt_number: str
    donor_name: str
    amount: Decimal = Field(gt=0)
    issued_at: datetime


class VolunteerReminder(BaseModel):
    volunteer_name: str
    activity: str
    scheduled_for: datetime
    acknowledged: bool = False


class CampaignResult(BaseModel):
    campaign_name: str
    raised: Decimal = Field(ge=0)
    goal: Decimal = Field(gt=0)
    report_date: date


class PeriodicReportRequest(BaseModel):
    organization_name: str
    period: ReportPeriod
    receipts: list[DonorReceipt] = Field(default_factory=list)
    volunteer_reminders: list[VolunteerReminder] = Field(default_factory=list)
    campaign_results: list[CampaignResult] = Field(default_factory=list)


class ReportRunResult(BaseModel):
    archive_record: str
    receipt_count: int
    reminder_count: int
    campaign_count: int
    pdf: dict[str, object]

