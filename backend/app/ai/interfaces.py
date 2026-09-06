"""Stable interfaces that future trained models can implement."""

from typing import Protocol, Sequence


class PriceModel(Protocol):
    def predict(self, features: dict) -> dict: ...


class DemandModel(Protocol):
    def predict(self, features: dict) -> dict: ...


class MatchingModel(Protocol):
    def rank(self, listing: dict, buyers: Sequence[dict]) -> list[dict]: ...