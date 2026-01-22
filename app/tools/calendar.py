# app/tools/calendar.py
"""
Calendar Tools - Check availability and schedule travel events.

This tool provides calendar integration capabilities for travel planning,
allowing the agent to check user availability and suggest optimal travel dates.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from semantic_kernel.functions import kernel_function
from app.utils.logger import setup_logger

logger = setup_logger("calendar_tool")


class CalendarTools:
    """
    Calendar integration tools for checking availability and scheduling.

    In a production environment, this would integrate with Google Calendar,
    Microsoft Outlook, or similar calendar APIs. This implementation provides
    a simulated calendar service for demonstration purposes.
    """

    def __init__(self):
        """Initialize calendar tool."""
        logger.info("Initialized CalendarTools")

    @kernel_function(
        name="check_availability",
        description="Check user's calendar availability for travel dates. Returns available date ranges and suggests optimal travel windows."
    )
    def check_availability(
        self,
        start_date: str,
        end_date: str,
        flexible_days: int = 3
    ) -> Dict[str, Any]:
        """
        Check calendar availability for travel planning.

        Args:
            start_date: Desired start date in YYYY-MM-DD format
            end_date: Desired end date in YYYY-MM-DD format
            flexible_days: Number of days flexibility (default: 3)

        Returns:
            Dictionary containing availability information, conflicts, and suggestions
        """
        try:
            logger.info(f"Checking availability from {start_date} to {end_date}")

            # Parse dates
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            duration_days = (end_dt - start_dt).days

            # Simulate calendar conflicts (in production, query actual calendar API)
            conflicts = self._simulate_conflicts(start_dt, end_dt)

            # Calculate availability score
            total_days = duration_days
            conflict_days = len(conflicts)
            availability_score = max(0, (total_days - conflict_days) / total_days) if total_days > 0 else 0

            # Generate alternative suggestions if there are conflicts
            alternatives = []
            if conflict_days > 0 and flexible_days > 0:
                alternatives = self._generate_alternatives(start_dt, end_dt, flexible_days, conflicts)

            result = {
                "requested_dates": {
                    "start": start_date,
                    "end": end_date,
                    "duration_days": duration_days
                },
                "availability": {
                    "is_available": conflict_days == 0,
                    "availability_score": round(availability_score, 2),
                    "conflict_count": conflict_days,
                    "free_days": total_days - conflict_days
                },
                "conflicts": conflicts,
                "alternative_dates": alternatives,
                "recommendation": self._generate_recommendation(
                    conflict_days, alternatives, availability_score
                )
            }

            logger.info(f"Availability check completed: {availability_score:.2%} available")
            return result

        except ValueError as e:
            logger.error(f"Date parsing error: {e}")
            return {"error": f"Invalid date format: {e}"}
        except Exception as e:
            logger.error(f"Error checking availability: {e}", exc_info=True)
            return {"error": str(e)}

    @kernel_function(
        name="schedule_travel_event",
        description="Schedule a travel event on the user's calendar with reminders and preparation tasks."
    )
    def schedule_travel_event(
        self,
        title: str,
        start_date: str,
        end_date: str,
        destination: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Schedule a travel event on the calendar.

        Args:
            title: Event title (e.g., "Paris Vacation")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            destination: Travel destination
            notes: Additional notes about the trip

        Returns:
            Dictionary with scheduled event details and confirmation
        """
        try:
            logger.info(f"Scheduling travel event: {title} to {destination}")

            # Parse dates
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            # Create event structure
            event = {
                "event_id": f"travel_{datetime.now(timezone.utc).timestamp()}",
                "title": title,
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "duration_days": (end_dt - start_dt).days,
                "notes": notes,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "scheduled"
            }

            # Generate preparation reminders
            reminders = self._generate_reminders(start_dt, title, destination)

            result = {
                "event": event,
                "reminders": reminders,
                "message": f"Successfully scheduled '{title}' from {start_date} to {end_date}",
                "next_steps": [
                    "Set up travel reminders",
                    "Book flights and accommodations",
                    "Check passport and visa requirements",
                    "Review credit card travel benefits",
                    "Purchase travel insurance"
                ]
            }

            logger.info(f"Travel event scheduled successfully: {event['event_id']}")
            return result

        except ValueError as e:
            logger.error(f"Date parsing error: {e}")
            return {"error": f"Invalid date format: {e}"}
        except Exception as e:
            logger.error(f"Error scheduling event: {e}", exc_info=True)
            return {"error": str(e)}

    def _simulate_conflicts(self, start_dt: datetime, end_dt: datetime) -> List[Dict[str, str]]:
        """
        Simulate calendar conflicts for demonstration.
        In production, this would query the actual calendar API.
        """
        conflicts = []

        # Simulate some conflicts (e.g., business meetings, existing commitments)
        current_dt = start_dt
        while current_dt <= end_dt:
            # Simulate conflicts on Mondays and Wednesdays
            if current_dt.weekday() in [0, 2]:  # 0=Monday, 2=Wednesday
                conflicts.append({
                    "date": current_dt.strftime("%Y-%m-%d"),
                    "type": "meeting",
                    "description": "Business meeting scheduled",
                    "duration_hours": 2
                })
            current_dt += timedelta(days=1)

        return conflicts

    def _generate_alternatives(
        self,
        start_dt: datetime,
        end_dt: datetime,
        flexible_days: int,
        conflicts: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Generate alternative date suggestions to avoid conflicts."""
        alternatives = []
        duration = (end_dt - start_dt).days

        # Try shifting dates forward
        for offset in range(1, flexible_days + 1):
            alt_start = start_dt + timedelta(days=offset)
            alt_end = end_dt + timedelta(days=offset)

            # Check if this alternative has fewer conflicts
            alt_conflicts = self._simulate_conflicts(alt_start, alt_end)
            if len(alt_conflicts) < len(conflicts):
                alternatives.append({
                    "start_date": alt_start.strftime("%Y-%m-%d"),
                    "end_date": alt_end.strftime("%Y-%m-%d"),
                    "conflict_count": len(alt_conflicts),
                    "reason": f"Shifted {offset} days forward to avoid conflicts"
                })

        # Try shifting dates backward
        for offset in range(1, flexible_days + 1):
            alt_start = start_dt - timedelta(days=offset)
            alt_end = end_dt - timedelta(days=offset)

            alt_conflicts = self._simulate_conflicts(alt_start, alt_end)
            if len(alt_conflicts) < len(conflicts):
                alternatives.append({
                    "start_date": alt_start.strftime("%Y-%m-%d"),
                    "end_date": alt_end.strftime("%Y-%m-%d"),
                    "conflict_count": len(alt_conflicts),
                    "reason": f"Shifted {offset} days backward to avoid conflicts"
                })

        # Sort by conflict count (fewest conflicts first)
        alternatives.sort(key=lambda x: x["conflict_count"])

        return alternatives[:3]  # Return top 3 alternatives

    def _generate_recommendation(
        self,
        conflict_days: int,
        alternatives: List[Dict[str, Any]],
        availability_score: float
    ) -> str:
        """Generate a recommendation based on availability analysis."""
        if conflict_days == 0:
            return "Your calendar is completely free for these dates. Perfect timing for your trip!"
        elif availability_score >= 0.7:
            return f"You have {conflict_days} conflict(s), but most days are available. Consider rescheduling meetings if possible."
        elif alternatives:
            best_alt = alternatives[0]
            return f"Consider alternative dates starting {best_alt['start_date']} to avoid conflicts."
        else:
            return "Significant conflicts detected. Consider extending flexibility or choosing different dates."

    def _generate_reminders(
        self,
        start_dt: datetime,
        title: str,
        destination: str
    ) -> List[Dict[str, str]]:
        """Generate preparation reminders leading up to the trip."""
        reminders = []

        # 30 days before: Initial planning
        reminder_30d = start_dt - timedelta(days=30)
        if reminder_30d > datetime.now():
            reminders.append({
                "date": reminder_30d.strftime("%Y-%m-%d"),
                "type": "planning",
                "message": f"Start planning your {title} to {destination}",
                "tasks": "Research activities, book flights and hotels"
            })

        # 14 days before: Documentation
        reminder_14d = start_dt - timedelta(days=14)
        if reminder_14d > datetime.now():
            reminders.append({
                "date": reminder_14d.strftime("%Y-%m-%d"),
                "type": "documentation",
                "message": "Check travel documents",
                "tasks": "Verify passport expiry, apply for visas if needed"
            })

        # 7 days before: Packing
        reminder_7d = start_dt - timedelta(days=7)
        if reminder_7d > datetime.now():
            reminders.append({
                "date": reminder_7d.strftime("%Y-%m-%d"),
                "type": "preparation",
                "message": "Prepare for your trip",
                "tasks": "Pack bags, arrange pet care, set up mail hold"
            })

        # 1 day before: Final check
        reminder_1d = start_dt - timedelta(days=1)
        if reminder_1d > datetime.now():
            reminders.append({
                "date": reminder_1d.strftime("%Y-%m-%d"),
                "type": "final_check",
                "message": "Final preparations",
                "tasks": "Check flight status, confirm reservations, charge devices"
            })

        return reminders
