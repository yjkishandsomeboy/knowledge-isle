# Knowledge Isle MVP 规格

状态：已冻结  
版本：1.0  
日期：2026-07-23

## 1. 产品目标

Knowledge Isle 是一个单管理员、支持中英文界面的私有 AI 知识库。管理员上传 PDF、Markdown 或 TXT 文档后，系统在本地完成解析、切片和向量化，并基于检索到的相关片段调用兼容 OpenAI Responses API 的模型生成带原文引用的回答。

MVP 的成功标准不是功能数量，而是完成一个可部署、可测试、可解释的完整闭环：

```text
初始化管理员 -> 登录 -> 创建知识库 -> 上传文档 -> 异步处理
-> 语义检索 -> AI 问答 -> 原文引用 -> 会话留存 -> 安全部署
```

## 2. 用户与权限

MVP 只有一个角色：管理员。

- 首次启动时，通过服务端配置的一次性初始化令牌创建唯一管理员。
- 初始化成功后，公开注册入口永久关闭。
- 管理员可以登录、退出、修改密码和注销其他会话。
- 所有知识库、文档、问答和系统设置接口都必须登录后访问。
- 未认证请求返回 `401`，不泄露资源是否存在。

## 3. 功能范围

### 3.1 管理员认证

- 唯一管理员初始化
- 登录与退出
- 服务端 Session 与 HttpOnly Cookie
- 密码安全哈希
- 登录失败限流
- 修改密码后注销其他会话

### 3.2 知识库

- 创建、查看、编辑和删除知识库
- 字段：名称、描述、默认回答语言、创建时间、更新时间
- 显示文档数量、切片数量和处理状态汇总
- 删除知识库时清理原文件、文本切片、向量、会话和引用

### 3.3 文档

支持格式：

- PDF（文字型，不含 OCR）
- Markdown
- TXT

限制：

- 单文件最大 20 MB
- PDF 最大 300 页
- 校验扩展名、MIME 类型和真实文件内容
- 文件存放于 MinIO 私有 Bucket，不提供永久公网地址

处理状态：

```text
pending -> parsing -> embedding -> ready
                         \-> failed
```

失败任务允许管理员手动重试。错误信息只保存必要的诊断摘要，不保存文档正文。

### 3.4 检索与问答

- 文档在本地完成清洗、切片和 BGE-M3 Embedding。
- 使用 PostgreSQL + pgvector 进行相似度检索。
- 只把与问题相关的必要文档片段发送给 AI 中转服务。
- AI Provider 使用 Responses API，Base URL、API Key 和模型 ID 均由环境变量配置。
- `AI_STREAM_MODE=auto` 时先探测流式能力；不可用时降级为非流式响应。
- 回答必须保留结构化引用，引用包含文档、页码或位置、片段预览。
- 保存会话、消息、引用、耗时和错误状态，不记录 API Key 或完整请求正文。

### 3.5 国际化

- 界面支持简体中文与英文即时切换。
- 管理员语言偏好持久化。
- 页面标题、按钮、表单校验和错误提示全部进入翻译文件。
- AI 默认使用提问语言回答，不自动翻译原始文档。

### 3.6 审计与运维

- 记录登录、退出、密码修改、文档上传、重试和删除等关键操作。
- 提供 API、数据库、Redis、MinIO 和 Worker 健康状态。
- 日志不得包含密码、Cookie、Token、API Key 或文档正文。
- 提供数据库和对象存储备份、恢复说明。

## 4. 非功能要求

### 安全

- PostgreSQL、Redis、MinIO 只监听服务器本地或 Docker 内部网络。
- 生产环境只公开 SSH、HTTP 和 HTTPS 所需端口。
- 全站 HTTPS；Cookie 使用 HttpOnly、Secure 和 SameSite。
- 密钥只通过环境变量或服务器 Secret 注入，不进入 Git。
- 下载使用短期签名 URL，默认有效期不超过 5 分钟。
- 删除操作必须验证权限，并保证关联数据最终被清理。

