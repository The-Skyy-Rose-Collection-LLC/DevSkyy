import os
import sys

from getpass import getpass
"""
User Creation Utility for DevSkyy Enterprise Platform
Creates new users with proper password hashing and authentication setup
"""

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    create_access_token,
    create_refresh_token,
    user_manager,
    UserRole,
)

def create_user_interactive():
    """Create a user interactively"""
    logger.info("🔐 DevSkyy Enterprise - User Creation Utility")
    logger.info("=" * 50)

    # Get user details
    username = input("Enter username: ").strip()
    if not username:
        logger.info("❌ Username cannot be empty")
        return False

    email = input("Enter email: ").strip()
    if not email:
        logger.info("❌ Email cannot be empty")
        return False

    # Get password securely
    password = getpass("Enter password: ")
    if not password:
        logger.info("❌ Password cannot be empty")
        return False

    password_confirm = getpass("Confirm password: ")
    if password != password_confirm:
        logger.info("❌ Passwords do not match")
        return False

    # Get role
    logger.info("\nAvailable roles:")
    logger.info("1. super_admin - Full system access")
    logger.info("2. admin - Administrative access")
    logger.info("3. developer - Development access")
    logger.info("4. api_user - API access (default)")
    logger.info("5. read_only - Read-only access")

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
        user = user_manager.create_user(
            email=email, username=username, password=password, role=role
        )

        logger.info(f"\n✅ User created successfully!")
        logger.info(f"   User ID: {user.user_id}")
        logger.info(f"   Username: {user.username}")
        logger.info(f"   Email: {user.email}")
        logger.info(f"   Role: {user.role}")
        logger.info(f"   Created: {user.created_at}")

        # Test authentication
        logger.info(f"\n🔍 Testing authentication...")
        auth_user = user_manager.authenticate_user(username, password)
        if auth_user:
            logger.info("✅ Authentication test successful!")

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

            logger.info("✅ JWT tokens generated successfully!")
            logger.info(f"\n📋 Authentication Details:")
            logger.info(f"   Username/Email: {username} or {email}")
            logger.info(f"   Password: [HIDDEN]")
            logger.info(f"   Access Token: {access_token[:50]}...")
            logger.info(f"   Refresh Token: {refresh_token[:50]}...")

        else:
            logger.info("❌ Authentication test failed!")
            return False

        return True

    except ValueError as e:
        logger.info(f"❌ Error creating user: {e}")
        return False
    except Exception as e:
        logger.info(f"❌ Unexpected error: {e}")
        return False

def create_user_programmatic(
    username: str, email: str, password: str, role: str = UserRole.API_USER
):
    """Create a user programmatically"""
    try:
        user = user_manager.create_user(
            email=email, username=username, password=password, role=role
        )

        # Test authentication
        auth_user = user_manager.authenticate_user(username, password)
        if not auth_user:
            raise Exception("Authentication test failed")

        return user

    except Exception as e:
        logger.info(f"❌ Error creating user: {e}")
        return None

def list_users():
    """List all existing users"""
    logger.info("👥 Existing Users:")
    logger.info("=" * 50)

    if not user_manager.users:
        logger.info("No users found.")
        return

    for user_id, user in user_manager.users.items():
        logger.info(f"   {user.username} ({user.email}) - {user.role}")

def test_authentication():
    """Test authentication with existing users"""
    logger.info("🔍 Authentication Test")
    logger.info("=" * 50)

    username_or_email = input("Enter username or email: ").strip()
    password = getpass("Enter password: ")

    user = user_manager.authenticate_user(username_or_email, password)
    if user:
        logger.info("✅ Authentication successful!")
        logger.info(f"   User: {user.username} ({user.email})")
        logger.info(f"   Role: {user.role}")
        logger.info(f"   Last Login: {user.last_login}")

        # Generate tokens
        access_token = create_access_token(
            {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
            }
        )

        logger.info(f"   Access Token: {access_token[:50]}...")

    else:
        logger.info("❌ Authentication failed!")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_users()
        elif sys.argv[1] == "test":
            test_authentication()
        else:
            logger.info("Usage: python create_user.py [list|test]")
    else:
        create_user_interactive()

if __name__ == "__main__":
    main()
