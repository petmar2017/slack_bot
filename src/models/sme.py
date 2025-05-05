"""
Subject Matter Expert (SME) models for the Slack Support Bot.
"""
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class SubjectMatterExpert(BaseModel):
    """
    Subject Matter Expert model representing a team member with specialized knowledge.
    """

    slack_id: str
    name: str
    expertise: List[str] = []
    availability: bool = True
    skills_rating: Dict[str, int] = {}
    current_load: int = 0
    max_concurrent_issues: int = 3

    def has_expertise(self, required_expertise: str) -> bool:
        """Check if SME has the required expertise."""
        return required_expertise.lower() in {e.lower() for e in self.expertise}

    def has_any_expertise(self, required_expertise: List[str]) -> bool:
        """Check if SME has any of the required expertise areas."""
        if not required_expertise:
            return True
        
        required_set = {e.lower() for e in required_expertise}
        expertise_set = {e.lower() for e in self.expertise}
        return bool(required_set.intersection(expertise_set))

    def get_rating_for_expertise(self, expertise: str) -> int:
        """Get the SME's rating for a specific expertise area."""
        return self.skills_rating.get(expertise.lower(), 0)

    def is_available(self) -> bool:
        """Check if SME is available to take on new issues."""
        return self.availability and self.current_load < self.max_concurrent_issues

    @classmethod
    def from_dict(cls, data: Dict) -> "SubjectMatterExpert":
        """Create an SME from dictionary data."""
        return cls(
            slack_id=data["slack_id"],
            name=data["name"],
            expertise=data.get("expertise", []),
            availability=data.get("availability", True),
            skills_rating=data.get("skills_rating", {}),
            current_load=data.get("current_load", 0),
            max_concurrent_issues=data.get("max_concurrent_issues", 3),
        )


class SMEDatabase:
    """
    Manages Subject Matter Expert data.
    """

    def __init__(self, experts: List[Dict] = None):
        """Initialize with optional experts data."""
        self.experts: List[SubjectMatterExpert] = []
        if experts:
            for expert_data in experts:
                self.experts.append(SubjectMatterExpert.from_dict(expert_data))

    def get_all_expertise_areas(self) -> Set[str]:
        """Get all expertise areas from all SMEs."""
        all_areas = set()
        for expert in self.experts:
            all_areas.update(e.lower() for e in expert.expertise)
        return all_areas

    def find_experts_by_expertise(
        self, required_expertise: List[str], available_only: bool = True
    ) -> List[SubjectMatterExpert]:
        """Find experts who have the required expertise."""
        matching_experts = []
        
        for expert in self.experts:
            if (not available_only or expert.is_available()) and expert.has_any_expertise(
                required_expertise
            ):
                matching_experts.append(expert)
        
        # Sort by expertise match quality and availability
        matching_experts.sort(
            key=lambda e: (
                sum(e.get_rating_for_expertise(exp) for exp in required_expertise),
                -e.current_load,
            ),
            reverse=True,
        )
        
        return matching_experts 