def validate_transition(current_status, new_status) -> bool:
    transitions = {
        "Pending": frozenset(("Paid", "Cancelled")),
        "Paid": frozenset(("Shipped", "Cancelled")),
        "Shipped": frozenset(("Delivered",)),
        "Delivered": frozenset(),
        "Cancelled": frozenset(),
    }

    if type(current_status) is not str or type(new_status) is not str:
        return False

    return new_status in transitions.get(current_status, frozenset())