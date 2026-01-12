import os
import smtplib
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from time import mktime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator

def get_mtn_intelligence():
    """获取 MTN 动态，具备双重搜索保底机制"""
    # 策略 A：高精准多子网搜索
    subsidaries = [
        'MTN Group', '"MTN South Africa"', '"MTN Nigeria"', 
        '"MTN Ghana"', '"MTN Uganda"', '"MTN Cameroon"', '"MTN Ivory Coast"'
    ]
    query_str = "(" + " OR ".join(subsidaries) + ") when:14d"
    
    # 尝试第一次检索
    news_items = fetch_from_google(query_str)
    
    # --- 策略 B：保底机制 ---
    # 如果高精准搜索没结果，切换到最基础的关键词，确保一定能搜到新闻
    if not news_items:
        print("⚠️ 高精准搜索未匹配到结果，正在启动保底搜索策略...")
        fallback_query = "MTN Telecom when:14d"
        news_items = fetch_from_google(fallback_query)
        
    return news_items

def fetch_from_google(query):
    """通用的 RSS 抓取逻辑"""
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    feed = feedparser.parse(rss_url)
    items = []
    two_weeks_ago = datetime.now() - timedelta(days=14)

    for entry in feed.entries:
        if not hasattr(entry, 'published_parsed'): continue
        published_time = datetime.fromtimestamp(mktime(entry.published_parsed))
        
        if published_time > two_weeks_ago:
            items.append({
                "title": entry.title,
                "url": entry.link,
                "source": entry.source.get('title', 'Global Media'),
                "date": published_time.strftime('%Y-%m-%d')
            })
        if len(items) >= 20: break
    return items

def send_news_email():
    sender_user = os.environ.get('EMAIL_ADDRESS')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_user = os.environ.get('RECEIVER_EMAIL')

    news_data = get_mtn_intelligence()
    
    # 再次兜底：如果连保底搜索都搜不到，强制生成一条系统提示，而不是直接退出
    if not news_data:
        news_data = [{
            "title": "System Alert: No major news found in the last 14 days for MTN subsidiaries.",
            "url": "https://news.google.com",
            "source": "System",
            "date": datetime.now().strftime('%Y-%m-%d')
        }]

    translator = GoogleTranslator(source='en', target='zh-CN')
    table_rows = ""
    
    for item in news_data:
        eng_title = item['title']
        try:
            chi_title = translator.translate(eng_title)
        except:
            chi_title = "翻译接口繁忙，请阅读原文"
            
        table_rows += f"""
        <tr>
            <td style="padding: 12px; border: 1px solid #ddd; font-size: 14px;">
                <strong>{eng_title}</strong><br>
                <span style="color: #666; font-size: 11px;">{item['source']} | {item['date']}</span>
            </td>
            <td style="padding: 12px; border: 1px solid #ddd; font-size: 14px; color: #333;">{chi_title}</td>
            <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">
                <a href="{item['url']}" style="display: inline-block; padding: 6px 12px; background-color: #ffcc00; color: #000; text-decoration: none; border-radius: 20px; font-weight: bold; font-size: 12px;">阅读原文</a>
            </td>
        </tr>
        """

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width:
