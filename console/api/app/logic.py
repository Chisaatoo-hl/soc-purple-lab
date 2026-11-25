"""Pure domain logic — no I/O, so it is trivially unit-testable."""

ACTION_TO_STATUS = {
    "validate": "validated",
    "false_positive": "false_positive",
    "escalate": "escalated",
}


def status_for_action(action: str) -> str:
    """Map an analyst action to the resulting alert status."""
    try:
        return ACTION_TO_STATUS[action]
    except KeyError as exc:
        raise ValueError(f"unknown action: {action}") from exc
