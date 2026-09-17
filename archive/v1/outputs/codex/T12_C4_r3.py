_ALLOWED_TRANSITIONS = {
    ("Pending", "Paid"),
    ("Pending", "Cancelled"),
    ("Paid", "Shipped"),
    ("Paid", "Cancelled"),
    ("Shipped", "Delivered"),
}


def validate_transition(current_status, new_status) -> bool:
    if type(current_status) is not str or type(new_status) is not str:
        return False
    return (current_status, new_status) in _ALLOWED_TRANSITIONS