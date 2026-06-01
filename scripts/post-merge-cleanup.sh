#!/bin/bash
# 合并上游更新后运行此脚本，删除不需要的文件
# 用法: bash scripts/post-merge-cleanup.sh

cd "$(dirname "$0")/.."

# 删除不需要的目录和文件
rm -rf docs/ skills/ .github/ISSUE_TEMPLATE/
rm -f VideoCaptioner.spec
rm -f scripts/build_desktop.py scripts/smoke_desktop.py
rm -f scripts/run.bat scripts/run.sh
rm -f scripts/trans-compile.sh scripts/trans-extract.sh scripts/translate_llm.py

# 删除 workflow 文件（如果上游重新引入）
rm -rf .github/workflows/

echo "清理完成。请检查 git status 后提交。"
