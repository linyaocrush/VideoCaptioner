<div align="center">
  <img src="./docs/images/logo.png" alt="VideoCaptioner Logo" width="120">
  <h1>VideoCaptioner</h1>
  <p><strong>基于大语言模型的视频字幕处理工具</strong></p>
  <p>语音识别 · 字幕优化 · 智能翻译 · 视频合成 — 一站式处理</p>
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

## 本版本改进

> 基于 [WEIFENG2333/VideoCaptioner](https://github.com/WEIFENG2333/VideoCaptioner) 的个人修改版本，以下为本版本独有功能。

<table>
  <tr>
    <td width="240" align="center"><b>ASS 字幕支持系统字体</b></td>
    <td>ASS 渲染模式的字体下拉框现在显示所有系统安装的字体，不再局限于内置字体。圆角背景模式保留 PIL 可用性验证。</td>
  </tr>
  <tr>
    <td width="240" align="center"><b>OpenAI 多配置管理</b></td>
    <td>设置页 LLM 配置新增「配置管理」下拉框，支持保存、切换、重命名多个 OpenAI 兼容服务商配置，切换时自动填充 API Key / Base URL / Model。</td>
  </tr>
  <tr>
    <td width="240" align="center"><b>字幕保存格式可选</b></td>
    <td>设置页「保存配置」新增「字幕保存格式」选项，全流程处理完成后可选择仅保存 SRT、仅保存 ASS 或两者都保存。默认两者都保存。</td>
  </tr>
</table>

<br>

## 快速开始

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

> 免费功能（必剪语音识别、必应/谷歌翻译）**无需任何配置，安装即用**。

<br>

## CLI 命令行

```bash
# 语音转录（免费，无需 API Key）
uv run videocaptioner transcribe video.mp4 --asr bijian

# 字幕翻译（免费必应翻译）
uv run videocaptioner subtitle input.srt --translator bing --target-language en

# 全流程：转录 → 优化 → 翻译 → 合成
uv run videocaptioner process video.mp4 --target-language ja

# 字幕烧录到视频
uv run videocaptioner synthesize video.mp4 -s subtitle.srt

# 下载在线视频
uv run videocaptioner download "https://youtube.com/watch?v=xxx"
```

<details>
<summary><b>所有 CLI 命令一览</b></summary>

<br>

| 命令 | 说明 |
|------|------|
| `gui` | 打开桌面版 |
| `transcribe` | 语音转字幕（`faster-whisper` `whisper-api` `bijian` `jianying` `whisper-cpp`） |
| `subtitle` | 字幕优化/翻译（`llm` `bing` `google`） |
| `dub` | 根据字幕生成配音音轨或配音视频 |
| `synthesize` | 字幕烧录到视频（软字幕/硬字幕） |
| `process` | 全流程处理 |
| `download` | 下载 YouTube、B站等平台视频 |
| `config` | 配置管理（`show` `set` `get` `path` `init`） |

运行 `uv run videocaptioner <命令> --help` 查看完整参数。

</details>

<br>

## LLM API 配置

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

## 开发

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
uv run pytest tests/test_cli/ -q           # CLI 测试
uv run pytest tests/ -q                    # 全部测试

# 构建
uv build                                   # Python 包
python scripts/build_desktop.py            # 桌面安装包 (PyInstaller)
```

<br>

<div align="center">

**[GPL-3.0](LICENSE)**

</div>
