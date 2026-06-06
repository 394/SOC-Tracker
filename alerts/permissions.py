from .models import UserProfile


def user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return UserProfile.Role.L3
    return getattr(getattr(user, "profile", None), "role", UserProfile.Role.L1)


def can_create_alert(user):
    return user_role(user) in {UserProfile.Role.L1, UserProfile.Role.L2, UserProfile.Role.L3}


def can_edit_alert(user, alert):
    role = user_role(user)
    if role == UserProfile.Role.L3:
        return True
    if role == UserProfile.Role.L2:
        return True
    if role == UserProfile.Role.L1:
        return alert.status != "Escalated"
    return False


def can_delete_alert(user):
    return user_role(user) == UserProfile.Role.L3


def can_escalate_alert(user):
    return user_role(user) in {UserProfile.Role.L1, UserProfile.Role.L2}


def can_assign_alert(user):
    return user_role(user) in {UserProfile.Role.L2, UserProfile.Role.L3}


def assignable_roles_for(user):
    role = user_role(user)
    if role == UserProfile.Role.L3:
        return [UserProfile.Role.L1, UserProfile.Role.L2]
    if role == UserProfile.Role.L2:
        return [UserProfile.Role.L1]
    return []
