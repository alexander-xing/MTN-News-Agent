import os
import smtplib
import feedparser
import urllib.parse
import google.generativeai as genai
from datetime import datetime, timedelta
from time import mktime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator

# 配置 Gemini
api_key = os.environ.get('GEMINI_API_KEY')
if api_key:
    genai.configure(api_key=api_key)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

def get_ai_summarizer(title):
    """尝试使用 Gemini 总结，失败则返回 None"""
    if not ai_model:
        return None
        
    prompt = f"针对新闻标题 '{title}'，给出3句中文精华总结：1.事件概括 2.商业影响 3.行业点评。总字数80字内。"
    try:
        response = ai_model.generate_content(prompt)
        return response.text.replace('\n', ' ')
    except Exception as e:
        print(f"AI 总结不可用: {e}")
        return None

def fetch_from_google(query):
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
                "source": entry.source.get('title', 'Media'),
                "date": published_time.strftime('%Y-%m-%d')
            })
        if len(items) >= 12: break
    return items

def send_news_email():
    sender_user = os.environ.get('EMAIL_ADDRESS')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_user = os.environ.get('RECEIVER_EMAIL')

    # 获取搜索词（保持你之前的多子网配置）
    subsidaries = ['MTN Group', '"MTN South Africa"', '"MTN Nigeria"', '"MTN Ghana"', '"MTN Uganda"']
    query_str = "(" + " OR ".join(subsidaries) + ") when:14d"
    news_data = fetch_from_google(query_str)
    
    if not news_data:
        print("未搜到新闻")
        return

    translator = GoogleTranslator(source='en', target='zh-CN')
    table_rows = ""
    
    for item in news_data:
        eng_title = item['title']
        
        # 1. 首先尝试获取 AI 总结
        ai_summary = get_ai_summarizer(eng_title)
        
        # 2. 获取中文翻译标题（保底显示）
        try:
            chi_title = translator.translate(eng_title)
        except:
            chi_title = "翻译暂不可用"

        # 3. 如果 AI 总结失败，显示翻译后的标题作为补充
        display_summary = ai_summary if ai_summary else f"【自动翻译】{chi_title}"
            
        table_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #eee; font-size: 14px; width: 40%; vertical-align: top;">
                <strong>{eng_title}</strong><br>
                <span style="font-size: 11px; color: #999;">{item['source']} | {item['date']}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; font-size: 13px; color: #444; background-color: #fffdf5;">
                {display_summary}
                <div style="margin-top: 8px;"><a href="{item['url']}" style="color: #0056b3; text-decoration: none; font-size: 12px;">查看原文 →</a></div>
            </td>
        </tr>
        """

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 900px; margin: 0 auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="background-color: #ffcc00; padding: 20px; text-align: center;">
                <h2 style="margin: 0;">MTN Intelligence AI Agent</h2>
            </div>
            <div style="padding: 20px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #333; color: #fff;">
                        <th style="padding: 10px; text-align: left;">Original News</th>
                        <th style="padding: 10px; text-align: left;">AI Summary / Translation</th>
                    </tr>
                    {table_rows}
                </table>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['Subject'] = f"MTN Intelligence Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = f"ALEX AI Reports <{sender_user}>"
    msg['To'] = receiver_user
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_user, sender_password)
            server.send_message(msg)
        print("✅ 邮件已成功发送。")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    send_news_email()
