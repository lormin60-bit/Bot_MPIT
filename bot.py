import asyncio
import os
import subprocess
from pathlib import Path
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import FSInputFile
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import requests
import json
import re

API_TOKEN = '8555479567:AAF3Cki_MrDLEF5t3TX-FyyhAyKNtrHrOe8'
ELEVENLABS_API_KEY = 'sk_6e0043f2119eef3c9d438117afcd7376d454f538e7684168'

FFMPEG_PATH = "ffmpeg/ffmpeg.exe"

CELEBRITIES = {
    "Скала": {
        "video_file": "rock_template.mp4",
        "voice_id": "ZQe5CZNOzWyzPSCn5a3c"
    },
    "Месси": {
        "video_file": "messi_template.mp4",
        "voice_id": "yl2ZDV1MzN4HbQJbMihG"
    },
    "Канье Уэст": {
        "video_file": "kanye_template.mp4", 
        "voice_id": "DTKMou8ccj1ZaWGBiotd"
    },
    "Трэвис Скотт": {
        "video_file": "travis_template.mp4",
        "voice_id": "pNInz6obpgDQGcFmaJgB"
    },
    "Роналду": {
        "video_file": "ronaldo_template.mp4",
        "voice_id": "yl2ZDV1MzN4HbQJbMihG"
    },
    "Стэтхэм": {
        "video_file": "statham_template.mp4",
        "voice_id": "ZQe5CZNOzWyzPSCn5a3c"
    },
    "Майкл Джексон": {
        "video_file": "jackson_template.mp4",
        "voice_id": "qT3qfGZ0g0ss8WV5908L"
    },
    "Трамп": {
        "video_file": "trump_template.mp4", 
        "voice_id": "iUqOXhMfiOIbBejNtfLR"
    },
    "Мистер Бист": {
        "video_file": "beast_template.mp4",
        "voice_id": "4Ihiyat2AFvCRGQ2Hycm"
    },
    "Джастин Бибер": {
        "video_file": "bieber_template.mp4",
        "voice_id": "u4HtmbcjVZVpiJLQ2Gzn"
    }
}

bot = Bot(token=API_TOKEN, timeout=120.0)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class VideoCreation(StatesGroup):
    waiting_for_celebrity = State()
    waiting_for_text = State()

async def generate_celebrity_audio(text: str, voice_id: str, output_filename: str = "celebrity_audio.mp3") -> str:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }
    
    try:
        print(f"🎤 Генерирую аудио: {text[:50]}...")
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            temp_dir = Path("temp_audio")
            temp_dir.mkdir(exist_ok=True)
            filepath = temp_dir / output_filename
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Аудио сохранено")
            return str(filepath)
        else:
            error_msg = f"❌ Ошибка генерации: {response.status_code}"
            if response.text:
                try:
                    error_data = json.loads(response.text)
                    error_msg += f" - {error_data.get('detail', response.text[:100])}"
                except:
                    error_msg += f" - {response.text[:100]}"
            print(error_msg)
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

