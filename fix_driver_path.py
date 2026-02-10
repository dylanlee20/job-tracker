import os

with open('scrapers/base_scraper.py', 'r') as f:
    content = f.read()

# 查找并替换 ChromeDriverManager 调用
old_pattern = """            # 使用 webdriver-manager 自动管理 ChromeDriver
            driver_path = ChromeDriverManager().install()
            
            # 修复：如果路径不正确，查找真正的chromedriver
            if not os.path.exists(driver_path) or 'THIRD_PARTY_NOTICES' in driver_path:
                # 获取目录
                driver_dir = os.path.dirname(driver_path)
                
                # 在目录及其父目录中查找chromedriver
                for root, dirs, files in os.walk(os.path.dirname(driver_dir)):
                    for file in files:
                        if file == 'chromedriver':
                            potential_path = os.path.join(root, file)
                            # 检查是否有执行权限
                            if os.access(potential_path, os.X_OK):
                                driver_path = potential_path
                                self.logger.info(f"Found chromedriver at: {driver_path}")
                                break
                    if os.access(driver_path, os.X_OK):
                        break
            
            service = Service(driver_path)"""

new_pattern = """            # 使用 webdriver-manager 自动管理 ChromeDriver
            try:
                driver_path = ChromeDriverManager().install()
                
                # 修复：webdriver-manager 可能返回错误的文件路径
                if 'THIRD_PARTY_NOTICES' in driver_path or not os.path.exists(driver_path):
                    # 获取缓存目录
                    cache_base = os.path.expanduser('~/.wdm/drivers/chromedriver')
                    
                    # 查找真正的 chromedriver 可执行文件
                    found = False
                    for root, dirs, files in os.walk(cache_base):
                        if 'chromedriver' in files:
                            potential_path = os.path.join(root, 'chromedriver')
                            # 检查是否是可执行文件（不是文本文件）
                            try:
                                # 给予执行权限
                                os.chmod(potential_path, 0o755)
                                # 验证是否是二进制文件
                                if os.path.getsize(potential_path) > 1000000:  # 大于1MB
                                    driver_path = potential_path
                                    self.logger.info(f"Found chromedriver at: {driver_path}")
                                    found = True
                                    break
                            except:
                                continue
                    
                    if not found:
                        raise Exception("Could not find valid chromedriver executable")
                
                service = Service(driver_path)
            except Exception as e:
                self.logger.error(f"ChromeDriver setup failed: {e}")
                raise"""

content = content.replace(old_pattern, new_pattern)

with open('scrapers/base_scraper.py', 'w') as f:
    f.write(content)

print("✓ ChromeDriver 路径逻辑已更新！")
