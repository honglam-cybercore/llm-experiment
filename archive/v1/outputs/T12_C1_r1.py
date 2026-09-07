def validate_transition(current_status, new_status) -> bool:
    valid_transitions = {
        "Pending": ["Paid", "Cancelled"],
        "Paid": ["Shipped", "Cancelled"],
        "Shipped": ["Delivered", "Cancelled"],
        "Delivered": [],
        "Cancelled": []
    }
    
    if current_status not in valid_transitions:
        return False
    
    return new_status in valid_transitions[current_status]
