#!/usr/bin/env python3
from pathlib import Path
import subprocess
import re
import textwrap

ROOT = Path(__file__).resolve().parent


def ensure_makefile():
    makefile = ROOT / "Makefile"
    if makefile.exists():
        content = makefile.read_text(encoding="utf-8")
    else:
        content = ""

    if "say-hello:" not in content:
        content += ("\n\n" if content else "") + textwrap.dedent("""\
        say-hello:
        \t@echo "Hello, World!"
        """)
        makefile.write_text(content, encoding="utf-8")
        print("Добавлен таргет say-hello в Makefile")
    else:
        print("Таргет say-hello уже есть в Makefile")


def ensure_workflows_dir():
    wf_dir = ROOT / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    return wf_dir


def create_hello_workflow(wf_dir: Path):
    path = wf_dir / "hello.yml"
    if not path.exists():
        path.write_text(textwrap.dedent("""\
        name: say-hello
        on: push

        jobs:
          say-hello:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - run: make say-hello
        """), encoding="utf-8")
        print(f"Создан {path}")
    else:
        print(f"{path} уже существует, пропускаем")


def create_ci_workflow(wf_dir: Path):
    path = wf_dir / "ci.yml"
    if not path.exists():
        path.write_text(textwrap.dedent("""\
        name: CI
        on: [push, pull_request]

        jobs:
          build:
            runs-on: ubuntu-latest

            steps:
              - uses: actions/checkout@v4

              - uses: actions/setup-node@v4
                with:
                  node-version: '18.x'
                  cache: 'npm'

              - run: make setup
              - run: make test
              - run: make lint

              - uses: hexlet-components/hello-from-hexlet-action@release
        """), encoding="utf-8")
        print(f"Создан {path}")
    else:
        print(f"{path} уже существует, пропускаем")


def detect_github_repo():
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None, None

    url = result.stdout.strip()
    m = re.search(r"github\\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)", url)
    if not m:
        return None, None
    return m.group("owner"), m.group("repo")


def ensure_badge():
    readme = ROOT / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
    else:
        content = ""

    if "actions/workflows/ci.yml/badge.svg" in content:
        print("Бейдж CI уже есть в README.md")
        return

    owner, repo = detect_github_repo()
    if not owner or not repo:
        print("Не удалось автоматически определить owner/repo из git remote.origin.url.")
        owner = input("Введите GitHub owner (user или org): ").strip()
        repo = input("Введите имя репозитория: ").strip()

    badge_line = f"![CI](https://github.com/{owner}/{repo}/actions/workflows/ci.yml/badge.svg)\n\n"

    if content.startswith("#"):
        lines = content.splitlines(keepends=True)
        new_content = lines[0] + "\n" + badge_line + "".join(lines[1:])
    else:
        new_content = badge_line + content

    readme.write_text(new_content, encoding="utf-8")
    print("Добавлен бейдж GitHub Actions в README.md")


def main():
    ensure_makefile()
    wf_dir = ensure_workflows_dir()
    create_hello_workflow(wf_dir)
    create_ci_workflow(wf_dir)
    ensure_badge()
    print("Готово. Не забудьте выполнить git add/commit/push.")


if __name__ == "__main__":
    main()
