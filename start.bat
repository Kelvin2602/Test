@echo off
chcp 65001 > nul
title Telegram Attendance Bot

echo ===================================
echo    KHỞI ĐỘNG BOT ĐIỂM DANH
echo ===================================
echo.

:: Kiểm tra Python đã được cài đặt chưa
python --version > nul 2>&1
if errorlevel 1 (
    echo [CẢNH BÁO] Không tìm thấy Python. Vui lòng cài đặt Python 3.8 trở lên.
    pause
    exit
)

:: Kiểm tra và tạo môi trường ảo nếu chưa có
if not exist "venv" (
    echo [INFO] Đang tạo môi trường ảo...
    python -m venv venv
    echo [OK] Đã tạo môi trường ảo
)

:: Kích hoạt môi trường ảo
echo [INFO] Kích hoạt môi trường ảo...
call venv\Scripts\activate

:: Cài đặt các thư viện cần thiết
echo [INFO] Kiểm tra và cài đặt thư viện...
pip install -r requirements.txt > nul

:: Chạy setup_config nếu chưa có file config
if not exist "config\config.ini" (
    echo [INFO] Đang tạo file cấu hình...
    python setup_config.py
)

:: Khởi động bot
echo [INFO] Khởi động bot...
echo.
python run.py

:: Nếu bot dừng, giữ cửa sổ để xem lỗi
pause 