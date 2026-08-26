# Cross Read

Cross Read 是一个运行在 Windows 电脑上的局域网只读文件阅读器。电脑端启动服务并配置允许访问的目录后，iPhone、iPad 或其他设备可通过浏览器浏览和阅读其中的文件。

项目的第一阶段只解决一个核心问题：**让手机方便、安全地阅读电脑上的文件**。

## 第一阶段目标

- 在 Windows 上启动一个本地 Web 服务。
- 自动读取 Windows 已发布的普通 SMB 共享目录。
- 可选配置没有发布为 Windows 共享的额外目录。
- 手机和电脑处于同一局域网时，通过 Safari 打开服务地址。
- 像文件管理器一样浏览目录和文件。
- 预览 Markdown、PDF、DOCX、图片和纯文本。
- 播放浏览器支持的 MP4、MOV 视频，并支持拖动播放进度。
- 界面移动端优先，适配 iPhone，同时兼容桌面浏览器。
- 所有共享内容只读，不提供上传、编辑、重命名、移动或删除能力。

## 暂不包含

以下能力不属于第一阶段：

- 文件上传、编辑、删除、移动和重命名
- 视频实时转码与 HLS 切片
- 外网直接访问
- 多用户和复杂权限系统
- 收藏、最近阅读和跨设备进度同步
- Windows 托盘、开机自启和安装程序
- Office 文档在线编辑

## 技术栈

### 后端

- Python 3.12
- FastAPI
- Uvicorn
- uv（Python 项目与依赖管理）
- Pytest

### 前端

- Vue 3
- TypeScript
- Vite
- pnpm（仅用于前端开发与构建）
- Vue Router
- Vitest
- markdown-it + Mermaid：Markdown 与流程图渲染
- DOMPurify：HTML 内容净化
- PDF.js：PDF 预览
- docx-preview：DOCX 预览

第一阶段不引入大型 UI 组件库。界面使用自定义 CSS 变量和轻量组件实现，以便保持简洁的 iOS 风格，并减少不必要的体积。

## 系统结构

```text
iPhone / iPad / Desktop Browser
              │
              │ HTTP（家庭局域网）
              ▼
       FastAPI Web 服务
              │
              ├── Vue 静态页面
              ├── 目录与文件元数据 API
              ├── 普通文件读取 API
              └── 视频 Range 分段传输
              │
              ▼
       Windows SMB 共享与可选手动目录
```

开发阶段前后端分别运行；Python 依赖由 uv 管理，前端依赖由 pnpm 管理。发布时将 Vue 构建产物交给 FastAPI 托管，最终用户不需要安装 Node.js，只需要启动一个服务。

## 核心原则

1. **只读**：后端不提供任何修改文件的接口。
2. **共享边界**：仅允许访问 Windows 已发布的普通共享和配置中额外声明的目录，自动排除盘符及管理共享。
3. **路径安全**：客户端只能提交共享目录 ID 和相对路径，不能提交或看到电脑绝对路径。
4. **移动优先**：主要交互以 iPhone Safari 为基准设计。
5. **渐进增强**：先保证常见文件可阅读，再逐步补充高级体验。
6. **原文件优先**：视频第一阶段不转码；浏览器不支持其内部编码时给出明确提示。

## 文档

- [MVP 产品与技术方案](docs/MVP.md)
- [原始需求记录](需求.txt)

## 开发与运行

### 1. 创建本地配置

```powershell
Copy-Item config.example.yaml config.yaml
```

默认配置会自动读取 Windows 已经发布的共享文件夹。`ADMIN$`、`C$`、`D$`、`IPC$` 等系统和管理共享不会显示。

```yaml
discovery:
  windows_smb: true

shares: []
```

以后在 Windows 中将任意文件夹设为共享，刷新 Cross Read 首页即可看到；取消共享后刷新也会消失。`shares` 可以额外配置没有发布为 Windows 共享、但仍希望在 Cross Read 中阅读的目录。

### 2. 安装依赖并构建页面

```powershell
uv sync --dev
Set-Location frontend
pnpm install
pnpm build
Set-Location ..
```

### 3. 启动服务

```powershell
uv run cross-read
```

电脑浏览器访问 `http://127.0.0.1:8000`。iPhone 与电脑连接同一 Wi-Fi 后，访问 `http://电脑的局域网IP:8000`。

开发前端时可分别运行：

```powershell
# 终端一
uv run cross-read --reload

# 终端二
Set-Location frontend
pnpm dev
```

Vite 会将 `/api` 请求代理到本机 8000 端口。

## 质量检查

```powershell
uv run ruff check .
uv run pytest

Set-Location frontend
pnpm type-check
pnpm test
pnpm build
```

## 当前状态

第一阶段核心代码已经初始化，具备共享目录浏览和 Markdown（含 Mermaid 图表）、PDF、DOCX、图片、文本、视频只读预览能力，正在进行浏览器与真机体验验证。
