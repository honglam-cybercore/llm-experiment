VALID_TRANSITIONS = {
    "Pending": {"Paid", "Cancelled"},
    "Paid": {"Shipped", "Cancelled"},
    "Shipped": {"Delivered", "Cancelled"},
}


def validate_transition(current_status, new_status) -> bool:
    return new_status in VALID_TRANSITIONS.get(current_status, set())
