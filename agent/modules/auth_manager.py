
import jwt
import bcrypt
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import secrets
import re
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    """Comprehensive authentication and user management system."""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(64))
        self.db_path = "devskyy_users.db"
        self.security = HTTPBearer()
        self.init_database()
    
    def init_database(self):
        """Initialize user database with secure schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                email_verified BOOLEAN DEFAULT 0,
                verification_token TEXT,
                reset_token TEXT,
                reset_token_expires TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token_hash TEXT UNIQUE,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                theme TEXT DEFAULT 'light',
                notifications_enabled BOOLEAN DEFAULT 1,
                marketing_emails BOOLEAN DEFAULT 0,
                dashboard_layout TEXT DEFAULT 'default',
                timezone TEXT DEFAULT 'UTC',
                language TEXT DEFAULT 'en',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password strength."""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def create_user(self, email: str, username: str, password: str, 
                   first_name: str = "", last_name: str = "") -> Dict[str, Any]:
        """Create new user account with validation."""
        
        # Validate input
        if not self.validate_email(email):
            return {"success": False, "error": "Invalid email format"}
        
        password_validation = self.validate_password(password)
        if not password_validation["valid"]:
            return {"success": False, "error": password_validation["errors"]}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", (email, username))
            if cursor.fetchone():
                return {"success": False, "error": "User with this email or username already exists"}
            
            # Hash password and create user
            password_hash = self.hash_password(password)
            verification_token = secrets.token_urlsafe(32)
            
            cursor.execute('''
                INSERT INTO users (email, username, password_hash, first_name, last_name, verification_token)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (email, username, password_hash, first_name, last_name, verification_token))
            
            user_id = cursor.lastrowid
            
            # Create default preferences
            cursor.execute('''
                INSERT INTO user_preferences (user_id) VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            
            return {
                "success": True,
                "user_id": user_id,
                "message": "User created successfully",
                "verification_token": verification_token
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating user: {str(e)}")
            return {"success": False, "error": "Failed to create user"}
        finally:
            conn.close()
    
    def authenticate_user(self, email: str, password: str, ip_address: str = "", 
                         user_agent: str = "") -> Dict[str, Any]:
        """Authenticate user and create session."""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get user data
            cursor.execute('''
                SELECT id, username, password_hash, is_active, failed_login_attempts, 
                       locked_until, email_verified
                FROM users WHERE email = ?
            ''', (email,))
            
            user_data = cursor.fetchone()
            if not user_data:
                return {"success": False, "error": "Invalid credentials"}
            
            user_id, username, password_hash, is_active, failed_attempts, locked_until, email_verified = user_data
            
            # Check if account is locked
            if locked_until and datetime.fromisoformat(locked_until) > datetime.now():
                return {"success": False, "error": "Account temporarily locked due to failed login attempts"}
            
            # Check if account is active
            if not is_active:
                return {"success": False, "error": "Account is deactivated"}
            
            # Verify password
            if not self.verify_password(password, password_hash):
                # Increment failed attempts
                new_failed_attempts = failed_attempts + 1
                locked_until_time = None
                
                if new_failed_attempts >= 5:
                    locked_until_time = (datetime.now() + timedelta(minutes=30)).isoformat()
                
                cursor.execute('''
                    UPDATE users SET failed_login_attempts = ?, locked_until = ?
                    WHERE id = ?
                ''', (new_failed_attempts, locked_until_time, user_id))
                conn.commit()
                
                return {"success": False, "error": "Invalid credentials"}
            
            # Reset failed attempts on successful login
            cursor.execute('''
                UPDATE users SET failed_login_attempts = 0, locked_until = NULL, last_login = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), user_id))
            
            # Create JWT token
            token_payload = {
                "user_id": user_id,
                "username": username,
                "email": email,
                "exp": datetime.utcnow() + timedelta(hours=24),
                "iat": datetime.utcnow()
            }
            
            token = jwt.encode(token_payload, self.secret_key, algorithm="HS256")
            
            # Store session
            token_hash = bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode()
            expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
            
            cursor.execute('''
                INSERT INTO user_sessions (user_id, token_hash, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, token_hash, expires_at, ip_address, user_agent))
            
            conn.commit()
            
            return {
                "success": True,
                "access_token": token,
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": email,
                    "email_verified": bool(email_verified)
                }
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {"success": False, "error": "Authentication failed"}
        finally:
            conn.close()
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Check if session is still valid
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM user_sessions 
                WHERE user_id = ? AND expires_at > ? AND is_active = 1
            ''', (payload["user_id"], datetime.now().isoformat()))
            
            if not cursor.fetchone():
                conn.close()
                return None
            
            conn.close()
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Dependency to get current authenticated user."""
        token = credentials.credentials
        payload = self.verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get complete user profile data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get user data
            cursor.execute('''
                SELECT id, email, username, first_name, last_name, role, 
                       created_at, last_login, email_verified
                FROM users WHERE id = ?
            ''', (user_id,))
            
            user_data = cursor.fetchone()
            if not user_data:
                return {"error": "User not found"}
            
            # Get preferences
            cursor.execute('''
                SELECT theme, notifications_enabled, marketing_emails, 
                       dashboard_layout, timezone, language
                FROM user_preferences WHERE user_id = ?
            ''', (user_id,))
            
            prefs_data = cursor.fetchone()
            
            # Get active sessions count
            cursor.execute('''
                SELECT COUNT(*) FROM user_sessions 
                WHERE user_id = ? AND expires_at > ? AND is_active = 1
            ''', (user_id, datetime.now().isoformat()))
            
            active_sessions = cursor.fetchone()[0]
            
            return {
                "id": user_data[0],
                "email": user_data[1],
                "username": user_data[2],
                "first_name": user_data[3],
                "last_name": user_data[4],
                "role": user_data[5],
                "created_at": user_data[6],
                "last_login": user_data[7],
                "email_verified": bool(user_data[8]),
                "active_sessions": active_sessions,
                "preferences": {
                    "theme": prefs_data[0] if prefs_data else "light",
                    "notifications_enabled": bool(prefs_data[1]) if prefs_data else True,
                    "marketing_emails": bool(prefs_data[2]) if prefs_data else False,
                    "dashboard_layout": prefs_data[3] if prefs_data else "default",
                    "timezone": prefs_data[4] if prefs_data else "UTC",
                    "language": prefs_data[5] if prefs_data else "en"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return {"error": "Failed to retrieve profile"}
        finally:
            conn.close()
    
    def logout_user(self, token: str) -> Dict[str, Any]:
        """Logout user by invalidating session."""
        payload = self.verify_token(token)
        if not payload:
            return {"success": False, "error": "Invalid token"}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE user_sessions SET is_active = 0 
                WHERE user_id = ? AND is_active = 1
            ''', (payload["user_id"],))
            
            conn.commit()
            return {"success": True, "message": "Logged out successfully"}
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {"success": False, "error": "Logout failed"}
        finally:
            conn.close()

# Initialize authentication manager
auth_manager = AuthManager()
