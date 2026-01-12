import feedparser
import datetime
import smtplib
import os
import pytz
from email.mime.text import MIMEText
from email.header import Header

# --- 核心配置（从 GitHub Secrets 读取） ---
EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
EMAIL_RECEIVER = "alex.xing@huawei.com"

def get_impact_score(title):
    """简单的影响力评分算法"""
    score = 0
    keywords = {
        "Share": 5, "Stock": 5, "Profit": 4, "Revenue": 4,  # 财务类
        "AI": 5, "Data Center": 5, "5G": 4, "Spectrum": 4, # 战略类
        "Outage": 3, "Network": 2, "Customer": 2           # 运营类
    }
    for kw, val in keywords.items():
        if kw.lower() in title.lower():
            score += val
    return score

def fetch_mtn_news():
    # Google News RSS (MTN Group)
    url = 'https://news.google.com/rss/search?q=MTN+Group+OR+MTN+Nigeria+when:14d&hl=en-US&gl=US&ceid=US:en'
    feed = feedparser.parse(url)
    
    news_items = []
    for entry in feed.entries:
        score = get_impact_score(entry.title)
        news_items.append({
            'title': entry.title,
            'link': entry.link,
            'score': score,
            'date': entry.published
        })
    
    # 按影响力分数排序
    return sorted(news_items, key=lambda x: x['score'], reverse=True)[:10]

def send_email(items):
    if not items: return
    
    # 构造 HTML 内容
    rows = ""
    for item in items:
        fire = "🔥" * min(item['score'], 5)
        rows += f"<tr><td>{fire}</td><td><b>{item['title']}</b><br><a href='{item['link']}'>Read More</a></td></tr>"

    html = f"""
    <html><body>
        <h2>MTN Group 双周情报简报 (南非时间 08:30 推送)</h2>
        <table border='1' cellpadding='10' style='border-collapse: collapse;'>
            <tr style='background-color: #FFCC00;'><th>影响力</th><th>情报摘要</th></tr>
            {rows}
        </table>
    </body></html>
    """

    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = Header("【MTN Intelligence】Weekly Briefing", 'utf-8')

    # 使用 SSL 发送 (以 Gmail 为例)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())

if __name__ == "__main__":
    print("Agent 正在抓取 MTN 最新情报...")
    news = fetch_mtn_news()
    send_email(news)
    print("任务完成！")
