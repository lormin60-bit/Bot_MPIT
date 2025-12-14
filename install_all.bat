@echo off
echo Установка всех библиотек...
echo.

py -3.10 -m pip install python-telegram-bot==20.7
py -3.10 -m pip install moviepy==1.0.3
py -3.10 -m pip install gTTS==2.4.0
py -3.10 -m pip install Pillow==10.2.0

echo.
echo Установка завершена!
echo Запускайте бота: python bot.py
pause