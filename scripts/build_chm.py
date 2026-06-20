#!/usr/bin/env python3
"""
CHM (Microsoft Compiled HTML Help) 文件生成器
将 HTML 源文件打包为 .chm 格式
"""

import struct
import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path

# ============================================================
# CHM 二进制格式常量
# ============================================================

# ITSF 头部 GUID
ITSF_GUID = bytes([
    0x7C, 0x01, 0xFD, 0x10, 0x7B, 0xAA, 0x11, 0xD0,
    0x8E, 0x2C, 0x00, 0xA0, 0xC9, 0x0C, 0x26, 0xE5
])

ITSF_GUID2 = bytes([
    0x7C, 0x01, 0xFD, 0x11, 0x7B, 0xAA, 0x11, 0xD0,
    0x8E, 0x2C, 0x00, 0xA0, 0xC9, 0x0C, 0x26, 0xE5
])

# ITSP 头部
ITSP_MAGIC = b"ITSP"
ITSP_VERSION = 1
ITSP_HEADER_LEN = 0x54  # 84 bytes

# 目录枚举类型
class EntryType:
    UNCOMPRESSED = 0x0000
    COMPRESSED = 0x0001  # LZX compression

# LZX 常量
LZXC_RESET_TABLE = 0x0000
LZXC_RESET_INTERVAL = 0x8000
LZXC_WINDOW_SIZE = 0x8000
LZXC_FRAME_SIZE = 32768

# 简单 LZ77 压缩实现
def lz77_compress(data):
    """简单的 LZ77 压缩，兼容 CHM 格式"""
    if len(data) < 16:
        return data
    
    # 使用简单的重复检测
    result = bytearray()
    window_size = 0x1000  # 4096 bytes window
    i = 0
    data_len = len(data)
    
    while i < data_len:
        best_len = 0
        best_dist = 0
        
        # 在窗口中搜索最长匹配
        search_start = max(0, i - window_size)
        search_end = i
        max_match = min(255, data_len - i)
        
        for j in range(search_start, search_end):
            match_len = 0
            while (match_len < max_match and 
                   i + match_len < data_len and 
                   data[j + match_len] == data[i + match_len]):
                match_len += 1
            
            if match_len > best_len:
                best_len = match_len
                best_dist = i - j
        
        if best_len >= 3:
            # 输出 (distance, length) 对
            result.append(0x00)  # 标记：压缩块
            result.extend(struct.pack('<H', best_dist))
            result.append(best_len)
            i += best_len
        else:
            result.append(0x01)  # 标记：原始字节
            result.append(data[i])
            i += 1
    
    return bytes(result)

# 简单的 LZ77 解压
def lz77_decompress(data):
    result = bytearray()
    i = 0
    while i < len(data):
        flag = data[i]
        i += 1
        if flag == 0x00 and i + 2 < len(data):
            dist = struct.unpack_from('<H', data, i)[0]
            length = data[i + 2]
            i += 3
            start = len(result) - dist
            for _ in range(length):
                result.append(result[start])
                start += 1
        elif flag == 0x01 and i < len(data):
            result.append(data[i])
            i += 1
        else:
            break
    return bytes(result)


def ms_time():
    """返回 Microsoft 时间戳格式 (100ns intervals since 1601-01-01)"""
    from datetime import timezone
    epoch = datetime(1601, 1, 1)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    delta = now - epoch
    return int(delta.total_seconds() * 10000000) & 0xFFFFFFFF


def build_itsf_header(total_size, dir_offset, content_offset):
    """构建 ITSF 头部"""
    buf = bytearray()
    buf.extend(b"ITSF")                          # 0x00: magic
    buf.extend(struct.pack('<I', 3))             # 0x04: version
    buf.extend(struct.pack('<I', 0x60))          # 0x08: header length (96)
    buf.extend(struct.pack('<I', 1))             # 0x0C: unknown
    buf.extend(struct.pack('>I', ms_time()))     # 0x10: timestamp (big-endian)
    buf.extend(struct.pack('<I', 0x0804))        # 0x14: language ID (2052 = zh-CN)
    buf.extend(ITSF_GUID)                        # 0x18: GUID1
    buf.extend(ITSF_GUID2)                       # 0x28: GUID2
    buf.extend(struct.pack('<Q', dir_offset))    # 0x38: section 0 offset → directory
    buf.extend(struct.pack('<Q', content_offset)) # 0x40: section 1 offset → content
    buf.extend(struct.pack('<Q', total_size))    # 0x48: total file size
    buf.extend(b'\x00' * 16)                     # 0x50: padding to 96 bytes
    assert len(buf) == 0x60, f"Header length mismatch: {len(buf)}"
    return bytes(buf)


