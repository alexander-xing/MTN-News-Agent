import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator

# --- 自动读取 GitHub Secrets ---
# 这里不需要改！os.environ 会自动去你的 GitHub 设置里抓取信息
SENDER_EMAIL = os.environ.get('MY_EMAIL')
SENDER_PASSWORD = os.environ.get('MY_PASS')
RECEIVER_EMAIL = os.environ.get('RECEIVER')

# 模拟的新闻数据
news_list = [
    {"title": "OpenAI announces new features for ChatGPT", "url": "https://openai.com"},
    {"title": "Global stock markets show recovery signs", "url": "https://finance.yahoo.com"}
]

def generate_email_content(news_data):
    translator = GoogleTranslator(source='en', target='zh-CN')
    html = """
    <html>
    <body>
        <h2 style="color: #333;">今日新闻推送 (翻译版)</h2>
        <table border="1" style="border-collapse: collapse; width: 100%; font-family: Arial;">
            <tr style="background-color: #4CAF50; color: white;">
                <th style="padding: 12px;">英文标题</th>
                <th style="padding: 12px;">中文翻译</th>
                <th style="padding: 12px;">操作</th>
            </tr>
    """
    for item in news_data:
        eng_title = item['title']
        link = item['url']
        try:
            chi_title = translator.translate(eng_title)
        except:
            chi_title = "翻译暂不可用"
            
        html += f"""
            <tr>
                <td style="padding: 10px;">{eng_title}</td>
                <td style="padding: 10px;">{chi_title}</td>
                <td style="padding: 10px;"><a href="{link}" style="color: #1a73e8;">点击阅读</a></td>
            </tr>
        """
    html += "</table><p style='font-size: 12px; color: #888;'>此邮件由 GitHub Actions 自动生成发送</p></body></html>"
    return html

def send_email():
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("错误: 未能在环境中找到邮箱或密码，请检查 GitHub Secrets 设置。")
        return

    msg = MIMEMultipart()
    msg['Subject'] = "今日新闻自动翻译推送"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    content = generate_email_content(news_list)
    msg.attach(MIMEText(content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_msg(msg)
        print("✅ 邮件发送成功！")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    send_email()
