import os
import smtplib
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from time import mktime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator

def fetch_news(query, limit=8):
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(rss_url)
    items = []
    seven_days_ago = datetime.now() - timedelta(days=7) # 缩短到7天，确保信息精准
    for entry in feed.entries:
        if not hasattr(entry, 'published_parsed'): continue
        published_time = datetime.fromtimestamp(mktime(entry.published_parsed))
        if published_time > seven_days_ago:
            items.append({
                "title": entry.title,
                "url": entry.link,
                "source": entry.source.get('title', 'Media'),
                "date": published_time.strftime('%m-%d')
            })
        if len(items) >= limit: break
    return items

def format_rows(news_list, translator):
    if not news_list:
        return "<tr><td style='padding:20px; color:#999;'>暂无相关动态</td></tr>"
    rows = ""
    for item in news_list:
        try:
            chi_title = translator.translate(item['title'])
        except:
            chi_title = item['title']
        
        rows += f"""
        <tr>
            <td style="padding: 15px; border-bottom: 1px solid #eee;">
                <div style="font-size: 15px; font-weight: bold; color: #2d3748; margin-bottom: 4px;">{chi_title}</div>
                <div style="font-size: 12px; color: #718096; margin-bottom: 8px;">{item['title']}</div>
                <div style="font-size: 11px; color: #a0aec0;">
                    <span style="background:#edf2f7; padding:2px 5px; border-radius:3px;">{item['source']}</span> | {item['date']} 
                    | <a href="{item['url']}" style="color:#3182ce; text-decoration:none;">查看原文 →</a>
                </div>
            </td>
        </tr>
        """
    return rows

def send_news_email():
    sender_user = os.environ.get('EMAIL_ADDRESS')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_user = os.environ.get('RECEIVER_EMAIL')

    translator = GoogleTranslator(source='en', target='zh-CN')

    # --- 分类搜索逻辑 ---
    # 1. 财务与业绩 (MTN + 竞争对手)
    fin_query = '(MTN OR "Airtel Africa" OR Vodacom) AND (Profit OR Dividend OR Result OR "Market Share" OR Revenue)'
    fin_news = fetch_news(fin_query, limit=6)

    # 2. 技术与基建 (5G, 数字化, 铁塔)
    tech_query = '(MTN OR "Airtel Africa" OR Vodacom) AND (5G OR Network OR Fiber OR "Data Center" OR Fintech)'
    tech_news = fetch_news(tech_query, limit=6)

    fin_html = format_rows(fin_news, translator)
    tech_html = format_rows(tech_news, translator)

    html_content = f"""
    <html>
    <body style="font-family: Arial; background-color: #f6f9fc; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <div style="background: #ffcc00; padding: 30px 20px; text-align: center;">
                <img src="https://www.mtn.com/wp-content/uploads/2022/02/MTN-Logo.png" width="50" style="margin-bottom:10px;">
                <h2 style="margin: 0; color: #000; font-size: 22px;">非洲电信市场深度观察</h2>
                <p style="margin: 5px 0 0; color: #444; font-size: 13px;">{datetime.now().strftime('%Y-%m-%d')} | 财务 & 技术双周报</p>
            </div>

            <div style="padding: 15px; background: #fff9e6; border-left: 4px solid #ffcc00; font-weight: bold; color: #856404;">
                💰 财务、业绩与市场头条
            </div>
            <table style="width: 100%; border-collapse: collapse;">{fin_html}</table>

            <div style="padding: 15px; background: #e6f4ff; border-left: 4px solid #3182ce; font-weight: bold; color: #004085; margin-top: 10px;">
                📡 5G、基建与数字化转型
            </div>
            <table style="width: 100%; border-collapse: collapse;">{tech_html}</table>

            <div style="padding: 20px; text-align: center; font-size: 11px; color: #a0aec0; background: #fafafa;">
                关键词范围：MTN, Airtel Africa, Vodacom<br>
                本报告由自动化分析引擎生成
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['Subject'] = f"MTN 竞对情报：财务与技术焦点 ({datetime.now().strftime('%m/%d')})"
    msg['From'] = f"MTN Intelligence <{sender_user}>"
    msg['To'] = receiver_user
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_user, sender_password)
            server.send_message(msg)
        print("✅ 报告已成功投递。")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    send_news_email()
