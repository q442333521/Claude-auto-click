import PyInstaller.__main__
import os
from pathlib import Path

# 获取当前目录
current_dir = Path(__file__).parent

# 设置排除的模块和包
excludes = [
    'matplotlib', 'notebook', 'scipy', 'pandas',
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
    'IPython', 'jupyter', 'jedi', 'pytz',
    'setuptools', 'docutils', 'sphinx',
    'selenium', 'qtpy', 'geopandas', 'sqlalchemy'
]

# 设置需要包含的资源文件
resources = [
    '1.png', '2.png', '3.png', '4.png', 'allow_button.png'
]

# 添加资源文件参数
resource_params = []
for resource in resources:
    resource_path = current_dir / resource
    if resource_path.exists():
        resource_params.append(f'--add-data={resource};.')

# 设置打包参数
params = [
    'main.py',        # 主程序文件（现在改为main.py）
    '--onefile',      # 打包成单个文件
    '--noconsole',    # 不显示控制台窗口
    '--name=Claude自动点击器',  # 可执行文件名称
    '--clean',        # 清理临时文件
    '--strip',        # 减小二进制文件大小
    '--noupx',        # 禁用UPX压缩（可能会导致某些杀毒软件误报）
    f'--exclude-module={",".join(excludes)}',  # 排除不需要的模块
]

# 添加资源文件参数
params.extend(resource_params)

# 添加模块包含
params.extend([
    '--add-data=utils;utils',
    '--add-data=core;core',
    '--add-data=gui;gui',
])

# 执行打包
print("开始打包Claude自动点击器...")
PyInstaller.__main__.run(params)
print("打包完成！")
