# LangExtract 使用說明

**版本**：v1.0.9  
**最後更新**：2025年11月
**專案網頁**：<https://github.com/google/langextract>  
**參考網頁**：<https://deepwiki.com/google/langextract>

---

## 1. 簡介

### 專案功能與架構

LangExtract 是一個 Python 函式庫，使用大型語言模型（LLM）從非結構化文字中提取結構化資訊。其核心特色包括：

- **精確來源標註**：每筆提取結果皆標註在原文中的精確位置（字元級別）
- **長文本處理**：內建分塊、平行處理與多輪提取機制，可處理數萬字以上的長文件
- **多 LLM 支援**：支援 Google Gemini、OpenAI、Azure OpenAI、Ollama 等多種 LLM 供應商
- **互動式視覺化**：可生成 HTML 視覺化報告，方便檢視與驗證提取結果

### 系統架構

```
使用者程式碼
    ↓
langextract.extract()
    ↓
Factory (模型工廠) → 選擇並初始化 LLM Provider
    ↓
Annotator (標註器) → 文本分塊 → 平行推論 → 結果解析與對齊
    ↓
AnnotatedDocument (輸出)
```

### 目標讀者

本文件針對負責部署與維護 LangExtract 的技術人員，包括：
- DevOps 工程師
- Python 開發人員
- 系統管理員

---

## 2. 環境變數詳解 (Environment Variables)

LangExtract 支援透過環境變數配置 API 金鑰與連線設定。以下表格列出所有支援的環境變數：

| 變數名稱 | 預設值 | 必填 | 說明 |
|---------|--------|------|------|
| `LANGEXTRACT_API_KEY` | - | 否 | 通用 API 金鑰，可作為 Gemini 或 OpenAI 的備用金鑰 |
| `GEMINI_API_KEY` | - | 是* | Google Gemini API 金鑰（使用 Gemini 模型時必填） |
| `OPENAI_API_KEY` | - | 是* | OpenAI API 金鑰（使用 OpenAI 模型時必填） |
| `AZURE_OPENAI_API_KEY` | - | 是* | Azure OpenAI 服務的 API 金鑰（使用 Azure OpenAI 時必填） |
| `AZURE_OPENAI_ENDPOINT` | - | 是* | Azure OpenAI 服務端點 URL（使用 Azure OpenAI 時必填）<br>格式：`https://your-resource.openai.azure.com` |
| `AZURE_OPENAI_API_VERSION` | `2024-02-15-preview` | 否 | Azure OpenAI API 版本 |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4o-mini` | 否 | Azure OpenAI 部署名稱 |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | 否 | Ollama 服務的基礎 URL（使用 Ollama 模型時） |
| `OLLAMA_HOST` | `http://localhost:11434` | 否 | Ollama 服務主機（與 `OLLAMA_BASE_URL` 同義） |
| `LANGEXTRACT_DISABLE_PLUGINS` | - | 否 | 設為 `1` 或 `true` 可停用外掛系統 |

**註**：標記為「是*」的變數在使用對應的 LLM 供應商時為必填，否則可選。

### Azure OpenAI 環境變數詳細說明

使用 Azure OpenAI 服務時，需要設定以下環境變數：

```bash
# Azure OpenAI 必填變數
export AZURE_OPENAI_API_KEY="your-azure-openai-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"

# Azure OpenAI 選填變數（有預設值）
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"  # 預設值
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini"     # 預設值
```

**重要提示**：
- `AZURE_OPENAI_ENDPOINT` 必須包含完整的 URL，格式為 `https://<resource-name>.openai.azure.com`
- `AZURE_OPENAI_API_VERSION` 建議使用最新穩定版本，預設為 `2024-02-15-preview`
- `AZURE_OPENAI_DEPLOYMENT_NAME` 必須與您在 Azure 入口網站中建立的部署名稱一致

### 環境變數載入順序

LangExtract 會依以下順序尋找 API 金鑰：

1. **函式參數**：直接在 `lx.extract()` 中傳入 `api_key`
2. **環境變數（供應商特定）**：
   - Gemini：`GEMINI_API_KEY` → `LANGEXTRACT_API_KEY`
   - OpenAI：`OPENAI_API_KEY` → `LANGEXTRACT_API_KEY`
3. **.env 檔案**：若使用 `python-dotenv`，會自動載入 `.env` 檔案中的變數

### .env 檔案範例

