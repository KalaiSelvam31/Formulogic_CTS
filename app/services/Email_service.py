import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv

load_dotenv()

# Get your API key from the environment variable
API_KEY = os.environ.get("BREVO_API_KEY")

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = API_KEY

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


def send_login_otp_email(user_email: str, otp: str):
    sender = {"email": "support@formulogic.systems", "name": "Formulogic Systems"}
    to = [{"email": user_email}]
    subject = f"Your FormuLogic Login Verification Code"

    # --- DARK THEME HTML (same style as above, only wording changed) ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login Verification</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap');
            body {{
                margin: 0;
                padding: 0;
                background-color: #f8f9fa;
                font-family: 'Lato', Arial, sans-serif;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #2C3E50;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .header {{
                padding: 40px;
                text-align: center;
            }}
            .header h1 {{
                color: #ffffff;
                font-size: 28px;
                font-weight: 700;
                margin: 0;
                letter-spacing: 1px;
            }}
            .header span {{
                color: #27AE60;
            }}
            .content {{
                padding: 20px 40px 40px;
                color: #EAECEE;
                font-size: 16px;
                line-height: 1.6;
            }}
            .otp-code {{
                background-color: #34495E;
                border-radius: 8px;
                padding: 25px;
                margin: 30px 0;
                text-align: center;
            }}
            .otp-code p {{
                margin: 0 0 10px;
                font-size: 16px;
                color: #BDC3C7;
            }}
            .otp-code h2 {{
                font-size: 42px;
                font-weight: 700;
                color: #27AE60;
                margin: 0;
                letter-spacing: 5px;
            }}
            .footer {{
                text-align: center;
                font-size: 12px;
                color: #7F8C8D;
                padding: 20px 40px;
            }}
            .footer a {{
                color: #27AE60;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Formu<span>Logic</span></h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>We noticed a login attempt to your account. Please use the following code to verify and complete your login. This code is valid for the next 10 minutes.</p>
                <div class="otp-code">
                    <p>Your Login Verification Code</p>
                    <h2>{otp}</h2>
                </div>
                <p>If you did not attempt to log in, please secure your account immediately by resetting your password.</p>
                <p>Thank you,<br>The FormuLogic Team</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 FormuLogic. All Rights Reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, sender=sender, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
        print(f"Login OTP email sent to {user_email}")
        return {"success": True}
    except ApiException as e:
        print(f"Error sending login OTP email via Brevo: {e}")
        return {"success": False, "error": str(e)}

def send_password_reset_email(user_email: str, otp: str):
    sender = {"email": "support@formulogic.systems", "name": "Formulogic Systems"}
    to = [{"email": user_email}]
    subject = f"Your FormuLogic Password Reset Code"

    # --- REVERTED DARK THEME HTML ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap');
            body {{
                margin: 0;
                padding: 0;
                background-color: #f8f9fa;
                font-family: 'Lato', Arial, sans-serif;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #2C3E50;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .header {{
                padding: 40px;
                text-align: center;
            }}
            .header h1 {{
                color: #ffffff;
                font-size: 28px;
                font-weight: 700;
                margin: 0;
                letter-spacing: 1px;
            }}
            .header span {{
                color: #27AE60;
            }}
            .content {{
                padding: 20px 40px 40px;
                color: #EAECEE;
                font-size: 16px;
                line-height: 1.6;
            }}
            .otp-code {{
                background-color: #34495E;
                border-radius: 8px;
                padding: 25px;
                margin: 30px 0;
                text-align: center;
            }}
            .otp-code p {{
                margin: 0 0 10px;
                font-size: 16px;
                color: #BDC3C7;
            }}
            .otp-code h2 {{
                font-size: 42px;
                font-weight: 700;
                color: #27AE60;
                margin: 0;
                letter-spacing: 5px;
            }}
            .footer {{
                text-align: center;
                font-size: 12px;
                color: #7F8C8D;
                padding: 20px 40px;
            }}
            .footer a {{
                color: #27AE60;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Formu<span>Logic</span></h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>We received a request to reset the password for your account. Please use the code below to complete the process. This code is valid for the next 10 minutes.</p>
                <div class="otp-code">
                    <p>Your Password Reset Code</p>
                    <h2>{otp}</h2>
                </div>
                <p>If you did not request a password reset, you can safely ignore this email. Only a person with access to your email can reset your password.</p>
                <p>Thank you,<br>The FormuLogic Team</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 FormuLogic. All Rights Reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, sender=sender, subject=subject, html_content=html_content)
    try:
        api_instance.send_transac_email(send_smtp_email)
        print(f"Password reset OTP email sent to {user_email}")
        return {"success": True}
    except ApiException as e:
        print(f"Error sending password reset email via Brevo: {e}")
        return {"success": False, "error": str(e)}

