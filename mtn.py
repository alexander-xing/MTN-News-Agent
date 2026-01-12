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

# --- 配置 Gemini ---
api_key = os.environ.get('GEMINI_API_KEY')
if api_key:
    try:
        genai.configure(api_key=api_key)
        # 修复 404 问题的关键：使用更通用的模型名称字符串
        ai_model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Gemini 初始化失败: {e}")
        ai_model = None
else:
    ai_model = None

def get_ai_summarizer(title):
    """尝试使用 Gemini 总结，失败则返回 None"""
    if not ai_model:
        return None
        
    prompt = f"针对新闻标题 '{title}'，给出3句中文精华总结：1.事件概括 2.商业影响 3.行业点评。每句一行，总字数80字内。"
    try:
        # 增加安全设置和简单的生成尝试
        response = ai_model.generate_content(prompt)
        # 确保返回的是文本且不为空
        if response and response.text:
            return response.text.strip().replace('\n', '<br>')
        return None
    except Exception as e:
        # 这里会捕获 404 或其他 API 错误
        print(f"AI 总结不可用 (API 错误): {e}")
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

    # 搜索关键词（包含你之前要求的所有子网）
    subsidaries = ['MTN Group', '"MTN South Africa"', '"MTN Nigeria"', '"MTN Ghana"', '"MTN Uganda"', '"MTN Cameroon"', '"MTN Ivory Coast"']
    query_str = "(" + " OR ".join(subsidaries) + ") when:14d"
    news_data = fetch_from_google(query_str)
    
    if not news_data:
        print("未搜到相关新闻。")
        return

    translator = GoogleTranslator(source='en', target='zh-CN')
    table_rows = ""
    
    print(f"正在处理 {len(news_data)} 条新闻...")
    
    for item in news_data:
        eng_title = item['title']
        
        # 1. 尝试 AI 总结
        ai_summary = get_ai_summarizer(eng_title)
        
        # 2. 无论 AI 是否成功，都准备一份标题翻译作为“定海神针”
        try:
            chi_title = translator.translate(eng_title)
        except:
            chi_title = "（翻译暂不可用）"

        # 3. 构造展示内容：有 AI 用 AI，没 AI 用翻译
        if ai_summary:
            display_content = f"<div style='color: #d4a017; font-weight: bold; margin-bottom: 5px;'>AI 深度分析：</div>{ai_summary}"
        else:
            display_content = f"<div style='color: #666; font-style: italic;'>AI 分析暂不可用，中文译文如下：</div><strong>{chi_title}</strong>"
            
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
    <body style="font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background-color: #f4f4f4; color: #333;">
        <div style="max-width: 900px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <div style="background-color: #ffcc00; padding: 30px; text-align: center;">
                <h1 style="margin: 0; font-size: 26px; color: #000;">MTN AI Intelligence Report</h1>
                <p style="margin: 5px 0 0; font-size: 16px;">ALEX AI Agent 商业决策参考</p>
            </div>
            <div style="padding: 25px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #222; color: #fff; font-size: 14px;">
                        <th style="padding: 12px; text-align: left;">原始资讯 (Original)</th>
                        <th style="padding: 12px; text-align: left;">AI 简评与导读 (Insights)</th>
                    </tr>
                    {table_rows}
                </table>
            </div>
            <div style="background-color: #fafafa; padding: 20px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #eee;">
                由 ALEX AI Agent 驱动 | 数据来源：Google News RSS<br>
                生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['Subject'] = f"MTN Intelligence: AI Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = f"ALEX AI Agent <{sender_user}>"
    msg['To'] = receiver_user
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_user, sender_password)
            server.send_message(msg)
        print("✅ 报告已送达收件箱。")
    except Exception as e:
        print(f"❌ 邮件投递失败: {e}")

if __name__ == "__main__":
    send_news_email()
