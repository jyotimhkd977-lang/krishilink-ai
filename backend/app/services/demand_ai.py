"""Prototype demand forecasting service behind a replaceable model interface."""

from statistics import mean

from app.schemas.ai import DemandForecastInput, DemandForecastOutput


class DemandAIService:
    model_version = "prototype-v1"

    def predict(self, features: DemandForecastInput) -> DemandForecastOutput:
        order_average = mean(features.historical_orders)
        trend_average = mean(features.market_trends)
        predicted = max(0, order_average * 0.7 + trend_average * 0.3)
        ratio = predicted / max(order_average, 1)
        level = "high" if ratio >= 1.15 else "low" if ratio <= 0.85 else "medium"
        confidence = min(95, 55 + min(len(features.historical_orders), 12) * 2)
        return DemandForecastOutput(predicted_demand=round(predicted, 2), demand_level=level, confidence=round(confidence, 2))