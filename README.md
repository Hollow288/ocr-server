# OCR Service

基于 [RapidOCR (ONNX Runtime)](https://github.com/RapidAI/RapidOCR) + FastAPI 的轻量 OCR 服务，支持图片与 PDF 识别，支持本地文件上传与远程 URL 拉取。

## 特性

- 图片 OCR：JPG / PNG / BMP / WebP 等 Pillow 支持的格式
- PDF OCR：基于 PyMuPDF 渲染逐页识别，可配置 DPI 与最大页数
- 远程 URL 拉取：内置 SSRF 防护，禁止访问私有/回环/保留地址（可关闭）
- API Key 鉴权（请求头 `X-API-KEY`）
- 两种返回模式：`detail`（含坐标/置信度）和 `list`（纯文本数组）
- 置信度阈值过滤

## 快速开始

### Docker Compose

```bash
cp .env.example .env
# 编辑 .env，至少修改 OCR_API_KEY
docker compose up -d
```

服务默认监听 `127.0.0.1:7634`（容器内 `8000`）。

### 本地运行

```bash
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `OCR_API_KEY` | `my_default_secret` | API Key，请求头 `X-API-KEY` 必须与之匹配 |
| `PDF_DPI` | `200` | PDF 页面渲染 DPI，越高越清晰也越慢 |
| `PDF_MAX_PAGES` | `50` | PDF 最大页数，超出返回 413 |
| `URL_DOWNLOAD_TIMEOUT` | `15` | URL 下载超时（秒） |
| `URL_MAX_BYTES` | `52428800` | URL 下载最大字节数（默认 50 MB） |
| `URL_MAX_REDIRECTS` | `3` | URL 最大重定向次数 |
| `ALLOW_PRIVATE_URLS` | `false` | 是否允许下载到私有/回环 IP（生产环境保持 `false`） |

## 鉴权

所有 OCR 接口均需在请求头携带 API Key：

```
X-API-KEY: <your-api-key>
```

未携带或不匹配返回 `403`。

## 接口

### 健康检查

```http
GET /
```

返回：

```json
{ "message": "OCR 服务正在运行中...请使用 POST /ocr 上传图片或 PDF" }
```

---

### `POST /ocr` — 文件上传

`multipart/form-data` 上传本地图片或 PDF。

#### 请求

| 位置 | 名称 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- | --- |
| header | `X-API-KEY` | string | 是 | — | API Key |
| form | `file` | file | 是 | — | 图片或 PDF 文件 |
| query | `mode` | `detail` \| `list` | 否 | `detail` | 返回格式 |
| query | `min_confidence` | float `[0, 1]` | 否 | 不过滤 | 仅返回置信度 ≥ 该值的条目 |

#### 示例：默认 detail 模式

```bash
curl -X POST "http://localhost:7634/ocr" \
  -H "X-API-KEY: your-api-key" \
  -F "file=@./sample.png"
```

#### 示例：list 模式 + 置信度过滤

```bash
curl -X POST "http://localhost:7634/ocr?mode=list&min_confidence=0.8" \
  -H "X-API-KEY: your-api-key" \
  -F "file=@./sample.pdf"
```

---

### `POST /ocr/url` — 远程 URL

通过 JSON body 提交远程 URL，由服务端拉取后识别。

#### 请求

Header：`X-API-KEY: <your-api-key>`、`Content-Type: application/json`

Body：

| 字段 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `url` | string (http/https) | 是 | — | 资源地址 |
| `mode` | `detail` \| `list` | 否 | `detail` | 返回格式 |
| `min_confidence` | float `[0, 1]` | 否 | 不过滤 | 仅返回置信度 ≥ 该值的条目 |

#### 示例：默认 detail 模式

```bash
curl -X POST "http://localhost:7634/ocr/url" \
  -H "X-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/sample.png"
  }'
```

#### 示例：list 模式 + 置信度过滤

```bash
curl -X POST "http://localhost:7634/ocr/url" \
  -H "X-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/sample.pdf",
    "mode": "list",
    "min_confidence": 0.8
  }'
```

---

## 返回格式

### `mode=detail`（默认）

```json
{
  "code": 200,
  "data": [
    {
      "text": "示例文字",
      "confidence": 0.987,
      "bbox": [[12.0, 34.0], [120.0, 34.0], [120.0, 60.0], [12.0, 60.0]],
      "page": 1
    }
  ],
  "elapse": 0.42,
  "pages": 1
}
```

字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | int | 业务状态码，固定 `200` |
| `data[].text` | string | 识别文本 |
| `data[].confidence` | float | 置信度，范围 `[0, 1]` |
| `data[].bbox` | float[4][2] | 文本框 4 个顶点坐标，顺序为左上、右上、右下、左下 |
| `data[].page` | int / null | 页码（PDF 时为 1-based；图片时为 `null`） |
| `elapse` | float | OCR 总耗时（秒，PDF 为各页累加） |
| `pages` | int / null | PDF 总页数；图片为 `null` |

### `mode=list`

```json
{
  "code": 200,
  "data": ["第一段文字", "第二段文字", "第三段文字"],
  "elapse": 0.42,
  "pages": 1
}
```

`data` 仅保留文本，按识别顺序（PDF 按页码顺序）排列。

---

## 错误响应

| HTTP | 场景 | 示例 detail |
| --- | --- | --- |
| 400 | 不支持的图片格式 | `Unsupported file format` |
| 400 | PDF 解析失败 | `Invalid PDF: <reason>` |
| 400 | URL 下载失败 / SSRF 拦截 / 重定向超限 | `Failed to download: ...` / `URL resolves to restricted IP: ...` |
| 403 | API Key 缺失或错误 | `Could not validate credentials` |
| 413 | PDF 页数超限 | `PDF has 80 pages, exceeds limit of 50` |
| 422 | 参数校验失败（如 `min_confidence` 超出 `[0, 1]`） | FastAPI 标准校验响应 |

---

## OpenAPI 文档

服务启动后访问：

- Swagger UI: `http://localhost:7634/docs`
- ReDoc: `http://localhost:7634/redoc`
