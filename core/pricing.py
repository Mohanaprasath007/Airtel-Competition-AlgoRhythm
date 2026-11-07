"""
Pricing & Product Catalogue Engine
Project Udyam Digital - Accel Telecom
"""

import os
import pandas as pd
from typing import Dict, List, Optional, Tuple

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CATALOGUE_PATH = os.path.join(DATA_DIR, "product_catalogue.csv")


def load_catalogue() -> pd.DataFrame:
    """Loads and returns the product catalogue dataframe."""
    if not os.path.exists(CATALOGUE_PATH):
        raise FileNotFoundError(f"Product catalogue not found at {CATALOGUE_PATH}")
    return pd.read_csv(CATALOGUE_PATH)


class PricingEngine:
    def __init__(self, catalogue_df: Optional[pd.DataFrame] = None):
        self.catalogue = catalogue_df if catalogue_df is not None else load_catalogue()
        self.products_by_id = {row["product_id"]: row.to_dict() for _, row in self.catalogue.iterrows()}

    def get_product(self, product_id: str) -> Optional[Dict]:
        return self.products_by_id.get(product_id)

    def validate_dependencies(self, selected_product_ids: List[str]) -> Tuple[bool, List[str]]:
        """
        Validates if selected products satisfy the 'requires_one_of' dependency constraints.
        Returns (is_valid, list_of_error_messages).
        """
        errors = []
        selected_set = set(selected_product_ids)

        for pid in selected_product_ids:
            p = self.get_product(pid)
            if not p:
                errors.append(f"Product ID '{pid}' does not exist in catalogue.")
                continue

            requires = p.get("requires_one_of")
            if pd.notna(requires) and requires:
                prereqs = [x.strip() for x in str(requires).split("|")]
                if not any(req in selected_set for req in prereqs):
                    req_names = [self.products_by_id.get(r, {}).get("product_name", r) for r in prereqs]
                    errors.append(
                        f"'{p['product_name']}' ({pid}) requires at least one base connectivity product: {', '.join(req_names)}"
                    )

        return len(errors) == 0, errors

    def calculate_bundle_quote(
        self,
        product_items: List[Tuple[str, int]],  # list of (product_id, quantity)
        contract_months: int = 12,
        apply_partner_discount: bool = False
    ) -> Dict:
        """
        Calculates itemized quote including monthly recurring charges, one-time setup,
        contract tenure discounts, and estimated installation days.
        """
        itemized = []
        total_monthly_min = 0.0
        total_monthly_max = 0.0
        total_monthly_standard = 0.0
        total_setup_fee = 0.0
        max_install_days = 0

        product_ids = [pid for pid, _ in product_items]
        valid, dep_errors = self.validate_dependencies(product_ids)

        for pid, qty in product_items:
            p = self.get_product(pid)
            if not p:
                continue

            qty = max(1, qty)
            p_min = float(p["price_min_inr_per_month"]) * qty
            p_max = float(p["price_max_inr_per_month"]) * qty
            # Standard price is the midpoint / optimal package price
            p_std = ((p_min + p_max) / 2.0)
            setup = float(p["one_time_setup_inr"]) * qty
            install_days = int(p["typical_install_days"])

            total_monthly_min += p_min
            total_monthly_max += p_max
            total_monthly_standard += p_std
            total_setup_fee += setup
            if install_days > max_install_days:
                max_install_days = install_days

            itemized.append({
                "product_id": pid,
                "product_name": p["product_name"],
                "category": p["category"],
                "quantity": qty,
                "unit": p["unit"],
                "price_min": p_min,
                "price_max": p_max,
                "price_standard": p_std,
                "setup_fee": setup,
                "install_days": install_days
            })

        # Tenure discounts: 12 months = 5% off, 24 months = 10% off, 36 months = 15% off
        discount_pct = 0.0
        if contract_months >= 36:
            discount_pct = 0.15
        elif contract_months >= 24:
            discount_pct = 0.10
        elif contract_months >= 12:
            discount_pct = 0.05

        if apply_partner_discount:
            discount_pct += 0.05

        discount_amount = total_monthly_standard * discount_pct
        discounted_monthly = total_monthly_standard - discount_amount

        # Setup fee waiver on 24+ month contracts
        setup_fee_waived = False
        effective_setup_fee = total_setup_fee
        if contract_months >= 24:
            setup_fee_waived = True
            effective_setup_fee = 0.0

        # GST calculation (18%)
        gst_monthly = discounted_monthly * 0.18
        grand_total_monthly = discounted_monthly + gst_monthly

        return {
            "itemized_products": itemized,
            "dependency_valid": valid,
            "dependency_errors": dep_errors,
            "contract_months": contract_months,
            "raw_monthly_standard": round(total_monthly_standard, 2),
            "discount_percentage": round(discount_pct * 100, 1),
            "discount_amount": round(discount_amount, 2),
            "discounted_monthly_base": round(discounted_monthly, 2),
            "gst_monthly_18pct": round(gst_monthly, 2),
            "grand_total_monthly": round(grand_total_monthly, 2),
            "total_setup_fee_standard": round(total_setup_fee, 2),
            "effective_setup_fee": round(effective_setup_fee, 2),
            "setup_fee_waived": setup_fee_waived,
            "typical_install_days": max_install_days
        }

