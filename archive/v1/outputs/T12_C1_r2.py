def validate_transition(current_status, new_status) -> bool:
    allowed_transitions = {
        "Pending": {"Paid", "Cancelled"},
        "Paid": {"Shipped", "Cancelled"},
        "Shipped": {"Delivered", "Cancelled"},
        "Delivered": set(),
        "Cancelled": set()
    }
    
    if current_status not in allowed_transitions:
        return False
    
    return new_status in allowed_transitions[current_status]
