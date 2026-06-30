<div align="center">
  <img src="./resource/assets/logo.png" alt="VideoCaptioner Logo" width="120">
  <h1>VideoCaptioner</h1>
  <p><strong>基于大语言模型的视频字幕处理工具</strong></p>
  <p>语音识别 · 字幕优化 · 智能翻译 · 视频合成 · AI 配音 — 一站式处理</p>
  <br>

  <a href="https://github.com/WEIFENG2333/VideoCaptioner"><img src="https://img.shields.io/badge/基于-WEIFENG2333%2FVideoCaptioner-2ea44f?style=for-the-badge&logo=github&logoColor=white" alt="上游原版"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/linyaocrush/VideoCaptioner/stargazers"><img src="https://img.shields.io/github/stars/linyaocrush/VideoCaptioner?style=for-the-badge&logo=github&logoColor=white" alt="Stars"></a>
  <a href="https://github.com/linyaocrush/VideoCaptioner/issues"><img src="https://img.shields.io/github/issues/linyaocrush/VideoCaptioner?style=for-the-badge&logo=github&logoColor=white" alt="Issues"></a>

  <br><br>

  <table>
    <td align="center"><a href="https://github.com/WEIFENG2333/VideoCaptioner/blob/master/README.md">查看上游原版 README</a></td>
  </table>
</div>

<br>

<div align="center">
  <table>
    <tr>
      <td align="center"><img src="https://h1.appinn.me/file/1731487410170_preview1.png" width="420"></td>
      <td align="center"><img src="https://h1.appinn.me/file/1731487410832_preview2.png" width="420"></td>
    </tr>
  </table>
</div>

<br>

---

## 📌 关于本分支

