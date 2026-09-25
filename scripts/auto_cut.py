#!/usr/bin/env python3
"""Render an approved edit_plan.json with FFmpeg; never modifies source media."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


def jianying_ffmpeg() -> str | None:
    if os.name != "nt":
        return None
    try:
        import winreg
        roots = (
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        )
        for hive, key_name in roots:
            try:
                with winreg.OpenKey(hive, key_name) as root:
                    for index in range(winreg.QueryInfoKey(root)[0]):
                        try:
                            with winreg.OpenKey(root, winreg.EnumKey(root, index)) as entry:
                                display = str(winreg.QueryValueEx(entry, "DisplayName")[0])
                                if "剪映" not in display and "Jianying" not in display:
                                    continue
                                icon = str(winreg.QueryValueEx(entry, "DisplayIcon")[0]).strip('"').split(",", 1)[0]
                                install = Path(icon).parent
                                versions = sorted((p for p in install.iterdir() if p.is_dir()), reverse=True)
                                for version in versions:
                                    candidate = version / "ffmpeg.exe"
                                    if candidate.is_file():
                                        return str(candidate)
                        except OSError:
                            continue
            except OSError:
                continue
    except (ImportError, OSError):
        pass
    command = (
        "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new();"
        "$p=Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\JianyingPro' -ErrorAction SilentlyContinue;"
        "if($p){$p.DisplayIcon}"
    )
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command], capture_output=True, check=False)
    try:
        icon = result.stdout.decode("utf-8-sig").strip().strip('"').split(",", 1)[0]
        install = Path(icon).parent
        versions = sorted((p for p in install.iterdir() if p.is_dir()), reverse=True)
        for version in versions:
            candidate = version / "ffmpeg.exe"
            if candidate.is_file():
                return str(candidate)
    except (OSError, UnicodeDecodeError):
        pass
    return None


def executable(name: str) -> str:
    override = os.environ.get(name.upper() + "_PATH")
    found = override or shutil.which(name) or (jianying_ffmpeg() if name == "ffmpeg" else None)
    if not found:
        raise SystemExit(f"未找到 {name}。请安装 FFmpeg，或设置 {name.upper()}_PATH。")
    return found


def has_audio(ffmpeg: str, path: Path) -> bool:
    result = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path), "-t", "0.01", "-f", "null", "NUL" if os.name == "nt" else "/dev/null"], capture_output=True, check=False)
    return b"Audio:" in result.stderr


def encoder_args(ffmpeg: str) -> list[str]:
    encoders = subprocess.run([ffmpeg, "-hide_banner", "-encoders"], capture_output=True, check=False).stdout
    if b"libx264" in encoders:
        return ["-c:v", "libx264", "-preset", "medium", "-crf", "19"]
    if b"h264_mf" in encoders:
        return ["-c:v", "h264_mf", "-b:v", "8M"]
    if b"h264_nvenc" in encoders:
        return ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "20"]
    return ["-c:v", "mpeg4", "-q:v", "3"]


def project_file(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if root != candidate and root not in candidate.parents:
        raise SystemExit(f"计划引用了项目外文件：{relative}")
    if not candidate.is_file():
        raise SystemExit(f"素材不存在：{relative}")
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser(description="根据 edit_plan.json 渲染 9:16 粗剪")
    parser.add_argument("project", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.project.resolve()
    plan = json.loads((root / "edit_plan.json").read_text(encoding="utf-8"))
    segments = plan.get("segments") or []
    if not segments:
        raise SystemExit("edit_plan.json 没有 segments；请先完成素材分析和剪辑计划。")
    ffmpeg = executable("ffmpeg")
    output = (args.output or root / "output" / "rough-cut.mp4").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    inputs: list[str] = []
    filters: list[str] = []
    links: list[str] = []
    for i, segment in enumerate(segments):
        path = project_file(root, str(segment["source"]))
        start, end = float(segment["in"]), float(segment["out"])
        duration = end - start
        if start < 0 or duration <= 0:
            raise SystemExit(f"非法入出点：{segment}")
        inputs += ["-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(path)]
        filters.append(f"[{i}:v]setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p[v{i}]")
        if has_audio(ffmpeg, path):
            filters.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]")
        else:
            filters.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={duration:.3f}[a{i}]")
        links.append(f"[v{i}][a{i}]")
    filters.append("".join(links) + f"concat=n={len(segments)}:v=1:a=1[v][a]")
    command = [ffmpeg, "-hide_banner", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]", *encoder_args(ffmpeg), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)]
    result = subprocess.run(command, check=False)
    if result.returncode:
        raise SystemExit(result.returncode)
    print(output)


if __name__ == "__main__":
    main()
