import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator  # 用于翻译

def send_news_email():
    # 1. 从 GitHub Secrets 中安全地读取配置
    sender_user = os.environ.get('EMAIL_ADDRESS')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_user = os.environ.get('RECEIVER_EMAIL')

    # 2. 准备新闻数据 (这里假设你已经有了一个新闻列表，如果没有，我们之后可以接入 RSS)
    # 格式示例: [{'title': 'English Title', 'url': 'https://...'}]
    news_items = [
        {"title": "OpenAI releases new GPT-5 preview", "url": "https://openai.com"},
        {"title": "Stock market reaches all-time high", "url": "https://finance.yahoo.com"},
        {"title": "NASA's James Webb telescope finds water on exoplanet", "url": "https://nasa.gov"}
    ]

    # 3. 翻译标题并构建 HTML 表格内容
    translator = GoogleTranslator(source='en', target='zh-CN')
    table_rows = ""
    
    for item in news_items:
        eng_title = item['title']
        link = item['url']
        try:
            # 执行翻译
            chi_title = translator.translate(eng_title)
        except:
            chi_title = "翻译失败"
        
        # 构建表格行
        table_rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{eng_title}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{chi_title}</td>
            <td style="padding: 8px; border: 1px solid #ddd;"><a href="{link}">查看原文</a></td>
        </tr>
        """

    # 4. 组装最终的 HTML 邮件正文
    html_content = f"""
    <html>
    <body>
        <h2 style="color: #2c3e50;">今日新闻自动推送</h2>
        <table style="width: 100%; border-collapse: collapse; font-family: sans-serif;">
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">英文标题</th>
                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">中文翻译</th>
                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">原文链接</th>
            </tr>
            {table_rows}
        </table>
        <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">数据由 GitHub Actions 自动生成发送</p>
    </body>
    </html>
    """

# 5. 发送邮件
    msg = MIMEMultipart()
    msg['Subject'] = "今日新闻自动翻译推送"
    msg['From'] = sender_user
    msg['To'] = receiver_user
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_user, sender_password)
            # 关键修改：将 send_msg 改为 send_message
            server.send_message(msg) 
        print("✅ 邮件发送成功！")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    send_news_email()