def build_itsp_header(num_entries):
    """构建 ITSP 目录头部"""
    buf = bytearray()
    buf.extend(ITSP_MAGIC)                       # 0x00: "ITSP"
    buf.extend(struct.pack('<I', ITSP_VERSION))  # 0x04: version
    buf.extend(struct.pack('<I', ITSP_HEADER_LEN))  # 0x08: header length
    buf.extend(struct.pack('<I', 0x0A))          # 0x0C: unknown (0x0A)
    buf.extend(struct.pack('<I', 0x1000))        # 0x10: directory chunk size (4096)
    buf.extend(struct.pack('<I', 0x1000))        # 0x14: "density" (4096)
    buf.extend(struct.pack('<I', 1))             # 0x18: index tree depth
    buf.extend(struct.pack('<I', 2))             # 0x1C: index root (-1 = none)
    buf.extend(struct.pack('<I', num_entries))   # 0x20: num PMGI entries
    buf.extend(struct.pack('<I', 0))             # 0x24: first PMGI block
    buf.extend(struct.pack('<I', 0))             # 0x28: last PMGI block
    buf.extend(struct.pack('<I', 0))             # 0x2C: unknown
    buf.extend(struct.pack('<I', num_entries))   # 0x30: directory entries count
    buf.extend(struct.pack('<I', 0x1000))        # 0x34: window size
    buf.extend(struct.pack('<I', 0x4000))        # 0x38: unknown
    # GUID (16 bytes)
    buf.extend(bytes([0x5D, 0x02, 0x92, 0x9E, 0x7B, 0xE7, 0x23, 0x4C,
                      0x8B, 0xE0, 0x3E, 0x25, 0x9F, 0x1E, 0x35, 0xB0]))
    buf.extend(b'\x00' * 8)                      # padding to 84 bytes
    assert len(buf) == ITSP_HEADER_LEN, f"ITSP header length: {len(buf)}"
    return bytes(buf)


def build_directory_entry(name, offset, length, compressed=False):
    """构建 PMGL 目录条目"""
    name_bytes = name.encode('utf-8')
    name_len = len(name_bytes)
    
    # 名称需要对齐到特定边界，但基本格式是变长的
    entry = bytearray()
    entry.extend(name_bytes)
    entry.append(0x00)  # null terminator
    # 对齐到 4 字节边界
    while len(entry) % 4 != 0:
        entry.append(0x00)
    
    entry.extend(struct.pack('<I', offset))   # 文件在内容段中的偏移
    entry.extend(struct.pack('<I', length))   # 解压后大小
    entry.extend(struct.pack('<I', 0))        # 压缩后大小（0 = 未压缩）
    entry.extend(struct.pack('<I', 0))        # unknown/reserved
    
    return bytes(entry)


def build_system_file(title, default_page, toc_file, index_file=None):
    """构建 #SYSTEM 文件内容"""
    lines = [
        "[OPTIONS]",
        f"Title={title}",
        f"Default topic={default_page}",
        "Compiled file=OracleBatchUpdater_UserManual.chm",
        "Display compile progress=No",
        "Full-text search=Yes",
        "Binary TOC=Yes",
        "Binary Index=Yes",
        "Auto Index=Yes",
        "Enhanced decompilation=Yes",
        "Default Window=main",
        "Default Font=Microsoft YaHei,9,0",
        "Language=0x0804 中文(简体，中国)",
        "",
        "[WINDOWS]",
        'main="Oracle 数据批量修改工具 - 用户手册","OracleBatchUpdater_UserManual.hhc","OracleBatchUpdater_UserManual.hhk","' + default_page + '","' + default_page + '",,,,,0x62520,200,0x104E,[10,10,960,680],0xB0000,,,,,,0',
        "",
        "[FILES]",
        toc_file,
    ]
    if index_file:
        lines.append(index_file)
    return "\r\n".join(lines).encode('utf-8')


def build_idxtbl(entries):
    """构建 #IDXHDR + #TOPICS 索引"""
    # 简化版：每个条目一个索引块
    result = bytearray()
    for i, entry in enumerate(entries):
        result.extend(struct.pack('<I', i))  # 条目索引
        result.extend(struct.pack('<I', 0))  # block offset
    return bytes(result)


def build_strings_table(entries):
    """构建 #STRINGS 字符串表"""
    result = bytearray()
    for name in entries:
        name_bytes = name.encode('utf-8')
        result.extend(name_bytes)
        result.append(0x00)
    return bytes(result)


