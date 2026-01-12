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
    # 1. 构造精准搜索关键词：涵盖集团及所有指定子网
    # 关键词包括：MTN Group, 南非, 尼日利亚, 加纳, 乌干达, 喀麦隆, 科特迪瓦
    subsidaries = [
        'MTN Group', 
        '"MTN South Africa"', 
        '"MTN Nigeria"', 
        '"MTN Ghana"', 
        '"MTN Uganda"', 
        '"MTN Cameroon"', 
        '"MTN Ivory Coast"', 
        '"MTN Cote d\'Ivoire"'
    ]
    
    # 组合成 Google News 搜索指令
    query_str = "(" + " OR ".join(subsidaries) + ") when:14d"
    
    # URL 编码处理：解决 InvalidURL 错误
    encoded_query = urllib.parse.quote(query_str)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    print(f"正在检索新闻: {query_str}")
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    # 2. 时间过滤：锁定在最近 14 天
    two_weeks_ago = datetime.now() - timedelta(days=14)

    for entry in feed.entries:
        if not hasattr(entry, 'published_parsed'):
            continue
            
        published_time = datetime.fromtimestamp(mktime(entry.published_parsed))
        
        if published_time > two_weeks_ago:
            source = entry.source.get('title', 'Unknown Source')
            news_items.append({
                "title": entry.title,
                "url": entry.link,
                "source": source,
                "date": published_time.strftime('%Y-%m-%d')
            })
        
        # 限制数量：获取 Top 20 条
        if len(news_items) >= 20:
            break
            
    return news_items

def send_news_email():
    sender_user = os.environ.get('EMAIL_ADDRESS')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_user = os.environ.get('RECEIVER_EMAIL')

    news_data = get_mtn_intelligence()
    
    if not news_data:
        print("未发现匹配的新闻动态。")
        return

    translator = GoogleTranslator(source='en', target='zh-CN')
    table_rows = ""
    
    for item in news_data:
        eng_title = item['title']
        link = item['url']
        source = item['source']
        date = item['date']
        
        try:
            chi_title = translator.translate(eng_title)
        except:
            chi_title = "翻译暂不可用"
            
        table_rows += f"""
        <tr>
            <td style="padding: 12px; border: 1px solid #ddd; font-size: 14px;">
                <strong>{eng_title}</strong><br>
                <span style="color: #666; font-size: 11px; background: #f0f0f0; padding: 2px 5px; border-radius: 3px;">
                    {source} | {date}
                </span>
            </td>
            <td style="padding: 12px; border: 1px solid #ddd; font-size: 14px; color: #333; line-height: 1.5;">
                {chi_title}
            </td>
            <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">
                <a href="{link}" style="display: inline-block; padding: 6px 12px; background-color: #ffcc00; color: #000; text-decoration: none; border-radius: 20px; font-weight: bold; font-size: 12px;">查看原文</a>
            </td>
        </tr>
        """

    html_content = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 900px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="background-color: #ffcc00; padding: 30px; text-align: center;">
                <h1 style="margin: 0; color: #000; font-size: 28px;">MTN Intelligence Report</h1>
                <p style="margin: 10px 0 0; color: #333; font-size: 16px;">集团及全球子网双周热点追踪</p>
            </div>
            
            <div style="padding: 20px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #000; color: #fff;">
                            <th style="padding: 15px; text-align: left;">原文摘要 (Original News)</th>
                            <th style="padding: 15px; text-align: left;">中文导读 (Chinese Intro)</th>
                            <th style="padding: 15px; text-align: center;">操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            
            <div style="background-color: #f9f9f9; padding: 20px; text-align: center; color: #777; font-size: 12px; border-top: 1px solid #eee;">
                此自动化报告由 ALEX AI Agent 生成<br>
                涵盖：Group, SA, Nigeria, Ghana, Uganda, Cameroon, Ivory Coast.<br>
                生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['Subject'] = f"【MTN 集团资讯】多国子网动态汇报 - {datetime.now().strftime('%Y年%m月%d日')}"
    
    # --- 关键修改：更新显示名称为 ALEX AI Agent ---
    msg['From'] = f"ALEX AI Agent - MTN Intelligence <{sender_user}>"
    
    msg['To'] = receiver_user
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_user, sender_password)
            server.send_message(msg)
        print("✅ 邮件已以 'Alex Xing 英华的AI Agent' 身份成功送达！")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    send_news_email()
