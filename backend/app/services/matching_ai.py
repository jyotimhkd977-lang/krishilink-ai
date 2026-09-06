"""Prototype buyer ranking service behind a replaceable model interface."""

from math import exp


class MatchingAIService:
    model_version = "prototype-v1"

    def rank(self, listing: dict, buyers: list[dict]) -> list[dict]:
        ranked = []
        for buyer in buyers:
            price_score = min(100, (buyer.get("offer_price", listing.get("asking_price", 0)) / max(listing.get("asking_price", 1), 1)) * 100)
            distance_score = max(0, 100 * exp(-buyer.get("distance_km", 100) / 50))
            quantity_score = min(100, (buyer.get("required_quantity", listing.get("quantity", 0)) / max(listing.get("quantity", 1), 1)) * 100)
            trust_score = float(buyer.get("trust_score", 0))
            payment_score = float(buyer.get("payment_reliability", 0))
            pickup_score = 100 if buyer.get("pickup_available", False) else 35
            score = (price_score * 0.28 + distance_score * 0.15 + quantity_score * 0.15 + trust_score * 0.18 + payment_score * 0.16 + pickup_score * 0.08)
            ranked.append({
                "buyer_id": buyer["buyer_id"],
                "business_name": buyer.get("business_name"),
                "match_score": round(min(100, max(0, score)), 2),
                "explanation": "Ranked using price, distance, quantity fit, trust, payment reliability, and pickup availability.",
            })
        return sorted(ranked, key=lambda item: item["match_score"], reverse=True)