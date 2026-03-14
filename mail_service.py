import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class MailService:
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.sender_email = os.environ.get('SENDER_EMAIL')
    
    def send_verification_email(self, to_email, verification_code):
        if not self.smtp_username or not self.smtp_password:
            print("SMTP credentials not set. Skipping email sending.")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = 'Coo注册验证码'
            
            body = f"您的Coo注册验证码是：{verification_code}\n请在10分钟内使用此验证码完成注册。"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, to_email, text)
            server.quit()
            return True
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False

mail_service = MailService()