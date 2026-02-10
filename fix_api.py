# 修复 API 路由
with open('routes/api.py', 'r') as f:
    content = f.read()

# 修复 trigger_scrape 函数
old_code = """    try:
        data = request.get_json() if request.is_json else {}
        company = data.get('company')"""

new_code = """    try:
        data = {}
        if request.is_json:
            try:
                data = request.get_json() or {}
            except:
                data = {}
        company = data.get('company')"""

content = content.replace(old_code, new_code)

with open('routes/api.py', 'w') as f:
    f.write(content)

print("✓ API 修复完成！")
