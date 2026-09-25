---
name: douyin-auto-editor
description: Organize daily creator footage and turn it into a Douyin-oriented vertical short-video package: trend-informed edit strategy, beat sheet, rough cut, captions, cover copy, publishing copy, and review notes. Use when the user uploads raw video, images, audio, transcripts, or competitor references and asks to plan or produce a short-form social video. Do not use for long-form film editing or requests to copy another creator frame-for-frame.
---

# Douyin Auto Editor

Turn a creator's daily footage into an original, publishable 9:16 short-video package. Preserve source files and make all generated outputs traceable to an edit plan.

## Start from the project

Accept either files uploaded directly in the conversation or a project folder created by the bundled workbench. If the user gives only a project folder, read `project.json`, `edit_plan.json`, and `READY.md`, then inspect the files under `source/` and `references/`.

If the creator profile is incomplete, infer a conservative first version from the footage and record assumptions in the edit brief. Ask only when the missing choice would materially change the story, such as whether the content is educational, sales-oriented, or personal narrative.

## Produce the package

1. Inventory media without altering originals. Record duration, orientation, audio availability, obvious quality problems, and the useful moments in each file.
2. Build a current trend brief when internet access is available. Use recent, public examples from the creator's niche; separate observed facts from editorial inference. Never claim access to private platform metrics. If current references cannot be verified, use only the user's supplied references and say so.
3. Design an original edit around the footage. Read [references/editing-playbook.md](references/editing-playbook.md) for the scoring and pacing framework. References are for structure and audience expectation, not shot-for-shot imitation.
4. Write `edit_plan.json` before rendering. Follow [references/project-schema.md](references/project-schema.md). Every retained segment needs a source filename, source in/out time, purpose, and on-screen text if any.
5. Render a rough cut when a usable video renderer is available. Prefer the user's established editor; otherwise the bundled `scripts/auto_cut.py` can render a deterministic FFmpeg rough cut from an approved plan. On Windows it may reuse a capability-checked FFmpeg component bundled with Jianying Pro, but must not write Jianying's undocumented private draft format. Do not download software, publish, or overwrite files without authorization.
6. Verify the rendered output: 9:16 frame, no accidental black frames, intelligible audio, readable safe-zone text, captions matching speech, and duration close to the plan. Spot-check the opening, each transition, and the ending.
7. Deliver the video together with `edit_plan.json`, subtitle text/SRT when speech exists, three title options, cover copy, a concise caption, hashtags, and a short note explaining the hook and retention logic.

## Editorial guardrails

- Optimize for a clear promise and sustained attention, not guaranteed virality. Do not promise views, sales, or platform distribution.
- Keep claims supported by the footage or sources. Flag health, finance, legal, and product-performance claims for verification.
- Remove private data, bystanders who should not appear, copyrighted music without usage rights, and accidental background screens or documents.
- Preserve the creator's voice. Do not clone another creator's identity, watermark, captions, or distinctive assets.
- Default to one strong story per video. Put unused worthwhile moments in a reuse list instead of forcing them into the cut.

## Workbench

Run `scripts/workbench_server.py --root <project-storage-folder>` and open the shown local address. The workbench creates structured project folders and a ready-to-use invocation prompt. It does not publish content or silently transmit files.

When Jianying Pro is installed, the launcher opens it as the optional refinement and export surface. The workbench remains the source of truth for project metadata and the edit plan. Treat Jianying draft files as application-owned; only import media or a rendered rough cut through supported user-facing flows.
