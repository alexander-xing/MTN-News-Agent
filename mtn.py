import os
import smtplib
import feedparser
import urllib.parse  # 导入用于处理 URL 编码的库
from datetime import datetime, timedelta
from time import mktime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator

def get_mtn_intelligence():
    # 1. 构造精准搜索关键词
    query = '(MTN Group OR "MTN South Africa" OR "MTN Nigeria" OR "MTN Ghana") when:14d'
    
    # --- 关键修复：对搜索关键词进行 URL 编码 ---
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    # 打印一下链接，方便在日志里调试（可选）
    print(f"Fetching RSS from: {rss_url}")
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    # 2. 时间过滤：严格锁定在 14 天内
    two_weeks_ago = datetime.now() - timedelta(days=14)

    for entry in feed.entries:
        if not hasattr(entry, 'published_parsed'):
            continue
            
        published_time = datetime.fromtimestamp(mktime(entry.published_parsed))
        
        if published_time > two_weeks_ago:
            source = entry.source.get('title', 'Unknown')
            news_items.append({
                "title": entry.title,
                "url": entry.link,
                "source": source,
                "date": published_time.strftime('%Y-%m-%d')
            })
        
        if len(news_items) >= 15:
            break
            
    return news_items

def send_news_email():
    sender_user = os.environ.get('EMAIL_ADDRESS')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_user = os.environ.get('RECEIVER_EMAIL')

    news_data = get_mtn_intelligence()
    
    if not news_data:
        print("近期未发现关于 MTN 集团或子网的重大新闻。")
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
            chi_title = "翻译服务暂时不可用"
            
        table_rows += f"""
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd; font-size: 14px;">
                <strong>{eng_title}</strong><br>
                <span style="color: #666; font-size: 12px;">来源: {source} | 日期: {date}</span>
            </td>
            <td style="padding: 10px; border: 1px solid #ddd; font-size: 14px; color: #333;">
                {chi_title}
            </td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">
                <a href="{link}" style="display: inline-block; padding: 5px 10px; background-color: #004f9f; color: white; text-decoration: none; border-radius: 4px; font-size: 12px;">阅读原文</a>
            </td>
        </tr>
        """

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <div style="background-color: #ffcc00; padding: 20px; text-align: center;">
            <h1 style="margin: 0; color: #000;">MTN Group Intelligence</h1>
            <p style="margin: 5px 0 0; color: #000;">双周热门新闻摘要 ({datetime.now().strftime('%Y-%m-%d')})</p>
        </div>
        
        <div style="padding: 20px;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 12px; border: 1px solid #ddd; text-align: left; width: 40%;">英文详情 (Original)</th>
                        <th style="padding: 12px; border: 1px solid #ddd; text-align: left; width: 45%;">中文翻译 (Translation)</th>
                        <th style="padding: 12px; border: 1px solid #ddd; text-align: center; width: 15%;">链接</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        
        <footer style="padding: 20px; text-align: center; color: #888; font-size: 12px;">
            此报告由自动化系统生成，检索词包含：MTN Group, MTN South Africa, MTN Nigeria, MTN Ghana.<br>
            时间范围：过去 14 天。
        </footer>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['Subject'] = f"【MTN 情报】双周热门动向 - {datetime.now().strftime('%m/%d')}"
    msg['From'] = f"MTN Intelligence <{sender_user}>"
    msg['To'] = receiver_user
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_user, sender_password)
            server.send_message(msg)
        print("✅ MTN 双周情报已成功送达！")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    send_news_email()
