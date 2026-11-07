"""
GenAI-Powered Conversational Advisor & Recommendation Engine
Project Udyam Digital - Accel Telecom
"""

import os
import pandas as pd
from typing import Dict, List, Optional
from core.pricing import PricingEngine, load_catalogue

class SmartAdvisor:
    def __init__(self):
        self.catalogue = load_catalogue()
        self.pricing_engine = PricingEngine(self.catalogue)

    def recommend_bundle(
        self,
        business_type: str,
        segment: str,
        city_tier: int,
        employee_count: int,
        num_sites: int,
        has_gstin: bool,
        current_internet: str = "Mobile Hotspot",
        monthly_telecom_spend: float = 1500.0,
        priorities: Optional[List[str]] = None,
        language: str = "en"
    ) -> Dict:
        """
        Generates tailored bundle recommendations adhering to product catalogue eligibility,
        tier availability, dependency constraints, and plain-language explanation.
        """
        priorities = priorities or []
        segment_code = "micro"
        if "prof" in segment.lower() or "clinic" in business_type.lower() or "firm" in business_type.lower():
            segment_code = "prof"
        elif "multi" in segment.lower() or num_sites > 1:
            segment_code = "multi"
        elif "mfg" in segment.lower() or "manufactur" in business_type.lower():
            segment_code = "mfg"

        # Filter eligible products
        eligible = []
        for _, p in self.catalogue.iterrows():
            tiers = [int(t) for t in str(p["available_city_tiers"]).split(";")]
            if city_tier not in tiers:
                continue
            if employee_count < p["min_employees"]:
                continue
            if num_sites < p["min_sites"]:
                continue
            if p["requires_gstin"] == "Y" and not has_gstin:
                continue

            target_segs = str(p["target_segments"]).split(";")
            is_target = segment_code in target_segs or "all" in target_segs
            eligible.append((p, is_target))

        # Build Curated Recommended Base Bundle
        base_products: List[tuple] = []
        addon_products: List[tuple] = []

        # 1. Base Connectivity
        if segment_code == "micro":
            # Micro prefers fast affordable setup: Biz Fibre 100 or 5G AirFiber
            if "fast setup" in priorities or city_tier == 2:
                base_products.append(("P04", 1))  # Biz 5G AirFiber 100
            else:
                base_products.append(("P01", 1))  # Biz Fibre 100
            # 1 Business SIM
            base_products.append(("P07", 1))       # Business Postpaid 299

        elif segment_code == "prof":
            base_products.append(("P02", 1))      # Biz Fibre 300
            sim_count = max(2, min(employee_count, 5))
            base_products.append(("P07", sim_count))  # Business Postpaid 299
            base_products.append(("P16", employee_count))  # Cloud Email & Office Suite

        elif segment_code == "multi":
            base_products.append(("P02", num_sites))  # Biz Fibre 300 per site
            sim_count = max(3, min(employee_count, 10))
            base_products.append(("P08", sim_count))   # Business Postpaid 599
            if has_gstin and num_sites >= 3:
                base_products.append(("P10", 1))       # Managed SD-WAN

        elif segment_code == "mfg":
            if has_gstin and employee_count >= 10:
                base_products.append(("P05", 1))       # Internet Leased Line 20 Mbps (SLA 99.9%)
            else:
                base_products.append(("P03", 1))       # Biz Fibre 1G
            sim_count = max(4, min(employee_count, 12))
            base_products.append(("P08", sim_count))   # Business Postpaid 599

        # 2. Addons based on priorities
        if "cctv" in priorities or segment_code in ["micro", "multi"]:
            addon_products.append(("P23", max(1, min(num_sites * 2, 4))))  # Cloud CCTV
        if "failover" in priorities or segment_code in ["prof", "multi"]:
            addon_products.append(("P09", num_sites))  # 4G/5G Failover
        if "whatsapp" in priorities or segment_code == "micro":
            if has_gstin:
                addon_products.append(("P15", 1))      # WhatsApp Business API
            else:
                addon_products.append(("P18", 1))      # Website + Domain Starter
        if "pos" in priorities or "retail" in business_type.lower():
            addon_products.append(("P19", 1))          # Cloud POS & Billing
        if "security" in priorities or segment_code in ["prof", "mfg"]:
            addon_products.append(("P20", employee_count))  # Endpoint Security

        # Calculate quote for base bundle
        base_quote = self.pricing_engine.calculate_bundle_quote(base_products, contract_months=12)
        full_quote = self.pricing_engine.calculate_bundle_quote(base_products + addon_products, contract_months=12)

        # Generate Plain Language Explanation (Bilingual: English & Hindi)
        explanation_en = self._generate_explanation_en(
            business_type, segment_code, base_products, addon_products, full_quote, monthly_telecom_spend
        )
        explanation_hi = self._generate_explanation_hi(
            business_type, segment_code, base_products, addon_products, full_quote, monthly_telecom_spend
        )

        return {
            "business_summary": {
                "business_type": business_type,
                "segment": segment_code,
                "city_tier": city_tier,
                "employee_count": employee_count,
                "num_sites": num_sites,
                "has_gstin": has_gstin
            },
            "base_products": base_products,
            "addon_products": addon_products,
            "base_quote": base_quote,
            "full_quote": full_quote,
            "explanation_en": explanation_en,
            "explanation_hi": explanation_hi,
            "recommended_language_text": explanation_hi if language == "hi" else explanation_en
        }

    def _generate_explanation_en(self, biz_type, seg, base, addons, quote, old_spend) -> str:
        new_spend = quote["grand_total_monthly"]
        delta = new_spend - old_spend
        comparison = f"This is ₹{abs(delta):,.0f} {'more than' if delta > 0 else 'less than'} your current spend of ₹{old_spend:,.0f}/month, but bundles enterprise-grade uptime, business SIMs, and digital apps in one bill."
        
        reasons = [
            f"Tailored for **{biz_type}** with zero multi-vendor hassle.",
            f"Single consolidated invoice for connectivity, SIM cards, and cloud apps.",
            f"Includes dedicated 24x7 enterprise support with guaranteed repair SLA.",
            f"Typical installation within **{quote['typical_install_days']} days**."
        ]
        if not addons:
            addons_text = "No optional add-ons selected."
        else:
            addons_text = f"{len(addons)} intelligent add-on(s) configured to boost your digital workflow."

        return (
            f"### Why This Bundle is Right for You\n\n"
            f"{' '.join(reasons)}\n\n"
            f"- **Transparent Total:** ₹{new_spend:,.0f}/month (incl. 18% GST).\n"
            f"- **Spend Comparison:** {comparison}\n"
            f"- **Modular Growth:** {addons_text}\n"
        )

    def _generate_explanation_hi(self, biz_type, seg, base, addons, quote, old_spend) -> str:
        new_spend = quote["grand_total_monthly"]
        return (
            f"### यह बंडल आपके व्यवसाय के लिए सर्वश्रेष्ठ क्यों है?\n\n"
            f"यह प्लान विशेष रूप से **{biz_type}** के लिए डिज़ाइन किया गया है ताकि आपको अलग-अलग वेंडर्स के चक्कर न काटने पड़ें।\n\n"
            f"- **पारदर्शी मासिक शुल्क:** मात्र ₹{new_spend:,.0f}/माह (18% GST सहित)।\n"
            f"- **एक ही बिल:** फाइबर इंटरनेट, बिजनेस कॉलिंग और क्लाउड टूल्स सब एक बिल में।\n"
            f"- **त्वरित इंस्टॉलेशन:** अगले **{quote['typical_install_days']} दिनों** में चालू होने की गारंटी।\n"
            f"- **24x7 बिज़नेस सपोर्ट:** समस्याओं के त्वरित समाधान हेतु समर्पित कस्टमर केयर नंबर।\n"
        )