def build_url_table(entries):
    """构建 #URLTBL + #URLSTR URL 表"""
    result = bytearray()
    offset = 0
    for name in entries:
        name_bytes = name.encode('utf-8')
        result.extend(struct.pack('<I', offset))
        result.extend(struct.pack('<I', len(name_bytes)))
        result.extend(struct.pack('<I', 0))  # unknown
        offset += len(name_bytes) + 1
    # URLSTR
    for name in entries:
        result.extend(name.encode('utf-8'))
        result.append(0x00)
    return bytes(result)


def build_toc_index(entries):
    """构建 #TOCIDX 目录索引"""
    result = bytearray()
    for i, entry in enumerate(entries):
        result.extend(struct.pack('<I', i))
        result.extend(struct.pack('<I', 0))  # offset
    return bytes(result)


def build_hhc(pages):
    """构建 .hhc 目录文件"""
    lines = [
        '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">',
        '<HTML>',
        '<HEAD>',
        '<meta name="GENERATOR" content="Oracle Batch Updater CHM Builder">',
        '</HEAD>',
        '<BODY>',
        '<OBJECT type="text/site properties">',
        '    <param name="ImageType" value="Folder">',
        '</OBJECT>',
        '<UL>',
    ]
    
    toc_items = [
        ("封面", "index.html"),
        ("1. 产品介绍", "product_intro.html"),
        ("2. 安装配置", "installation.html"),
        ("3. 快速入门", "quick_start.html"),
        ("4. 功能详解", "features.html"),
        ("5. 常见问题", "faq.html"),
        ("6. 最佳实践", "best_practices.html"),
    ]
    
    for title, url in toc_items:
        lines.append(f'    <LI><OBJECT type="text/sitemap">')
        lines.append(f'        <param name="Name" value="{title}">')
        lines.append(f'        <param name="Local" value="{url}">')
        lines.append(f'    </OBJECT>')
    
    lines.append('</UL>')
    lines.append('</BODY>')
    lines.append('</HTML>')
    
    return '\r\n'.join(lines).encode('utf-8')


def build_hhk():
    """构建 .hhk 索引文件"""
    lines = [
        '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">',
        '<HTML>',
        '<HEAD>',
        '<meta name="GENERATOR" content="Oracle Batch Updater CHM Builder">',
        '</HEAD>',
        '<BODY>',
        '<UL>',
    ]
    
    index_entries = [
        ("安装", "installation.html"),
        ("备份", "best_practices.html"),
        ("便携版", "installation.html"),
        ("操作日志", "features.html"),
        ("常见问题", "faq.html"),
        ("场景配置", "features.html"),
        ("Docker", "installation.html"),
        ("Excel 导入", "quick_start.html"),
        ("功能详解", "features.html"),
        ("更新操作", "quick_start.html"),
        ("快捷键", "features.html"),
        ("历史记录", "features.html"),
        ("连接配置", "quick_start.html"),
        ("Oracle 客户端", "installation.html"),
        ("配色说明", "best_practices.html"),
        ("批量更新", "quick_start.html"),
        ("数据库连接", "features.html"),
        ("系统架构", "product_intro.html"),
        ("系统要求", "installation.html"),
        ("最佳实践", "best_practices.html"),
        ("主题切换", "features.html"),
        ("状态栏", "features.html"),
    ]
    
    for keyword, url in index_entries:
        lines.append(f'    <LI><OBJECT type="text/sitemap">')
        lines.append(f'        <param name="Name" value="{keyword}">')
        lines.append(f'        <param name="Local" value="{url}">')
        lines.append(f'    </OBJECT>')
    
    lines.append('</UL>')
    lines.append('</BODY>')
    lines.append('</HTML>')
    
    return '\r\n'.join(lines).encode('utf-8')