> 基于 [WEIFENG2333/VideoCaptioner](https://github.com/WEIFENG2333/VideoCaptioner) 的个人维护分支。

上游原版已更新至 **2.0 版本**，对 UI 界面和底层架构做了较大重构。我个人更习惯 1.x 版本的经典界面风格，因此决定**保留原版 UI 框架**，同时将 2.0 版本中的新功能逐一移植到本分支。

如果你也喜欢经典的界面布局，又想要新版本的功能，这个分支可能会适合你。

<br>

## ✨ 从 2.0 移植的功能

<table>
  <tr>
    <th width="180" align="center">功能</th>
    <th align="center">说明</th>
  </tr>
  <tr>
    <td align="center"><b>🤖 阿里云百炼 FunASR</b></td>
    <td>新增阿里云百炼 FunAudio-ASR 语音识别引擎，支持 30+ 语言和词级时间戳，纯 HTTP 实现无需 SDK。</td>
  </tr>
  <tr>
    <td align="center"><b>🎙️ AI 配音</b></td>
    <td>独立的配音页面，支持 Edge TTS（免费）、Gemini TTS、SiliconFlow CosyVoice 三大提供商。包含声音选择、试听、声音克隆（SiliconFlow）。</td>
  </tr>
  <tr>
    <td align="center"><b>🩺 系统诊断</b></td>
    <td>诊断页面一键检查 FFmpeg、ASR 服务、视频下载、配音服务等系统依赖和配置状态，快速定位问题。</td>
  </tr>
  <tr>
    <td align="center"><b>⬇️ 模型管理 CLI</b></td>
    <td><code>videocaptioner models list/download</code> 命令管理本地 ASR 模型，支持多镜像兜底下载（HuggingFace → hf-mirror → ModelScope）。</td>
  </tr>
  <tr>
    <td align="center"><b>🔧 配音配置构建器</b></td>
    <td>统一的配音参数构建器，CLI 和 GUI 共享同一套预设解析、提供商校验、时序对齐和混音策略。</td>
  </tr>
  <tr>
    <td align="center"><b>🔄 批量并发处理</b></td>
    <td>批量处理页面新增并发数设置（1-3），可同时处理多个任务，充分利用带宽和算力。</td>
  </tr>
  <tr>
    <td align="center"><b>🧵 通用 Worker 基类</b></td>
    <td>新增 WorkerThread 基类，统一管理线程取消、超时、错误信号，简化异步任务开发。</td>
  </tr>
  <tr>
    <td align="center"><b>📦 依赖更新</b></td>
    <td>openai 更新至 2.44.0，yt-dlp 更新至 2026.6.9，与新版本保持一致。</td>
  </tr>
</table>

<br>

## 🛠️ 本版本原有改进

<table>
  <tr>
    <th width="180" align="center">功能</th>
    <th align="center">说明</th>
  </tr>
  <tr>
    <td align="center"><b>ASS 字幕支持系统字体</b></td>
    <td>ASS 渲染模式的字体下拉框显示所有系统安装字体，不再局限于内置字体。</td>
  </tr>
  <tr>
    <td align="center"><b>OpenAI 多配置管理</b></td>
    <td>设置页 LLM 配置支持保存、切换、重命名多个 OpenAI 兼容服务商配置，一键切换。</td>
  </tr>
  <tr>
    <td align="center"><b>字幕保存格式可选</b></td>
    <td>全流程处理完成后可选择仅保存 SRT、仅保存 ASS 或两者都保存。</td>
  </tr>
  <tr>
    <td align="center"><b>缓存清理按钮</b></td>
    <td>设置页新增缓存清理按钮，实时显示缓存占用，一键清除 ASR、翻译、TTS 和 LLM 缓存。</td>
  </tr>
</table>

<br>

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/linyaocrush/VideoCaptioner.git
cd VideoCaptioner
uv sync
```

### 运行

```bash
uv run videocaptioner                 # 启动桌面版 GUI
uv run videocaptioner --help          # 查看 CLI 帮助
```

> 💡 免费功能（必剪语音识别、必应/谷歌翻译）**无需任何配置，安装即用**。

<br>

## 💻 CLI 命令行

```bash
# 语音转录（免费，无需 API Key）
uv run videocaptioner transcribe video.mp4 --asr bijian

# 字幕翻译（免费必应翻译）
uv run videocaptioner subtitle input.srt --translator bing --target-language en

# 全流程：转录 → 优化 → 翻译 → 合成
uv run videocaptioner process video.mp4 --target-language ja

# 字幕烧录到视频
uv run videocaptioner synthesize video.mp4 -s subtitle.srt

# 配音
uv run videocaptioner dub subtitle.srt -v video.mp4 --preset edge-cn-xiaoxiao

# 模型管理
uv run videocaptioner models list                          # 列出可用 ASR 模型
uv run videocaptioner models download whisper-cpp tiny     # 下载模型

# 下载在线视频
uv run videocaptioner download "https://youtube.com/watch?v=xxx"

# 系统诊断
uv run videocaptioner doctor --check-api
```

<details>
<summary><b>所有 CLI 命令一览</b></summary>

<br>

| 命令 | 说明 |
|------|------|
| `gui` | 打开桌面版 |
| `transcribe` | 语音转字幕（`faster-whisper` `whisper-api` `bijian` `jianying` `whisper-cpp` `fun-asr`） |
| `subtitle` | 字幕优化/翻译（`llm` `bing` `google`） |
| `dub` | 根据字幕生成配音音轨或配音视频 |
| `synthesize` | 字幕烧录到视频（软字幕/硬字幕） |
| `process` | 全流程处理 |
| `download` | 下载 YouTube、B站等平台视频 |
| `models` | 管理本地 ASR 模型（`list` / `download`） |
| `config` | 配置管理（`show` `set` `get` `path` `init`） |
| `doctor` | 系统诊断 |

运行 `uv run videocaptioner <命令> --help` 查看完整参数。

</details>

<br>

## 🔑 LLM API 配置

LLM 仅用于字幕优化和大模型翻译，免费功能无需配置。支持所有 OpenAI 兼容接口的服务商：

| 服务商 | 官网 |
|--------|------|
| SiliconCloud | [cloud.siliconflow.cn](https://cloud.siliconflow.cn/i/HF95kaoz) |
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com) |

在软件设置中选择 **OpenAI 兼容**，填入 API Base URL 和 API Key。可使用「配置管理」保存多个服务商配置，一键切换。

需要 LLM 功能时 CLI 配置：

```bash
uv run videocaptioner config set llm.api_key <your-key>
uv run videocaptioner config set llm.api_base https://api.openai.com/v1
uv run videocaptioner config set llm.model gpt-4o-mini
```

<br>

## 🎯 功能路线

<details>
<summary><b>支持的 ASR 引擎</b></summary>

| 引擎 | 类型 | 免费 | 说明 |
|------|------|------|------|
| B 接口（必剪） | 在线 API | ✅ | Bilibili 内置接口，需网络 |
| J 接口（剪映） | 在线 API | ✅ | 剪映内置接口，需网络 |
| Whisper API | 在线 API | ❌ | OpenAI 兼容接口 |
| **阿里云百炼 FunASR** | 在线 API | ❌ | 新增，支持 30+ 语言 |
| whisper-cpp | 本地 | ✅ | 需下载模型 |
| FasterWhisper | 本地 | ✅ | 需下载模型 |

</details>

<details>
<summary><b>支持的 TTS/配音提供商</b></summary>

| 提供商 | 免费 | 声音克隆 | 说明 |
|--------|------|----------|------|
| Edge TTS | ✅ | ❌ | 免费，18+ 中文/英语声音 |
| Gemini TTS | ❌ | ❌ | Google TTS，需 API Key |
| SiliconFlow CosyVoice | ❌ | ✅ | 支持中文声音克隆，需 API Key |

</details>

<br>

## 🧪 开发

```bash
# 安装依赖
uv sync

# 运行
uv run videocaptioner                      # GUI
uv run videocaptioner --help               # CLI

# 代码检查
uv run ruff check videocaptioner/          # Lint
uv run pyright                             # 类型检查

# 测试
uv run pytest tests/ -q                    # 全部测试

# 构建
uv build                                   # Python 包
```

<br>

---

<div align="center">

**📄 [GPL-3.0](LICENSE)** · 感谢上游作者 [WEIFENG2333](https://github.com/WEIFENG2333/VideoCaptioner) 的开源贡献

</div>
