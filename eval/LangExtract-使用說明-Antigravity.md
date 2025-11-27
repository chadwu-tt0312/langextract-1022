# LangExtract 使用說明

## 1. 簡介
**LangExtract** 是一個專為從非結構化文本中提取結構化資料而設計的 Python 函式庫。它利用 LLM (Large Language Models) 的強大理解能力，結合精確的來源溯源 (Source Grounding) 機制，解決了傳統 NLP 工具在處理複雜語意時的痛點。

- **專案網頁**：<https://github.com/google/langextract>
- **參考網頁**：<https://deepwiki.com/google/langextract>
- **目標讀者**：負責部署、維護與整合 LangExtract 的 DevOps 工程師與後端開發人員。

## 2. 環境變數詳解 (Environment Variables)
以下列出 LangExtract 及其整合服務所需的關鍵環境變數。

| 變數名稱 | 預設值 | 必填 | 說明 |
| :--- | :--- | :--- | :--- |
| `LANGEXTRACT_API_KEY` | 無 | **是** (若使用 Cloud LLM) | LangExtract 的主要 API Key，通常用於 Google Gemini。 |
| `OPENAI_API_KEY` | 無 | 否 | 若使用 OpenAI 模型，需設定此變數。 |
| **Azure OpenAI 相關** | | | **若使用 Azure OpenAI 服務，請設定以下變數：** |
| `AZURE_OPENAI_API_KEY` | 無 | 否 | Azure OpenAI 的 API Key。 |
| `AZURE_OPENAI_ENDPOINT` | 無 | 否 | Azure OpenAI 的 Endpoint URL (例如 `https://my-resource.openai.azure.com/`)。 |
| `OPENAI_API_VERSION` | `2023-05-15` | 否 | 指定使用的 API 版本。 |

## 3. 安裝與部署 (Installation & Deployment)

### 3.1 Python 套件安裝 (本機/開發環境)
本專案使用 `pyproject.toml` 管理相依性。

1.  **建立虛擬環境**：
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    ```
2.  **安裝套件**：
    ```bash
    pip install .
    # 若需開發或測試工具
    pip install -e ".[dev,test]"
    ```

### 3.2 Kubernetes Helm 部署 (生產環境)
由於專案包含 `Dockerfile`，建議使用 Helm 進行容器化部署。

**Helm Chart 規格建議**：

- **Service Type**: `NodePort` (方便外部存取或搭配 Ingress)。
- **Storage**: 建議配置 NFS Persistent Volume (PV/PVC) 以持久化提取結果或快取模型數據。

**values.yaml 範例片段**：
```yaml
service:
  type: NodePort
  port: 80

persistence:
  enabled: true
  storageClass: "nfs-client" # 請依實際環境調整
  accessMode: ReadWriteMany
  size: 10Gi
```

**部署指令**：
```bash
# 假設您已建立名為 langextract 的 Chart
helm install langextract ./charts/langextract \
  --set service.type=NodePort \
  --set persistence.enabled=true
```

## 4. 操作指南 (Operations)

### 4.1 基本操作
- **啟動服務** (假設以 Docker 執行)：
    ```bash
    docker run --rm -e LANGEXTRACT_API_KEY="your-key" langextract python your_script.py
    ```

### 4.2 進階設定：Azure OpenAI 整合
若需整合 Azure OpenAI，除了設定環境變數外，需在呼叫 `lx.extract` 時指定模型參數。

**設定範例**：
```python
import langextract as lx
import os

# 確保環境變數已設定：
# AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, OPENAI_API_VERSION

result = lx.extract(
    text_or_documents="...",
    prompt_description="...",
    examples=[...],
    model_id="gpt-4", # 對應 Azure 上的 Deployment Name
    language_model_params={
        "azure_deployment": "your-deployment-name", # 指定 Deployment Name
        "api_version": os.getenv("OPENAI_API_VERSION", "2023-05-15")
    }
)
```

### 4.3 故障排除 (Troubleshooting)
- **Azure 連線錯誤 (401/404)**：
    - 檢查 `AZURE_OPENAI_ENDPOINT` 是否包含完整的資源路徑。
    - 確認 `model_id` 與 Azure Portal 上的 **Deployment Name** 是否一致 (注意：非模型名稱)。
- **NFS 掛載失敗**：
    - 檢查 Kubernetes 節點是否已安裝 `nfs-common`。
    - 確認 NFS Server 的防火牆設定允許 K8s 節點連線。
- **Python 套件衝突**：
    - 若遇到 `ImportError`，請嘗試重新建立虛擬環境並執行 `pip install -e .` 確保安裝的是當前源碼版本。

## 5. 範例與截圖 (Examples)

> [圖片說明：此處應顯示 LangExtract 執行後的互動式 HTML 視覺化報告截圖，展示提取實體與原始文本的對照。]

**文字輸出範例 (JSONL)**：
```json
{"extraction_text": "ROMEO", "extraction_class": "character", "attributes": {"emotional_state": "wonder"}}
{"extraction_text": "Juliet", "extraction_class": "character", "attributes": {"emotional_state": "longing"}}
```
