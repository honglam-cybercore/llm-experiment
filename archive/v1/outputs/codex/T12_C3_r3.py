_ALLOWED_TRANSITIONS = {
    "Pending": frozenset({"Paid", "Cancelled"}),
    "Paid": frozenset({"Shipped", "Cancelled"}),
    "Shipped": frozenset({"Delivered"}),
    "Delivered": frozenset(),
    "Cancelled": frozenset(),
}


def validate_transition(current_status, new_status) -> bool:
    if not isinstance(current_status, str) or not isinstance(new_status, str):
        return False

    return new_status in _ALLOWED_TRANSITIONS.get(current_status, frozenset())