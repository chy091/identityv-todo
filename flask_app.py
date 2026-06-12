"""
PythonAnywhere WSGI 兼容入口
如果你的 WSGI 配置指向此文件，它会自动加载 app.py 中的 Flask 应用。
"""
import sys
import os

# 确保当前目录在 sys.path 中
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from app import app as application  # noqa: F401
