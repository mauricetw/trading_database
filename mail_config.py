import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

# --- 重大邏輯修正 ---
# 產生驗證碼的職責已移至 routers/auth.py。
# 此函式現在只負責傳送郵件，因此需要接收 `code` 作為參數。
def send_reset_email(email: str, code: str):
    """
    發送包含驗證碼的密碼重設郵件。

    :param email: 收件人的電子郵件地址。
    :param code: 由外部生成並傳入的 6 位數驗證碼。
    """
    sender_email = os.getenv('SMTP_EMAIL')
    password = os.getenv('SMTP_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER', "smtp.gmail.com")
    smtp_port = int(os.getenv('SMTP_PORT', 587))

    if not sender_email or not password:
        # 在伺服器端紀錄錯誤，但不要將敏感資訊拋給前端。
        print("錯誤：SMTP 寄件資訊未在 .env 檔案中設定。")
        raise ValueError("無法發送郵件，伺服器設定不完整。")

    msg = MIMEMultipart()
    msg['From'] = f"交易平台 <{sender_email}>"
    msg['To'] = email
    msg['Subject'] = "交易平台 | 重設密碼驗證碼"

    # --- 優化：使用 HTML 格式讓郵件更美觀 ---
    body = f"""
    <html>
    <body>
        <p>您好，</p>
        <p>您正在申請重設您在交易平台的帳號密碼。</p>
        <p>您的驗證碼是：</p>
        <h2 style="font-weight:bold; color: #333;">{code}</h2>
        <p>請在 10 分鐘內於應用程式中輸入此驗證碼以完成後續步驟。</p>
        <p>如果您未申請此操作，請忽略本郵件。</p>
        <br>
        <p>祝順心</p>
        <p>交易平台團隊</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # 啟用 TLS 加密
            server.login(sender_email, password)
            server.sendmail(sender_email, email, msg.as_string())
        print(f"密碼重設郵件已成功寄至 {email}")
    except Exception as e:
        print(f"發送郵件至 {email} 失敗：{e}")
        # 向上拋出一個通用的例外，避免洩漏伺服器內部細節
        raise Exception("發送郵件時發生未預期的錯誤。")

