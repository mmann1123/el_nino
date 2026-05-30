"""Streamlit native OIDC sign-in gate. Disabled by default (AUTH_MODE=disabled)
so local dev runs without an OAuth client configured. In cloud, set
AUTH_MODE=oidc and ALLOWED_EMAILS (comma-separated) to enable the gate.
"""

from __future__ import annotations

import streamlit as st

from .. import config


def require_login() -> None:
    if config.AUTH_MODE == "disabled":
        return

    user = getattr(st, "experimental_user", None)
    if user is None or not getattr(user, "is_logged_in", False):
        st.title(f"{config.CC['display_name']} Drought Dashboard")
        st.write("Sign in with your Google account to continue.")
        if hasattr(st, "login"):
            st.button("Sign in with Google", on_click=lambda: st.login("google"))
        else:
            st.error("This deployment requires Streamlit ≥1.42 for OIDC support.")
        st.stop()

    email = getattr(user, "email", "")
    if config.ALLOWED_EMAILS and email not in config.ALLOWED_EMAILS:
        st.error(f"Access denied for {email}. Contact the dashboard administrator.")
        if hasattr(st, "logout"):
            st.button("Sign out", on_click=st.logout)
        st.stop()
