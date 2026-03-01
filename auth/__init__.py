from .auth_manager import (
    register_user, login_user, logout_user,
    is_authenticated, is_admin, get_current_user_id,
    get_current_username, require_auth, require_admin,
    seed_admin_if_needed
)
