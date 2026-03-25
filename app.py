from flask import Flask, render_template, request, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import vertexai
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models
import json
import os
import sentry_sdk

# 取得Sentry DSN
SENTRY_DSN = os.environ.get('SENTRY_DSN')
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

# 設定 Google Cloud 專案 ID 和地區
PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION", "us-central1")
# Gemini 2.5 is not available in all regions (e.g. asia-east1).
# Use MODEL_REGION to specify where the model runs (e.g. asia-northeast1).
MODEL_REGION = os.environ.get("MODEL_REGION", "asia-northeast1")

MAX_TEXT_LENGTH = 1000

# 初始化 Vertex AI
if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=MODEL_REGION)

# 載入 gemini-2.5-flash-lite 模型
model = GenerativeModel(
    "gemini-2.5-flash-lite",
    system_instruction=["""你是很棒的評論家，你的服務很有幫助。

分析使用者提供的文字情緒，並標註其中的實體且自動貼標。
情緒應為以下其中之一：非常正面、正面、稍微正面、中性、稍微負面、負面、非常負面。
實體可以是人名、地名、組織名、產品名等。
自動貼標可以是牛肉麵品質(正面)、炒飯品質(負面)、服務(正面)、環境(中性)、等候或處理時間(負面)、價格（正面）等。
請用 JSON 格式回答，包含以下欄位：
- sentiment: 情緒
- gemini_explanation: Gemini自己的情緒解釋
- entities: 實體列表
- labels: 自動貼標列表"""]
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
    # 呼叫模型進行預測，利用明確邊界包圍使用者輸入以減緩 Prompt Injection 風險
    safe_text = f"請分析以下被 <<< 以及 >>> 包圍的使用者文字內容：\n<<<\n{text}\n>>>"
    
    response = model.generate_content(
        safe_text,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    # 解析回應
    try:
        result_json = json.loads(response.text)
        sentiment = result_json.get("sentiment", "中性")
        gemini_explanation = result_json.get("gemini_explanation", "Gemini 沒有提供解釋")
        entities = result_json.get("entities", [])
        labels = result_json.get("labels", [])
        
        # 根據 sentiment 取得 explanation
        explanation = sentiment_explanations.get(sentiment_labels.get(sentiment, "unknown"), "無法解釋")

        return sentiment, explanation, gemini_explanation, entities, labels, text
    except json.JSONDecodeError as exc:
        # 如果 JSON 解析失敗，回傳預設值或拋出錯誤
        raise ValueError("Model response is not valid JSON") from exc


# 設定模型生成內容的參數
generation_config = {
    "max_output_tokens": 1024,   # 增加 token 數量以容納 JSON
    "temperature": 1.0, 
    "top_p": 0.95,
    "top_k": 5,
    "response_mime_type": "application/json", # 強制 JSON 輸出
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
    # 動態調整正式環境的追蹤頻率避免產生過高成本及敏感資料外洩
    traces_sample_rate=1.0 if FLASK_ENV == 'development' else 0.1,
    profiles_sample_rate=1.0 if FLASK_ENV == 'development' else 0.1,
)

# 建立 Flask 應用程式
app = Flask(__name__)

# 安全性設定：CSRF 與頻率限制 (Limiter)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-secret-key-change-in-prod')
csrf = CSRFProtect(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# 首頁路由
@app.route("/")
def index():
    return render_template("index.html")

# 分析路由
@app.route("/analyze", methods=["POST"])
@limiter.limit("5 per minute")
def analyze():
    text = request.form.get("text", "")
    # 檢查文字長度是否超過 MAX_TEXT_LENGTH 字
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({"error": f"輸入文字長度超過 {MAX_TEXT_LENGTH} 字，請縮短文字。"}), 400

    try:
        sentiment, explanation, gemini_explanation, entities, labels, text = analyze_text(text)
    except ValueError:
        return jsonify({"error": "模型回應格式錯誤，無法解析結果。"}), 500
    except Exception as e:
        return jsonify({"error": "伺服器發生未預期的錯誤，請稍後再試。"}), 500

    result = {
        "text": text,  # 新增整理過的輸入文字值
        "sentiment": sentiment,
        "explanation": explanation,
        "gemini_explanation": gemini_explanation,
        "entities": entities,
        "labels": labels
    }

    # 支援 AJAX 或 Fetch API 的 JSON 回傳
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.accept_mimetypes:
        return jsonify(result)

    # 將 result 用一個網頁方式呈現 (Traditional fallback)
    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
