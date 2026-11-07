"""
FastAPI REST API Service for Headless & Omnichannel Integration
Project Udyam Digital - Accel Telecom
"""

from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.pricing import PricingEngine, load_catalogue
from core.advisor import SmartAdvisor
from core.kyc_engine import SmartKYCEngine
from core.ml_scoring import LeadScoringEngine
from core.tracker import OrderTrackerEngine

app = FastAPI(
    title="Project Udyam Digital - Enterprise Onboarding API",
    description="Unified API powering GenAI Advisor, Smart KYC, Modular Pricing, and Propensity Analytics",
    version="1.0.0"
)

catalogue_df = load_catalogue()
pricing_engine = PricingEngine(catalogue_df)
advisor_engine = SmartAdvisor()
kyc_engine = SmartKYCEngine()
lead_engine = LeadScoringEngine()
tracker_engine = OrderTrackerEngine()


# --- Pydantic Request Models ---

class AdvisorRequest(BaseModel):
    business_type: str = Field(..., example="Dental Clinic")
    segment: str = Field(..., example="Professional offices")
    city_tier: int = Field(1, ge=1, le=2)
    employee_count: int = Field(5, ge=1)
    num_sites: int = Field(1, ge=1)
    has_gstin: bool = Field(True)
    current_internet: str = Field("Home Broadband")
    monthly_telecom_spend: float = Field(2500.0)
    priorities: List[str] = Field(default_factory=list, example=["cctv", "failover"])
    language: str = Field("en", example="en")


class QuoteRequest(BaseModel):
    product_items: List[List] = Field(..., example=[["P02", 1], ["P07", 2]])
    contract_months: int = Field(12, ge=1, le=36)
    apply_partner_discount: bool = Field(False)


class GSTINVerifyRequest(BaseModel):
    gstin: str = Field(..., example="32TTNXB7384T1ZW")


class UdyamVerifyRequest(BaseModel):
    udyam_number: str = Field(..., example="UDYAM-KL-00-3078801")


class LeadScoreRequest(BaseModel):
    city_tier: int = Field(1)
    employee_count: int = Field(8)
    num_sites: int = Field(1)
    monthly_telecom_spend_inr: float = Field(3500.0)
    has_gstin: str = Field("Y")
    has_udyam: str = Field("Y")
    lead_source: str = Field("Channel partner")
    segment: str = Field("Professional offices")
    drop_reason: Optional[str] = Field(None)


class CreateOrderRequest(BaseModel):
    customer_name: str
    business_name: str
    city: str
    products: List[str]
    monthly_total: float
    install_days: int = 5


# --- API Endpoints ---

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Project Udyam Digital REST API",
        "version": "1.0.0"
    }


@app.get("/api/catalogue")
def get_catalogue():
    return catalogue_df.to_dict(orient="records")


@app.post("/api/advisor/recommend")
def get_recommendation(req: AdvisorRequest):
    return advisor_engine.recommend_bundle(
        business_type=req.business_type,
        segment=req.segment,
        city_tier=req.city_tier,
        employee_count=req.employee_count,
        num_sites=req.num_sites,
        has_gstin=req.has_gstin,
        current_internet=req.current_internet,
        monthly_telecom_spend=req.monthly_telecom_spend,
        priorities=req.priorities,
        language=req.language
    )


@app.post("/api/pricing/quote")
def calculate_quote(req: QuoteRequest):
    items = [(item[0], int(item[1])) for item in req.product_items]
    return pricing_engine.calculate_bundle_quote(
        product_items=items,
        contract_months=req.contract_months,
        apply_partner_discount=req.apply_partner_discount
    )


@app.post("/api/kyc/verify-gstin")
def verify_gstin(req: GSTINVerifyRequest):
    is_valid, msg = kyc_engine.validate_gstin_format_and_checksum(req.gstin)
    registry_record = kyc_engine.lookup_gstin(req.gstin) if is_valid else None
    return {
        "gstin_input": kyc_engine.mask_gstin(req.gstin),
        "format_valid": is_valid,
        "format_message": msg,
        "found_in_registry": registry_record is not None,
        "registry_details": registry_record
    }


@app.post("/api/kyc/verify-udyam")
def verify_udyam(req: UdyamVerifyRequest):
    is_valid, msg = kyc_engine.validate_udyam_format(req.udyam_number)
    registry_record = kyc_engine.lookup_udyam(req.udyam_number) if is_valid else None
    return {
        "udyam_input": req.udyam_number,
        "format_valid": is_valid,
        "format_message": msg,
        "found_in_registry": registry_record is not None,
        "registry_details": registry_record
    }


@app.post("/api/leads/score")
def score_lead(req: LeadScoreRequest):
    return lead_engine.score_lead(req.model_dump())


@app.get("/api/leads/analytics")
def get_funnel_analytics():
    return lead_engine.get_funnel_analytics()


@app.get("/api/orders/{order_id}")
def get_order_status(order_id: str):
    res = tracker_engine.get_order(order_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return res


@app.post("/api/orders/create")
def create_order(req: CreateOrderRequest):
    return tracker_engine.create_new_order(
        customer_name=req.customer_name,
        business_name=req.business_name,
        city=req.city,
        product_names=req.products,
        monthly_total=req.monthly_total,
        install_days=req.install_days
    )