建立 `.env` 檔案（建議加入 `.gitignore`）：

```bash
# Gemini API 金鑰
GEMINI_API_KEY=your-gemini-api-key-here

# OpenAI API 金鑰
OPENAI_API_KEY=your-openai-api-key-here

# Azure OpenAI 設定
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Ollama 設定（本地部署）
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 3. 安裝與部署 (Installation & Deployment)

### 3.1 套件安裝

#### 從 PyPI 安裝（推薦）

```bash
# 基本安裝
pip install langextract

# 使用虛擬環境（推薦）
python -m venv langextract_env
source langextract_env/bin/activate  # Windows: langextract_env\Scripts\activate
pip install langextract
```

#### 安裝可選依賴

```bash
# 安裝 OpenAI 支援（使用 OpenAI 或 Azure OpenAI 時需要）
pip install langextract[openai]

# 安裝開發工具
pip install langextract[dev]

# 安裝測試工具
pip install langextract[test]

# 安裝所有可選依賴
pip install langextract[all]
```

#### 從原始碼安裝

```bash
# 克隆儲存庫
git clone https://github.com/google/langextract.git
cd langextract

# 開發模式安裝（可修改程式碼）
pip install -e .

# 包含開發工具
pip install -e ".[dev]"

# 包含測試工具
pip install -e ".[test]"
```

### 3.2 Docker 容器化部署

#### 使用官方 Dockerfile

專案根目錄提供 `Dockerfile`，可用於建立容器映像：

```bash
# 建立映像
docker build -t langextract:latest .

# 執行容器（需設定環境變數）
docker run --rm \
  -e GEMINI_API_KEY="your-api-key" \
  -v $(pwd):/app \
  langextract:latest \
  python your_script.py
```

#### 使用 docker-compose（Ollama 範例）

專案提供 `examples/ollama/docker-compose.yml` 範例，展示如何整合 Ollama：

```yaml
services:
  ollama:
    image: ollama/ollama:0.5.4
    ports:
      - "127.0.0.1:11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    command: serve

  langextract:
    build: .
    depends_on:
      ollama:
        condition: service_healthy
    environment:
      - OLLAMA_HOST=http://ollama:11434
    volumes:
      - .:/app
    command: python demo_ollama.py
```

執行方式：

```bash
cd examples/ollama
docker-compose up
```

### 3.3 Kubernetes Helm 部署

> **註**：專案目前未提供現成的 Helm Chart，以下為根據 `Dockerfile` 與 `docker-compose.yml` 反推的部署指引。

#### 建立 Helm Chart 結構

```bash
mkdir -p helm/langextract
cd helm/langextract
```

#### values.yaml 範例

```yaml
replicaCount: 2

image:
  repository: langextract
  tag: "1.0.9"
  pullPolicy: IfNotPresent

service:
  type: NodePort
  port: 8000

env:
  - name: GEMINI_API_KEY
    valueFrom:
      secretKeyRef:
        name: langextract-secrets
        key: gemini-api-key
  - name: AZURE_OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: langextract-secrets
        key: azure-openai-api-key
  - name: AZURE_OPENAI_ENDPOINT
    valueFrom:
      secretKeyRef:
        name: langextract-secrets
        key: azure-openai-endpoint

persistence:
  enabled: true
  storageClass: "nfs-client"
  accessMode: ReadWriteMany
  size: 10Gi
  mountPath: /app/data

resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

#### deployment.yaml 範例

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langextract
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: langextract
  template:
    metadata:
      labels:
        app: langextract
    spec:
      containers:
      - name: langextract
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        env: {{ .Values.env | toYaml | nindent 12 }}
        volumeMounts:
        - name: data
          mountPath: {{ .Values.persistence.mountPath }}
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
      volumes:
      - name: data
        {{- if .Values.persistence.enabled }}
        persistentVolumeClaim:
          claimName: langextract-pvc
        {{- end }}
```

#### service.yaml 範例（NodePort）

```yaml
apiVersion: v1
kind: Service
metadata:
  name: langextract-service
spec:
  type: {{ .Values.service.type }}
  ports:
  - port: {{ .Values.service.port }}
    targetPort: 8000
    nodePort: 30080
  selector:
    app: langextract
```

#### persistentvolumeclaim.yaml 範例（NFS）

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: langextract-pvc
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: nfs-client
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
```

#### 部署指令

