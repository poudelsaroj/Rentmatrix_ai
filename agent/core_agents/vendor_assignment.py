"""
Simple Round-Robin Vendor Assignment with Time Matching

Filters by trade AND availability matching with tenant's preferred times.
Returns 3 vendors: 1 primary + 2 backups.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class VendorAssignmentResult:
    """Result of vendor assignment."""
    primary_vendor: Dict[str, Any]
    backup_vendors: List[Dict[str, Any]]
    trade: str
    total_available: int
    matched_times: Dict[str, List[str]]  # vendor_id -> matched time slots


class VendorAssignment:
    """
    Round-robin vendor assignment with time matching.

    Matches vendors based on:
    1. Trade category (required)
    2. Availability matching tenant's preferred times (prioritized)
    """

    def __init__(self):
        self._trade_pointers: Dict[str, int] = {}

    def assign_vendors(
        self,
        trade: str,
        vendors: List[Dict[str, Any]],
        tenant_times: Optional[List[str]] = None,
        count: int = 3
    ) -> Optional[VendorAssignmentResult]:
        """
        Assign vendors for a trade category using round-robin with time matching.

        Args:
            trade: Trade category (PLUMBING, ELECTRICAL, etc.)
            vendors: List of vendor dicts
            tenant_times: Tenant's preferred times (e.g., ["Monday 09:00-12:00", "Wednesday 14:00-17:00"])
            count: Number of vendors to return (default 3)

        Returns:
            VendorAssignmentResult with primary + backup vendors
        """
        trade_upper = trade.upper()

        # Filter vendors by trade
        trade_vendors = self._filter_by_trade(vendors, trade_upper)

        if not trade_vendors:
            return None

        # Score vendors by time matching
        if tenant_times:
            scored_vendors = self._score_by_availability(trade_vendors, tenant_times)
            # Sort by match count (descending), then by original order
            scored_vendors.sort(key=lambda x: (-x[1], trade_vendors.index(x[0])))
            sorted_vendors = [v[0] for v in scored_vendors]
            matched_times = {v[0].get("vendor_id", str(i)): v[2] for i, v in enumerate(scored_vendors)}
        else:
            sorted_vendors = trade_vendors
            matched_times = {}

        # Get current pointer for this trade
        pointer = self._trade_pointers.get(trade_upper, 0)

        # Select vendors using round-robin
        selected = []
        total = len(sorted_vendors)

        for i in range(min(count, total)):
            idx = (pointer + i) % total
            selected.append(sorted_vendors[idx])

        # Update pointer for next assignment
        self._trade_pointers[trade_upper] = (pointer + 1) % total

        return VendorAssignmentResult(
            primary_vendor=selected[0],
            backup_vendors=selected[1:] if len(selected) > 1 else [],
            trade=trade_upper,
            total_available=total,
            matched_times=matched_times
        )

    def _filter_by_trade(
        self,
        vendors: List[Dict[str, Any]],
        trade: str
    ) -> List[Dict[str, Any]]:
        """Filter vendors that can handle the given trade."""
        matching = []

        for vendor in vendors:
            # Check primary_trade field
            primary = vendor.get("primary_trade", vendor.get("trade", "")).upper()
            if primary == trade:
                matching.append(vendor)
                continue

            # Check secondary_trades
            secondary = vendor.get("secondary_trades", [])
            if isinstance(secondary, list):
                secondary_upper = [t.upper() if isinstance(t, str) else t for t in secondary]
                if trade in secondary_upper:
                    matching.append(vendor)
                    continue

            # Check expertise.primary_trade (nested format)
            expertise = vendor.get("expertise", {})
            if isinstance(expertise, dict):
                exp_primary = expertise.get("primary_trade", "").upper()
                if exp_primary == trade:
                    matching.append(vendor)
                    continue

                exp_secondary = expertise.get("secondary_trades", [])
                if isinstance(exp_secondary, list):
                    exp_secondary_upper = [t.upper() if isinstance(t, str) else t for t in exp_secondary]
                    if trade in exp_secondary_upper:
                        matching.append(vendor)

        return matching

    def _score_by_availability(
        self,
        vendors: List[Dict[str, Any]],
        tenant_times: List[str]
    ) -> List[Tuple[Dict[str, Any], int, List[str]]]:
        """
        Score vendors by how many tenant time slots they can match.

        Returns: List of (vendor, match_count, matched_slots)
        """
        parsed_tenant_times = [self._parse_time_slot(t) for t in tenant_times]
        parsed_tenant_times = [t for t in parsed_tenant_times if t]  # Remove failed parses

        results = []

        for vendor in vendors:
            vendor_availability = self._get_vendor_availability(vendor)
            matched_slots = []

            for tenant_slot in parsed_tenant_times:
                if self._check_availability_match(vendor_availability, tenant_slot):
                    matched_slots.append(tenant_slot["original"])

            results.append((vendor, len(matched_slots), matched_slots))

        return results

    def _parse_time_slot(self, slot: str) -> Optional[Dict[str, Any]]:
        """
        Parse time slot string like "Monday 09:00-12:00" or "2024-12-23 14:00-17:00"

        Returns: {"day": "monday", "start": "09:00", "end": "12:00", "original": "..."}
        """
        if not slot:
            return None

        slot = slot.strip()

        # Pattern: "Day HH:MM-HH:MM" or "Day Start-End"
        patterns = [
            r"^(\w+)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$",  # Monday 09:00-12:00
            r"^(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$",  # 2024-12-23 09:00-12:00
        ]

        for pattern in patterns:
            match = re.match(pattern, slot, re.IGNORECASE)
            if match:
                day = match.group(1).lower()
                start = match.group(2)
                end = match.group(3)
                return {"day": day, "start": start, "end": end, "original": slot}

        # Fallback: just extract the day if possible
        day_match = re.match(r"^(\w+)", slot)
        if day_match:
            return {"day": day_match.group(1).lower(), "start": "00:00", "end": "23:59", "original": slot}

        return None

    def _get_vendor_availability(self, vendor: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract vendor availability from various formats."""
        availability = []

        # Check 'availability' field (list of strings or objects)
        avail_data = vendor.get("availability", [])

        if isinstance(avail_data, list):
            for slot in avail_data:
                if isinstance(slot, str):
                    parsed = self._parse_time_slot(slot)
                    if parsed:
                        availability.append(parsed)
                elif isinstance(slot, dict):
                    # Object format: {"day": "Monday", "start_time": "09:00", "end_time": "17:00"}
                    day = slot.get("day", slot.get("day_of_week", "")).lower()
                    start = slot.get("start_time", slot.get("start", "00:00"))
                    end = slot.get("end_time", slot.get("end", "23:59"))
                    if day:
                        availability.append({"day": day, "start": start, "end": end, "original": str(slot)})

        # Check 'available_times' field
        avail_times = vendor.get("available_times", [])
        if isinstance(avail_times, list):
            for slot in avail_times:
                if isinstance(slot, str):
                    parsed = self._parse_time_slot(slot)
                    if parsed:
                        availability.append(parsed)

        return availability

    def _check_availability_match(
        self,
        vendor_slots: List[Dict[str, Any]],
        tenant_slot: Dict[str, Any]
    ) -> bool:
        """Check if any vendor slot overlaps with tenant slot."""
        tenant_day = tenant_slot["day"].lower()
        tenant_start = self._time_to_minutes(tenant_slot["start"])
        tenant_end = self._time_to_minutes(tenant_slot["end"])

        for v_slot in vendor_slots:
            v_day = v_slot["day"].lower()

            # Check if days match
            if not self._days_match(tenant_day, v_day):
                continue

            v_start = self._time_to_minutes(v_slot["start"])
            v_end = self._time_to_minutes(v_slot["end"])

            # Check time overlap
            if self._times_overlap(tenant_start, tenant_end, v_start, v_end):
                return True

        return False

    def _days_match(self, day1: str, day2: str) -> bool:
        """Check if two day strings match."""
        day1 = day1.lower()
        day2 = day2.lower()

        # Direct match
        if day1 == day2:
            return True

        # Handle abbreviations
        day_map = {
            "mon": "monday", "tue": "tuesday", "wed": "wednesday",
            "thu": "thursday", "fri": "friday", "sat": "saturday", "sun": "sunday"
        }

        full_day1 = day_map.get(day1[:3], day1)
        full_day2 = day_map.get(day2[:3], day2)

        return full_day1 == full_day2

    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM to minutes since midnight."""
        try:
            parts = time_str.split(":")
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + minutes
        except (ValueError, IndexError):
            return 0

    def _times_overlap(self, start1: int, end1: int, start2: int, end2: int) -> bool:
        """Check if two time ranges overlap."""
        return start1 < end2 and start2 < end1

    def reset_pointer(self, trade: Optional[str] = None):
        """Reset round-robin pointer."""
        if trade:
            self._trade_pointers[trade.upper()] = 0
        else:
            self._trade_pointers.clear()


# Singleton instance
_vendor_assignment: Optional[VendorAssignment] = None


def get_vendor_assignment() -> VendorAssignment:
    """Get singleton vendor assignment instance."""
    global _vendor_assignment
    if _vendor_assignment is None:
        _vendor_assignment = VendorAssignment()
    return _vendor_assignment


def assign_vendors_simple(
    trade: str,
    vendors: List[Dict[str, Any]],
    tenant_times: Optional[List[str]] = None,
    count: int = 3
) -> Dict[str, Any]:
    """
    Assign vendors with trade and time matching.

    Args:
        trade: Trade category
        vendors: List of vendor dicts (must include 'availability')
        tenant_times: Tenant's preferred times ["Monday 09:00-12:00", ...]
        count: Number of vendors (default 3)

    Returns:
        Dict with assigned vendors and matched times
    """
    assigner = get_vendor_assignment()
    result = assigner.assign_vendors(trade, vendors, tenant_times, count)

    if result is None:
        return {
            "success": False,
            "error": f"No vendors available for trade: {trade}",
            "trade": trade,
            "assigned_vendors": []
        }

    # Build response with matched times
    assigned = []

    primary_id = result.primary_vendor.get("vendor_id", "primary")
    assigned.append({
        "vendor": result.primary_vendor,
        "role": "primary",
        "matched_times": result.matched_times.get(primary_id, [])
    })

    for i, vendor in enumerate(result.backup_vendors):
        vendor_id = vendor.get("vendor_id", f"backup_{i}")
        assigned.append({
            "vendor": vendor,
            "role": "backup",
            "matched_times": result.matched_times.get(vendor_id, [])
        })

    return {
        "success": True,
        "trade": result.trade,
        "total_available": result.total_available,
        "tenant_preferred_times": tenant_times or [],
        "assigned_vendors": assigned
    }
