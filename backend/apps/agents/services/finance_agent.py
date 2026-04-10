"""
Finance Agent Service
AI-powered budget tracking, savings discovery, and budget optimization for trips.
"""
import hashlib
import json
import logging
import os
import random
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class FinanceAgent:
    """Tracks budgets, finds savings, and optimises trip spending."""

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def track_budget(
        self,
        destination: str,
        budget: float,
        items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Analyse spending against budget.

        Parameters
        ----------
        destination : str
            The trip destination.
        budget : float
            Total trip budget.
        items : list[dict]
            Each item has keys: type, name, cost.

        Returns
        -------
        dict with total_spent, remaining, percentage_used,
        breakdown_by_category, savings_tips, status.
        """
        total_spent = sum(float(item.get('cost', 0)) for item in items)
        remaining = budget - total_spent
        percentage_used = round((total_spent / budget) * 100, 1) if budget else 0

        # Breakdown by category (item 'type')
        breakdown: Dict[str, float] = {}
        for item in items:
            cat = item.get('type', 'other')
            breakdown[cat] = round(breakdown.get(cat, 0) + float(item.get('cost', 0)), 2)

        if percentage_used > 100:
            budget_status = 'over_budget'
        elif percentage_used < 70:
            budget_status = 'under_budget'
        else:
            budget_status = 'on_track'

        # Try OpenAI for savings tips, fall back to deterministic
        savings_tips = self._savings_tips_openai(destination, budget, items, remaining)
        if savings_tips is None:
            savings_tips = self._savings_tips_fallback(destination, budget, items, remaining)

        return {
            'total_spent': round(total_spent, 2),
            'remaining': round(remaining, 2),
            'percentage_used': percentage_used,
            'breakdown_by_category': breakdown,
            'savings_tips': savings_tips,
            'status': budget_status,
        }

    def find_savings(
        self,
        destination: str,
        current_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Suggest cheaper alternatives for current spending items.

        Returns list of {original_item, suggested_alternative,
                         potential_saving, tip}.
        """
        result = self._find_savings_openai(destination, current_items)
        if result is not None:
            return result
        return self._find_savings_fallback(destination, current_items)

    def optimize_budget(
        self,
        destination: str,
        budget: float,
        start_date: str,
        end_date: str,
        travelers: int = 1,
    ) -> Dict[str, Any]:
        """
        Return optimal budget allocation across categories.

        Returns dict with flights_budget, hotels_budget, food_budget,
        activities_budget, transport_budget, emergency_fund and their
        percentages.
        """
        result = self._optimize_openai(destination, budget, start_date, end_date, travelers)
        if result is not None:
            return result
        return self._optimize_fallback(destination, budget, start_date, end_date, travelers)

    # ------------------------------------------------------------------ #
    #  OpenAI helpers
    # ------------------------------------------------------------------ #

    def _savings_tips_openai(
        self, destination, budget, items, remaining,
    ) -> Optional[List[str]]:
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini', temperature=0.5,
                api_key=api_key, request_timeout=30,
            )
            response = model.invoke([
                SystemMessage(content=(
                    "You are a travel finance advisor. "
                    "Return a JSON array of 3-5 short savings tips. No markdown fences."
                )),
                HumanMessage(content=(
                    f"Destination: {destination}\n"
                    f"Budget: ${budget}, Remaining: ${remaining}\n"
                    f"Items: {json.dumps(items)}\n"
                    "Give 3-5 actionable money-saving tips."
                )),
            ])
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            tips = json.loads(content)
            if isinstance(tips, list):
                return [str(t) for t in tips[:5]]
            return None
        except Exception as e:
            logger.warning("OpenAI savings tips failed: %s", e)
            return None

    def _find_savings_openai(
        self, destination, current_items,
    ) -> Optional[List[Dict[str, Any]]]:
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini', temperature=0.5,
                api_key=api_key, request_timeout=30,
            )
            response = model.invoke([
                SystemMessage(content=(
                    "You are a travel finance advisor. "
                    "Return JSON only, no markdown fences."
                )),
                HumanMessage(content=(
                    f"Destination: {destination}\n"
                    f"Current items: {json.dumps(current_items)}\n\n"
                    "For each item, suggest a cheaper alternative. Return a JSON array:\n"
                    '[{"original_item": "<name>", "suggested_alternative": "<alt>", '
                    '"potential_saving": <float>, "tip": "<advice>"}]'
                )),
            ])
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, list):
                return data
            return None
        except Exception as e:
            logger.warning("OpenAI find_savings failed: %s", e)
            return None

    def _optimize_openai(
        self, destination, budget, start_date, end_date, travelers,
    ) -> Optional[Dict[str, Any]]:
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini', temperature=0.4,
                api_key=api_key, request_timeout=30,
            )
            response = model.invoke([
                SystemMessage(content=(
                    "You are a travel budget optimizer. "
                    "Return JSON only, no markdown fences."
                )),
                HumanMessage(content=(
                    f"Destination: {destination}\nBudget: ${budget}\n"
                    f"Dates: {start_date} to {end_date}\nTravelers: {travelers}\n\n"
                    "Return optimal allocation as JSON:\n"
                    '{"flights_budget": <float>, "hotels_budget": <float>, '
                    '"food_budget": <float>, "activities_budget": <float>, '
                    '"transport_budget": <float>, "emergency_fund": <float>, '
                    '"flights_pct": <float>, "hotels_pct": <float>, '
                    '"food_pct": <float>, "activities_pct": <float>, '
                    '"transport_pct": <float>, "emergency_pct": <float>}'
                )),
            ])
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, dict):
                return data
            return None
        except Exception as e:
            logger.warning("OpenAI budget optimize failed: %s", e)
            return None

    # ------------------------------------------------------------------ #
    #  Deterministic fallbacks
    # ------------------------------------------------------------------ #

    def _savings_tips_fallback(
        self, destination, budget, items, remaining,
    ) -> List[str]:
        seed = int(
            hashlib.md5(f"tips:{destination}:{budget}".encode()).hexdigest()[:8], 16,
        )
        rng = random.Random(seed)
        pool = [
            f"Use public transport in {destination} instead of taxis to save 40-60%.",
            f"Eat at local markets in {destination} for meals at half the restaurant price.",
            "Book attractions online in advance for early-bird discounts of 10-20%.",
            "Travel during shoulder season for lower accommodation rates.",
            "Use a travel rewards credit card to earn points on every purchase.",
            f"Look for free walking tours in {destination} to explore without spending.",
            "Cook some meals at your accommodation if a kitchen is available.",
            "Compare prices on multiple booking platforms before committing.",
            "Avoid exchanging currency at airports; use local ATMs instead.",
            "Set a daily spending limit and track expenses with a budgeting app.",
        ]
        rng.shuffle(pool)
        # Choose 3-5 tips based on budget status
        tip_count = 5 if remaining < budget * 0.3 else 3
        return pool[:tip_count]

    def _find_savings_fallback(
        self, destination, current_items,
    ) -> List[Dict[str, Any]]:
        seed = int(
            hashlib.md5(
                f"savings:{destination}:{len(current_items)}".encode()
            ).hexdigest()[:8], 16,
        )
        rng = random.Random(seed)

        alt_map = {
            'flight': {
                'alt': 'Budget airline or connecting flight',
                'pct': (0.15, 0.35),
                'tip': 'Book 6-8 weeks ahead and use fare comparison tools.',
            },
            'hotel': {
                'alt': 'Hostel, guesthouse, or vacation rental',
                'pct': (0.20, 0.45),
                'tip': 'Consider staying slightly outside the city centre.',
            },
            'restaurant': {
                'alt': 'Street food or local market eatery',
                'pct': (0.30, 0.60),
                'tip': 'Ask locals for their favourite affordable spots.',
            },
            'transport': {
                'alt': 'Day pass or shared ride service',
                'pct': (0.20, 0.40),
                'tip': 'Purchase multi-day transit passes for best value.',
            },
            'activity': {
                'alt': 'Free walking tour or self-guided visit',
                'pct': (0.25, 0.50),
                'tip': 'Many museums have free-entry days or hours.',
            },
        }

        results = []
        for item in current_items:
            item_type = item.get('type', 'other').lower()
            cost = float(item.get('cost', 0))
            info = alt_map.get(item_type, {
                'alt': 'Lower-cost alternative',
                'pct': (0.10, 0.30),
                'tip': 'Compare options online before purchasing.',
            })
            saving_pct = rng.uniform(*info['pct'])
            results.append({
                'original_item': item.get('name', item_type),
                'suggested_alternative': info['alt'],
                'potential_saving': round(cost * saving_pct, 2),
                'tip': info['tip'],
            })

        return results

    def _optimize_fallback(
        self, destination, budget, start_date, end_date, travelers,
    ) -> Dict[str, Any]:
        seed = int(
            hashlib.md5(
                f"opt:{destination}:{budget}:{travelers}".encode()
            ).hexdigest()[:8], 16,
        )
        rng = random.Random(seed)

        # Base percentages with slight randomisation
        base = {
            'flights': 0.25,
            'hotels': 0.30,
            'food': 0.15,
            'activities': 0.12,
            'transport': 0.08,
            'emergency': 0.10,
        }

        # Add small jitter
        raw = {k: max(0.05, v + rng.uniform(-0.03, 0.03)) for k, v in base.items()}
        total_raw = sum(raw.values())
        # Normalise to 100%
        pcts = {k: round(v / total_raw * 100, 1) for k, v in raw.items()}

        return {
            'flights_budget': round(budget * pcts['flights'] / 100, 2),
            'hotels_budget': round(budget * pcts['hotels'] / 100, 2),
            'food_budget': round(budget * pcts['food'] / 100, 2),
            'activities_budget': round(budget * pcts['activities'] / 100, 2),
            'transport_budget': round(budget * pcts['transport'] / 100, 2),
            'emergency_fund': round(budget * pcts['emergency'] / 100, 2),
            'flights_pct': pcts['flights'],
            'hotels_pct': pcts['hotels'],
            'food_pct': pcts['food'],
            'activities_pct': pcts['activities'],
            'transport_pct': pcts['transport'],
            'emergency_pct': pcts['emergency'],
            'travelers': travelers,
            'destination': destination,
            'total_budget': budget,
        }
