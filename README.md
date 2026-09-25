# Douyin Auto Editor

一个面向自媒体创作者的 Codex Skill 与本地素材工作台。它把每日视频、图片、音频、口播稿和对标参考整理成结构化项目，辅助生成抖音竖屏短视频的剪辑策略、镜头计划、粗剪、字幕和发布物料。

> 本项目不承诺“必爆”，不自动发布作品，也不会静默上传素材。素材默认只保存在本机。

## 能做什么

- 一次选择或拖入多份原始素材与对标素材
- 建立统一的 `project.json` 与 `edit_plan.json`
- 规划前 3 秒钩子、节奏、转折、结尾和复用镜头
- 使用 FFmpeg 按剪辑计划生成 9:16 粗剪
- 交付字幕、标题、封面文案、发布文案、标签和审片记录
- Windows 下检测剪映专业版，并将其作为可选的精剪与导出工具

## 项目结构

```text
douyin-auto-editor/
├─ SKILL.md
├─ agents/openai.yaml
├─ assets/workbench/index.html
├─ references/
│  ├─ editing-playbook.md
│  └─ project-schema.md
├─ scripts/
│  ├─ workbench_server.py
│  ├─ auto_cut.py
│  ├─ start_workbench.ps1
│  └─ launch_jianying.ps1
└─ 启动剪辑台.cmd
```

## 环境要求

- Python 3.10 或更高版本
- Codex（使用完整 Skill 工作流时）
- FFmpeg（生成粗剪时需要）
- 剪映专业版（可选，仅用于后续精剪）

工作台服务本身只使用 Python 标准库，不需要安装额外 Python 包。

## 安装为 Codex Skill

把仓库放入个人 Skill 目录：

```text
%USERPROFILE%\.codex\skills\douyin-auto-editor
```

重新启动 Codex 后，可使用：

```text
使用 $douyin-auto-editor 处理我今天上传的素材，先给出剪辑策略，再输出成片和发布文案。
```

## 启动本地工作台

Windows 用户可双击 `启动剪辑台.cmd`，也可以运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_workbench.ps1
```

工作台默认地址为 <http://127.0.0.1:8765/>，项目默认保存到“文档/Codex/自媒体剪辑台项目”。

如需自定义路径：

```powershell
$env:DOUYIN_EDITOR_PROJECTS = 'D:\CreatorProjects'
$env:PYTHON_PATH = 'C:\Python312\python.exe' # 仅在 Python 不在 PATH 时需要
.\scripts\start_workbench.ps1
```

也可以直接启动服务：

```powershell
python .\scripts\workbench_server.py --root D:\CreatorProjects --port 8765
```

## 生成粗剪

先由 Codex 或人工完成项目目录中的 `edit_plan.json`，再运行：

```powershell
python .\scripts\auto_cut.py D:\CreatorProjects\项目目录
```

脚本优先使用环境变量 `FFMPEG_PATH` 指定的 FFmpeg，其次查找系统 PATH；Windows 下还可以检测剪映安装目录中的兼容 FFmpeg 组件。脚本不会修改原始素材。

## 隐私与版权

- 不要把真实素材目录、人物隐私、API Key 或平台 Cookie 提交到 GitHub。
- 发布前确认出镜授权、场地授权、音乐版权和路人处理。
- 对标作品仅用于学习结构和受众预期，不应逐帧复刻他人的作品、身份、水印或独特资产。
- 本项目与抖音、字节跳动、剪映或 OpenAI 无官方隶属或背书关系。

## 参与贡献

欢迎提交 Issue 与 Pull Request。建议修改后至少运行：

```powershell
python -m py_compile .\scripts\workbench_server.py .\scripts\auto_cut.py
python .\scripts\workbench_server.py --help
python .\scripts\auto_cut.py --help
```

## License

[MIT](LICENSE)
