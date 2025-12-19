@echo off
:: 切换编码为UTF-8，避免中文输出乱码
chcp 65001 >nul 2>&1

:: 核心：切换到bat文件所在目录（确保无论从哪启动，都以bat目录为基准）
cd /d "%~dp0"

:: 第一步：激活虚拟环境
echo ==============================
echo 正在激活Python虚拟环境...
echo ==============================
:: 调用虚拟环境激活脚本（call 确保激活后继续执行后续命令）
call venv\Scripts\activate.bat

:: 检查激活是否失败
if errorlevel 1 (
    echo [91m❌ 错误：虚拟环境激活失败！[0m
    echo 请检查以下问题：
    echo 1. bat文件同目录是否存在「venv」文件夹；
    echo 2. venv\Scripts\activate.bat 是否存在；
    echo 3. 是否为Python venv创建的虚拟环境。
    pause
    exit /b 1
)

:: 第二步：运行main.py
echo ==============================
echo [92m✅ 虚拟环境激活成功！[0m
echo 正在运行main.py...
echo ==============================
:: 运行同目录的main.py（虚拟环境激活后，python命令自动指向环境内的Python）
python main.py

:: 检查main.py运行是否失败
if errorlevel 1 (
    echo [91m❌ 错误：main.py运行失败！[0m
    echo 请检查：
    echo 1. bat文件同目录是否存在main.py；
    echo 2. 虚拟环境内是否安装了main.py依赖；
    echo 3. main.py是否有语法/运行错误。
    pause
    exit /b 1
)

:: 运行成功提示
echo ==============================
echo [92m✅ main.py运行完成！[0m
echo ==============================

:: 防止运行完直接闪退（按任意键关闭窗口）
pause

:: 可选：退出虚拟环境（无需手动退出，窗口关闭后自动退出）
:: deactivate