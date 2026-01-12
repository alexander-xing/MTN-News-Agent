import feedparser
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 配置信息（从 GitHub Secrets 安全读取）
EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
RECIPIENT = "alex.xing@huawei.com"

def get_impact_score(title):
    """影响力评分：根据关键词赋予权重"""
    score = 0
    weights = {
        "Share": 5, "Stock": 5, "Dividend": 5, "Profit": 4, # 财务
        "AI": 5, "Data Center": 5, "5G": 4, "Spectrum": 4, # 战略
        "Merger": 5, "Acquisition": 5,                    # 资本动作
        "Outage": 3, "Regulatory": 3, "Fine": 4           # 风险
    }
    for kw, val in weights.items():
        if kw.lower() in title.lower():
            score += val
    return score

def fetch_news():
    # 搜索 MTN 集团及核心子公司最近 14 天的新闻
    url = 'https://news.google.com/rss/search?q=MTN+Group+OR+MTN+Nigeria+when:14d&hl=en-US&gl=US&ceid=US:en'
    feed = feedparser.parse(url)
    
    news_list = []
    for entry in feed.entries:
        score = get_impact_score(entry.title)
        news_list.append({
            'title': entry.title,
            'link': entry.link,
            'score': score,
            'date': entry.published
        })
    
    # 按照评分从高到低排序，取前 10 条
    return sorted(news_list, key=lambda x: x['score'], reverse=True)[:10]

def send_email(items):
    if not items: return
    
    html = "<h2>MTN Group 2周热搜简报 (Impact Ranking)</h2><table border='1' style='border-collapse:collapse; width:100%'>"
    html += "<tr style='background-color:#FFCC00;'><th>影响力</th><th>新闻标题</th></tr>"
    
    for item in items:
        fire = "🔥" * max(1, min(item['score'], 5))
        html += f"<tr><td style='text-align:center'>{fire}</td><td><b>{item['title']}</b><br><a href='{item['link']}'>点击阅读</a></td></tr>"
    html += "</table><p>推送时间：周一 09:30 AM (GMT+2)</p>"

    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = EMAIL_SENDER
    msg['To'] = RECIPIENT
    msg['Subject'] = Header("【情报追踪】MTN 集团双周影响力报告", 'utf-8')

    try:
        # 这里以 Gmail 为例，如果是其他邮箱请修改 SMTP 服务器
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, [RECIPIENT], msg.as_string())
        print("邮件已成功发送！")
    except Exception as e:
        print(f"发送失败: {e}")

if __name__ == "__main__":
    news = fetch_news()
    send_email(news)
