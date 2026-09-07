def validate_transition(current_status, new_status) -> bool:
    valid_transitions = {
        "Pending": {"Paid", "Cancelled"},
        "Paid": {"Shipped", "Cancelled"},
        "Shipped": {"Delivered"},
        "Delivered": set(),
        "Cancelled": set()
    }
    
    return (current_status in valid_transitions and 
            new_status in valid_transitions[current_status])
