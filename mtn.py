import os
import smtplib
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from time import mktime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator

def fetch_from_google(query):
    """通用的 RSS 抓取逻辑"""
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    feed = feedparser.parse(rss_url)
    items = []
    two_weeks_ago = datetime.now() - timedelta(days=14)

    for entry in feed.entries:
        if not hasattr(entry, 'published_parsed'): 
            continue
        published_time = datetime.fromtimestamp(mktime(entry.published_parsed))
        
        if published_time > two_weeks_ago:
            items.append({
                "title": entry.title,
                "url": entry.link,
                "source": entry.source.get('title', 'International Media'),
                "date": published_time.strftime('%Y-%m-%d')
            })
        if len(items) >= 15: 
            break
    return items

def get_mtn_intelligence():
    """获取 MTN 动态，具备双重搜索保底机制"""
    subsidaries = [
        'MTN Group', '"MTN South Africa"', '"MTN Nigeria"', 
        '"MTN Ghana"', '"MTN Uganda"', '"MTN Cameroon"', '"MTN Ivory Coast"'
    ]
    query_str = "(" + " OR ".join(subsidaries) + ") when:14d"
    
    news_items = fetch_from_google(query_str)
    
    if not news_items:
        fallback_query = "MTN Global Telecom when:14d"
        news_items = fetch_from_google(fallback_query)
        
    return news_items

def send_news_email():
    sender_user = os.environ.get('EMAIL_ADDRESS')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_user = os.environ.get('RECEIVER_EMAIL')

    news_data = get_mtn_intelligence()
    
    if not news_data:
        # 如果依然没新闻，发送一份简单的系统状态报告，避免邮件内容过空
        news_data = [{"title": "No major updates found in the specified period.", "url": "#", "source": "System", "date": "-"}]

    translator = GoogleTranslator(source='en', target='zh-CN')
    table_rows = ""
    
    for item in news_data:
        eng_title = item['title']
        try:
            # 翻译逻辑
            chi_title = translator.translate(eng_title)
        except:
            chi_title = "Translation temporary unavailable."
            
        table_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #eee; font-size: 14px; width: 50%;">
                <div style="font-weight: bold; color: #333;">{eng_title}</div>
                <div style="font-size: 12px; color: #999; margin-top: 4px;">{item['source']} | {item['date']}</div>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; font-size: 14px; color: #666;">
                {chi_title}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">
                <a href="{item['url']}" style="color: #0056b3; text-decoration: none; font-size: 13px;">View Details →</a>
            </td>
        </tr>
        """

    # 邮件 HTML 结构优化：减少花哨颜色，增加正文描述
    html_content = f"""
    <html>
    <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; line-height: 1.6; margin: 0; padding: 20px;">
        <div style="max-width: 800px; margin: 0 auto; background: #ffffff;">
            <div style="padding-bottom: 20px; border-bottom: 2px solid #333;">
                <h2 style="margin: 0; color: #000;">MTN Market Update</h2>
                <p style="color: #666; font-size: 14px; margin: 5px 0 0;">Prepared by ALEX AI Intelligence Service</p>
            </div>
            
            <p style="font-size: 14px; color: #444; margin-top: 20px;">
                Hello, <br><br>
                Please find the latest business updates and news summaries for MTN Group and its regional subsidiaries (Last 14 days).
            </p>

            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="text-align: left; background-color: #f9f9f9;">
                        <th style="padding: 12px; border-bottom: 1px solid #ddd;">Headline</th>
                        <th style="padding: 12px; border-bottom: 1px solid #ddd;">Summary (CN)</th>
                        <th style="padding: 12px; border-bottom: 1px solid #ddd;">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>

            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; text-align: center;">
                This is an automated professional briefing. <br>
                Markets covered: South Africa, Nigeria, Ghana, Uganda, Cameroon, Ivory Coast. <br>
                Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    
    # --- 策略：使用全英文专业标题，极大地降低被拦截概率 ---
    msg['Subject'] = f"MTN Business Update: Global Subsidiary News - {datetime.now().strftime('%Y-%m-%d')}"
    
    # --- 策略：规范发件人名称 ---
    msg['From'] = f"ALEX AI Reports <{sender_user}>"
    msg['To'] = receiver_user
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_user, sender_password)
            server.send_message(msg)
        print("✅ Report sent successfully.")
    except Exception as e:
        print(f"❌ Error occurred: {e}")

if __name__ == "__main__":
    send_news_email()
