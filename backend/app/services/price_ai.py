"""Prototype price prediction service behind a replaceable model interface."""

from statistics import mean

from app.schemas.ai import PricePredictionInput, PricePredictionOutput, PriceRange


class PriceAIService:
    model_version = "prototype-v1"

    def predict(self, features: PricePredictionInput) -> PricePredictionOutput:
        historical_average = mean(features.historical_price)
        market_weight = (features.market_price * 0.55) + (historical_average * 0.45)
        balance = min(max((features.demand / features.supply) * 0.08, -0.15), 0.15)
        predicted = max(0, market_weight * (1 + balance))
        spread = max(predicted * 0.08, 0.01)
        confidence = min(95, 55 + min(len(features.historical_price), 12) * 2 + (10 if features.demand > 0 else 0))
        recommendation = "Hold for a stronger demand window" if features.demand > features.supply else "Consider selling at the predicted range"
        return PricePredictionOutput(
            predicted_price=round(predicted, 2),
            price_range=PriceRange(minimum=round(max(0, predicted - spread), 2), maximum=round(predicted + spread, 2)),
            recommendation=recommendation,
            confidence_score=round(confidence, 2),
        )