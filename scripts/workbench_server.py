#!/usr/bin/env python3
"""Local, dependency-free upload workbench for the douyin-auto-editor skill."""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import secrets
import subprocess
import sys
try:
    import winreg
except ImportError:  # Non-Windows workbenches simply omit editor detection.
    winreg = None  # type: ignore[assignment]
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

SKILL_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = SKILL_ROOT / "assets" / "workbench" / "index.html"
MAX_UPLOAD = 20 * 1024 * 1024 * 1024


def detect_jianying() -> dict | None:
    if winreg is None:
        return None
    registry_roots = (
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    )
    for hive, key_name in registry_roots:
        try:
            with winreg.OpenKey(hive, key_name) as root:
                for index in range(winreg.QueryInfoKey(root)[0]):
                    try:
                        with winreg.OpenKey(root, winreg.EnumKey(root, index)) as entry:
                            name = str(winreg.QueryValueEx(entry, "DisplayName")[0])
                            if "剪映" not in name and "Jianying" not in name:
                                continue
                            version = str(winreg.QueryValueEx(entry, "DisplayVersion")[0])
                            icon = str(winreg.QueryValueEx(entry, "DisplayIcon")[0]).strip('"').split(",", 1)[0]
                            exe = Path(icon).parent / "JianyingPro.exe"
                            return {"name": name, "version": version, "path": str(exe), "available": exe.is_file()}
                    except OSError:
                        continue
        except OSError:
            continue
    if sys.platform == "win32":
        command = (
            "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new();"
            "$p=Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\JianyingPro' -ErrorAction SilentlyContinue;"
            "if($p){@{name=$p.DisplayName;version=$p.DisplayVersion;icon=$p.DisplayIcon}|ConvertTo-Json -Compress}"
        )
        result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command], capture_output=True, check=False)
        try:
            info = json.loads(result.stdout.decode("utf-8-sig"))
            exe = Path(str(info["icon"]).strip('"').split(",", 1)[0]).parent / "JianyingPro.exe"
            return {"name": info["name"], "version": info["version"], "path": str(exe), "available": exe.is_file()}
        except (KeyError, OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass
    return None


def safe_name(value: str, fallback: str = "file") -> str:
    value = Path(value).name.strip().replace("\x00", "")
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", value)
    return value[:180] or fallback


def project_id(title: str) -> str:
    stem = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", title).strip("-")[:24]
    return f"{datetime.now():%Y%m%d}-{stem or 'project'}-{secrets.token_hex(2)}"


class Workbench:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, pid: str) -> Path:
        if not re.fullmatch(r"[\w\-\u4e00-\u9fff]+", pid):
            raise ValueError("invalid project id")
        path = (self.root / pid).resolve()
        if path.parent != self.root:
            raise ValueError("project escapes storage root")
        return path

    def create(self, payload: dict) -> dict:
        title = str(payload.get("title") or "今日素材").strip()[:80]
        pid = project_id(title)
        folder = self.path(pid)
        for name in ("source", "references", "output"):
            (folder / name).mkdir(parents=True, exist_ok=False)
        data = {
            "id": pid,
            "title": title,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "niche": str(payload.get("niche") or "待确认")[:80],
            "goal": str(payload.get("goal") or "涨粉")[:80],
            "target_seconds": max(8, min(180, int(payload.get("target_seconds") or 30))),
            "style": str(payload.get("style") or "真实、有节奏")[:120],
            "hook": str(payload.get("hook") or "")[:300],
            "reference_notes": str(payload.get("reference_notes") or "")[:2000],
            "files": [],
            "status": "uploading",
        }
        self.write_json(folder / "project.json", data)
        self.write_json(folder / "edit_plan.json", {
            "version": 1,
            "format": {"width": 1080, "height": 1920, "fps": 30},
            "target_seconds": data["target_seconds"],
            "strategy": {"promise": "待分析", "hook": data["hook"], "payoff": "待分析", "cta": "待分析"},
            "segments": [], "titles": [], "cover_copy": "", "caption": "", "hashtags": [], "reuse_notes": []
        })
        return {**data, "folder": str(folder)}

    @staticmethod
    def write_json(path: Path, data: dict) -> None:
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)

    def list(self) -> list[dict]:
        projects = []
        for item in sorted(self.root.iterdir(), reverse=True):
            meta = item / "project.json"
            if item.is_dir() and meta.exists():
                try:
                    data = json.loads(meta.read_text(encoding="utf-8"))
                    projects.append({k: data.get(k) for k in ("id", "title", "created_at", "niche", "goal", "status", "files")})
                except (OSError, json.JSONDecodeError):
                    continue
        return projects


