#!/usr/bin/env python3
"""
User Creation Utility for DevSkyy Enterprise Platform
Creates new users with proper password hashing and authentication setup
"""

from getpass import getpass
import os
import sys


# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from security.jwt_auth import (
    UserRole,
    create_access_token,
    create_refresh_token,
    user_manager,
)


def create_user_interactive():
    """Create a user interactively"""

    # Get user details
    username = input("Enter username: ").strip()
    if not username:
        return False

    email = input("Enter email: ").strip()
    if not email:
        return False

    # Get password securely
    password = getpass("Enter password: ")
    if not password:
        return False

    password_confirm = getpass("Confirm password: ")
    if password != password_confirm:
        return False

    # Get role

    role_choice = input("Select role (1-5, default: 4): ").strip()
    role_map = {
        "1": UserRole.SUPER_ADMIN,
        "2": UserRole.ADMIN,
        "3": UserRole.DEVELOPER,
        "4": UserRole.API_USER,
        "5": UserRole.READ_ONLY,
        "": UserRole.API_USER,  # default
    }

    role = role_map.get(role_choice, UserRole.API_USER)

    try:
        # Create the user
        user = user_manager.create_user(email=email, username=username, password=password, role=role)

        # Test authentication
        auth_user = user_manager.authenticate_user(username, password)
        if auth_user:

            # Generate test tokens
            create_access_token(
                {
                    "user_id": user.user_id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                }
            )

            create_refresh_token(
                {
                    "user_id": user.user_id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                }
            )

        else:
            return False

        return True

    except ValueError:
        return False
    except Exception:
        return False


def create_user_programmatic(username: str, email: str, password: str, role: str = UserRole.API_USER):
    """Create a user programmatically"""
    try:
        user = user_manager.create_user(email=email, username=username, password=password, role=role)

        # Test authentication
        auth_user = user_manager.authenticate_user(username, password)
        if not auth_user:
            raise Exception("Authentication test failed")

        return user

    except Exception:
        return None


def list_users():
    """List all existing users"""

    if not user_manager.users:
        return

    for _user_id, _user in user_manager.users.items():
        pass


def test_authentication():
    """Test authentication with existing users"""

    username_or_email = input("Enter username or email: ").strip()
    password = getpass("Enter password: ")

    user = user_manager.authenticate_user(username_or_email, password)
    if user:

        # Generate tokens
        create_access_token(
            {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
            }
        )

    else:
        pass


def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_users()
        elif sys.argv[1] == "test":
            test_authentication()
        else:
            pass
    else:
        create_user_interactive()


if __name__ == "__main__":
    main()