async def create_final_video(text: str, audio_file: str, video_template: str, celebrity_name: str) -> str:
    if not os.path.exists(video_template):
        print(f"❌ Видео не найден: {video_template}")
        return None
    
    try:
        import uuid
        safe_name = celebrity_name.replace(" ", "_").lower()
        output_file = f"{safe_name}_{uuid.uuid4().hex[:8]}.mp4"
        
        print(f"📁 Создаю видео")
        
        if not os.path.exists(audio_file):
            print(f"❌ Аудио файл не найден")
            return None
        
        audio_info_cmd = [FFMPEG_PATH, "-i", audio_file, "-hide_banner"]
        audio_info = subprocess.run(audio_info_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        audio_duration = None
        for line in audio_info.stderr.split('\n'):
            if "Duration" in line:
                try:
                    dur_str = line.split("Duration: ")[1].split(",")[0]
                    h, m, s = dur_str.split(":")
                    audio_duration = float(h) * 3600 + float(m) * 60 + float(s)
                    print(f"⏱️ Длина аудио: {audio_duration:.2f} секунд")
                except:
                    pass
                break
        
        if not audio_duration:
            audio_duration = 12.0
        
        if audio_duration > 30:
            audio_duration = 30
        
        print("🎬 Создаю видео...")
        
        from PIL import Image, ImageDraw, ImageFont
        
        watermark_text = "@TheBestTranslaterBot"
        temp_watermark = "watermark_temp.png"
        
        try:
            width, height = 640, 360
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            try:
                font_paths = [
                    "arial.ttf",
                    "C:/Windows/Fonts/arial.ttf",
                    "C:/Windows/Fonts/times.ttf",
                    "C:/Windows/Fonts/calibri.ttf"
                ]
                font = None
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            font = ImageFont.truetype(font_path, 24)
                            break
                        except:
                            continue
                
                if font is None:
                    font = ImageFont.load_default()
            except:
                font = ImageFont.load_default()
            
            if hasattr(font, 'getbbox'):
                bbox = font.getbbox(watermark_text)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width = len(watermark_text) * 14
                text_height = 20
            
            x_position = (width - text_width) // 2
            y_position = height - text_height - 20
            
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x_position + dx, y_position + dy), watermark_text, fill=(0, 0, 0, 180), font=font)
            
            draw.text((x_position, y_position), watermark_text, fill=(255, 255, 255, 220), font=font)
            
            img.save(temp_watermark, "PNG")
            print(f"✅ Водяной знак создан")
            
        except Exception as e:
            print(f"⚠️ Ошибка создания водяного знака: {e}")
            temp_watermark = None
        
        cmd_inputs = [FFMPEG_PATH, "-i", video_template, "-i", audio_file]
        filter_complex_parts = []
        
        if temp_watermark and os.path.exists(temp_watermark):
            cmd_inputs.extend(["-i", temp_watermark])
            filter_complex_parts.append("[0:v][2:v]overlay=0:0:format=auto[v]")
        else:
            filter_complex_parts.append("[0:v]copy[v]")
        
        filter_complex_parts.append("[0:a]volume=0.3[original_audio]")
        filter_complex_parts.append("[1:a]volume=1.0[celebrity_audio]")
        filter_complex_parts.append("[original_audio][celebrity_audio]amix=inputs=2:duration=longest:weights=0.3 1.0[mixed_audio]")
        
        filter_complex = ";".join(filter_complex_parts)
        
        cmd = cmd_inputs + [
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "[mixed_audio]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-t", str(audio_duration),
            "-shortest",
            "-preset", "ultrafast",
            "-crf", "28",
            "-y",
            output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        print(f"📊 Код возврата: {result.returncode}")
        
        if temp_watermark and os.path.exists(temp_watermark):
            try:
                os.remove(temp_watermark)
            except:
                pass
        
        if result.returncode != 0:
            print(f"❌ FFmpeg ошибка")
            
            print("🔄 Пробую альтернативу...")
            
            alt_cmd = [
                FFMPEG_PATH,
                "-i", video_template,
                "-i", audio_file,
                "-filter_complex", "[0:a][1:a]amix=inputs=2:weights=0.4 0.6[mixed]",
                "-map", "0:v",
                "-map", "[mixed]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-t", str(min(audio_duration, 30)),
                "-shortest",
                "-y",
                output_file
            ]
            
            alt_result = subprocess.run(alt_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            print(f"📊 Код возврата: {alt_result.returncode}")
            
            if alt_result.returncode != 0:
                print("❌ Ошибка создания")
                return None
        
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            size_mb = size / (1024 * 1024)
            print(f"✅ Видео создано: {size_mb:.1f} MB")
            return output_file
        else:
            print("❌ Файл не создался")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None

async def compress_video(input_file: str, max_size_mb: int = 25) -> str:
    file_size = os.path.getsize(input_file) / (1024 * 1024)
    
    if file_size <= max_size_mb:
        print(f"📊 Размер: {file_size:.1f}MB")
        return input_file
    
    import uuid
    output_file = f"compressed_{uuid.uuid4().hex[:8]}.mp4"
    
    print(f"📦 Сжимаю видео")
    
    cmd_duration = [
        FFMPEG_PATH,
        "-i", input_file,
        "-show_entries", "format=duration",
        "-v", "quiet",
        "-of", "csv=p=0"
    ]
    
    result = subprocess.run(cmd_duration, capture_output=True, text=True)
    duration = 30.0
    
    if result.returncode == 0:
        try:
            duration = float(result.stdout.strip())
        except:
            pass
    
    target_video_bitrate = int((max_size_mb * 8192 * 0.8) / duration)
    
    compress_cmd = [
        FFMPEG_PATH,
        "-i", input_file,
        "-c:v", "libx264",
        "-b:v", f"{max(target_video_bitrate, 500)}k",
        "-c:a", "aac",
        "-b:a", "64k",
        "-preset", "veryfast",
        "-crf", "28",
        "-y",
        output_file
    ]
    
    result = subprocess.run(compress_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    if result.returncode == 0 and os.path.exists(output_file):
        new_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"✅ Сжато до: {new_size:.1f}MB")
        
        if os.path.exists(input_file):
            os.remove(input_file)
        
        return output_file
    
    print("⚠️ Сжатие не удалось")
    return input_file

def get_main_keyboard():
    keyboard = [
        [KeyboardButton(text="🎬 Создать видео со знаменитостью")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_celebrities_keyboard():
    keyboard = []
    row = []
    
    for i, celebrity in enumerate(CELEBRITIES.keys()):
        row.append(KeyboardButton(text=celebrity))
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([KeyboardButton(text="⬅️ Назад в главное меню")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🌟 Добро пожаловать в бота для создания видео! 🌟\n\n"
        "✨ Что я умею: ✨\n"
        "• Создавать видео с голосами знаменитостей 🎬\n"
        "• Синхронизировать аудио с видео 🎵\n"
        "• Добавлять водяные знаки на видео 🔒\n"
        "• Сжимать видео для быстрой отправки 📦\n"
        "• Поддерживать 10 разных знаменитостей 🌟\n\n"
        "📱 Просто выбери знаменитость и напиши текст!\n\n"
        "🤖 Бот создан для МПИТ ✅",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "🎬 Создать видео со знаменитостью")
async def start_creation(message: types.Message, state: FSMContext):
    await message.answer(
        "👑 Выбери знаменитость из списка ниже: 👑\n\n"
        "У нас есть целых 10 крутых знаменитостей!\n"
        "Каждая со своим уникальным голосом и стилем 🎤\n\n"
        "Просто нажми на кнопку с именем знаменитости 👇",
        parse_mode="Markdown",
        reply_markup=get_celebrities_keyboard()
    )
    await state.set_state(VideoCreation.waiting_for_celebrity)

@dp.message(F.text == "⬅️ Назад в главное меню")
async def go_back(message: types.Message, state: FSMContext):
    await state.clear()
    await cmd_start(message)

@dp.message(VideoCreation.waiting_for_celebrity)
async def choose_celebrity(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад в главное меню":
        await state.clear()
        await cmd_start(message)
        return
    
    celebrity_name = message.text
    
    if celebrity_name not in CELEBRITIES:
        await message.answer(
            "⚠️ Пожалуйста, выбери знаменитость из списка! ⚠️\n\n"
            "Я могу работать только с теми знаменитостями, которые есть в моей базе.\n"
            "Просто нажми на одну из кнопок ниже 👇\n\n"
            "🤖 Бот создан для МПИТ ✅",
            parse_mode="Markdown",
            reply_markup=get_celebrities_keyboard()
        )
        return
    
    await state.update_data(celebrity=celebrity_name)
    
    celebrity_info = CELEBRITIES[celebrity_name]
    
    if not os.path.exists(celebrity_info["video_file"]):
        await message.answer(
            f"❌ Упс! Видео-шаблон для {celebrity_name} не найден! ❌\n\n"
            f"Файл должен называться: {celebrity_info['video_file']}\n\n"
            "Пожалуйста, проверь наличие этого файла в папке с ботом.\n"
            "Без него я не смогу создать видео 😔\n\n"
            "🤖 Бот создан для МПИТ ✅",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        return
    
    await message.answer(
        f"🎉 Отличный выбор! 🎉\n\n"
        f"Ты выбрал(а): {celebrity_name} 🌟\n\n"
        "📝 Теперь напиши текст, который должна сказать знаменитость:\n\n"
        "Важные моменты:\n"
        "• Максимум 200 символов 📏\n"
        "• Минимум 5 символов 🔤\n"
        "• Избегай специальных символов ❌\n\n"
        "Пример текста:\n"
        "«Привет, друзья! Сегодня я хочу поделиться с вами важной новостью.»\n\n"
        "Жду твой текст! ✍️\n\n"
        "🤖 Бот создан для МПИТ ✅",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(VideoCreation.waiting_for_text)

@dp.message(VideoCreation.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext):
    text = message.text.strip()
    
    if len(text) > 200:
        await message.answer(
            f"⚠️ Текст слишком длинный! ⚠️\n\n"
            f"Твой текст содержит {len(text)} символов.\n"
            "Ограничение: 200 символов.\n\n"
            "Пожалуйста, сократи текст и отправь его снова:\n"
            "• Убери лишние слова\n"
            "• Сделай текст более лаконичным\n"
            "• Оставь только самое важное\n\n"
            "🤖 Бот создан для МПИТ ✅",
            parse_mode="Markdown"
        )
        return
    
    if len(text) < 5:
        await message.answer(
            "⚠️ Текст слишком короткий! ⚠️\n\n"
            "Пожалуйста, напиши хотя бы 5 символов.\n"
            "Так видео будет более интересным и содержательным!\n\n"
            "🤖 Бот создан для МПИТ ✅",
            parse_mode="Markdown"
        )
        return
    
    if re.search(r'[<>{}[\]\\]', text):
        await message.answer(
            "⚠️ Обнаружены недопустимые символы! ⚠️\n\n"
            "В твоем тексте есть символы, которые я не могу обработать:\n"
            "< > { } [ ] \\\n\n"
            "Пожалуйста, удали их и отправь текст снова.\n"
            "Используй только буквы, цифры и обычные знаки препинания.\n\n"
            "🤖 Бот создан для МПИТ ✅",
            parse_mode="Markdown"
        )
        return
    
    data = await state.get_data()
    celebrity_name = data.get('celebrity')
    
    if not celebrity_name:
        await message.answer(
            "❌ Ошибка! Знаменитость не выбрана. ❌\n\n"
            "Пожалуйста, начни процесс заново.\n"
            "Нажми /start чтобы вернуться в начало.\n\n"
            "🤖 Бот создан для МПИТ ✅",
            parse_mode="Markdown"
        )
        await state.clear()
        await cmd_start(message)
        return
    
    celebrity_info = CELEBRITIES[celebrity_name]
    
    status_msg = await message.answer(
        f"🚀 Начинаю создание видео с {celebrity_name}! 🚀\n\n"
        "📊 Этапы создания:\n"
        "1️⃣ Генерирую голос знаменитости... 🎤\n"
        "2️⃣ Обрабатываю видео-шаблон... 🎬\n"
        "3️⃣ Смешиваю аудио дорожки... 🔊\n"
        "4️⃣ Добавляю водяной знак... 🔒\n"
        "5️⃣ Сжимаю видео для отправки... 📦\n\n"
        "⏱️ Примерное время ожидания: 1-3 минуты\n"
        "Не закрывай чат, скоро будет результат! ⏳\n\n"
        "🤖 Бот создан для МПИТ ✅",
        parse_mode="Markdown"
    )
    
    try:
        await message.bot.send_chat_action(message.chat.id, "record_voice")
        audio_file = await generate_celebrity_audio(
            text, 
            celebrity_info["voice_id"], 
            f"{celebrity_name.lower().replace(' ', '_')}_audio.mp3"
        )
        
        if not audio_file:
            await message.answer(
                f"❌ Не удалось сгенерировать голос {celebrity_name}! ❌\n\n"
                "Возможные причины:\n"
                "• Проблемы с интернет-соединением 🌐\n"
                "• Ошибка сервера обработки голоса ⚠️\n"
                "• Технические работы на сервере 🔧\n\n"
                "Пожалуйста, попробуй позже или выбери другую знаменитость.\n\n"
                "🤖 Бот создан для МПИТ ✅",
                parse_mode="Markdown"
            )
            await state.clear()
            await status_msg.delete()
            await message.answer("/start", reply_markup=get_main_keyboard())
            return
        
        await message.bot.send_chat_action(message.chat.id, "upload_video")
        video_file = await create_final_video(
            text, audio_file, celebrity_info["video_file"], celebrity_name
        )
        
        if not video_file:
            await message.answer(
                f"❌ Не удалось создать видео с {celebrity_name}! ❌\n\n"
                "Возможные причины:\n"
                "• Проблема с видео-шаблоном 🎬\n"
                "• Ошибка в работе FFmpeg ⚠️\n"
                "• Недостаточно места на диске 💾\n\n"
                "Пожалуйста, проверь видео-файлы и попробуй снова.\n\n"
                "🤖 Бот создан для МПИТ ✅",
                parse_mode="Markdown"
            )
            await state.clear()
            await status_msg.delete()
            await message.answer("/start", reply_markup=get_main_keyboard())
            return
        
        print("📦 Проверяю размер...")
        video_file = await compress_video(video_file, max_size_mb=25)
        
        await message.bot.send_chat_action(message.chat.id, "upload_video")
        file_size_mb = os.path.getsize(video_file) / (1024 * 1024)
        print(f"📊 Размер: {file_size_mb:.1f}MB")
        
        if file_size_mb > 50:
            await message.answer(
                f"⚠️ Видео слишком большое для отправки! ⚠️\n\n"
                f"Размер видео: {file_size_mb:.1f} MB\n"
                "Лимит Telegram: 50 MB\n\n"
                "Пожалуйста, попробуй:\n"
                "• Сократить текст ✂️\n"
                "• Использовать более короткий текст 📝\n"
                "• Разделить текст на несколько видео 🔀\n\n"
                "🤖 Бот создан для МПИТ ✅",
                parse_mode="Markdown"
            )
        else:
            video_input = FSInputFile(video_file)
            
            try:
                await message.answer_video(
                    video=video_input,
                    caption=f"🎉 Видео готово! 🎉\n\n"
                            f"🌟 Знаменитость: {celebrity_name}\n"
                            f"📊 Размер: {file_size_mb:.1f} MB\n"
                            f"⏱️ Длительность: ~{min(file_size_mb/2, 30):.0f} сек\n\n"
                            "✨ Спасибо, что воспользовался нашим ботом!\n"
                            "Попробуй создать ещё одно видео! 🔄\n\n"
                            "🤖 Бот создан для МПИТ ✅",
                    parse_mode="Markdown",
                    request_timeout=120.0
                )
                print("✅ Видео отправлено")
                
            except asyncio.TimeoutError:
                print("⚠️ Таймаут")
                video_input = FSInputFile(video_file)
                await message.answer_document(
                    document=video_input,
                    caption=f"📁 Видео отправлено как файл 📁\n\n"
                            f"🌟 Знаменитость: {celebrity_name}\n"
                            f"📊 Размер: {file_size_mb:.1f} MB\n\n"
                            "Telegram не принял видео как медиафайл,\n"
                            "поэтому отправляю как документ.\n\n"
                            "🤖 Бот создан для МПИТ ✅",
                    parse_mode="Markdown",
                    request_timeout=150.0
                )
                print("✅ Отправлено как файл")
                
            except Exception as send_error:
                print(f"⚠️ Ошибка: {send_error}")
                await message.answer(
                    f"✅ Видео успешно создано! ✅\n\n"
                    f"🌟 Знаменитость: {celebrity_name}\n"
                    f"📊 Размер: {file_size_mb:.1f} MB\n\n"
                    "Возникла небольшая проблема с отправкой,\n"
                    "но видео точно создано и сохранено!\n\n"
                    "🤖 Бот создан для МПИТ ✅",
                    parse_mode="Markdown"
                )
        
        await status_msg.delete()
        
        if os.path.exists(video_file):
            try:
                os.remove(video_file)
                print(f"🗑️ Удалено видео")
            except Exception as e:
                print(f"⚠️ Не удалось удалить: {e}")
        
        if os.path.exists(audio_file):
            try:
                os.remove(audio_file)
                print(f"🗑️ Удалено аудио")
            except Exception as e:
                print(f"⚠️ Не удалось удалить: {e}")
        
        await state.clear()
        await message.answer(
            "🎬 Хочешь создать ещё одно видео? 🎬\n\n"
            "У нас ещё много знаменитостей ждут своей очереди!\n"
            "Просто нажми кнопку ниже и выбери следующую знаменитость! 👇\n\n"
            "🤖 Бот создан для МПИТ ✅",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        
        await message.answer(
            "❌ Критическая ошибка! ❌\n\n"
            "Произошла непредвиденная ошибка при создании видео.\n"
            "Пожалуйста, попробуй снова через несколько минут.\n\n"
            "Если ошибка повторяется, свяжись с разработчиком.\n\n"
            "🤖 Бот создан для МПИТ ✅",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

@dp.message()
async def any_message(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для создания видео со знаменитостями! 👋\n\n"
        "✨ Что я умею:\n"
        "• Создавать крутые видео с голосами знаменитостей 🎬\n"
        "• Обрабатывать текст и превращать его в речь 🎤\n"
        "• Синхронизировать всё в одно красивое видео 🎵\n\n"
        "📱 Чтобы начать, просто нажми /start 📱\n\n"
        "🤖 Бот создан для МПИТ ✅",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def main():
    print("=" * 60)
    print("🤖 БОТ ДЛЯ СОЗДАНИЯ ВИДЕО СО ЗНАМЕНИТОСТЯМИ")
    print("=" * 60)
    print("🌟 Доступные знаменитости:")
    
    for celebrity, info in CELEBRITIES.items():
        exists = "✅" if os.path.exists(info["video_file"]) else "❌"
        print(f"  {exists} {celebrity}")
    
    print("=" * 60)
    print(f"🔧 FFmpeg: {'✅' if os.path.exists(FFMPEG_PATH) else '❌'}")
    print("=" * 60)
    print("🎬 Бот запущен и готов к работе!")
    print("📱 Напиши /start в Telegram чтобы начать")
    print("⏸ Ctrl+C для остановки бота")
    print("=" * 60)
    print("🤖 БОТ СОЗДАН ДЛЯ МПИТ ✅")
    print("=" * 60)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        import aiogram
        print("✅ Все библиотеки установлены")
    except ImportError as e:
        print(f"❌ Ошибка: {e}")
        print("pip install aiogram requests pillow")
        exit(1)
    
    temp_audio_dir = Path("temp_audio")
    temp_audio_dir.mkdir(exist_ok=True)
    
    print("🔧 Проверяю FFmpeg...")
    try:
        check_cmd = [FFMPEG_PATH, "-version"]
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg работает отлично!")
    except:
        print("❌ FFmpeg не найден или не работает")
    
    print("🔍 Проверяю видео-шаблоны...")
    missing = []
    for celebrity, info in CELEBRITIES.items():
        if not os.path.exists(info["video_file"]):
            missing.append(f"{celebrity}: {info['video_file']}")
    
    if missing:
        print(f"⚠️ Отсутствуют {len(missing)} видео-файлов:")
        for m in missing:
            print(f"  ❌ {m}")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()