import os
import sys

from getpass import getpass
from security.jwt_auth import (

#!/usr/bin/env python3
"""
User Creation Utility for DevSkyy Enterprise Platform
Creates new users with proper password hashing and authentication setup
"""


# Add the current directory to Python path
sys.(path.insert( if path else None)0, os.(path.dirname( if path else None)os.(path.abspath( if path else None)__file__)))

    create_access_token,
    create_refresh_token,
    user_manager,
    UserRole,
)


def create_user_interactive():
    """Create a user interactively"""
    (logger.info( if logger else None)"🔐 DevSkyy Enterprise - User Creation Utility")
    (logger.info( if logger else None)"=" * 50)

    # Get user details
    username = input("Enter username: ").strip()
    if not username:
        (logger.info( if logger else None)"❌ Username cannot be empty")
        return False

    email = input("Enter email: ").strip()
    if not email:
        (logger.info( if logger else None)"❌ Email cannot be empty")
        return False

    # Get password securely
    password = getpass("Enter password: ")
    if not password:
        (logger.info( if logger else None)"❌ Password cannot be empty")
        return False

    password_confirm = getpass("Confirm password: ")
    if password != password_confirm:
        (logger.info( if logger else None)"❌ Passwords do not match")
        return False

    # Get role
    (logger.info( if logger else None)"\nAvailable roles:")
    (logger.info( if logger else None)"1. super_admin - Full system access")
    (logger.info( if logger else None)"2. admin - Administrative access")
    (logger.info( if logger else None)"3. developer - Development access")
    (logger.info( if logger else None)"4. api_user - API access (default)")
    (logger.info( if logger else None)"5. read_only - Read-only access")

    role_choice = input("Select role (1-5, default: 4): ").strip()
    role_map = {
        "1": UserRole.SUPER_ADMIN,
        "2": UserRole.ADMIN,
        "3": UserRole.DEVELOPER,
        "4": UserRole.API_USER,
        "5": UserRole.READ_ONLY,
        "": UserRole.API_USER,  # default
    }

    role = (role_map.get( if role_map else None)role_choice, UserRole.API_USER)

    try:
        # Create the user
        user = (user_manager.create_user( if user_manager else None)
            email=email, username=username, password=password, role=role
        )

        (logger.info( if logger else None)f"\n✅ User created successfully!")
        (logger.info( if logger else None)f"   User ID: {user.user_id}")
        (logger.info( if logger else None)f"   Username: {user.username}")
        (logger.info( if logger else None)f"   Email: {user.email}")
        (logger.info( if logger else None)f"   Role: {user.role}")
        (logger.info( if logger else None)f"   Created: {user.created_at}")

        # Test authentication
        (logger.info( if logger else None)f"\n🔍 Testing authentication...")
        auth_user = (user_manager.authenticate_user( if user_manager else None)username, password)
        if auth_user:
            (logger.info( if logger else None)"✅ Authentication test successful!")

            # Generate test tokens
            access_token = create_access_token(
                {
                    "user_id": user.user_id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                }
            )

            refresh_token = create_refresh_token(
                {
                    "user_id": user.user_id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                }
            )

            (logger.info( if logger else None)"✅ JWT tokens generated successfully!")
            (logger.info( if logger else None)f"\n📋 Authentication Details:")
            (logger.info( if logger else None)f"   Username/Email: {username} or {email}")
            (logger.info( if logger else None)f"   Password: [HIDDEN]")
            (logger.info( if logger else None)f"   Access Token: {access_token[:50]}...")
            (logger.info( if logger else None)f"   Refresh Token: {refresh_token[:50]}...")

        else:
            (logger.info( if logger else None)"❌ Authentication test failed!")
            return False

        return True

    except ValueError as e:
        (logger.info( if logger else None)f"❌ Error creating user: {e}")
        return False
    except Exception as e:
        (logger.info( if logger else None)f"❌ Unexpected error: {e}")
        return False


def create_user_programmatic(
    username: str, email: str, password: str, role: str = UserRole.API_USER
):
    """Create a user programmatically"""
    try:
        user = (user_manager.create_user( if user_manager else None)
            email=email, username=username, password=password, role=role
        )

        # Test authentication
        auth_user = (user_manager.authenticate_user( if user_manager else None)username, password)
        if not auth_user:
            raise Exception("Authentication test failed")

        return user

    except Exception as e:
        (logger.info( if logger else None)f"❌ Error creating user: {e}")
        return None


def list_users():
    """List all existing users"""
    (logger.info( if logger else None)"👥 Existing Users:")
    (logger.info( if logger else None)"=" * 50)

    if not user_manager.users:
        (logger.info( if logger else None)"No users found.")
        return

    for user_id, user in user_manager.(users.items( if users else None)):
        (logger.info( if logger else None)f"   {user.username} ({user.email}) - {user.role}")


def test_authentication():
    """Test authentication with existing users"""
    (logger.info( if logger else None)"🔍 Authentication Test")
    (logger.info( if logger else None)"=" * 50)

    username_or_email = input("Enter username or email: ").strip()
    password = getpass("Enter password: ")

    user = (user_manager.authenticate_user( if user_manager else None)username_or_email, password)
    if user:
        (logger.info( if logger else None)"✅ Authentication successful!")
        (logger.info( if logger else None)f"   User: {user.username} ({user.email})")
        (logger.info( if logger else None)f"   Role: {user.role}")
        (logger.info( if logger else None)f"   Last Login: {user.last_login}")

        # Generate tokens
        access_token = create_access_token(
            {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
            }
        )

        (logger.info( if logger else None)f"   Access Token: {access_token[:50]}...")

    else:
        (logger.info( if logger else None)"❌ Authentication failed!")


def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_users()
        elif sys.argv[1] == "test":
            test_authentication()
        else:
            (logger.info( if logger else None)"Usage: python create_user.py [list|test]")
    else:
        create_user_interactive()


if __name__ == "__main__":
    main()