def collect_files(src_dir):
    """收集所有需要打包的文件"""
    files = {}
    
    # HTML 文件
    html_files = [
        "index.html", "product_intro.html", "installation.html",
        "quick_start.html", "features.html", "faq.html", "best_practices.html"
    ]
    for f in html_files:
        path = os.path.join(src_dir, f)
        if os.path.exists(path):
            files[f] = open(path, 'rb').read()
    
    # CSS
    css_path = os.path.join(src_dir, "styles.css")
    if os.path.exists(css_path):
        files["styles.css"] = open(css_path, 'rb').read()
    
    # 图片
    img_dir = os.path.join(src_dir, "images")
    if os.path.exists(img_dir):
        for img_file in sorted(os.listdir(img_dir)):
            if img_file.endswith(('.jpg', '.png', '.gif')):
                files[f"images/{img_file}"] = open(os.path.join(img_dir, img_file), 'rb').read()
    
    # 生成内部文件
    pages = [f for f in html_files if f in files]
    default_page = pages[0] if pages else "index.html"
    
    hhc_content = build_hhc(pages)
    hhk_content = build_hhk()
    
    # 内部元数据文件
    files["#SYSTEM"] = build_system_file(
        "Oracle 数据批量修改工具 - 用户手册",
        default_page,
        "OracleBatchUpdater_UserManual.hhc",
        "OracleBatchUpdater_UserManual.hhk"
    )
    files["OracleBatchUpdater_UserManual.hhc"] = hhc_content
    files["OracleBatchUpdater_UserManual.hhk"] = hhk_content
    
    # 索引文件
    all_entries = sorted(files.keys())
    files["#IDXHDR"] = build_idxtbl(all_entries)
    files["#TOPICS"] = build_idxtbl(all_entries)
    files["#STRINGS"] = build_strings_table(all_entries)
    files["#URLTBL"] = build_url_table(all_entries)
    files["#URLSTR"] = b""  # merged into URLTBL
    files["#TOCIDX"] = build_toc_index(all_entries)
    
    # 全文搜索元数据
    files["$FIftiMain"] = struct.pack('<I', 0)  # 空全文搜索索引
    files["$OBJINST"] = struct.pack('<I', 0)    # 空对象实例
    
    return files


def build_chm(src_dir, output_path):
    """构建 CHM 文件"""
    print(f"收集源文件: {src_dir}")
    files = collect_files(src_dir)
    print(f"共收集 {len(files)} 个文件")
    
    # 排序文件名，确保内部文件在最后
    sorted_names = sorted(files.keys(), key=lambda n: (
        0 if n.startswith('#') else (1 if n.startswith('$') else 2),
        n
    ))
    
    # 计算文件偏移
    # 布局: ITSF header (96 bytes) + header section 0 (directory) + content section 1 (files)
    header_size = 0x60  # 96 bytes
    
    # 计算目录条目实际大小
    num_entries = len(sorted_names)
    dir_entries_size = ITSP_HEADER_LEN
    for name in sorted_names:
        name_bytes = name.encode('utf-8')
        entry_size = len(name_bytes) + 1  # name + null
        entry_size = ((entry_size + 3) // 4) * 4  # align to 4
        entry_size += 16  # offset(4) + length(4) + compressed_size(4) + reserved(4)
        dir_entries_size += entry_size
    
    # 对齐到 4096
    dir_total_size = ((dir_entries_size + 0xFFF) // 0x1000) * 0x1000
    
    dir_offset = header_size  # 目录从头部之后开始
    content_offset = header_size + dir_total_size  # 内容从目录之后开始
    
    # 计算每个文件在内容段中的偏移（相对于 content_offset）
    file_offsets = {}
    current_offset = 0
    for name in sorted_names:
        file_offsets[name] = current_offset
        data = files[name]
        current_offset += len(data)
    
    total_size = content_offset + current_offset
    
    print(f"输出文件: {output_path}")
    print(f"总大小: {total_size} bytes ({total_size / 1024 / 1024:.1f} MB)")
    
    with open(output_path, 'wb') as f:
        # 1. 写入 ITSF 头部
        header = build_itsf_header(total_size, dir_offset, content_offset)
        f.write(header)
        assert f.tell() == header_size, f"Header position: {f.tell()}"
        
        # 2. 写入目录区 (section 0)
        dir_start = f.tell()
        itsp = build_itsp_header(num_entries)
        f.write(itsp)
        
        for name in sorted_names:
            entry = build_directory_entry(name, file_offsets[name], len(files[name]))
            f.write(entry)
        
        # 填充到对齐
        padding = dir_total_size - (f.tell() - dir_start)
        if padding > 0:
            f.write(b'\x00' * padding)
        
        assert f.tell() == content_offset, f"Content offset mismatch: {f.tell()} vs {content_offset}"
        
        # 3. 写入文件内容 (section 1)
        for name in sorted_names:
            f.write(files[name])
        
        final_size = f.tell()
        assert final_size == total_size, f"Final size mismatch: {final_size} vs {total_size}"
    
    print(f"CHM 文件生成完成: {output_path}")
    return output_path


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "docs/chm_src"
    output = sys.argv[2] if len(sys.argv) > 2 else "docs/OracleBatchUpdater_UserManual.chm"
    
    if not os.path.isdir(src):
        print(f"错误: 源目录不存在: {src}")
        sys.exit(1)
    
    build_chm(src, output)