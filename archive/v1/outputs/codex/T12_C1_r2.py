def validate_transition(current_status, new_status) -> bool:
    transitions = {
        "Pending": {"Paid", "Cancelled"},
        "Paid": {"Shipped", "Cancelled"},
        "Shipped": {"Delivered"},
        "Delivered": set(),
        "Cancelled": set(),
    }

    return (
        isinstance(current_status, str)
        and isinstance(new_status, str)
        and new_status in transitions.get(current_status, set())
    )