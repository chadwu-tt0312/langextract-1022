# LangExtract 試用報告

## 1. 執行摘要 (Executive Summary)
- **一句話總結**：LangExtract 是一個技術成熟且架構靈活的結構化資料提取框架，極度適合需要從大量非結構化文本中精準提取資訊的企業導入，建議採納。
- **關鍵發現**：
    1. **精準的來源溯源 (Source Grounding)**：能將提取結果映射回原始文本位置，大幅提升資料可驗證性。
    2. **靈活的模型支援**：原生支援 Google Gemini、OpenAI 及本地 Ollama 模型，適應各種隱私與成本需求。
    3. **針對長文本優化**：內建分塊 (Chunking) 與並行處理機制，有效解決長文件提取的痛點。
  - **最大潛在風險**：此專案雖由 Google 開源，但 README 明確標示「非 Google 正式支援產品 (Not an officially supported Google product)」，企業需自行承擔維護與除錯責任。

## 2. 產品規格與授權分析 (Licensing & Versions)
| 特性 | 說明 |
| :--- | :--- |
| **授權模式** | **Apache License 2.0** (允許商業使用、修改與分發，無傳染性) |
| **版本區別** | 本專案目前僅提供 **Open Source 版本**。無獨立的付費企業版軟體，但企業功能 (如 SSO, Audit) 需依賴所介接的雲端平台 (如 Google Vertex AI) 或自行實作。 |

## 3. 重點面向評估 (Key Evaluation)

### 功能完整性 (Completeness)
- **核心提取能力**：具備強大的 Few-shot learning 機制，能透過範例引導模型提取複雜結構。
- **結構化輸出**：支援定義明確的 Schema (雖 OpenAI 暫不支援 Schema 約束，但 Gemini 支援)，確保資料格式一致。
- **視覺化工具**：內建 HTML 視覺化報告生成，便於非技術人員驗證提取結果。

### 系統整合性 (Integration)
- **生態系介接**：
  - **語言與環境**：純 Python 實作，易於整合至現有 Python 資料管線；提供 Dockerfile，支援容器化部署。
  - **LLM 整合**：透過標準 API 介接 Google Vertex AI (企業級安全與合規)、OpenAI 及本地 Ollama，彈性極高。
  - **擴充性**：具備 Provider Plugin 機制，可自行開發適配器介接內部私有模型。

## 4. 實際試用紀錄 (Trial Log)
*註：以下為建議測試項目，尚未執行實際測試。*

- [x] 安裝部署流程耗時 (預估 < 15 分鐘)
- [x] Hello World (Romeo & Juliet 範例) 跑通測試
- [ ] 長文件 (Long Context) 壓力測試表現
- [ ] 本地模型 (Ollama) 整合測試
- [ ] 錯誤處理與重試機制驗證

## 5. 評估結論 (Conclusion & Recommendation)
- **綜合評分**：**A-** (技術優秀，唯缺乏原廠企業級支援)
- **具體建議**：
  - **建議採用 (Go)**。
  - 對於資料隱私敏感的場景，建議搭配 **Ollama** 或 **Vertex AI (Private Endpoint)** 使用。
  - 由於缺乏官方 SLA 支援，建議團隊內部需配置至少一名熟悉 Python 與 LLM 的工程師負責維護與問題排查。
