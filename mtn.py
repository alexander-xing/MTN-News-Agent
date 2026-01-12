import os
import smtplib
import feedparser
import urllib.parse
import google.generativeai as genai
from datetime import datetime, timedelta
from time import mktime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. 配置 Gemini AI
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
ai_model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_summarizer(title):
    """
    方案 D 核心：调用 AI 进行三句话精华总结
    """
    prompt = f"""
    你是一个资深的电信行业分析师。请针对下面这则关于 MTN 集团的新闻标题，直接给出中文分析：
    标题: "{title}"
    要求：
    1. 请给出 3 句精华总结。
    2. 第一句概括事件，第二句分析对商业的影响，第三句给出你的行业点评。
    3. 每句话尽量简练，总字数控制在 80 字以内。
    """
    try:
        response = ai_model.generate_content(prompt)
        # 将生成的文本按行或分号处理，确保展示美观
        return response.text.replace('\n', '<br>')
    except Exception as e:
        print(f"AI Summarizer Error: {e}")
        return "AI 总结暂时无法生成，请查看原文详情。"

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
        if len(items) >= 12: # 摘要版建议保留 10-12 条精华，阅读体验更好
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
        news_data = [{"title": "No major updates found in the specified period.", "url": "#", "source": "System", "date": "-"}]

    table_rows = ""
    
    print(f"ALEX AI Agent 正在分析 {len(news_data)} 条新闻...")
    
    for item in news_data:
        eng_title = item['title']
        
        # 使用方案 D：AI 自动总结
        ai_summary = get_ai_summarizer(eng_title)
            
        table_rows += f"""
        <tr>
            <td style="padding: 15px; border-bottom: 1px solid #eee; font-size: 14px; width: 45%; vertical-align: top;">
                <div style="font-weight: bold; color: #333; line-height: 1.4;">{eng_title}</div>
                <div style="font-size: 12px; color: #999; margin-top: 8px;">{item['source']} | {item['date']}</div>
            </td>
            <td style="padding: 15px; border-bottom: 1px solid #eee; font-size: 13px; color: #444; background-color: #fffdf5; line-height: 1.6;">
                <strong style="color: #d4a017;">AI 深度简评：</strong><br>
                {ai_summary}
                <div style="margin-top: 10px;">
                    <a href="{item['url']}" style="color: #0056b3; text-decoration: none; font-size: 12px;">查看原文详情 →</a>
                </div>
            </td>
        </tr>
        """

    html_content = f"""
    <html>
    <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 900px; margin: 0 auto; background: #ffffff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden;">
            <div style="background-color: #ffcc00; padding: 30px; text-align: center;">
                <h2 style="margin: 0; color: #000; font-size: 24px;">MTN AI Summarizer Report</h2>
                <p style="color: #333; font-size: 15px; margin: 8px 0 0;">由 ALEX AI Agent 自动生成的双周深度简报</p>
            </div>
            
            <div style="padding: 25px;">
                <p style="font-size: 15px; color: #555;">
                    您好，<br><br>
                    以下是 AI 为您从全球渠道提取并分析的 <b>MTN 集团</b> 关键动态。AI 已将长篇资讯浓缩为核心精华：
                </p>

                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <tr style="background-color: #333; color: #fff; font-size: 14px;">
                        <th style="padding: 12px; text-align: left;">新闻原标题</th>
                        <th style="padding: 12px; text-align: left;">AI 三句话分析</th>
                    </tr>
                    {table_rows}
                </table>
            </div>

            <div style="margin-top: 20px; padding: 20px; background-color: #fafafa; border-top: 1px solid #eee; font-size: 12px; color: #999; text-align: center;">
                <b>自动化分析引擎：</b> Gemini 1.5 Flash Model<br>
                <b>覆盖市场：</b> SA, Nigeria, Ghana, Uganda, Cameroon, Ivory Coast.<br>
                生成日期：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['Subject'] = f"MTN Intelligence: AI-Powered Summaries - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = f"XING Yinnghua's AI Agent's Reports <{sender_user}>"
    msg['To'] = receiver_user
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_user, sender_password)
            server.send_message(msg)
        print("✅ AI Summarizer Report sent successfully.")
    except Exception as e:
        print(f"❌ Error occurred: {e}")

if __name__ == "__main__":
    send_news_email()
