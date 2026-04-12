# ruff: noqa: E501
# ruff: noqa: E501
import sys

path = "C:/Users/jichu/Downloads/mcp_obsidian/vault/wiki/analyses/logistics_issue_project_lightning_2024-10-01_10.md"  # noqa: E501
with open(path, encoding="utf-8") as f:
    content = f.read()

# Using print directly will still fail with cp949 encode error in Windows cmd, so encode it
sys.stdout.buffer.write(content.encode("utf-8"))
