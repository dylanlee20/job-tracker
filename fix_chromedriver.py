import os

# 读取原文件
with open('scrapers/base_scraper.py', 'r') as f:
    content = f.read()

# 找到 init_driver 方法中的 Service 初始化部分
old_code = """            # 使用 webdriver-manager 自动管理 ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)"""

new_code = """            # 使用 webdriver-manager 自动管理 ChromeDriver
            driver_path = ChromeDriverManager().install()
            
            # 修复：如果路径指向错误的文件，找到正确的 chromedriver
            if 'THIRD_PARTY_NOTICES' in driver_path or not os.path.exists(driver_path):
                driver_dir = os.path.dirname(driver_path)
                # 在目录中查找真正的 chromedriver
                for root, dirs, files in os.walk(driver_dir):
                    for file in files:
                        if file == 'chromedriver' and os.access(os.path.join(root, file), os.X_OK):
                            driver_path = os.path.join(root, file)
                            break
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)"""

content = content.replace(old_code, new_code)

# 写回文件
with open('scrapers/base_scraper.py', 'w') as f:
    f.write(content)

print("✓ ChromeDriver 路径修复完成！")
