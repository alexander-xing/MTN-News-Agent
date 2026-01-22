import os
import smtplib
import feedparser
import urllib.parse
import time
from datetime import datetime, timedelta
from time import mktime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator

def fetch_all_mtn_news(days=14):
    """
    循环抓取10个分公司的新闻，确保不遗漏
    """
    countries = [
        "MTN Group", "MTN Nigeria", "MTN South Africa", "MTN Ghana", 
        "MTN Uganda", "MTN Cameroon", "MTN Ivory Coast", "MTN Benin", 
        "MTN Zambia", "MTN Rwanda"
    ]
    
    all_items = []
    seen_links = set()
    threshold = datetime.now() - timedelta(days=days)
    
    print(f"开始抓取过去 {days} 天的 10 国市场新闻...")

    for country in countries:
        # 对每个分公司进行宽泛搜索
        query = f'"{country}"'
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(rss_url)
        count = 0
        for entry in feed.entries:
            if not hasattr(entry, 'published_parsed'): continue
            published_time = datetime.fromtimestamp(mktime(entry.published_parsed))
            
            if published_time > threshold:
                link = entry.link
                if link not in seen_links:
                    seen_links.add(link)
                    all_items.append({
                        "title": entry.title,
                        "url": link,
                        "source": entry.source.get('title', 'Media'),
                        "date": published_time.strftime('%Y-%m-%d'),
                        "timestamp": published_time
                    })
                    count += 1
            if count >= 8: break # 每个国家抓取最新的8条，防止单个国家刷屏
        
        print(f" - {country}: 找到 {count} 条相关动态")
        time.sleep(1) # 稍微停顿防止被 Google 屏蔽

    # 按时间降序排列
    all_items.sort(key=lambda x: x['timestamp'], reverse=True)
    return all_items

def send_news_email():
    sender_user = os.environ.get('EMAIL_ADDRESS')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_user = os.environ.get('RECEIVER_EMAIL')
    
    news_data = fetch_all_mtn_news(days=14)
    
    if not news_data:
        print("过去14天未搜到任何MTN相关新闻。")
        return

    translator = GoogleTranslator(source='en', target='zh-CN')
    table_rows = ""
    print(f"开始翻译并生成报告，共 {len(news_data)} 条...")
    
    for item in news_data:
        try:
            chi_title = translator.translate(item['title'])
        except:
            chi_title = item['title']
            
        table_rows += f"""
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

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f7f6; padding: 20px;">
        <div style="max-width: 750px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <div style="background: #ffcc00; padding: 30px 20px; text-align: center;">
                <h1 style="margin: 0; color: #000; font-size: 24px;">MTN 集团区域市场动态看板</h1>
                <p style="margin: 8px 0 0; color: #333; font-size: 14px;">覆盖：尼日利亚、南非、加纳、赞比亚、卢旺达等10大市场</p>
                <p style="margin: 5px 0 0; color: #666; font-size: 12px;">时间跨度：过去14天 | 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                {table_rows}
            </table>
            <div style="padding: 20px; text-align: center; font-size: 11px; color: #999; background: #fafafa;">
                抓取源：Google News 全球版 (去重汇总)<br>
                此报告由Alex Xing(820801)的agent负责每日更新一次，所有信息均基于网络公开信息
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    # 修改后的邮件标题
    msg['Subject'] = f"MTN热点新闻追踪 ({datetime.now().strftime('%m/%d')})"
    msg['From'] = f"MTN Intelligence <{sender_user}>"
    msg['To'] = receiver_user
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_user, sender_password)
            server.send_message(msg)
        print(f"✅ 报告已送达，共包含 {len(news_data)} 条动态。")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

if __name__ == "__main__":
    send_news_email()
