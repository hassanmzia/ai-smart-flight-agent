"""
Multi-Agent Debate/Negotiation System
Multiple specialized agents debate to find the best travel option.
Budget Agent vs Quality Agent vs Location Agent — transparent reasoning.
"""
import os
import logging
import json
from typing import Dict, Any, List
from django.conf import settings

logger = logging.getLogger(__name__)


class DebateAgent:
    """Base class for debate agents."""

    def __init__(self, name: str, perspective: str):
        self.name = name
        self.perspective = perspective

    def argue(self, options: List[Dict], context: Dict) -> Dict[str, Any]:
        raise NotImplementedError


class BudgetAgent(DebateAgent):
    """Argues for the most cost-effective option."""

    def __init__(self):
        super().__init__('Budget Advisor', 'cost-effectiveness and savings')

    def argue(self, options: List[Dict], context: Dict) -> Dict[str, Any]:
        budget = context.get('budget')
        scored = []
        for opt in options:
            price = self._get_price(opt)
            score = 100
            if price and budget:
                ratio = price / budget
                if ratio <= 0.3:
                    score = 95
                elif ratio <= 0.5:
                    score = 80
                elif ratio <= 0.7:
                    score = 60
                else:
                    score = max(10, 100 - ratio * 100)
            elif price:
                score = max(10, 100 - price / 10)

            scored.append({
                'option': opt.get('name', 'Unknown'),
                'score': round(score, 1),
                'price': price,
                'argument': self._make_argument(opt, price, budget),
            })

        scored.sort(key=lambda x: x['score'], reverse=True)
        winner = scored[0] if scored else None

        return {
            'agent': self.name,
            'perspective': self.perspective,
            'recommendation': winner['option'] if winner else None,
            'top_score': winner['score'] if winner else 0,
            'reasoning': winner['argument'] if winner else 'No options to evaluate',
            'all_scores': scored,
        }

    def _get_price(self, opt):
        price = opt.get('price', 0)
        if isinstance(price, str):
            try:
                return float(price.replace('$', '').replace(',', ''))
            except (ValueError, TypeError):
                return 0
        return float(price) if price else 0

    def _make_argument(self, opt, price, budget):
        name = opt.get('name', 'This option')
        if budget and price:
            pct = price / budget * 100
            if pct <= 30:
                return f"{name} at ${price:.0f} uses only {pct:.0f}% of budget — excellent value, leaves room for activities."
            elif pct <= 50:
                return f"{name} at ${price:.0f} is reasonably priced at {pct:.0f}% of budget."
            else:
                return f"{name} at ${price:.0f} consumes {pct:.0f}% of budget — consider cheaper alternatives."
        return f"{name} at ${price:.0f} — evaluate against total budget."


class QualityAgent(DebateAgent):
    """Argues for the highest quality option."""

    def __init__(self):
        super().__init__('Quality Advisor', 'ratings, reviews, and overall experience')

    def argue(self, options: List[Dict], context: Dict) -> Dict[str, Any]:
        scored = []
        for opt in options:
            rating = float(opt.get('rating', 0) or 0)
            reviews = int(opt.get('reviews_count', 0) or 0)
            score = rating * 15  # Up to 75 for a 5-star
            if reviews > 500:
                score += 15
            elif reviews > 100:
                score += 10
            elif reviews > 20:
                score += 5

            amenities = opt.get('amenities', [])
            if isinstance(amenities, list):
                score += min(len(amenities) * 2, 10)

            scored.append({
                'option': opt.get('name', 'Unknown'),
                'score': min(round(score, 1), 100),
                'rating': rating,
                'reviews': reviews,
                'argument': self._make_argument(opt, rating, reviews),
            })

        scored.sort(key=lambda x: x['score'], reverse=True)
        winner = scored[0] if scored else None

        return {
            'agent': self.name,
            'perspective': self.perspective,
            'recommendation': winner['option'] if winner else None,
            'top_score': winner['score'] if winner else 0,
            'reasoning': winner['argument'] if winner else 'No options to evaluate',
            'all_scores': scored,
        }

    def _make_argument(self, opt, rating, reviews):
        name = opt.get('name', 'This option')
        if rating >= 4.5 and reviews > 100:
            return f"{name} has an outstanding {rating}★ rating from {reviews} reviews — proven excellence."
        elif rating >= 4.0:
            return f"{name} rated {rating}★ with {reviews} reviews — solid quality choice."
        elif rating >= 3.5:
            return f"{name} at {rating}★ is decent but there may be better options available."
        return f"{name} has limited rating data — higher risk choice."


