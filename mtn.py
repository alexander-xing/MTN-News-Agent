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
            if count >= 8: break 
        
        print(f" - {country}: 找到 {count} 条相关动态")
        time.sleep(1) 

    all_items.sort(key=lambda x: x['timestamp'], reverse=True)
    return all_items

def send_news_email():
    sender_user = os.environ.get('EMAIL_ADDRESS')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_user = os.environ.get('RECEIVER_EMAIL')
    
    # 设定跨度为 14 天
    fetch_days = 14
    news_data = fetch_all_mtn_news(days=fetch_days)
    
    if not news_data:
        print(f"过去 {fetch_days} 天未搜到任何MTN相关新闻。")
        return

    translator = GoogleTranslator(source='en', target='zh-CN')
    table_rows = ""
    print(f"开始翻译并生成报告，共 {len(news_data)} 条...")
    
    for item in news_data:
        try:
            chi_title = translator.translate(item['title'])
        except:
            chi_title = item['title']
            
        # 核心优化：构建带有实线边框和层级感的表格行
        table_rows += f"""
        <tr>
            <td style="padding: 12px; border: 1px solid #cbd5e0; text-align: center; background-color: #f7fafc; width: 90px; font-size: 12px; color: #4a5568; font-weight: bold;">
                {item['date']}
            </td>
            <td style="padding: 15px; border: 1px solid #cbd5e0; background-color: #ffffff;">
                <div style="font-size: 15px; font-weight: bold; color: #1a202c; margin-bottom: 5px; line-height: 1.4;">{chi_title}</div>
                <div style="font-size: 12px; color: #718096; font-style: italic; margin-bottom: 10px; line-height: 1.2;">{item['title']}</div>
                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                    <tr>
                        <td>
                            <span style="display: inline-block; background:#fff7e6; color:#b48900; padding:2px 8px; border: 1px solid #ffe58f; border-radius:4px; font-size:11px; font-weight:bold;">{item['source']}</span>
                        </td>
                        <td style="text-align: right;">
                            <a href="{item['url']}" style="color:#3182ce; text-decoration:none; font-size: 12px; font-weight: bold;">阅读详情 →</a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        """

    # 核心优化：高级感 HTML 模版，明确 14 天标注
    html_content = f"""
    <html>
    <body style="font-family: 'PingFang SC', 'Microsoft YaHei', Helvetica, Arial, sans-serif; background-color: #edf2f7; padding: 20px; margin: 0;">
        <div style="max-width: 800px; margin: 0 auto; background: #fff; border: 1px solid #a0aec0; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            
            <div style="background: #ffcc00; padding: 30px 25px; text-align: center; border-bottom: 5px solid #000;">
                <h1 style="margin: 0; color: #000; font-size: 22px; font-weight: 900; letter-spacing: 0.5px;">Ying大人的"垂直教育情报每日滚动刷新"</h1>
                <p style="margin: 10px 0 0; color: #000; font-size: 16px; font-weight: bold;">MTN 集团区域市场深度精华版</p>
                <div style="margin-top: 15px; display: inline-block; background: #000; color: #ffcc00; padding: 6px 18px; border-radius: 4px; font-size: 13px; font-weight: bold;">
                    📅 抓取范围：过去 {fetch_days} 天新闻情报 | 🕒 更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}
                </div>
            </div>

            <div style="padding: 20px;">
                <table style="width: 100%; border-collapse: collapse; border: 2px solid #2d3748;">
                    <thead>
                        <tr style="background-color: #2d3748;">
                            <th style="padding: 12px; border: 1px solid #2d3748; color: #fff; font-size: 14px; width: 90px;">日期</th>
                            <th style="padding: 12px; border: 1px solid #2d3748; color: #fff; font-size: 14px; text-align: left;">情报摘要 (过去14天动态滚动)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>

            <div style="padding: 25px; text-align: center; font-size: 12px; color: #718096; background: #f7fafc; border-top: 1px solid #e2e8f0;">
                🛡️ 本报告由 <strong>Alex Xing(820801)</strong> 的私人 Agent 负责每日更新<br>
                数据源：Google News 全球版 (去重汇总) | <strong>时间跨度：14天</strong><br>
                <p style="margin-top: 10px; color: #a0aec0; font-size: 10px;">© 2026 MTN Intelligence News Tracker</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    # 设置邮件标题
    msg['Subject'] = f"Ying大人的\"垂直教育情报每日滚动刷新\"：14天全球深度精华版"
    msg['From'] = f"MTN Intelligence Agent <{sender_user}>"
    msg['To'] = receiver_user
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_user, sender_password)
            server.send_message(msg)
        print(f"✅ 报告已送达，包含过去14天共 {len(news_data)} 条动态。")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

if __name__ == "__main__":
    send_news_email()
