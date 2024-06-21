# 使用 Python 3.9-slim 作為基礎映像
FROM python:3.9-slim

# 設定工作目錄為 /app
WORKDIR /app

# 將 requirements.txt 複製到工作目錄
COPY requirements.txt .

# 安裝依賴套件，使用 --no-cache-dir 避免使用快取
RUN pip install --no-cache-dir -r requirements.txt

# 將所有檔案複製到工作目錄
COPY . .

# 執行 Flask 應用程式，設定監聽所有介面 (0.0.0.0) 和端口 8080
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]