### 性能

- 普通 API 在本地开发环境下 P95 小于 500 ms，不含 AI 与文件处理。
- 上传请求快速返回任务 ID，耗时处理进入 Celery。
- 首版单 Worker，避免在 4 vCPU / 16 GiB 服务器上过度并发。
- 向量检索默认返回 8 个候选片段，最终上下文数量可通过评估调整。

### 可靠性

- 文档任务可重试且具有幂等保护，不重复写入切片。
- 容器重启后数据库、Redis 队列和文件数据不丢失。
- AI 流式调用失败时记录明确状态，并允许重新回答。

### 可维护性

- FastAPI 自动生成 OpenAPI 文档。
- TypeScript API 类型从 OpenAPI 生成，避免手写重复契约。
- Python 使用 Ruff、mypy、Pytest；前端使用 ESLint、vue-tsc、Vitest、Playwright。
- 核心业务逻辑不依赖大型 RAG 框架，检索和引用链路保持可读。

## 5. 技术架构

```text
Browser
  -> Caddy / HTTPS
      -> Vue 3 Web
      -> FastAPI
          -> PostgreSQL + pgvector
          -> Redis -> Celery Worker
          -> MinIO
          -> Local BGE-M3 Embedding
          -> AI Provider Adapter -> Responses API relay
```

核心技术：

- Web：Vue 3、TypeScript、Vite、Vue Router、Pinia、Vue I18n
- API：FastAPI、Pydantic v2、SQLAlchemy 2、Alembic
- Worker：Celery、Redis、PyMuPDF
- Data：PostgreSQL、pgvector、MinIO
- AI：BGE-M3、本地向量化、Responses API Provider
- Delivery：Docker Compose、Caddy、GitHub Actions、GHCR

## 6. 核心数据实体

- `users`：唯一管理员及安全字段
- `sessions`：登录会话、过期时间、撤销状态
- `knowledge_bases`：知识库配置与统计
- `documents`：文件元数据、对象存储键和处理状态
- `document_chunks`：正文片段、位置元数据和向量
- `conversations`：问答会话
- `messages`：用户问题、AI 回答和生成状态
- `citations`：回答与文档片段的引用关系
- `audit_logs`：安全相关操作记录
- `system_settings`：初始化状态及非敏感系统配置

## 7. MVP 页面

- 首次初始化页
- 登录页
- 总览页
- 知识库列表页
- 知识库详情与文档管理页
- 文档处理状态页
- 知识库问答页
- 会话历史页
- 设置与安全页
- 404 与通用错误页

## 8. 明确不做

- 公开注册、多管理员、多租户与团队权限
- 邮件验证、找回密码和第三方登录
- OCR、图片理解、语音、网页抓取
- 在线编辑、公开分享和多人协作
- 订阅、支付、额度售卖
- 移动端原生应用
- 多模型选择界面

这些能力不得在 MVP 阶段以“预留功能”为由提前实现。

## 9. 发布验收

只有同时满足以下条件，MVP 才算完成：

1. 唯一管理员初始化与登录流程通过端到端测试。
2. 能上传三种支持格式并正确展示异步状态。
3. 文档可被检索，回答包含可追溯的原文引用。
4. 中英文界面覆盖所有核心页面。
5. 核心权限、安全删除和任务重试具有自动化测试。
6. Docker Compose 可在目标服务器启动全部服务。
7. 域名、HTTPS、备份和 CI/CD 完成线上验证。
8. README、架构图、API 文档和演示材料齐全。

## 10. 已知风险与控制

- 中转站的流式协议尚未验证：运行时能力探测，并支持非流式降级。
- 中转站可能记录私密片段：UI 明确提示数据边界，仅发送必要片段。
- 本地 BGE-M3 占用内存和处理时间：单 Worker、限制并发并记录处理耗时。
- 扫描 PDF 无文本：MVP 明确报错，不静默返回空文档。
- 128 GB 磁盘有限：设置上传限制、显示存储统计并建立备份清理策略。
