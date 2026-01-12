import os
import smtplib
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from time import mktime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator

def fetch_news(query, days=14, limit=20):
    encoded_query = urllib.parse.quote(query)
    # 使用更广的 gl=US 确保国际媒体源，ceid 控制输出
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(rss_url)
    items = []
    threshold = datetime.now() - timedelta(days=days)
    
    for entry in feed.entries:
        if not hasattr(entry, 'published_parsed'): continue
        published_time = datetime.fromtimestamp(mktime(entry.published_parsed))
        if published_time > threshold:
            items.append({
                "title": entry.title,
                "url": entry.link,
                "source": entry.source.get('title', 'Media'),
                "date": published_time.strftime('%Y-%m-%d'),
                "id": entry.id if hasattr(entry, 'id') else entry.link
            })
        if len(items) >= limit: break
    return items

def format_rows(news_list, translator, seen_urls):
    if not news_list:
        return "<tr><td style='padding:15px; color:#999;'>过去14天暂无此类动态</td></tr>"
    
    rows = ""
    for item in news_list:
        if item['url'] in seen_urls: continue
        seen_urls.add(item['url'])
        
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
                    <span style="background:#fff7e6; color:#d4a017; padding:2px 5px; border-radius:3px; font-weight:bold;">{item['source']}</span> | {item['date']} 
                    | <a href="{item['url']}" style="color:#3182ce; text-decoration:none;">阅读全文 →</a>
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
    seen_urls = set()

    # --- 10大分公司关键词定义 ---
    countries = [
        "MTN Group", "MTN Nigeria", "MTN South Africa", "MTN Ghana", 
        "MTN Uganda", "MTN Cameroon", "MTN Ivory Coast", "MTN Benin", 
        "MTN Zambia", "MTN Rwanda"
    ]
    base_query = "(" + " OR ".join([f'"{c}"' for c in countries]) + ")"

    # 分类 1：财务、业绩、集团战略 (过去14天)
    fin_query = f"{base_query} (Profit OR Dividend OR Result OR Revenue OR Acquisition OR CEO)"
    fin_news = fetch_news(fin_query, days=14, limit=15)

    # 分类 2：市场动态、基建、各分公司业务 (过去14天)
    market_query = f"{base_query} (5G OR Network OR Subscriber OR Fintech OR MoMo OR SIM OR Spectrum)"
    market_news = fetch_news(market_query, days=14, limit=20)

    fin_html = format_rows(fin_news, translator, seen_urls)
    market_html = format_rows(market_news, translator, seen_urls)

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f7f6; padding: 20px;">
        <div style="max-width: 700px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <div style="background: #ffcc00; padding: 35px 20px; text-align: center;">
                <h1 style="margin: 0; color: #000; font-size: 24px;">MTN 集团全区域动态情报</h1>
                <p style="margin: 8px 0 0; color: #333; font-size: 14px;">覆盖：尼日利亚、南非、加纳、赞比亚等10大市场</p>
                <p style="margin: 5px 0 0; color: #666; font-size: 12px;">报告周期：最近14天 | 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>

            <div style="padding: 15px; background: #fffbe6; border-left: 5px solid #ffcc00; font-weight: bold; color: #856404;">
                📊 财务业绩与集团战略
            </div>
            <table style="width: 100%; border-collapse: collapse;">{fin_html}</table>

            <div style="padding: 15px; background: #e6f7ff; border-left: 5px solid #1890ff; font-weight: bold; color: #004085; margin-top: 15px;">
                🌍 分公司市场、基建与数字化
            </div>
            <table style="width: 100%; border-collapse: collapse;">{market_html}</table>

            <div style="padding: 20px; text-align: center; font-size: 11px; color: #999; background: #fafafa;">
                抓取源：Google News (Global Edition)<br>
                此报告每日自动追踪 MTN 10大分公司动态
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['Subject'] = f"MTN 全球情报看板：10国市场追踪 ({datetime.now().strftime('%m/%d')})"
    msg['From'] = f"MTN Intelligence <{sender_user}>"
    msg['To'] = receiver_user
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_user, sender_password)
            server.send_message(msg)
        print("✅ 14天深度简报已送达。")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

if __name__ == "__main__":
    send_news_email()
