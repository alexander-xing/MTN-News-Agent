import os
import smtplib
import feedparser
import urllib.parse
import time
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
        # 【核心修正】强制锁定 v1 版本，彻底解决 v1beta 导致的 404 错误
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1'})
        print("✅ Gemini SDK 已初始化 (强制 v1 模式)")
    except Exception as e:
        print(f"❌ SDK 初始化失败: {e}")

def get_ai_summarizer(title):
    if not client: return None
    
    prompt = f"针对电信新闻标题 '{title}'，给出3句中文总结：1.事件概括 2.商业影响 3.行业点评。总字数80字内。"
    
    # 在 v1 模式下，直接使用这两个官方 ID，不加 models/ 前缀
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro"]
    
    for model_id in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_id, 
                contents=prompt
            )
            if response and response.text:
                return response.text.strip().replace('\n', '<br>')
        except Exception as e:
            # 如果是 API Key 过期错误，直接抛出，不再尝试其他模型
            if "API key expired" in str(e):
                print(f"🛑 严重错误: API Key 已失效，请去 AI Studio 重新生成！")
                return None
            continue
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
        
        # 频率控制，防止被 Google 封锁
        time.sleep(1.5)
        
        try:
            chi_title = translator.translate(eng_title)
        except:
            chi_title = "（翻译暂不可用）"

        if ai_summary:
            display_content = f"<div style='color: #d4a017; font-weight: bold; margin-bottom: 5px;'>AI 深度分析：</div>{ai_summary}"
        else:
            display_content = f"<div style='color: #666; font-style: italic;'>AI 分析暂不可用，内容如下：</div><strong>{chi_title}</strong>"
            
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

    html_content = f"<html><body style='font-family: Arial; padding: 20px;'><div style='max-width: 800px; margin: 0 auto; border: 1px solid #ddd;'> <div style='background: #ffcc00; padding: 20px; text-align: center;'><h2>MTN Intelligence Report</h2></div> <table style='width: 100%; border-collapse: collapse;'>{table_rows}</table></div></body></html>"

    msg = MIMEMultipart()
    msg['Subject'] = f"MTN Intelligence Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = f"ALEX AI <{sender_user}>"
    msg['To'] = receiver_user
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_user, sender_password)
            server.send_message(msg)
        print("✅ 报告已送达。")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    send_news_email()
