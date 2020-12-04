"""Objects for making requests to the API."""
from typing import Dict, NamedTuple


class IssueLinkRequest(NamedTuple):
    """Issue to add to a task annotation."""

    issue_key: str
    url: str

    def as_dict(self) -> Dict[str, str]:
        """Get a dictionary representation of the issue link."""
        return {"issue_key": self.issue_key, "url": self.url}
