"""Pricing policies for hotel stays."""

from .pricing_strategy import PricingStrategy
from .standard_pricing_strategy import StandardPricingStrategy
from .weekend_pricing_decorator import WeekendPricingDecorator

__all__ = ["PricingStrategy", "StandardPricingStrategy", "WeekendPricingDecorator"]
