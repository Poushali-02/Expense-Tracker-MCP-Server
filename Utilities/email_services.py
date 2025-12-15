import smtplib
import os
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import secrets
from datetime import datetime, timedelta
from pathlib import Path

# Load .env from project root (works regardless of where server is started)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
APP_URL = os.getenv("APP_URL", "https://transaction-tracker.fastmcp.app")

class EmailService:
    @staticmethod
    def generate_code():
        """Generate a 6-digit verification code"""
        return str(random.randint(100000, 999999))
    
    @staticmethod
    def get_code_expiry(minutes=5):
        """Get code expiry timestamp (default 5 minutes for security)"""
        return datetime.utcnow() + timedelta(minutes=minutes)
    
    @staticmethod
    async def send_email(to_email:str, subject: str, html_content:str):
        """Send email via smtp"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = FROM_EMAIL
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(FROM_EMAIL, to_email, msg.as_string())
            
            return True, 'Email sent successfully'
        
        except Exception as e:
            return False, str(e)
        
    @staticmethod
    async def send_verification_code(to_email:str, username:str, code:str):
        """Send 6-digit verification code for email verification"""
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">Welcome to Transaction Tracker, {username}! 🎉</h2>
            <p>Please use the following code to verify your email address:</p>
            <div style="background: linear-gradient(135deg, #4CAF50, #45a049); padding: 30px; border-radius: 10px; text-align: center; margin: 25px 0;">
                <span style="font-size: 36px; font-weight: bold; color: white; letter-spacing: 8px;">{code}</span>
            </div>
            <p style="color: #666;">Enter this code in Claude to verify your email.</p>
            <p style="color: #f44336; font-weight: bold;">⏱️ This code expires in 5 minutes.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">
                If you didn't create an account, please ignore this email.
            </p>
        </body>
        </html>
        """
        
        return await EmailService.send_email(
            to_email,
            f"Your verification code: {code}",
            html_content
        )
    
    @staticmethod
    async def send_password_reset_code(to_email:str, username:str, code:str):
        """Send 6-digit code for password reset"""
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">Password Reset Request 🔐</h2>
            <p>Hi {username},</p>
            <p>We received a request to reset your password. Use this code:</p>
            <div style="background: linear-gradient(135deg, #2196F3, #1976D2); padding: 30px; border-radius: 10px; text-align: center; margin: 25px 0;">
                <span style="font-size: 36px; font-weight: bold; color: white; letter-spacing: 8px;">{code}</span>
            </div>
            <p style="color: #666;">Enter this code in Claude along with your new password.</p>
            <p style="color: #f44336; font-weight: bold;">⏱️ This code expires in 5 minutes.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">
                If you didn't request this, please ignore this email. Your password won't change.
            </p>
        </body>
        </html>
        """
        
        return await EmailService.send_email(
            to_email, 
            f"Your password reset code: {code}",
            html_content
        )