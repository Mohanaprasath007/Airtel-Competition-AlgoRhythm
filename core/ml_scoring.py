"""
Machine Learning Lead Propensity & Partner Copilot Engine
Project Udyam Digital - Accel Telecom
"""

import os
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
LEADS_PATH = os.path.join(DATA_DIR, "smb_leads.csv")


class LeadScoringEngine:
    def __init__(self, leads_df: Optional[pd.DataFrame] = None):
        if leads_df is not None:
            self.df = leads_df
        elif os.path.exists(LEADS_PATH):
            self.df = pd.read_csv(LEADS_PATH)
        else:
            self.df = pd.DataFrame()

        self.model = None
        self.feature_columns = []
        if not self.df.empty:
            self._train_model()

    def _train_model(self):
        """Trains an ensemble lead propensity scoring model on the SMB leads dataset."""
        df_clean = self.df.copy()
        df_clean["target"] = (df_clean["outcome"] == "Activated").astype(int)

        base_num = ["city_tier", "employee_count", "num_sites", "monthly_telecom_spend_inr"]
        X = df_clean[base_num].copy()
        X["has_gstin"] = (df_clean["has_gstin"] == "Y").astype(int)
        X["has_udyam"] = (df_clean["has_udyam"] == "Y").astype(int)

        # Categorical dummies
        cats = pd.get_dummies(df_clean[["lead_source", "segment"]], drop_first=False)
        X = pd.concat([X, cats], axis=1)

        self.feature_columns = list(X.columns)
        y = df_clean["target"]

        # Train Random Forest Classifier
        self.model = RandomForestClassifier(
            n_estimators=120,
            max_depth=7,
            min_samples_split=8,
            random_state=42
        )
        self.model.fit(X, y)

    def score_lead(self, lead_dict: Dict) -> Dict:
        """
        Scores a single lead and returns propensity probability, tier, and Next Best Action.
        """
        if self.model is None or not self.feature_columns:
            return {"propensity_score": 0.5, "tier": "Medium", "next_best_action": "Follow up via phone"}

        # Construct feature vector
        row = {col: 0 for col in self.feature_columns}
        row["city_tier"] = int(lead_dict.get("city_tier", 1))
        row["employee_count"] = int(lead_dict.get("employee_count", 5))
        row["num_sites"] = int(lead_dict.get("num_sites", 1))
        row["monthly_telecom_spend_inr"] = float(lead_dict.get("monthly_telecom_spend_inr", 2000.0))
        row["has_gstin"] = 1 if lead_dict.get("has_gstin") in [True, "Y", "yes", 1] else 0
        row["has_udyam"] = 1 if lead_dict.get("has_udyam") in [True, "Y", "yes", 1] else 0

        source_col = f"lead_source_{lead_dict.get('lead_source', 'Website form')}"
        if source_col in row:
            row[source_col] = 1

        seg_col = f"segment_{lead_dict.get('segment', 'Micro retail & services')}"
        if seg_col in row:
            row[seg_col] = 1

        x_vec = pd.DataFrame([row])[self.feature_columns]
        prob = float(self.model.predict_proba(x_vec)[0, 1])

        # Normalize score to 0-100 range for display
        score_pct = round(prob * 100, 1)

        # Determine tier
        if score_pct >= 60.0:
            tier = "High"
            tier_color = "green"
        elif score_pct >= 30.0:
            tier = "Medium"
            tier_color = "orange"
        else:
            tier = "Low"
            tier_color = "red"

        # Determine Next Best Action (NBA)
        nba = self._derive_next_best_action(lead_dict, score_pct)

        return {
            "propensity_score": score_pct,
            "tier": tier,
            "tier_color": tier_color,
            "next_best_action": nba["action"],
            "recommended_channel": nba["channel"],
            "urgency": nba["urgency"],
            "talking_points": nba["talking_points"]
        }

    def _derive_next_best_action(self, lead: Dict, score: float) -> Dict:
        has_gst = lead.get("has_gstin") in [True, "Y", "yes", 1]
        spend = float(lead.get("monthly_telecom_spend_inr", 1500))
        drop_reason = str(lead.get("drop_reason", ""))

        if not has_gst:
            return {
                "action": "Offer Simplified Non-GST Biz 5G AirFiber + Assist with Udyam Registration",
                "channel": "WhatsApp Interactive Assistant",
                "urgency": "High",
                "talking_points": [
                    "Non-GST businesses can onboard instantly with Biz 5G AirFiber (P04).",
                    "Offer 1-click free Udyam registration assistance directly through partner app.",
                    "Highlight UPI payment stability guarantee for kiranas/salons."
                ]
            }

        if "Quote too complex" in drop_reason or "Quote took too long" in drop_reason:
            return {
                "action": "Dispatch Instant 1-Page Consolidated Digital Quote with 10% First-Year Discount",
                "channel": "Direct WhatsApp & Email PDF",
                "urgency": "Immediate (Within 2 Hours)",
                "talking_points": [
                    "Eliminate product code confusion: show transparent flat monthly billing.",
                    "Waiver of setup fee on 24-month contract.",
                    "Dedicated onboarding manager assigned."
                ]
            }

        if score >= 60.0:
            return {
                "action": "Priority Field Visit by Senior Enterprise Specialist",
                "channel": "In-Person Field Sales",
                "urgency": "Within 24 Hours",
                "talking_points": [
                    f"Customer current spend is ₹{spend:,.0f} - pitch consolidated multi-product bundle.",
                    "Demonstrate cloud backup, 4G failover, and dual-SIM enterprise plans.",
                    "Commit to 5-day SLA activation."
                ]
            }

        return {
            "action": "Nurture via Self-Serve Digital Trial & Demo Video",
            "channel": "Automated WhatsApp Campaign",
            "urgency": "Standard",
            "talking_points": [
                "Send 90-second customer testimonial from similar businesses in the city.",
                "Offer 14-day zero-risk trial of cloud telephony or endpoint security."
            ]
        }

    def get_funnel_analytics(self) -> Dict:
        """Returns macro funnel conversion statistics and drop-off diagnosis."""
        if self.df.empty:
            return {}

        total_leads = len(self.df)
        contacted = len(self.df[self.df["contacted_date"].notna()])
        needs = len(self.df[self.df["needs_assessed_date"].notna()])
        quote = len(self.df[self.df["quote_accepted_date"].notna()])
        kyc = len(self.df[self.df["kyc_complete_date"].notna()])
        activated = len(self.df[self.df["activated_date"].notna()])

        # GSTIN impact
        gst_leads = self.df[self.df["has_gstin"] == "Y"]
        non_gst_leads = self.df[self.df["has_gstin"] == "N"]

        gst_act_rate = (len(gst_leads[gst_leads["outcome"] == "Activated"]) / len(gst_leads)) * 100 if len(gst_leads) else 0
        non_gst_act_rate = (len(non_gst_leads[non_gst_leads["outcome"] == "Activated"]) / len(non_gst_leads)) * 100 if len(non_gst_leads) else 0

        # Activated stats
        act_subset = self.df[self.df["outcome"] == "Activated"]
        avg_cycle_days = act_subset["days_lead_to_activation"].mean() if not act_subset.empty else 17.6
        avg_calls = act_subset["customer_follow_up_calls"].mean() if not act_subset.empty else 3.1
        avg_nps = act_subset["nps_score"].mean() if not act_subset.empty else 8.4
        blended_cac = self.df["acquisition_cost_inr"].sum() / activated if activated > 0 else 15000

        top_drop_reasons = self.df["drop_reason"].value_counts().head(8).to_dict()

        return {
            "funnel_stages": {
                "Leads Generated": total_leads,
                "Contacted": contacted,
                "Needs Assessed": needs,
                "Quote Accepted": quote,
                "KYC Completed": kyc,
                "Activated": activated
            },
            "gstin_activation_rate_pct": round(gst_act_rate, 2),
            "non_gstin_activation_rate_pct": round(non_gst_act_rate, 2),
            "average_cycle_days": round(avg_cycle_days, 1),
            "average_follow_up_calls": round(avg_calls, 1),
            "average_nps": round(avg_nps, 1),
            "blended_cac_inr": round(blended_cac, 0),
            "top_drop_reasons": top_drop_reasons
        }

