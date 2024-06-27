from flask import Flask, render_template, request, jsonify
import vertexai
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models
import json
import os
import sentry_sdk

# 取得Sentry DSN
SENTRY_DSN = os.environ.get('SENTRY_DSN')
# 設定 Google Cloud 專案 ID 和地區
# PROJECT_ID = "Your PROJECT ID"  # 請替換為您的專案 ID
# REGION = "Your REGION"  # 請替換為您的地區

# 初始化 Vertex AI
# vertexai.init(project=PROJECT_ID, location=REGION)

# 載入 gemini-1.5-flash 模型
model = GenerativeModel(
    "gemini-1.5-flash-001",
    system_instruction=["""你是很棒的評論家，你的服務很有幫助"""]
)

# 定義情緒標籤對應表
sentiment_labels = {
    "非常正面": "positive",
    "正面": "positive",
    "稍微正面": "slightly_positive",
    "中性": "neutral",
    "稍微負面": "slightly_negative",
    "負面": "negative",
    "非常負面": "very_negative"
}

# 定義情緒解釋
sentiment_explanations = {
    "positive": "表達了積極、樂觀、愉悅的情感。",
    "slightly_positive": "表達了輕微的積極情感。",
    "neutral": "沒有明顯的情感傾向。",
    "slightly_negative": "表達了輕微的消極情感。",
    "negative": "表達了消極、悲觀、不滿的情感。",
    "very_negative": "表達了極為強烈的消極情感。"
}

# 定義進行情緒分析和實體標註的函式
def analyze_text(text):
    # 呼叫模型進行預測，提供明確的指示
    response = model.generate_content(
        f"""分析以下文字的情緒，並標註其中的實體且自動貼標：
        "{text}"
        情緒應為以下其中之一：非常正面、正面、稍微正面、中性、稍微負面、負面、非常負面。
        實體可以是人名、地名、組織名、產品名等。
        自動貼標可以是品質、價格，服務、環境、等候或處理時間等。
        請用以下格式回答：
        情緒: <情緒>
        解釋: <情緒解釋>
        Gemini的解釋: <Gemini自己的情緒解釋>
        實體: <實體1>, <實體2>, ...
        自動貼標: <標籤1>, <標籤2>, ...
        """,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    # 解析回應
    lines = response.text.strip().split("\n")
    sentiment = lines[0].split(": ")[1]
    explanation = sentiment_explanations.get(sentiment_labels.get(sentiment, "unknown"), "無法解釋")
    gemini_explanation = lines[2].split(": ")[1] if len(lines) > 2 else "Gemini 沒有提供解釋"
    entities = [e.strip() for e in lines[3].split(": ")[1].split(",")] if len(lines) > 3 else []
    labels = [e.strip() for e in lines[4].split(": ")[1].split(",")] if len(lines) > 4 else []

    return sentiment, explanation, gemini_explanation, entities, labels, text

# 設定模型生成內容的參數
generation_config = {
    "max_output_tokens": 256,   # 設定模型生成的最大 token 數量，限制輸出長度
    "temperature": 1.0,         # 設定模型生成文字的隨機性，值越高越隨機
    "top_p": 0.95,              # 設定模型生成文字的機率分佈，值越高越傾向於高機率的詞彙
    "top_k": 5,                 # 設定模型生成文字時考慮的候選詞彙數量，值越高越傾向於罕見的詞彙
}

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,  # 阻擋中度及以上仇恨言論
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,  # 阻擋中度及以上危險內容
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,  # 阻擋中度及以上性暗示內容
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,  # 阻擋中度及以上騷擾內容
}

# 初始化 Sentry SDK，用於錯誤追蹤和效能監控
sentry_sdk.init(
    dsn=SENTRY_DSN,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

# 建立 Flask 應用程式
app = Flask(__name__)

# 首頁路由
@app.route("/")
def index():
    return render_template("index.html")

# 分析路由
@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.form["text"]
    # 檢查文字長度是否超過 500 字
    if len(text) > 500:
        return jsonify({"error": "輸入文字長度超過 500 字，請縮短文字。"}), 400

    try:
        sentiment, explanation, gemini_explanation, entities, labels, text = analyze_text(text)
    except IndexError:
        return jsonify({"error": "模型回應格式錯誤，無法解析結果。"}), 500

    result = {
        "text": text,  # 新增整理過的輸入文字值
        "sentiment": sentiment,
        "explanation": explanation,
        "gemini_explanation": gemini_explanation,
        "entities": entities,
        "labels": labels
    }

    # 將 result 用一個網頁方式呈現
    return render_template("index.html", result=result)  # 渲染 index.html 並傳遞 result

    # return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
