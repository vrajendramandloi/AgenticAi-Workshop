"""
Tools for Multi-Agent Planning, Statistics & Reflection System
=============================================================
Provides deterministic financial/statistical budget calculation and
loop-control tools for the Google ADK multi-agent pipeline.
"""

import sys
from typing import Any, Dict
from google.adk.tools.tool_context import ToolContext

# Prevent __pycache__ bytecode generation in this project
sys.dont_write_bytecode = True


def calculate_budget_breakdown(
    total_budget: float,
    duration_days: int,
    num_travelers: int = 1,
    currency: str = "USD"
) -> Dict[str, Any]:
    """
    Deterministically computes category-wise budget allocations, daily spend
    ceilings per person, and financial sanity benchmarks for trip planning.

    Args:
        total_budget: Total available budget for the trip.
        duration_days: Number of days of the trip.
        num_travelers: Total number of travelers (default 1).
        currency: Currency symbol or code (default USD).

    Returns:
        Dictionary with itemized budget allocations and per-day caps.
    """
    if duration_days <= 0:
        duration_days = 1
    if num_travelers <= 0:
        num_travelers = 1
    if total_budget <= 0:
        return {"error": "Total budget must be greater than zero."}

    # Standard healthy travel expenditure allocation model
    allocations = {
        "flights_and_transit_pct": 32.0,     # Flights, inter-city trains, airport transfers
        "lodging_accommodation_pct": 28.0,   # Hotels, stays, airbnb
        "food_and_dining_pct": 18.0,         # Daily meals, cafes, culinary tastings
        "activities_and_tours_pct": 12.0,    # Museum tickets, guides, entry passes
        "contingency_reserve_pct": 10.0,     # Emergency cushion, unexpected transit
    }

    flights_transit = round(total_budget * (allocations["flights_and_transit_pct"] / 100.0), 2)
    lodging_total = round(total_budget * (allocations["lodging_accommodation_pct"] / 100.0), 2)
    food_total = round(total_budget * (allocations["food_and_dining_pct"] / 100.0), 2)
    activities_total = round(total_budget * (allocations["activities_and_tours_pct"] / 100.0), 2)
    contingency_buffer = round(total_budget * (allocations["contingency_reserve_pct"] / 100.0), 2)

    # Per night accommodation cap (number of nights = duration_days - 1 if > 1 else 1)
    num_nights = max(1, duration_days - 1)
    max_lodging_per_night = round(lodging_total / num_nights, 2)

    # Daily allowances per traveler
    daily_food_per_person = round(food_total / (duration_days * num_travelers), 2)
    daily_activity_per_person = round(activities_total / (duration_days * num_travelers), 2)
    daily_discretionary_per_person = round((food_total + activities_total) / (duration_days * num_travelers), 2)

    return {
        "currency": currency,
        "total_budget": total_budget,
        "duration_days": duration_days,
        "num_travelers": num_travelers,
        "category_allocations": {
            "flights_and_transit": flights_transit,
            "lodging_total": lodging_total,
            "food_total": food_total,
            "activities_and_sights": activities_total,
            "contingency_reserve": contingency_buffer,
        },
        "planning_benchmarks": {
            "max_lodging_per_night": max_lodging_per_night,
            "daily_food_budget_per_person": daily_food_per_person,
            "daily_activities_budget_per_person": daily_activity_per_person,
            "total_daily_spend_per_person": daily_discretionary_per_person,
        },
        "feasibility_assessment": (
            "Feasible for Budget/Mid-Tier" if daily_discretionary_per_person >= 40.0
            else "Tight Budget - Focus on Hostels, Street Food, and Free Attractions"
        )
    }


