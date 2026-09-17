def validate_transition(current_status, new_status) -> bool:
    valid_transitions = {
        "Pending": {"Paid", "Cancelled"},
        "Paid": {"Shipped", "Cancelled"},
        "Shipped": {"Delivered", "Cancelled"},
        "Delivered": set(),
        "Cancelled": set(),
    }

    return new_status in valid_transitions.get(current_status, set())