```bash
# 建立 Secret（包含 API 金鑰）
kubectl create secret generic langextract-secrets \
  --from-literal=gemini-api-key='your-key' \
  --from-literal=azure-openai-api-key='your-key' \
  --from-literal=azure-openai-endpoint='https://your-resource.openai.azure.com'

# 安裝 Helm Chart
helm install langextract ./helm/langextract

# 檢查部署狀態
kubectl get pods -l app=langextract
kubectl get svc langextract-service
```

---

## 4. 操作指南 (Operations)

### 4.1 基本操作

#### 啟動服務（Python 腳本）

建立基本提取腳本 `extract_example.py`：

```python
import langextract as lx
import textwrap

# 定義提取任務
prompt = textwrap.dedent("""
    從文字中提取人物、地點和情感。
    使用精確文字，不要改寫或重疊實體。
""")

# 提供範例
examples = [
    lx.data.ExampleData(
        text="Romeo 在 Verona 感到憂傷。",
        extractions=[
            lx.data.Extraction(
                extraction_class="character",
                extraction_text="Romeo",
                attributes={"emotion": "憂傷"}
            ),
            lx.data.Extraction(
                extraction_class="location",
                extraction_text="Verona"
            ),
        ]
    )
]

# 執行提取
result = lx.extract(
    text_or_documents="Juliet 在 Verona 感到快樂。",
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-2.5-flash",
)

# 儲存結果
lx.io.save_annotated_documents(
    [result],
    output_name="extraction_results.jsonl",
    output_dir="."
)

# 生成視覺化
html_content = lx.visualize("extraction_results.jsonl")
with open("visualization.html", "w") as f:
    if hasattr(html_content, 'data'):
        f.write(html_content.data)
    else:
        f.write(html_content)
```

執行：

```bash
python extract_example.py
```

#### 處理長文本

```python
# 處理長文件（支援 URL）
result = lx.extract(
    text_or_documents="https://www.gutenberg.org/files/1513/1513-0.txt",
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-2.5-flash",
    extraction_passes=3,    # 多輪提取提高召回率
    max_workers=20,         # 平行處理加速
    max_char_buffer=1000    # 較小的上下文提高準確度
)
```

### 4.2 進階設定 (LLM Integration)

#### Azure OpenAI 整合設定

##### 方法 1：使用環境變數（推薦）

```bash
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini"
```

在 Python 程式碼中：

```python
import langextract as lx

result = lx.extract(
    text_or_documents=input_text,
    prompt_description=prompt,
    examples=examples,
    model_id="gpt-4o-mini",  # 或您的部署名稱
    fence_output=True,
    use_schema_constraints=False
)
```

##### 方法 2：直接在程式碼中指定

```python
import langextract as lx
import os

result = lx.extract(
    text_or_documents=input_text,
    prompt_description=prompt,
    examples=examples,
    model_id="gpt-4o-mini",
    language_model_params={
        "deployment_name": "gpt-4o-mini",  # Azure 部署名稱
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": "2024-02-15-preview",  # 或使用最新版本
    },
    fence_output=True,
    use_schema_constraints=False
)
```

##### 方法 3：使用 Factory 直接建立模型

```python
import langextract as lx
import os

# 建立 Azure OpenAI 模型配置
config = lx.factory.ModelConfig(
    model_id="gpt-4o-mini",
    provider="AzureLanguageModel",
    provider_kwargs={
        "deployment_name": "gpt-4o-mini",
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": "2024-02-15-preview",
    }
)

model = lx.factory.create_model(config)

# 使用模型進行提取（需透過 Annotator）
# 建議使用 lx.extract() 高階 API
```

#### Azure OpenAI 部署名稱與 API 版本設定

**部署名稱（Deployment Name）**：
- 在 Azure 入口網站中建立 OpenAI 部署時指定的名稱
- 必須與 `AZURE_OPENAI_DEPLOYMENT_NAME` 或 `language_model_params["deployment_name"]` 一致
- 常見範例：`gpt-4o-mini`、`gpt-4o`、`gpt-35-turbo`

**API 版本（API Version）**：
- 預設值：`2024-02-15-preview`
- 建議使用最新穩定版本，可在 Azure 入口網站查看可用版本
- 設定方式：環境變數 `AZURE_OPENAI_API_VERSION` 或 `language_model_params["api_version"]`

#### Gemini 整合設定

