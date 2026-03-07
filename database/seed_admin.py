"""Seed an admin user into the DevSkyy database.

Usage:
    python3 -m database.seed_admin
"""

from __future__ import annotations

import asyncio
import os
import uuid


async def seed_admin():
    from database.db import User, db_manager
    from security.jwt_oauth2_auth import password_manager

    await db_manager.initialize()

    admin_email = os.getenv("ADMIN_EMAIL", "admin@skyyrose.co")
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "SkyyRose!2026Admin")

    async with db_manager.session() as db:
        from database.db import UserRepository

        repo = UserRepository(db)

        existing = await repo.get_by_username(admin_username)
        if existing:
            print(f"Admin user '{admin_username}' already exists — skipping.")
            return

        hashed = password_manager.hash_password(admin_password)
        admin = User(
            id=str(uuid.uuid4()),
            email=admin_email,
            username=admin_username,
            hashed_password=hashed,
            role="super_admin",
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        await db.commit()
        print(f"Admin user created: {admin_username} / {admin_email}")
        print("  Role: super_admin")
        print(f"  Password: {'*' * len(admin_password)} (from ADMIN_PASSWORD env or default)")


if __name__ == "__main__":
    asyncio.run(seed_admin())
