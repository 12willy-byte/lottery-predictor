@echo off
chcp 65001 >nul
title 彩票智能选号系统 v2.0
cd /d "%~dp0"

echo.
echo ============================================
echo     彩票智能选号系统 v2.0
echo     数据驱动 | 智能分析 | 科学选号
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python
    pause
    exit /b 1
)

echo [系统] 数据库状态:
python -c "from database import init_db; init_db(); from database import get_ssq_count as s, get_dlt_count as d; print(f"  双色球(SSQ): {s()}\" + "\u671f"); print(f"  大乐透(DLT): {d()}\" + "\u671f"); print(f"  总计: {s()+d()}\" + "\u671f")"

if not exist "data\backtest_cache.json" (
    echo.
    echo [系统] 正在生成回测缓存...
    python -c "exec(open(\"backtester.py\").read().split(\"if __name__\")[0]); import json, os; r1=run_ssq_backtest(); r2=run_dlt_backtest(); json.dump({\"ssq\":r1[\"stats\"],\"dlt\":r2[\"stats\"]}, open(os.path.join(\"data\",\"backtest_cache.json\"),\"w\"),ensure_ascii=False)"
    if errorlevel 1 echo [提示] 回测较耗时，启动后点"回测分析"按钮即可
) else (
    echo [系统] 回测缓存已就绪
)

echo.
echo [启动] 正在加载图形界面...
echo.

python main.py

if errorlevel 1 (
    echo [错误] 程序异常，请检查依赖
    echo   pip install requests beautifulsoup4
    pause
)