```python
# 使用 API 金鑰
result = lx.extract(
    text_or_documents=input_text,
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-2.5-flash",
)

# 使用 Vertex AI（服務帳號認證）
result = lx.extract(
    text_or_documents=input_text,
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-2.5-flash",
    language_model_params={
        "vertexai": True,
        "project": "your-project-id",
        "location": "global"  # 或區域端點如 "us-central1"
    }
)
```

#### OpenAI 整合設定

```python
# 安裝 OpenAI 支援
# pip install langextract[openai]

result = lx.extract(
    text_or_documents=input_text,
    prompt_description=prompt,
    examples=examples,
    model_id="gpt-4o",
    api_key=os.environ.get("OPENAI_API_KEY"),
    fence_output=True,
    use_schema_constraints=False
)
```

#### Ollama 本地模型整合

```python
result = lx.extract(
    text_or_documents=input_text,
    prompt_description=prompt,
    examples=examples,
    model_id="gemma2:2b",  # Ollama 模型名稱
    model_url="http://localhost:11434",  # 或使用環境變數 OLLAMA_BASE_URL
    fence_output=False,
    use_schema_constraints=False
)
```

### 4.3 故障排除 (Troubleshooting)

#### Azure 連線錯誤

**錯誤：401 Unauthorized**

```
InferenceConfigError: Azure OpenAI API error: 401
```

**可能原因與解決方案**：
1. **API 金鑰錯誤**：檢查 `AZURE_OPENAI_API_KEY` 是否正確
   ```bash
   echo $AZURE_OPENAI_API_KEY  # 確認環境變數已設定
   ```
2. **金鑰過期**：在 Azure 入口網站重新產生 API 金鑰
3. **權限不足**：確認 API 金鑰具有適當權限

**錯誤：404 Not Found**

```
InferenceConfigError: Azure OpenAI API error: 404
```

**可能原因與解決方案**：
1. **端點 URL 錯誤**：確認 `AZURE_OPENAI_ENDPOINT` 格式正確
   ```bash
   # 正確格式
   https://your-resource.openai.azure.com
   
   # 錯誤格式（不要包含路徑）
   https://your-resource.openai.azure.com/v1/chat/completions  # ❌
   ```
2. **部署名稱不存在**：確認 `AZURE_OPENAI_DEPLOYMENT_NAME` 與 Azure 入口網站中的部署名稱一致
3. **區域錯誤**：確認部署所在的區域與端點一致

**錯誤：API 版本不支援**

```
InferenceConfigError: Azure OpenAI API error: Invalid API version
```

**解決方案**：
- 更新 `AZURE_OPENAI_API_VERSION` 為最新支援版本
- 在 Azure 入口網站查看可用 API 版本

#### NFS 掛載失敗（Kubernetes）

**錯誤**：
```
MountVolume.SetUp failed for volume "langextract-pvc": mount failed
```

**可能原因與解決方案**：
1. **StorageClass 不存在**：確認 NFS StorageClass 已建立
   ```bash
   kubectl get storageclass
   ```
2. **NFS 伺服器連線問題**：檢查 NFS 伺服器可達性
   ```bash
   # 在 Pod 中測試
   kubectl exec -it <pod-name> -- ping <nfs-server-ip>
   ```
3. **權限問題**：確認 NFS 目錄權限設定正確

#### Python 套件相依性問題

**錯誤：ImportError**

```
ImportError: No module named 'google.genai'
```

**解決方案**：
```bash
# 安裝缺失的套件
pip install google-genai

# 或重新安裝完整套件
pip install --upgrade langextract
```

**錯誤：版本衝突**

```
pydantic.exceptions.ValidationError
```

**解決方案**：
```bash
# 使用虛擬環境隔離
python -m venv venv
source venv/bin/activate
pip install langextract

# 或檢查相依性版本
pip check
```

#### API 速率限制錯誤

**錯誤**：
```
InferenceRuntimeError: Rate limit exceeded
```

**解決方案**：
1. **降低並行度**：減少 `max_workers` 參數
   ```python
   result = lx.extract(
       ...,
       max_workers=5,  # 降低並行度
   )
   ```
2. **增加重試機制**：實作自訂重試邏輯
3. **升級 API 配額**：在供應商入口網站申請更高配額

#### 記憶體不足

**錯誤**：
```
MemoryError: Unable to allocate array
```

