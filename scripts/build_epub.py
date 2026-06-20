#!/usr/bin/env python3
"""
EPUB 文件生成器
将 docs/chm_src/ 下的 HTML 源文件打包为 .epub 格式，供安卓掌阅等阅读器使用。

掌阅 APP 不支持 CHM 格式，但支持 EPUB。本脚本不依赖外部库，仅使用标准库。
"""

import os
import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "docs" / "chm_src"
OUT_DIR = BASE_DIR / "docs"

# 阅读顺序（与 CHM 目录一致）
SPINE = [
    ("index.html", "封面"),
    ("product_intro.html", "产品简介"),
    ("features.html", "功能特性"),
    ("installation.html", "安装说明"),
    ("quick_start.html", "快速入门"),
    ("best_practices.html", "最佳实践"),
    ("faq.html", "常见问题"),
]


def extract_title(html_path: Path) -> str:
    """从 <title> 标签提取标题，失败时返回文件名。"""
    try:
        text = html_path.read_text(encoding="utf-8")
        m = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return html_path.stem


def read_file_bytes(path: Path) -> bytes:
    return path.read_bytes()


def build_epub(output_name: str = "DBForge_UserManual.epub") -> Path:
    """生成 EPUB 文件。"""
    out_path = OUT_DIR / output_name
    out_path.parent.mkdir(parents=True, exist_ok=True)

    book_uuid = str(uuid.uuid4())
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    version = "v2.8.0"

    # 收集资源文件
    html_files = [name for name, _ in SPINE]
    image_files = []
    if (SRC_DIR / "images").exists():
        image_files = sorted(
            p.name for p in (SRC_DIR / "images").iterdir() if p.is_file()
        )
    has_css = (SRC_DIR / "styles.css").exists()

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype 必须不压缩且放在第一个
        zf.writestr("mimetype", "application/epub+zip", zipfile.ZIP_STORED)

        # META-INF/container.xml
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""
        zf.writestr("META-INF/container.xml", container_xml)

        # OEBPS/content.opf
        manifest_items = []
        for html in html_files:
            manifest_items.append(
                f'    <item id="{Path(html).stem}" href="{html}" media-type="application/xhtml+xml"/>'
            )
        if has_css:
            manifest_items.append(
                '    <item id="styles" href="styles.css" media-type="text/css"/>'
            )
        for idx, img in enumerate(image_files):
            ext = Path(img).suffix.lower()
            mt = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
            }.get(ext, "image/jpeg")
            manifest_items.append(
                f'    <item id="img{idx}" href="images/{img}" media-type="{mt}"/>'
            )

        spine_items = []
        for html, default_title in SPINE:
            title = extract_title(SRC_DIR / html) or default_title
            spine_items.append(
                f'    <itemref idref="{Path(html).stem}" linear="yes"/>'
            )

        content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:{book_uuid}</dc:identifier>
    <dc:title>DBForge - 用户手册</dc:title>
    <dc:language>zh-CN</dc:language>
    <dc:creator>Oracle Updater Team</dc:creator>
    <dc:date>{modified[:10]}</dc:date>
    <meta property="dcterms:modified">{modified}</meta>
    <meta name="version" content="{version}"/>
  </metadata>
  <manifest>\n""" + "\n".join(manifest_items) + """
  </manifest>
  <spine toc="ncx">\n""" + "\n".join(spine_items) + """
  </spine>
</package>
"""
        zf.writestr("OEBPS/content.opf", content_opf)

        # OEBPS/toc.ncx
        nav_points = []
        play_order = 1
        for html, default_title in SPINE:
            title = extract_title(SRC_DIR / html) or default_title
            nav_points.append(
                f"""    <navPoint id="navPoint-{play_order}" playOrder="{play_order}">
      <navLabel><text>{title}</text></navLabel>
      <content src="{html}"/>
    </navPoint>"""
            )
            play_order += 1

        toc_ncx = f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
  <head>
    <meta name="dtb:uid" content="urn:uuid:{book_uuid}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>DBForge - 用户手册</text></docTitle>
  <navMap>\n""" + "\n".join(nav_points) + """
  </navMap>
</ncx>
"""
        zf.writestr("OEBPS/toc.ncx", toc_ncx)

        # OEBPS/toc.xhtml (EPUB3 导航文档)
        toc_entries = []
        for html, default_title in SPINE:
            title = extract_title(SRC_DIR / html) or default_title
            toc_entries.append(f'      <li><a href="{html}">{title}</a></li>')

        toc_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <meta charset="UTF-8"/>
  <title>目录</title>
  <link rel="stylesheet" href="styles.css"/>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>目录</h1>
    <ol>
""" + "\n".join(toc_entries) + """
    </ol>
  </nav>
</body>
</html>
"""
        zf.writestr("OEBPS/toc.xhtml", toc_xhtml)

        # 复制 HTML 文件
        for html in html_files:
            src = SRC_DIR / html
            data = read_file_bytes(src)
            # 简单修复：将本地路径调整为 EPUB 内相对路径（CHM 源通常已经是相对的）
            zf.writestr(f"OEBPS/{html}", data)

        # 复制 CSS
        if has_css:
            zf.writestr("OEBPS/styles.css", read_file_bytes(SRC_DIR / "styles.css"))

        # 复制图片
        if image_files:
            for img in image_files:
                zf.writestr(
                    f"OEBPS/images/{img}",
                    read_file_bytes(SRC_DIR / "images" / img),
                )

    print(f"EPUB 已生成: {out_path}")
    print(f"文件大小: {out_path.stat().st_size / 1024:.1f} KB")
    return out_path


if __name__ == "__main__":
    build_epub()
