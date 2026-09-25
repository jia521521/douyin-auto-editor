# 项目结构与剪辑计划

工作台项目采用以下目录：

```text
project-id/
  project.json
  edit_plan.json
  READY.md
  source/
  references/
  output/
```

`project.json` 至少包含 `id`、`title`、`created_at`、`niche`、`goal`、`target_seconds`、`style`、`hook`、`reference_notes` 和 `files`。

`edit_plan.json` 的稳定字段：

```json
{
  "version": 1,
  "format": {"width": 1080, "height": 1920, "fps": 30},
  "target_seconds": 30,
  "strategy": {"promise": "", "hook": "", "payoff": "", "cta": ""},
  "segments": [
    {
      "source": "source/example.mp4",
      "in": 0.0,
      "out": 2.4,
      "purpose": "hook",
      "screen_text": ""
    }
  ],
  "titles": [],
  "cover_copy": "",
  "caption": "",
  "hashtags": [],
  "reuse_notes": []
}
```

时间单位为秒，`out` 必须大于 `in`。渲染前确认所有 `source` 都位于项目目录内；禁止通过 `..` 读取项目外文件。工作台生成的是待完善的初始计划，素材分析后应替换为真实入出点。
