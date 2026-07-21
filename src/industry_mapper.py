"""Target company classification for data source selection."""

from __future__ import annotations

import re

SourceList = list[str]

# Physical / local businesses — best found on Google Maps
LOCAL_SIGNALS: dict[str, int] = {
    "hotel": 3, "motel": 3, "hostel": 3, "resort": 3, "inn": 2, "lodging": 3,
    "luxury hotel": 4, "boutique hotel": 4,
    "restaurant": 3, "cafe": 3, "coffee shop": 3, "coffee": 2, "bar": 2, "bakery": 3,
    "salon": 3, "barbershop": 3, "spa": 3, "gym": 3, "fitness": 2, "yoga studio": 3,
    "dental": 3, "dentist": 3, "clinic": 2, "pharmacy": 3, "veterinary": 3, "vet clinic": 3,
    "retail": 2, "store": 2, "shop": 2, "boutique": 2,
    "coworking space": 4, "coworking": 4, "co-working": 4, "shared office": 3,
    "daycare": 3, "preschool": 3, "tutoring center": 3,
    "plumber": 3, "electrician": 3, "hvac": 3, "auto repair": 3, "garage": 2,
    "cleaning service": 3, "laundry": 3, "florist": 3, "landscaping": 3,
    "real estate office": 3, "property management": 2,
}

# B2B / professional companies — best found on LinkedIn
B2B_SIGNALS: dict[str, int] = {
    "startup": 3, "start-up": 3, "scale-up": 3,
    "ai startup": 4, "tech startup": 4, "fintech startup": 4,
    "saas": 4, "software company": 4, "software": 3, "tech company": 3,
    "consulting firm": 4, "consulting": 3, "agency": 3, "marketing agency": 4,
    "manufacturer": 4, "manufacturing company": 4, "manufacturing": 3,
    "machining company": 4, "precision machining": 4, "machining": 3, "fabrication": 3,
    "medical device manufacturer": 5, "medical device": 4, "device manufacturer": 4,
    "biotech": 4, "pharma": 3, "aerospace": 4, "defense contractor": 4,
    "logistics company": 3, "supply chain": 3, "enterprise": 2, "b2b": 3,
    "staffing agency": 3, "recruiting firm": 3, "cybersecurity": 3,
    "ai company": 4, "machine learning": 3, "data platform": 3, "cloud company": 3,
    "venture capital": 3, "private equity": 3, "investment firm": 3,
}

# Ambiguous — try both sources
HYBRID_SIGNALS: dict[str, int] = {
    "healthcare": 2, "medical center": 3, "hospital": 3,
    "legal": 2, "law firm": 3, "construction company": 3, "construction": 2,
    "architecture firm": 3, "engineering firm": 3, "education": 2, "university": 3,
    "nonprofit": 2, "design studio": 2, "media company": 2, "event company": 2,
    "real estate": 2, "property developer": 3,
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _score_signals(text: str, signals: dict[str, int]) -> tuple[int, list[str]]:
    normalized = _normalize(text)
    score = 0
    matched: list[str] = []
    for signal, weight in sorted(signals.items(), key=lambda x: len(x[0]), reverse=True):
        if signal in normalized:
            score += weight
            matched.append(signal)
            normalized = normalized.replace(signal, " ")
    return score, matched


class IndustryMapper:
    """Classifies target company descriptions to pick data sources."""

    def suggest_sources(self, target_company: str) -> tuple[SourceList, str]:
        """Rule-based source selection from a target company search phrase."""
        local_score, local_hits = _score_signals(target_company, LOCAL_SIGNALS)
        b2b_score, b2b_hits = _score_signals(target_company, B2B_SIGNALS)
        hybrid_score, hybrid_hits = _score_signals(target_company, HYBRID_SIGNALS)

        label = f"'{target_company}'"

        if hybrid_score > 0 and local_score > 0 and b2b_score > 0:
            return (
                ["google_maps", "linkedin"],
                f"{label} matches local ({', '.join(local_hits)}), B2B ({', '.join(b2b_hits)}), "
                f"and hybrid ({', '.join(hybrid_hits)}) signals — using both sources.",
            )

        if hybrid_score > 0 and (local_score > 0 or b2b_score > 0):
            return (
                ["google_maps", "linkedin"],
                f"{label} has hybrid signals ({', '.join(hybrid_hits)}) — using both sources.",
            )

        if local_score > b2b_score and local_score > 0:
            return (
                ["google_maps"],
                f"{label} looks like a local/physical business ({', '.join(local_hits)}) "
                "— Google Maps is the best source.",
            )

        if b2b_score > local_score and b2b_score > 0:
            return (
                ["linkedin"],
                f"{label} looks like a B2B company ({', '.join(b2b_hits)}) "
                "— LinkedIn Company Search is the best source.",
            )

        if local_score > 0 and b2b_score > 0:
            return (
                ["google_maps", "linkedin"],
                f"{label} has mixed signals ({', '.join(local_hits)} vs {', '.join(b2b_hits)}) "
                "— using both sources.",
            )

        if hybrid_score > 0:
            return (
                ["google_maps", "linkedin"],
                f"{label} matches hybrid category ({', '.join(hybrid_hits)}) — using both sources.",
            )

        return (
            ["linkedin"],
            f"No strong signal for {label} — defaulting to LinkedIn. "
            "Set OPENAI_API_KEY for smarter selection on niche phrases.",
        )

    def build_search_terms(self, target_company: str) -> tuple[str, str]:
        """Return (google_maps_term, linkedin_query) — usually the raw phrase."""
        phrase = _normalize(target_company)
        return phrase, phrase
