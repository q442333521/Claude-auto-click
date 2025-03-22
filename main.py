import os
import sys
from pathlib import Path
from utils.admin_utils import run_as_admin
from gui.main_gui import AutoClickerGUI

if __name__ == "__main__":
    run_as_admin()  # 检查并提升权限
    app = AutoClickerGUI()
    app.run()
