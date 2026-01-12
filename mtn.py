import os
import smtplib
import feedparser
import urllib.parse
from google import genai
from datetime import datetime, timedelta
from time import mktime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator

# --- 配置 Gemini SDK ---
api_key = os.environ.get('GEMINI_API_KEY')
client = None

if api_key:
    try:
        # 2026 生产级标准：强制锁定 v1 稳定版接口
        client = genai.Client(
            api_key=api_key,
            http_options={'api_version': 'v1'}
        )
        print("✅ Gemini SDK 已成功初始化 (v1 稳定版)")
    except Exception as e:
        print(f"❌ Gemini 初始化失败: {e}")

def get_ai_summarizer(title):
    """调用 Gemini 生成三句话总结"""
    if not client:
        return None
        
    prompt = f"你是一个资深电信分析师。请针对新闻标题 '{title}'，给出3句中文精华总结：1.事件概括 2.商业影响 3.行业点评。总字数80字内。"
    try:
        # 【重要修正】：添加 'models/' 前缀，这是彻底消除 404 的最后一步
        response = client.models.generate_content(
            model="models/gemini-1.5-flash", 
            contents=prompt
        )
        if response and response.text:
            return response.text.strip().replace('\n', '<br>')
        return None
    except Exception as e:
        # 增加具体错误捕获，方便最后一次排查
        print(f"⚠️ AI 总结不可用: {e}")
        return None

def fetch_from_google(query):
    """从 Google News 获取最近 14 天的新闻"""
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
    """执行搜索、总结并发送邮件"""
    sender_user = os.environ.get('EMAIL_ADDRESS')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_user = os.environ.get('RECEIVER_EMAIL')

    # 定义搜索关键词
    subsidaries = ['MTN Group', '"MTN South Africa"', '"MTN Nigeria"', '"MTN Ghana"', '"MTN Uganda"', '"MTN Cameroon"', '"MTN Ivory Coast"']
    query_str = "(" + " OR ".join(subsidaries) + ") when:14d"
    news_data = fetch_from_google(query_str)
    
    if not news_data:
        print("未搜到新闻。")
        return

    translator = GoogleTranslator(source='en', target='zh-CN')
    table_rows = ""
    print(f"正在处理 {len(news_data)} 条新闻...")
    
    for item in news_data:
        eng_title = item['title']
        ai_summary = get_ai_summarizer(eng_title)
        
        try:
            chi_title = translator.translate(eng_title)
        except:
            chi_title = "（翻译暂不可用）"

        # 展示逻辑
        if ai_summary:
            display_content = f"<div style='color: #d4a017; font-weight: bold; margin-bottom: 5px;'>AI 深度分析：</div>{ai_summary}"
        else:
            display_content = f"<div style='color: #666; font-style: italic;'>AI 分析暂不可用，中文标题如下：</div><strong>{chi_title}</strong>"
            
        table_rows += f"""
        <tr>
            <td style="padding: 15px; border-bottom: 1px solid #eee; font-size: 14px; width: 45%; vertical-align: top;">
                <div style="color: #333; font-weight: bold;">{eng_title}</div>
                <div style="font-size: 11px; color: #999; margin-top: 8px;">{item['source']} | {item['date']}</div>
            </td>
            <td style="padding: 15px; border-bottom: 1px solid #eee; font-size: 13px; color: #444; background-color: #fffdf5; line-height: 1.6;">
                {display_content}
                <div style="margin-top: 10px;"><a href="{item['url']}" style="color: #0056b3; text-decoration: none; font-size: 12px; font-weight: bold;">阅读全文 →</a></div>
            </td>
        </tr>
        """

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 900px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <div style="background-color: #ffcc00; padding: 30px; text-align: center;">
                <h1 style="margin: 0; font-size: 26px;">MTN AI Intelligence Report</h1>
                <p style="margin: 5px 0 0;">ALEX AI Agent 2.0 (Modernized)</p>
            </div>
            <div style="padding: 25px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #222; color: #fff;">
                        <th style="padding: 12px; text-align: left;">Original News</th>
                        <th style="padding: 12px; text-align: left;">AI Summary & Insights</th>
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
        print("✅ 报告已成功投递到您的邮箱。")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    send_news_email()
