# Cross Read

Cross Read 是一个运行在 Windows 电脑上的局域网只读文件阅读器。电脑启动服务后，iPhone、iPad 或桌面浏览器可以通过一个网址浏览电脑上的共享目录，并直接阅读文档、图片、源码、音视频等内容。

它解决的是一个很具体的问题：文件留在电脑上，不需要先传到手机，也不需要为 Markdown、PDF 或其他格式单独安装阅读器。

## 功能概览

- 自动发现 Windows 已发布的普通 SMB 共享文件夹。
- 支持额外配置没有发布为 SMB 共享的本地目录。
- 只读浏览：不提供上传、编辑、删除、移动、复制或重命名。
- 目录逐级浏览、面包屑导航和文件名筛选。
- 支持搜索当前目录，或递归搜索当前目录及所有子文件夹。
- Markdown 标题目录、当前章节高亮、代码高亮、Mermaid 流程图和本地相对图片。
- PDF 翻页、缩放和文本搜索。
- DOCX 只读预览。
- CSV、XLSX 表格预览，支持切换工作表。
- PPTX 按幻灯片提取文字摘要。
- 图片自适应预览，源码和纯文本按扩展名语法高亮。
- MP4、MOV 等视频和 WAV、MP3 等音频使用浏览器原生播放器，并支持 Range 分段读取。
- 移动端优先的 Apple 风格界面，兼容 iPhone Safari 和桌面浏览器。
- 浅色、深色和跟随系统主题设置。

## 使用方式

```text
Windows 电脑配置共享目录并启动服务
                    |
                    v
          Safari 打开电脑局域网地址
                    |
                    v
       选择共享文件夹并逐级浏览文件
                    |
                    v
       使用对应阅读器直接查看内容
```

电脑和手机需要连接到同一个局域网。电脑必须保持开机并运行 Cross Read 服务；大文件不会先完整传输到手机，视频和音频会按浏览器请求分段读取。

## 支持的文件格式

| 类别 | 支持格式 | 说明 |
| --- | --- | --- |
| Markdown | `.md`、`.markdown` | 标题目录、代码高亮、Mermaid、相对路径图片 |
| 文本与源码 | `.txt`、`.log`、`.json`、`.jsonl`、`.yaml`、`.yml`、`.toml`、`.ini`、`.cfg`、`.conf`、`.py`、`.js`、`.ts`、`.tsx`、`.vue`、`.html`、`.css`、`.xml`、`.sql`、`.sh`、`.ps1`、`.c`、`.cpp`、`.java`、`.go`、`.rs` 等 | 只读显示，按扩展名进行语法高亮；HTML 显示源码，不执行 |
| PDF | `.pdf` | PDF.js 浏览器内预览 |
| Word | `.docx` | 浏览器内只读渲染；复杂版式不保证与 Word 完全一致 |
| 表格 | `.csv`、`.xlsx` | 表格数据和多工作表预览；复杂样式、图表和交互不保证保留 |
| 演示文稿 | `.pptx` | 提取并显示每张幻灯片的文字摘要，不还原完整视觉版式 |
| 图片 | `.png`、`.jpg`、`.jpeg`、`.gif`、`.webp`、`.svg` | 浏览器原生预览和缩放 |
| 视频 | `.mp4`、`.mov`、`.m4v` | HTML5 流式播放；是否能播放取决于内部编码，H.264 + AAC 兼容性最好 |
| 音频 | `.wav`、`.mp3`、`.m4a`、`.aac`、`.flac`、`.ogg`、`.opus` | HTML5 流式播放；是否能播放取决于浏览器和内部编码 |

`.doc` 等旧版 Word 格式暂不解析，建议先转换为 `.docx`。不支持的文件类型会显示说明，不提供下载入口。

## 安全边界

- 后端只允许访问已发现或配置的共享根目录。
- 客户端只能提交共享 ID 和共享目录内的相对路径，不能读取电脑绝对路径。
- 路径会进行规范化和越界检查，符号链接或 junction 不能逃出共享根目录。
- 默认隐藏以 `.` 开头的文件，并忽略 `.git`、`__pycache__` 等目录。
- API 只开放 `GET`、`HEAD` 和必要的 `OPTIONS` 请求，不提供文件修改接口。
- 服务适合家庭或可信局域网使用。不要直接把端口暴露到公网；需要外网访问时，应使用 Tailscale、WireGuard 等安全组网方案。

## 环境要求

- Windows 10/11
- Python 3.12
- [uv](https://docs.astral.sh/uv/)：Python 依赖和项目命令管理
- Node.js 与 pnpm：仅在开发或重新构建前端时需要

最终运行时只需要 Python 环境和构建后的静态页面，不需要单独启动 Node.js 服务。

## 快速开始

### 1. 创建配置文件

在项目根目录执行：

```powershell
Copy-Item config.example.yaml config.yaml
```

默认配置会自动发现 Windows 已发布的普通 SMB 共享。系统和管理共享（例如 `ADMIN$`、`C$`、`IPC$`）会自动排除。

如果需要额外加入没有设置为 Windows 共享的目录，可以编辑 `config.yaml`：

```yaml
server:
  host: "0.0.0.0"
  port: 8000

discovery:
  windows_smb: true

shares:
  - id: "documents"
    name: "文档"
    path: "D:/Documents"
```

Windows 中新增或取消共享后，刷新 Cross Read 首页即可同步共享列表。

### 2. 安装依赖并构建前端

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

电脑浏览器访问：

```text
http://127.0.0.1:8000
```

在 Windows 上使用 `ipconfig` 查看电脑的局域网 IPv4 地址。iPhone 与电脑连接同一 Wi-Fi 后，在 Safari 中访问：

```text
http://电脑局域网IP:8000
```

例如：`http://192.168.0.100:8000`。

如果 Windows 防火墙首次拦截 Python 或端口访问，需要允许 Python 在专用网络中通信。

## 开发模式

后端和前端可以分别运行：

```powershell
# 终端一：后端
uv run cross-read --reload

# 终端二：前端
Set-Location frontend
pnpm dev
```

开发前端默认运行在 `http://127.0.0.1:5173`，Vite 会将 `/api` 请求代理到后端的 8000 端口。

## 质量检查

```powershell
uv run ruff check src tests
uv run pytest

Set-Location frontend
pnpm type-check
pnpm test
pnpm build
```

## 项目结构

```text
cross-read/
├── src/cross_read/        # FastAPI 后端、路径安全、文件流和静态资源
├── frontend/              # Vue 3 + TypeScript 前端
├── tests/                 # 后端自动化测试
├── docs/MVP.md            # 产品边界、技术方案和验收标准
├── config.example.yaml    # 配置示例
└── pyproject.toml         # uv/Python 项目配置
```

## 文档

- [MVP 产品与技术方案](docs/MVP.md)

## 当前状态

第一阶段已经完成：局域网共享目录发现、只读浏览、递归搜索、Markdown/PDF/DOCX/表格/PPTX/图片/文本/源码/音视频预览，以及移动端和桌面端适配。后续可以在此基础上继续完善 Windows 托盘程序、访问密码和安装包等桌面化能力。
