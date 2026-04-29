#!/usr/bin/env python3
"""
更新 _redirects 中的后端地址
用法：python scripts/update_redirects.py <new-backend-url>
示例：python scripts/update_redirects.py caviar-crm-backend.onrender.com
"""
import sys
import re

REDIRECTS_PATH = __file__.parent.parent / "frontend" / "public" / "_redirects"


def main():
    if len(sys.argv) < 2:
        print("用法: python update_redirects.py <backend-url>")
        print("示例: python update_redirects.py caviar-crm-backend.onrender.com")
        sys.exit(1)

    backend_url = sys.argv[1].rstrip("/")

    with open(REDIRECTS_PATH, "r") as f:
        content = f.read()

    # 替换 /api/* 行（保留 200 proxy flag）
    new_line = f"/api/*        https://{backend_url}/api/:splat   200"
    updated = re.sub(r"/api/\*.*:splat\s+200", new_line, content)

    with open(REDIRECTS_PATH, "w") as f:
        f.write(updated)

    print(f"✅ 已更新 _redirects → https://{backend_url}")


if __name__ == "__main__":
    main()