**解決方案**：
1. **減少批次大小**：調整 `max_char_buffer` 參數
2. **增加系統記憶體**：在 Kubernetes 中調整資源限制
3. **使用串流處理**：處理超長文件時分批處理

---

## 5. 範例與截圖 (Examples)

### 5.1 基本提取範例

**輸入文字**：
```
Romeo 是 Montague 家族的成員，他愛上了 Capulet 家族的 Juliet。
他們在 Verona 相遇，但兩家是世仇。
```

**提取結果（JSONL 格式）**：
```json
{
  "text": "Romeo 是 Montague 家族的成員，他愛上了 Capulet 家族的 Juliet。\n他們在 Verona 相遇，但兩家是世仇。",
  "extractions": [
    {
      "extraction_class": "character",
      "extraction_text": "Romeo",
      "char_interval": [0, 5],
      "attributes": {"family": "Montague"}
    },
    {
      "extraction_class": "character",
      "extraction_text": "Juliet",
      "char_interval": [35, 41],
      "attributes": {"family": "Capulet"}
    },
    {
      "extraction_class": "location",
      "extraction_text": "Verona",
      "char_interval": [45, 51],
      "attributes": {}
    },
    {
      "extraction_class": "relationship",
      "extraction_text": "兩家是世仇",
      "char_interval": [54, 59],
      "attributes": {"type": "conflict"}
    }
  ]
}
```

> [圖片說明：此處應顯示互動式 HTML 視覺化截圖，展示提取結果在原文中的高亮標示]

### 5.2 Azure OpenAI 完整範例

```python
import langextract as lx
import os
import textwrap

# 設定環境變數（或在 .env 檔案中設定）
os.environ["AZURE_OPENAI_API_KEY"] = "your-api-key"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://your-resource.openai.azure.com"
os.environ["AZURE_OPENAI_API_VERSION"] = "2024-02-15-preview"
os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4o-mini"

# 定義提取任務
prompt = textwrap.dedent("""
    從醫療記錄中提取藥物名稱、劑量和給藥途徑。
    使用精確文字，不要改寫。
""")

examples = [
    lx.data.ExampleData(
        text="患者每日服用 Aspirin 100mg，口服。",
        extractions=[
            lx.data.Extraction(
                extraction_class="medication",
                extraction_text="Aspirin",
                attributes={"dosage": "100mg", "route": "口服"}
            )
        ]
    )
]

# 執行提取
result = lx.extract(
    text_or_documents="患者需要 Metformin 500mg，每日兩次，飯後口服。",
    prompt_description=prompt,
    examples=examples,
    model_id="gpt-4o-mini",  # 使用 Azure 部署名稱
    fence_output=True,
    use_schema_constraints=False
)

# 儲存結果
lx.io.save_annotated_documents([result], "azure_extraction.jsonl")
print("提取完成！結果已儲存至 azure_extraction.jsonl")
```

### 5.3 長文本處理範例

```python
# 處理完整文件（從 URL）
result = lx.extract(
    text_or_documents="https://www.gutenberg.org/files/1513/1513-0.txt",
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-2.5-flash",
    extraction_passes=3,      # 多輪提取
    max_workers=20,           # 平行處理
    max_char_buffer=1000,     # 較小的上下文
    temperature=0.0           # 確定性輸出
)

# 儲存並視覺化
lx.io.save_annotated_documents([result], "long_document_extraction.jsonl")
html = lx.visualize("long_document_extraction.jsonl")
with open("long_document_visualization.html", "w") as f:
    f.write(html if isinstance(html, str) else html.data)
```

> [圖片說明：此處應顯示長文本處理的進度條與效能指標截圖]

---

## 附錄：快速參考

### 常用指令

```bash
# 安裝
pip install langextract

# 安裝 OpenAI 支援
pip install langextract[openai]

# 執行測試
pytest tests/

# Docker 建置
docker build -t langextract:latest .

# 檢查環境變數
env | grep -E "(GEMINI|OPENAI|AZURE|OLLAMA)"
```

### 支援的模型 ID 格式

- **Gemini**：`gemini-2.5-flash`、`gemini-2.5-pro`、`gemini-1.5-pro-latest`
- **OpenAI**：`gpt-4o`、`gpt-4o-mini`、`gpt-35-turbo`
- **Azure OpenAI**：使用部署名稱（如 `gpt-4o-mini`）
- **Ollama**：`gemma2:2b`、`llama3`（需先執行 `ollama pull <model>`）

---
