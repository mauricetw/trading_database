import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import random
from dotenv import load_dotenv

load_dotenv()

def send_reset_email(email: str):
    sender_email = os.getenv('SMTP_EMAIL')
    password = os.getenv('SMTP_PASSWORD')

    #sender = "Private Person <from@example.com>"
    #receiver = "A Test User <to@example.com>"

    if not sender_email or not password:
        raise ValueError("SMTP 資訊未設定")

    # 產生 5 位數驗證碼
    code = str(random.randint(10000, 99999))

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = "重設密碼"

    body = f"您的驗證碼為：{code}\n請在應用程式中輸入此驗證碼以重設密碼。"
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # 啟用加密
            server.login(sender_email, password)
            server.sendmail(sender_email, email, msg.as_string())
        
        #with smtplib.SMTP("sandbox.smtp.mailtrap.io", 587) as server:
        #    server.starttls()  # 啟用加密
        #    server.login("ea5cf55988efef", "5292652b26cb88")
        #    server.sendmail(sender, receiver, msg.as_string())

    except Exception as e:
        raise Exception(f"發送郵件失敗：{str(e)}")