class Handler(BaseHTTPRequestHandler):
    server_version = "CreatorWorkbench/1.0"

    @property
    def wb(self) -> Workbench:
        return self.server.workbench  # type: ignore[attr-defined]

    def json_response(self, data: object, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1024 * 1024:
            raise ValueError("request too large")
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = INDEX_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == "/api/projects":
            self.json_response({"projects": self.wb.list(), "storage": str(self.wb.root)})
        elif parsed.path == "/api/health":
            self.json_response({"ok": True, "storage": str(self.wb.root), "editor": detect_jianying()})
        else:
            self.json_response({"error": "not found"}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/projects":
                self.json_response(self.wb.create(self.read_json()), 201)
                return
            upload = re.fullmatch(r"/api/projects/([^/]+)/files", parsed.path)
            if upload:
                self.handle_upload(unquote(upload.group(1)), parse_qs(parsed.query))
                return
            finish = re.fullmatch(r"/api/projects/([^/]+)/finish", parsed.path)
            if finish:
                self.handle_finish(unquote(finish.group(1)))
                return
            self.json_response({"error": "not found"}, 404)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            self.json_response({"error": str(exc)}, 400)

    def handle_upload(self, pid: str, query: dict) -> None:
        folder = self.wb.path(pid)
        meta_path = folder / "project.json"
        if not meta_path.exists():
            raise ValueError("project not found")
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_UPLOAD:
            raise ValueError("invalid file size")
        name = safe_name((query.get("name") or [""])[0], "material.bin")
        kind = (query.get("kind") or ["source"])[0]
        target_dir = folder / ("references" if kind == "reference" else "source")
        target = target_dir / name
        if target.exists():
            target = target.with_name(f"{target.stem}-{secrets.token_hex(2)}{target.suffix}")
        remaining = length
        with target.open("xb") as stream:
            while remaining:
                chunk = self.rfile.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise ValueError("upload interrupted")
                stream.write(chunk)
                remaining -= len(chunk)
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        rel = target.relative_to(folder).as_posix()
        data["files"].append({"path": rel, "bytes": length, "type": self.headers.get("Content-Type", mimetypes.guess_type(name)[0] or "application/octet-stream")})
        self.wb.write_json(meta_path, data)
        self.json_response({"ok": True, "path": rel, "bytes": length})

    def handle_finish(self, pid: str) -> None:
        folder = self.wb.path(pid)
        meta_path = folder / "project.json"
        if not meta_path.exists():
            raise ValueError("project not found")
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        if not data.get("files"):
            raise ValueError("请先上传至少一个素材文件")
        data["status"] = "ready"
        self.wb.write_json(meta_path, data)
        prompt = f"使用 $douyin-auto-editor 处理工作台项目：{folder}。分析素材，完善剪辑计划，完成粗剪并交付发布物料。"
        (folder / "READY.md").write_text("# 项目已就绪\n\n" + prompt + "\n", encoding="utf-8")
        self.json_response({"ok": True, "folder": str(folder), "prompt": prompt})

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stdout.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    parser = argparse.ArgumentParser(description="启动自媒体爆款剪辑工作台")
    parser.add_argument("--root", type=Path, default=Path.cwd() / "creator-projects", help="项目存储目录")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.workbench = Workbench(args.root)  # type: ignore[attr-defined]
    print(f"工作台已启动：http://{args.host}:{args.port}")
    print(f"素材只保存在本机：{server.workbench.root}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