class LocationAgent(DebateAgent):
    """Argues based on location convenience."""

    def __init__(self):
        super().__init__('Location Advisor', 'convenience, proximity, and accessibility')

    def argue(self, options: List[Dict], context: Dict) -> Dict[str, Any]:
        scored = []
        for opt in options:
            score = 50
            location = (opt.get('location', '') or '').lower()
            if any(w in location for w in ['center', 'central', 'downtown', 'city center']):
                score += 30
            if any(w in location for w in ['station', 'metro', 'transit']):
                score += 15
            if any(w in location for w in ['airport', 'terminal']):
                score += 10

            # For flights: fewer stops = better
            stops = opt.get('stops', None)
            if stops is not None:
                if stops == 0:
                    score += 25
                elif stops == 1:
                    score += 10

            duration = opt.get('duration_hours', None)
            if duration and isinstance(duration, (int, float)):
                if duration <= 4:
                    score += 15
                elif duration <= 8:
                    score += 5

            scored.append({
                'option': opt.get('name', 'Unknown'),
                'score': min(round(score, 1), 100),
                'argument': self._make_argument(opt, location),
            })

        scored.sort(key=lambda x: x['score'], reverse=True)
        winner = scored[0] if scored else None

        return {
            'agent': self.name,
            'perspective': self.perspective,
            'recommendation': winner['option'] if winner else None,
            'top_score': winner['score'] if winner else 0,
            'reasoning': winner['argument'] if winner else 'No options to evaluate',
            'all_scores': scored,
        }

    def _make_argument(self, opt, location):
        name = opt.get('name', 'This option')
        stops = opt.get('stops')
        if stops == 0:
            return f"{name} is a direct route — fastest and most convenient."
        if 'center' in location or 'central' in location:
            return f"{name} in {location} — centrally located, easy access to attractions."
        return f"{name} — evaluate transport connections to key destinations."


class TravelDebateSystem:
    """
    Orchestrates a debate between Budget, Quality, and Location agents.
    Produces a final recommendation with transparent reasoning.
    """

    def __init__(self):
        self.agents = [BudgetAgent(), QualityAgent(), LocationAgent()]

    def debate(self, options: List[Dict], context: Dict = None) -> Dict[str, Any]:
        """
        Run the debate across all agents and produce a final verdict.

        Args:
            options: List of options (flights, hotels, etc.) with name, price, rating, etc.
            context: Budget, preferences, and other context
        """
        context = context or {}
        arguments = []

        for agent in self.agents:
            try:
                arg = agent.argue(options, context)
                arguments.append(arg)
            except Exception as e:
                logger.error(f"Agent {agent.name} failed: {e}")

        # Synthesize final recommendation
        final = self._synthesize(arguments, options, context)

        return {
            'success': True,
            'debate': arguments,
            'final_recommendation': final,
            'options_evaluated': len(options),
        }

    def debate_with_llm(self, options: List[Dict], context: Dict = None) -> Dict[str, Any]:
        """Enhanced debate using LLM to synthesize agent arguments."""
        basic_result = self.debate(options, context)

        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return basic_result

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(model='gpt-4o-mini', temperature=0.3, api_key=api_key, request_timeout=30)

            debate_summary = json.dumps(basic_result['debate'], indent=2, default=str)

            response = model.invoke([
                SystemMessage(content="You are a travel expert moderator. Analyze the debate between agents and give a final recommendation. Be concise."),
                HumanMessage(content=f"""Three travel advisors debated these options. Here are their arguments:

{debate_summary}

User context: Budget=${context.get('budget', 'flexible')}, travelers={context.get('travelers', 1)}

Give a final verdict in 2-3 sentences explaining which option wins and why, balancing all three perspectives.""")
            ])

            basic_result['final_recommendation']['llm_verdict'] = response.content
        except Exception as e:
            logger.warning(f"LLM debate synthesis failed: {e}")

        return basic_result

    def _synthesize(self, arguments: List[Dict], options: List[Dict], context: Dict) -> Dict[str, Any]:
        """Combine agent scores into a weighted final recommendation.
        Weights adapt to user preferences when provided in context."""
        # Default weights
        weights = {'Budget Advisor': 0.35, 'Quality Advisor': 0.40, 'Location Advisor': 0.25}

        # Adapt weights based on user context/preferences
        user_priority = context.get('priority', '').lower() if context else ''
        if user_priority == 'budget':
            weights = {'Budget Advisor': 0.55, 'Quality Advisor': 0.25, 'Location Advisor': 0.20}
        elif user_priority == 'quality':
            weights = {'Budget Advisor': 0.20, 'Quality Advisor': 0.55, 'Location Advisor': 0.25}
        elif user_priority == 'location':
            weights = {'Budget Advisor': 0.20, 'Quality Advisor': 0.30, 'Location Advisor': 0.50}
        option_scores = {}

        for arg in arguments:
            agent_name = arg.get('agent', '')
            weight = weights.get(agent_name, 0.33)
            for item in arg.get('all_scores', []):
                name = item['option']
                if name not in option_scores:
                    option_scores[name] = {'total': 0, 'breakdown': {}}
                weighted = item['score'] * weight
                option_scores[name]['total'] += weighted
                option_scores[name]['breakdown'][agent_name] = {
                    'raw_score': item['score'],
                    'weighted_score': round(weighted, 1),
                    'argument': item.get('argument', ''),
                }

        if not option_scores:
            return {'winner': None, 'message': 'No options to evaluate'}

        winner_name = max(option_scores, key=lambda x: option_scores[x]['total'])
        winner = option_scores[winner_name]

        return {
            'winner': winner_name,
            'total_score': round(winner['total'], 1),
            'score_breakdown': winner['breakdown'],
            'all_rankings': [
                {'name': k, 'score': round(v['total'], 1)}
                for k, v in sorted(option_scores.items(), key=lambda x: x[1]['total'], reverse=True)
            ],
            'consensus': all(arg.get('recommendation') == winner_name for arg in arguments),
        }