def validate_budget(
    baseline_budget: float,
    quoted_cost: float,
    agent_role: str = "luxury",
    min_pct: float = None,
    max_pct: float = None,
    target_min_cost: float = None,
    target_max_cost: float = None,
    num_hotels: int = None,
    num_places: int = None,
    current_iteration: int = 1,
    max_iterations: int = None
) -> Dict[str, Any]:
    """
    Validates whether a research agent's quoted cost and proposal structure satisfy
    strict budget criteria and hotel/visiting places bounds.

    Rules enforced:
    1. Luxury Research (Aarav):
       - Mandatory proposal 10%–20% above budget ($B * 1.10 <= Cost <= B * 1.20),
         UNLESS eval_agent specifies a dynamic budget range (target_min_cost to target_max_cost,
         or min_pct to max_pct), in which case the quote must fit within that decided range.
       - Hotels: at least 1 hotel and at most 2 hotels (1 <= num_hotels <= 2).
       - Places to visit: at least 5 places and at most 7 places (5 <= num_places <= 7).
       - Max iterations: at most 3 iterations before cancellation/discarding.
    2. Value Research (Kabir):
       - Mandatory proposal at-max 10% below budget, never cross budget ($B * 0.90 <= Cost <= B * 1.00).
       - Hotels: at least 1 hotel and at most 2 hotels (1 <= num_hotels <= 2).
       - Places to visit: at least 3 places and at most 5 places (3 <= num_places <= 5).
       - Max iterations: at most 2 iterations before cancellation/discarding.

    Args:
        baseline_budget: Total baseline client budget from Phase 1.
        quoted_cost: Total cost quoted by the research agent.
        agent_role: "luxury" (or "aarav") / "value" (or "kabir").
        min_pct: Optional percentage increment floor (defaults: +10.0 for luxury, -10.0 for value).
        max_pct: Optional percentage increment ceiling (defaults: +20.0 for luxury, 0.0 for value).
        target_min_cost: Optional specific dollar floor prescribed by eval_agent.
        target_max_cost: Optional specific dollar ceiling prescribed by eval_agent.
        num_hotels: Optional count of hotels included in proposal.
        num_places: Optional count of visiting places included in proposal.
        current_iteration: Current iteration number (1-indexed).
        max_iterations: Maximum allowed reflection iterations (default: 3 for luxury, 2 for value).

    Returns:
        Dict with:
            - is_approved: bool indicating if quote meets budget and structural requirements
            - percentage_change: float percentage difference vs baseline budget
            - action: "APPROVE", "RE_OPTIMIZE", or "DISCARD"
            - current_iteration: int
            - max_iterations: int
            - violations: list of specific violation strings (if any)
            - message: Actionable instruction for Eval Agent
    """
    if baseline_budget <= 0:
        return {
            "error": "Baseline budget must be greater than zero.",
            "is_approved": False,
            "action": "DISCARD",
            "message": "DISCARD: Baseline budget must be greater than zero."
        }

    role = agent_role.strip().lower()
    pct_change = round(((quoted_cost - baseline_budget) / baseline_budget) * 100.0, 2)

    # Determine default max_iterations if not provided
    if max_iterations is None:
        if role in ["luxury", "aarav", "research1"]:
            max_iterations = 3
        else:
            max_iterations = 2

    violations = []

    # 1. Budget & Structure validation by role
    if role in ["luxury", "aarav", "research1"]:
        # If eval_agent provided explicit target dollar range
        if target_min_cost is not None and target_max_cost is not None:
            if not (target_min_cost <= quoted_cost <= target_max_cost):
                violations.append(
                    f"Quoted cost ${quoted_cost:,.2f} is outside the range decided by eval_agent "
                    f"(${target_min_cost:,.2f} to ${target_max_cost:,.2f})."
                )
            target_desc = f"eval-decided range ${target_min_cost:,.2f}–${target_max_cost:,.2f}"
        else:
            # Check percentage bounds (default mandatory 10.0% to 20.0% above budget)
            eff_min_pct = 10.0 if min_pct is None else min_pct
            eff_max_pct = 20.0 if max_pct is None else max_pct
            min_allowed = round(baseline_budget * (1.0 + eff_min_pct / 100.0), 2)
            max_allowed = round(baseline_budget * (1.0 + eff_max_pct / 100.0), 2)

            if not (min_allowed <= quoted_cost <= max_allowed):
                violations.append(
                    f"Quoted cost ${quoted_cost:,.2f} ({pct_change:+0.2f}%) is outside mandatory "
                    f"{eff_min_pct}%–{eff_max_pct}% increment over baseline (${min_allowed:,.2f} to ${max_allowed:,.2f})."
                )
            target_desc = f"{eff_min_pct}%–{eff_max_pct}% above budget (${min_allowed:,.2f} to ${max_allowed:,.2f})"

        # Structural requirements for luxury: 1-2 hotels, 5-7 places
        if num_hotels is not None:
            if not (1 <= num_hotels <= 2):
                violations.append(f"Hotels count ({num_hotels}) must be at-least 1 and at-max 2.")
        if num_places is not None:
            if not (5 <= num_places <= 7):
                violations.append(f"Visiting places count ({num_places}) must be at-least 5 and at-max 7.")

    elif role in ["value", "kabir", "research2"]:
        # Value research: mandatory at-max 10% below budget, never cross budget (90% to 100% of B)
        eff_min_pct = -10.0 if min_pct is None else min_pct
        eff_max_pct = 0.0 if max_pct is None else max_pct
        min_allowed = round(baseline_budget * (1.0 + eff_min_pct / 100.0), 2)
        max_allowed = round(baseline_budget * (1.0 + eff_max_pct / 100.0), 2)

        if quoted_cost > baseline_budget:
            violations.append(
                f"Quoted cost ${quoted_cost:,.2f} ({pct_change:+0.2f}%) crosses the budget limit of ${baseline_budget:,.2f}."
            )
        elif not (min_allowed <= quoted_cost <= max_allowed):
            violations.append(
                f"Quoted cost ${quoted_cost:,.2f} ({pct_change:+0.2f}%) is outside allowed bounds "
                f"at-max 10% below budget (${min_allowed:,.2f} to ${max_allowed:,.2f})."
            )
        target_desc = f"at-max 10% below budget without crossing (${min_allowed:,.2f} to ${max_allowed:,.2f})"

        # Structural requirements for value: 1-2 hotels, 3-5 places
        if num_hotels is not None:
            if not (1 <= num_hotels <= 2):
                violations.append(f"Hotels count ({num_hotels}) must be at-least 1 and at-max 2.")
        if num_places is not None:
            if not (3 <= num_places <= 5):
                violations.append(f"Visiting places count ({num_places}) must be at-least 3 and at-max 5.")

    else:
        # Generic role check
        eff_min_pct = 0.0 if min_pct is None else min_pct
        eff_max_pct = 15.0 if max_pct is None else max_pct
        if not (eff_min_pct <= pct_change <= eff_max_pct):
            violations.append(f"Cost ${quoted_cost:,.2f} ({pct_change:+0.2f}%) outside {eff_min_pct}%–{eff_max_pct}%.")
        target_desc = f"{eff_min_pct}%–{eff_max_pct}% range"

    is_compliant = (len(violations) == 0)

    if is_compliant:
        return {
            "agent_role": agent_role,
            "quoted_cost": quoted_cost,
            "baseline_budget": baseline_budget,
            "percentage_change": pct_change,
            "num_hotels": num_hotels,
            "num_places": num_places,
            "is_approved": True,
            "action": "APPROVE",
            "current_iteration": current_iteration,
            "max_iterations": max_iterations,
            "message": f"APPROVED: Quoted cost ${quoted_cost:,.2f} ({pct_change:+0.2f}%) and structure satisfy {target_desc}."
        }
    else:
        violation_summary = " ".join(violations)
        if current_iteration < max_iterations:
            return {
                "agent_role": agent_role,
                "quoted_cost": quoted_cost,
                "baseline_budget": baseline_budget,
                "percentage_change": pct_change,
                "num_hotels": num_hotels,
                "num_places": num_places,
                "is_approved": False,
                "action": "RE_OPTIMIZE",
                "current_iteration": current_iteration,
                "max_iterations": max_iterations,
                "violations": violations,
                "message": (
                    f"RE-OPTIMIZE: {violation_summary} "
                    f"Iteration {current_iteration} of {max_iterations}. "
                    f"Request rectification from {agent_role} to fit within required bounds."
                )
            }
        else:
            return {
                "agent_role": agent_role,
                "quoted_cost": quoted_cost,
                "baseline_budget": baseline_budget,
                "percentage_change": pct_change,
                "num_hotels": num_hotels,
                "num_places": num_places,
                "is_approved": False,
                "action": "DISCARD",
                "current_iteration": current_iteration,
                "max_iterations": max_iterations,
                "violations": violations,
                "message": (
                    f"DISCARD: {violation_summary} "
                    f"Reached maximum limit of {max_iterations} iterations without compliance. "
                    f"Cancel the proposal and move on."
                )
            }


def exit_loop(tool_context: ToolContext):
    """
    Call this function ONLY when the Critic's audit verifies that the plan
    satisfies all budget constraints, logistical timelines, and user preferences,
    signaling the iterative reflection loop should terminate.
    """
    print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    tool_context.actions.skip_summarization = True
    return {}

