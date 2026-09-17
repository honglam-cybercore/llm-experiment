def validate_transition(current_status, new_status) -> bool:
    allowed_transitions = {
        "Pending": {"Paid", "Cancelled"},
        "Paid": {"Shipped", "Cancelled"},
        "Shipped": {"Delivered"},
        "Delivered": set(),
        "Cancelled": set(),
    }

    return new_status in allowed_transitions.get(current_status, set())