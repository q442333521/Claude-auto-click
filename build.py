import PyInstaller.__main__
import os
from pathlib import Path

# 获取当前目录
current_dir = Path(__file__).parent

# 设置图标文件路径（如果有的话）
# icon_path = current_dir / "icon.ico"

# 设置打包参数
params = [
    'auto_click.py',  # 主程序文件
    '--onefile',      # 打包成单个文件
    '--noconsole',    # 不显示控制台窗口
    '--name=Claude自动点击器',  # 可执行文件名称
    # f'--icon={icon_path}',  # 如果有图标的话
    '--add-data=allow_button.png;.',  # 添加资源文件
]

# 执行打包
PyInstaller.__main__.run(params)
