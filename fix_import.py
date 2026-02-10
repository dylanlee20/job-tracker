# 读取文件
with open('scrapers/base_scraper.py', 'r') as f:
    lines = f.readlines()

# 找到导入部分，添加 os
import_section_end = 0
for i, line in enumerate(lines):
    if line.startswith('from') or line.startswith('import'):
        import_section_end = i
    elif import_section_end > 0 and line.strip() == '':
        break

# 检查是否已有 import os
has_os_import = any('import os' in line for line in lines[:import_section_end+5])

if not has_os_import:
    # 在导入部分添加 import os
    lines.insert(import_section_end + 1, 'import os\n')
    
    with open('scrapers/base_scraper.py', 'w') as f:
        f.writelines(lines)
    
    print("✓ 已添加 os 模块导入！")
else:
    print("✓ os 模块已存在，无需修改")
