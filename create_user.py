#!/usr/bin/env python3
"""
User Creation Utility for DevSkyy Enterprise Platform
Creates new users with proper password hashing and authentication setup
"""

import os
import sys
from getpass import getpass

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from security.jwt_auth import UserRole, create_access_token, create_refresh_token, user_manager


def create_user_interactive():
    """Create a user interactively"""
    print("🔐 DevSkyy Enterprise - User Creation Utility")
    print("=" * 50)

    # Get user details
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return False

    email = input("Enter email: ").strip()
    if not email:
        print("❌ Email cannot be empty")
        return False

    # Get password securely
    password = getpass("Enter password: ")
    if not password:
        print("❌ Password cannot be empty")
        return False

    password_confirm = getpass("Confirm password: ")
    if password != password_confirm:
        print("❌ Passwords do not match")
        return False

    # Get role
    print("\nAvailable roles:")
    print("1. super_admin - Full system access")
    print("2. admin - Administrative access")
    print("3. developer - Development access")
    print("4. api_user - API access (default)")
    print("5. read_only - Read-only access")

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

        print("\n✅ User created successfully!")
        print(f"   User ID: {user.user_id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role}")
        print(f"   Created: {user.created_at}")

        # Test authentication
        print("\n🔍 Testing authentication...")
        auth_user = user_manager.authenticate_user(username, password)
        if auth_user:
            print("✅ Authentication test successful!")

            # Generate test tokens
            access_token = create_access_token(
                {"user_id": user.user_id, "email": user.email, "username": user.username, "role": user.role}
            )

            refresh_token = create_refresh_token(
                {"user_id": user.user_id, "email": user.email, "username": user.username, "role": user.role}
            )

            print("✅ JWT tokens generated successfully!")
            print("\n📋 Authentication Details:")
            print(f"   Username/Email: {username} or {email}")
            print("   Password: [HIDDEN]")
            print(f"   Access Token: {access_token[:50]}...")
            print(f"   Refresh Token: {refresh_token[:50]}...")

        else:
            print("❌ Authentication test failed!")
            return False

        return True

    except ValueError as e:
        print(f"❌ Error creating user: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
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

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return None


def list_users():
    """List all existing users"""
    print("👥 Existing Users:")
    print("=" * 50)

    if not user_manager.users:
        print("No users found.")
        return

    for user_id, user in user_manager.users.items():
        print(f"   {user.username} ({user.email}) - {user.role}")


def test_authentication():
    """Test authentication with existing users"""
    print("🔍 Authentication Test")
    print("=" * 50)

    username_or_email = input("Enter username or email: ").strip()
    password = getpass("Enter password: ")

    user = user_manager.authenticate_user(username_or_email, password)
    if user:
        print("✅ Authentication successful!")
        print(f"   User: {user.username} ({user.email})")
        print(f"   Role: {user.role}")
        print(f"   Last Login: {user.last_login}")

        # Generate tokens
        access_token = create_access_token(
            {"user_id": user.user_id, "email": user.email, "username": user.username, "role": user.role}
        )

        print(f"   Access Token: {access_token[:50]}...")

    else:
        print("❌ Authentication failed!")


def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_users()
        elif sys.argv[1] == "test":
            test_authentication()
        else:
            print("Usage: python create_user.py [list|test]")
    else:
        create_user_interactive()


if __name__ == "__main__":
    main()
