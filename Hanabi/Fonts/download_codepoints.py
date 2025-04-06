# Download codepoints from Google Material Icons
# Auto Generated by download_codepoints.py By ZZBuAoYe
import os
import requests
import sys
import time

def download_codepoints():
    try:
        save_dir = os.path.join(os.path.dirname(__file__), 'icons')
        os.makedirs(save_dir, exist_ok=True)
        
        # 主要链接和备用链接
        urls = [
            "https://raw.githubusercontent.com/google/material-design-icons/master/font/MaterialIcons-Regular.codepoints",
            "https://github.com/google/material-design-icons/raw/master/font/MaterialIcons-Regular.codepoints",
            "https://cdn.jsdelivr.net/gh/google/material-design-icons/font/MaterialIcons-Regular.codepoints"
        ]
        
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        

        for url in urls:
            try:
                print(f"正在尝试从 {url} 下载...")
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                save_path = os.path.join(save_dir, 'codepoints')
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                    
                print(f"成功下载 codepoints 文件到: {save_path}")
                return True
                
            except Exception as e:
                print(f"从 {url} 下载失败: {str(e)}")
                print("尝试下一个链接...")
                time.sleep(1)
                continue
        
        raise Exception("所有下载链接都失败了")
        
    except Exception as e:
        print(f"下载 codepoints 文件失败: {str(e)}")
        return False

if __name__ == '__main__':
    success = download_codepoints()
    if not success:
        sys.exit(1) 