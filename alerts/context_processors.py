from .permissions import can_create_alert, can_delete_alert, user_role


def role_context(request):
    return {
        "current_role": user_role(request.user),
        "can_create_alert": can_create_alert(request.user),
        "can_delete_alert": can_delete_alert(request.user),
    }
