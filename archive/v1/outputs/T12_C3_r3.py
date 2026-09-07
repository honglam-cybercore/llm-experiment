def validate_transition(current_status, new_status) -> bool:
    allowed_transitions = {
        ("Pending", "Paid"),
        ("Pending", "Cancelled"),
        ("Paid", "Shipped"),
        ("Paid", "Cancelled"),
        ("Shipped", "Delivered"),
    }
    
    valid_statuses = {"Pending", "Paid", "Shipped", "Delivered", "Cancelled"}
    
    if not isinstance(current_status, str) or not isinstance(new_status, str):
        return False
    
    if current_status not in valid_statuses or new_status not in valid_statuses:
        return False
    
    return (current_status, new_status) in allowed_transitions
