import asyncio
import os
import logging
import random
from datetime import datetime
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, ConversationHandler, filters
from telegram.error import TimedOut, NetworkError
from playwright.async_api import async_playwright
from jinja2 import Template
import json
import pytz
import subprocess

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
SELECTING_COUNTRY, SELECTING_TYPE, ENTERING_ACCOUNT, ENTERING_AMOUNT = range(4)

# Данные стран
COUNTRIES = {
    'colombia': {
        'name': 'Colombia',
        'flag': '🇨🇴',
        'currency': 'COP',
        'currency_symbol': '$',
        'timezone': 'America/Bogota'  # UTC-5
    },
    'paraguay': {
        'name': 'Paraguay',
        'flag': '🇵🇾',
        'currency': 'PYG',
        'currency_symbol': '₲',
        'timezone': 'America/Asuncion'  # UTC-4
    },
    'bolivia': {
        'name': 'Bolivia',
        'flag': '🇧🇴',
        'currency': 'BOB',
        'currency_symbol': 'Bs.',
        'timezone': 'America/La_Paz'  # UTC-4
    },
    'argentina': {
        'name': 'Argentina',
        'flag': '🇦🇷',
        'currency': 'ARS',
        'currency_symbol': '$',
        'timezone': 'America/Argentina/Buenos_Aires'  # UTC-3
    },
    'ecuador': {
        'name': 'Ecuador',
        'flag': '🇪🇨',
        'currency': 'USD',
        'currency_symbol': '$',
        'timezone': 'America/Guayaquil'  # UTC-5
    }
}

# Хранилище данных пользователей
user_data: Dict[int, Dict] = {}

# Глобальная переменная для application (используется в Vercel)
application = None


def check_user_access(user_id: int) -> bool:
    """Проверяет доступ пользователя по Telegram ID"""
    # Получаем список разрешенных ID из переменной окружения
    allowed_ids_str = os.getenv('ALLOWED_TELEGRAM_IDS', '')
    
    logger.info(f"Checking access for user_id: {user_id}")
    logger.info(f"ALLOWED_TELEGRAM_IDS env var: {allowed_ids_str[:50]}..." if len(allowed_ids_str) > 50 else f"ALLOWED_TELEGRAM_IDS env var: {allowed_ids_str}")
    
    if not allowed_ids_str:
        # Если список не задан, разрешаем всем (для разработки)
        logger.warning("ALLOWED_TELEGRAM_IDS not set, allowing all users")
        return True
    
    # Разбираем список ID (может быть через запятую или пробел)
    allowed_ids = []
    for part in allowed_ids_str.replace(',', ' ').split():
        try:
            allowed_ids.append(int(part.strip()))
        except ValueError:
            continue
    
    logger.info(f"Parsed allowed IDs: {allowed_ids}")
    logger.info(f"User ID type: {type(user_id)}, User ID value: {user_id}")
    logger.info(f"Allowed IDs types: {[type(id) for id in allowed_ids]}")
    
    # Проверяем, есть ли пользователь в списке
    has_access = user_id in allowed_ids
    logger.info(f"Access check result: {has_access}")
    return has_access


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.message.from_user.id
    
    # Сбрасываем предыдущее состояние пользователя
    if user_id in user_data:
        del user_data[user_id]
    
    # Сбрасываем состояние разговора
    if context.user_data:
        context.user_data.clear()
    
    keyboard = [
        [InlineKeyboardButton("🇨🇴 Colombia", callback_data='country_colombia')],
        [InlineKeyboardButton("🇵🇾 Paraguay", callback_data='country_paraguay')],
        [InlineKeyboardButton("🇧🇴 Bolivia", callback_data='country_bolivia')],
        [InlineKeyboardButton("🇦🇷 Argentina", callback_data='country_argentina')],
        [InlineKeyboardButton("🇪🇨 Ecuador", callback_data='country_ecuador')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Выберите страну для генерации скриншота:",
        reply_markup=reply_markup
    )
    return SELECTING_COUNTRY


async def country_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора страны"""
    query = update.callback_query
    await query.answer()
    
    country_code = query.data.split('_')[1]
    country_info = COUNTRIES[country_code]
    
    user_id = query.from_user.id
    user_data[user_id] = {
        'country': country_code,
        'country_info': country_info
    }
    
    # Показываем кнопки выбора типа скриншота
    keyboard = [
        [InlineKeyboardButton("⏳ Ожидание отправки", callback_data='type_waiting')],
        [InlineKeyboardButton("❌ Ошибка отправки выигрыша", callback_data='type_error')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ Выбрана страна: {country_info['flag']} {country_info['name']}\n"
        f"Валюта: {country_info['currency']}\n\n"
        "Выберите тип скриншота:",
        reply_markup=reply_markup
    )
    return SELECTING_TYPE


async def type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора типа скриншота"""
    query = update.callback_query
    await query.answer()
    
    screenshot_type = query.data.split('_')[1]  # 'waiting' или 'error'
    
    user_id = query.from_user.id
    if user_id not in user_data:
        await query.edit_message_text("Ошибка. Начните с /start")
        return ConversationHandler.END
    
    user_data[user_id]['screenshot_type'] = screenshot_type
    
    await query.edit_message_text(
        "Введите номер аккаунта:"
    )
    return ENTERING_ACCOUNT


async def account_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода номера аккаунта"""
    account_number = update.message.text.strip()
    user_id = update.message.from_user.id
    
    if user_id not in user_data:
        await update.message.reply_text("Ошибка. Начните с /start")
        return ConversationHandler.END
    
    user_data[user_id]['account'] = account_number
    
    await update.message.reply_text(
        f"✅ Номер аккаунта: {account_number}\n\n"
        "Введите сумму выигрыша:"
    )
    return ENTERING_AMOUNT


async def amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода суммы выигрыша"""
    try:
        amount = float(update.message.text.strip().replace(',', '.'))
        user_id = update.message.from_user.id
        
        if user_id not in user_data:
            await update.message.reply_text("Ошибка. Начните с /start")
            return ConversationHandler.END
        
        user_data[user_id]['amount'] = amount
        
        await update.message.reply_text(
            "⏳ Генерирую скриншот...\n"
            "Пожалуйста, подождите..."
        )
        
        # Генерируем скриншот
        screenshot_path = await generate_screenshot(user_id)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                # Проверяем размер файла
                file_size = os.path.getsize(screenshot_path)
                logger.info(f"Screenshot size: {file_size} bytes")
                
                # Если файл слишком большой, отправляем как документ
                if file_size > 10 * 1024 * 1024:  # Больше 10MB
                    with open(screenshot_path, 'rb') as doc:
                        await update.message.reply_document(
                            document=doc,
                            filename='screenshot.png',
                            caption=f"✅ Скриншот готов!\n"
                                   f"Страна: {user_data[user_id]['country_info']['name']}\n"
                                   f"Аккаунт: {user_data[user_id]['account']}\n"
                                   f"Сумма: {user_data[user_id]['country_info']['currency_symbol']} {amount}",
                            read_timeout=60,
                            write_timeout=60,
                            connect_timeout=60
                        )
                else:
                    with open(screenshot_path, 'rb') as photo:
                        await update.message.reply_photo(
                            photo=photo,
                            caption=f"✅ Скриншот готов!\n"
                                   f"Страна: {user_data[user_id]['country_info']['name']}\n"
                                   f"Аккаунт: {user_data[user_id]['account']}\n"
                                   f"Сумма: {user_data[user_id]['country_info']['currency_symbol']} {amount}",
                            read_timeout=60,
                            write_timeout=60,
                            connect_timeout=60
                        )
                os.remove(screenshot_path)
            except (TimedOut, NetworkError) as e:
                logger.error(f"Error sending photo: {e}")
                await update.message.reply_text(
                    "❌ Ошибка при отправке скриншота (таймаут).\n"
                    "Попробуйте еще раз или используйте /start для начала."
                )
                if screenshot_path and os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await update.message.reply_text(
                    f"❌ Произошла ошибка: {str(e)}\n"
                    "Попробуйте еще раз или используйте /start для начала."
                )
                if screenshot_path and os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
        else:
            await update.message.reply_text("❌ Ошибка при генерации скриншота")
        
        # Очищаем данные пользователя
        if user_id in user_data:
            del user_data[user_id]
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат суммы. Введите число (например: 1000 или 1000.50):"
        )
        return ENTERING_AMOUNT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик отмены"""
    user_id = update.message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text("❌ Операция отменена. Используйте /start для начала.")
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик глобальных ошибок"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка при обработке запроса.\n"
                "Попробуйте еще раз или используйте /start для начала."
            )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")


async def generate_screenshot(user_id: int) -> str:
    """Генерирует скриншот страницы с данными пользователя"""
    if user_id not in user_data:
        return None
    
    data = user_data[user_id]
    country_info = data['country_info']
    account = data['account']
    amount = data['amount']
    screenshot_type = data.get('screenshot_type', 'waiting')  # По умолчанию 'waiting'
    
    # Генерируем HTML
    is_error = (screenshot_type == 'error')
    html_content = generate_html(country_info, account, amount, is_error)
    
    # Сохраняем во временный файл в /tmp (единственная доступная для записи директория в serverless)
    tmp_dir = '/tmp'
    html_path = os.path.join(tmp_dir, f"temp_{user_id}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Генерируем скриншот с помощью Playwright
    screenshot_path = os.path.join(tmp_dir, f"screenshot_{user_id}.png")
    
    # Устанавливаем переменные окружения для Playwright в serverless
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', '/tmp/.cache/ms-playwright')
    
    async with async_playwright() as p:
        # Запускаем браузер с параметрами для serverless окружения
        try:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process'
                ]
            )
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            # Пытаемся установить браузеры, если они не установлены
            try:
                logger.info("Attempting to install Playwright browsers...")
                # Используем subprocess с правильными параметрами для serverless
                result = subprocess.run(
                    ['python', '-m', 'playwright', 'install', 'chromium'], 
                    check=False, 
                    timeout=120,
                    capture_output=True,
                    text=True,
                    env={**os.environ, 'PLAYWRIGHT_BROWSERS_PATH': '/tmp/.cache/ms-playwright'}
                )
                logger.info(f"Playwright install output: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Playwright install warnings: {result.stderr}")
                
                # Пытаемся снова запустить браузер
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--single-process'
                    ]
                )
            except Exception as install_error:
                logger.error(f"Failed to install/launch browser: {install_error}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return None
        # Устанавливаем нормальный размер viewport
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})
        
        # Нормализуем путь для file:// URL (заменяем обратные слеши на прямые для Windows)
        abs_path = os.path.abspath(html_path)
        file_url = f"file:///{abs_path.replace(os.sep, '/')}"
        
        try:
            await page.goto(file_url, wait_until='networkidle', timeout=30000)
            # Ждем немного для полной загрузки стилей и рендеринга
            await asyncio.sleep(2)
            
            # Делаем скриншот фиксированного размера (не full_page)
            await page.screenshot(
                path=screenshot_path,
                type='png'
            )
            
            # Проверяем размер файла
            file_size = os.path.getsize(screenshot_path)
            logger.info(f"Generated screenshot: {file_size / 1024 / 1024:.2f} MB")
            
        except Exception as e:
            logger.error(f"Error generating screenshot: {e}")
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            return None
        finally:
            await browser.close()
    
    # Удаляем временный HTML файл
    os.remove(html_path)
    
    return screenshot_path


def generate_html(country_info: Dict, account: str, amount: float, is_error: bool = False) -> str:
    """Генерирует HTML страницу в стиле 1xBet"""
    template_str = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>1xBet - Lista de Cuentas</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #0a0e27;
            color: #fff;
            height: 800px;
            overflow: hidden;
            line-height: 1.5;
        }
        
        .header {
            background: #1a1f3a;
            border-bottom: 2px solid #2a2f4a;
            padding: 12px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: 0;
        }
        
        .logo {
            display: inline-flex;
            align-items: baseline;
            text-decoration: none;
            font-weight: 900;
            font-size: 30px;
            line-height: 1;
            letter-spacing: -0.5px;
            font-family: 'Arial Black', 'Arial Bold', Arial, sans-serif;
        }
        
        .logo-1x {
            color: #0d47a1;
            display: inline-block;
            position: relative;
            transform: skewX(-6deg);
        }
        
        .logo-1x::before {
            content: '';
            position: absolute;
            left: -6px;
            top: -1px;
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #0d47a1;
            transform: rotate(-30deg);
        }
        
        .logo-1x-inner {
            display: inline-block;
            position: relative;
            z-index: 1;
        }
        
        .logo-bet {
            color: #1976d2;
            margin-left: 2px;
            font-weight: 900;
        }
        
        .nav-menu {
            display: flex;
            gap: 8px;
            list-style: none;
            flex: 1;
            justify-content: center;
        }
        
        .nav-item {
            color: #b8bcc8;
            text-decoration: none;
            font-size: 13px;
            padding: 8px 14px;
            border-radius: 4px;
            transition: all 0.2s;
            position: relative;
        }
        
        .nav-item:hover {
            background: rgba(255,255,255,0.08);
            color: #fff;
        }
        
        .nav-item::after {
            content: '▼';
            font-size: 8px;
            margin-left: 4px;
            opacity: 0.6;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .balance {
            background: rgba(255,255,255,0.1);
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 13px;
            color: #fff;
        }
        
        .deposit-btn {
            background: #00b26b;
            color: #fff;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 12px;
            font-weight: 600;
            transition: background 0.2s;
        }
        
        .deposit-btn:hover {
            background: #00a05c;
        }
        
        .container {
            display: flex;
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
            gap: 20px;
            height: calc(100vh - 60px);
            overflow: hidden;
        }
        
        .sidebar-left {
            width: 240px;
            flex-shrink: 0;
        }
        
        .sidebar-block {
            background: #14182e;
            border: 1px solid #2a2f4a;
            border-radius: 6px;
            margin-bottom: 12px;
            padding: 12px;
        }
        
        .sidebar-title {
            font-size: 12px;
            color: #8a8f9f;
            margin-bottom: 8px;
            text-transform: uppercase;
            font-weight: 600;
        }
        
        .sidebar-link {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #b8bcc8;
            text-decoration: none;
            padding: 8px;
            border-radius: 4px;
            font-size: 13px;
            transition: all 0.2s;
        }
        
        .sidebar-link:hover {
            background: rgba(255,255,255,0.05);
            color: #fff;
        }
        
        .main-content {
            flex: 1;
            min-width: 0;
            overflow-y: auto;
            max-height: 100%;
        }
        
        .content-block {
            background: #14182e;
            border: 1px solid #2a2f4a;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .page-title {
            font-size: 24px;
            margin-bottom: 8px;
            color: #fff;
            font-weight: 700;
        }
        
        .page-subtitle {
            font-size: 14px;
            color: #8a8f9f;
            margin-bottom: 20px;
        }
        
        .coupon-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #2a2f4a;
        }
        
        .coupon-tabs {
            display: flex;
            gap: 4px;
        }
        
        .coupon-tab {
            padding: 8px 16px;
            background: transparent;
            border: none;
            color: #8a8f9f;
            font-size: 13px;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.2s;
        }
        
        .coupon-tab.active {
            background: #1a1f3a;
            color: #00b26b;
            font-weight: 600;
        }
        
        .coupon-item {
            background: #1a1f3a;
            border: 1px solid #2a2f4a;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 12px;
        }
        
        .coupon-item.priority {
            border-color: #00b26b;
            background: linear-gradient(135deg, rgba(0, 178, 107, 0.1) 0%, #1a1f3a 100%);
        }
        
        .coupon-number {
            font-size: 11px;
            color: #8a8f9f;
            margin-bottom: 8px;
        }
        
        .coupon-date {
            font-size: 11px;
            color: #8a8f9f;
            margin-bottom: 12px;
        }
        
        .coupon-type {
            display: inline-block;
            background: rgba(0, 178, 107, 0.2);
            color: #00b26b;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        
        .coupon-bet-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .bet-amount {
            font-size: 16px;
            font-weight: 700;
            color: #fff;
        }
        
        .bet-winnings {
            font-size: 14px;
            color: #00b26b;
            font-weight: 600;
        }
        
        .bet-details {
            background: #0f1325;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 8px;
        }
        
        .bet-sport {
            font-size: 11px;
            color: #8a8f9f;
            margin-bottom: 4px;
        }
        
        .bet-match {
            font-size: 13px;
            color: #fff;
            font-weight: 600;
            margin-bottom: 6px;
        }
        
        .bet-selection {
            font-size: 12px;
            color: #b8bcc8;
            margin-bottom: 4px;
        }
        
        .bet-status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-top: 8px;
        }
        
        .bet-status.waiting {
            background: rgba(255, 193, 7, 0.2);
            color: #ffc107;
        }
        
        .bet-status.processing {
            background: rgba(33, 150, 243, 0.2);
            color: #2196f3;
        }
        
        .coupon-actions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }
        
        .action-btn {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .action-btn.primary {
            background: #00b26b;
            color: #fff;
        }
        
        .action-btn.primary:hover {
            background: #00a05c;
        }
        
        .action-btn.secondary {
            background: #1a1f3a;
            color: #b8bcc8;
            border: 1px solid #2a2f4a;
        }
        
        .action-btn.secondary:hover {
            background: #2a2f4a;
            color: #fff;
        }
        
        .sidebar-right {
            width: 280px;
            flex-shrink: 0;
        }
        
        .stats-box {
            background: #14182e;
            border: 1px solid #2a2f4a;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 12px;
        }
        
        .stats-title {
            font-size: 12px;
            color: #8a8f9f;
            margin-bottom: 12px;
            text-transform: uppercase;
            font-weight: 600;
        }
        
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #2a2f4a;
        }
        
        .stat-row:last-child {
            border-bottom: none;
        }
        
        .stat-label {
            font-size: 13px;
            color: #b8bcc8;
        }
        
        .stat-value {
            font-size: 13px;
            color: #fff;
            font-weight: 600;
        }
        
        .stat-value.highlight {
            color: #00b26b;
        }
        
        .error-status {
            background: rgba(244, 67, 54, 0.2);
            color: #f44336;
        }
        
        .error-message {
            background: rgba(244, 67, 54, 0.1);
            border: 1px solid #f44336;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 16px;
            color: #f44336;
            font-weight: 600;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-section">
            <a href="#" class="logo">
                <span class="logo-1x">
                    <span class="logo-1x-inner">1X</span>
                </span>
                <span class="logo-bet">BET</span>
            </a>
        </div>
        <ul class="nav-menu">
            <li><a href="#" class="nav-item">TOP-EVENTS</a></li>
            <li><a href="#" class="nav-item">DEPORTES</a></li>
            <li><a href="#" class="nav-item">DIRECTO</a></li>
            <li><a href="#" class="nav-item">1XGAMES</a></li>
            <li><a href="#" class="nav-item">CASINO</a></li>
            <li><a href="#" class="nav-item">CASINO EN DIRECTO</a></li>
            <li><a href="#" class="nav-item">ESPORTS</a></li>
            <li><a href="#" class="nav-item">PROMO</a></li>
            <li><a href="#" class="nav-item">MÁS</a></li>
        </ul>
    </div>
    
    <div class="container">
        <div class="sidebar-left">
            <div class="sidebar-block">
                <div class="sidebar-title">Navegación</div>
                <a href="#" class="sidebar-link">⭐ Partidos favoritos</a>
                <a href="#" class="sidebar-link">👍 Recomendados</a>
                <a href="#" class="sidebar-link">🏆 Campeonatos destacados</a>
                <a href="#" class="sidebar-link">🎮 Mejores juegos</a>
            </div>
            <div class="sidebar-block">
                <div class="sidebar-title">Deportes</div>
                <a href="#" class="sidebar-link">⚽ Fútbol (32)</a>
                <a href="#" class="sidebar-link">🏀 Baloncesto (28)</a>
                <a href="#" class="sidebar-link">🏐 Voleibol (23)</a>
                <a href="#" class="sidebar-link">🎾 Tenis (12)</a>
            </div>
        </div>
        
        <div class="main-content">
            <div class="content-block">
                {% if is_error %}
                <h1 class="page-title">Error en Envío de Ganancias</h1>
                <p class="page-subtitle">Error al procesar el envío de ganancias - {{ country_name }} ({{ currency }})</p>
                <div class="error-message">
                    ❌ Error: No se pudo enviar el pago. Por favor, intente nuevamente o contacte con el soporte.
                </div>
                {% else %}
                <h1 class="page-title">Lista de Cuentas en Espera</h1>
                <p class="page-subtitle">Cuentas pendientes de envío de ganancias - {{ country_name }} ({{ currency }})</p>
                {% endif %}
                
                <div class="coupon-header">
                    <div class="coupon-tabs">
                        <button class="coupon-tab active">Boleto de apuestas</button>
                        <button class="coupon-tab">Mis apuestas</button>
                    </div>
                </div>
                
                <div class="coupon-item priority">
                    <div class="coupon-number">Boleto № {{ account_number }}</div>
                    <div class="coupon-date">{{ current_date }}</div>
                    {% if is_error %}
                    <div class="coupon-type" style="background: rgba(244, 67, 54, 0.2); color: #f44336;">ERROR</div>
                    {% else %}
                    <div class="coupon-type">EN ESPERA</div>
                    {% endif %}
                    <div class="coupon-bet-info">
                        <div class="bet-amount">{{ currency_symbol }} {{ amount }}</div>
                        <div class="bet-winnings">Ganancia: {{ currency_symbol }} {{ amount }}</div>
                    </div>
                    <div class="bet-details">
                        <div class="bet-sport">Cuenta de Pago</div>
                        <div class="bet-match">{{ account_number }}</div>
                        <div class="bet-selection">Monto: {{ currency_symbol }} {{ amount }}</div>
                        {% if is_error %}
                        <div class="bet-status error-status">ERROR AL ENVIAR</div>
                        {% else %}
                        <div class="bet-status waiting">EN ESPERA DE ENVÍO</div>
                        {% endif %}
                    </div>
                    <div class="coupon-actions">
                        {% if is_error %}
                        <button class="action-btn primary" style="background: #f44336;">Reintentar Pago</button>
                        {% else %}
                        <button class="action-btn primary">Procesar Pago</button>
                        {% endif %}
                        <button class="action-btn secondary">Detalles</button>
                    </div>
                </div>
                
                {% for account in other_accounts %}
                <div class="coupon-item">
                    <div class="coupon-number">Boleto № {{ account.number }}</div>
                    <div class="coupon-date">{{ current_date }}</div>
                    <div class="coupon-type">PROCESANDO</div>
                    <div class="coupon-bet-info">
                        <div class="bet-amount">{{ currency_symbol }} {{ account.amount }}</div>
                        <div class="bet-winnings">Ganancia: {{ currency_symbol }} {{ account.amount }}</div>
                    </div>
                    <div class="bet-details">
                        <div class="bet-sport">Cuenta de Pago</div>
                        <div class="bet-match">{{ account.number }}</div>
                        <div class="bet-selection">Monto: {{ currency_symbol }} {{ account.amount }}</div>
                        <div class="bet-status processing">EN PROCESO</div>
                    </div>
                    <div class="coupon-actions">
                        <button class="action-btn secondary">Ver Detalles</button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="sidebar-right">
            <div class="stats-box">
                <div class="stats-title">Estadísticas</div>
                <div class="stat-row">
                    <span class="stat-label">Total Cuentas</span>
                    <span class="stat-value">{{ total_accounts }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">En Espera</span>
                    <span class="stat-value highlight">{{ waiting_count }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Procesando</span>
                    <span class="stat-value">{{ total_accounts - waiting_count }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Monto Total</span>
                    <span class="stat-value highlight">{{ currency_symbol }} {{ total_amount }}</span>
                </div>
            </div>
            
            <div class="stats-box">
                <div class="stats-title">Información</div>
                <div class="stat-row">
                    <span class="stat-label">País</span>
                    <span class="stat-value">{{ country_name }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Moneda</span>
                    <span class="stat-value">{{ currency }}</span>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    template = Template(template_str)
    
    # Генерируем дополнительные данные для списка со случайными значениями
    other_accounts = []
    other_amounts_sum = 0
    random.seed()  # Инициализируем генератор случайных чисел
    
    # Пытаемся преобразовать account в число для вычисления диапазона
    try:
        account_num = int(account)
    except (ValueError, TypeError):
        # Если не удалось преобразовать, используем случайное число
        account_num = random.randint(100000, 999999)
    
    # Вычисляем диапазон для сумм (от 30% до 200% от суммы пользователя)
    min_amount = max(10, amount * 0.3)  # Минимум 10 или 30% от суммы
    max_amount = amount * 2.0  # Максимум 200% от суммы
    
    # Вычисляем диапазон для ID (±100000 от ID пользователя)
    min_id = max(0, account_num - 100000)  # Минимум 0
    max_id = account_num + 100000
    
    for i in range(2, 11):
        # Генерируем случайную сумму в диапазоне суммы пользователя
        acc_amount = round(random.uniform(min_amount, max_amount), 2)
        other_amounts_sum += acc_amount
        
        # Генерируем случайный ID в диапазоне ±100000 от ID пользователя
        random_id = random.randint(min_id, max_id)
        
        other_accounts.append({
            'index': i,
            'number': f"{random_id}",
            'amount': f"{acc_amount:,.2f}".replace(',', ' ')
        })
    
    total_accounts = 10
    waiting_count = 1
    total_amount = amount + other_amounts_sum
    
    # Получаем текущую дату и время в часовом поясе выбранной страны
    timezone = pytz.timezone(country_info['timezone'])
    now_utc = datetime.now(pytz.UTC)
    now_local = now_utc.astimezone(timezone)
    current_date = now_local.strftime("%d.%m.%Y (%H:%M)")
    
    html = template.render(
        currency=country_info['currency'],
        currency_symbol=country_info['currency_symbol'],
        country_name=country_info['name'],
        account_number=account,
        amount=f"{amount:,.2f}".replace(',', ' '),
        other_accounts=other_accounts,
        total_accounts=total_accounts,
        total_amount=f"{total_amount:,.2f}".replace(',', ' '),
        waiting_count=waiting_count,
        current_date=current_date,
        is_error=is_error
    )
    
    return html


def init_application():
    """Инициализирует приложение бота (используется и локально, и на Vercel)
    В serverless окружении создает новое приложение для каждого запроса
    """
    # Получаем токен из переменной окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
    
    # Создаем новое приложение для каждого запроса (важно для serverless)
    app = Application.builder().token(token).build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_COUNTRY: [
                CallbackQueryHandler(country_selected, pattern='^country_'),
                CommandHandler('start', start)  # Позволяет перезапустить в любой момент
            ],
            SELECTING_TYPE: [
                CallbackQueryHandler(type_selected, pattern='^type_'),
                CommandHandler('start', start)  # Позволяет перезапустить в любой момент
            ],
            ENTERING_ACCOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, account_received),
                CommandHandler('start', start)  # Позволяет перезапустить в любой момент
            ],
            ENTERING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, amount_received),
                CommandHandler('start', start)  # Позволяет перезапустить в любой момент
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)],
    )
    
    app.add_handler(conv_handler)
    
    # Добавляем обработчик ошибок
    app.add_error_handler(error_handler)
    
    # НЕ инициализируем приложение здесь
    # Для webhook приложение будет инициализировано при каждом запросе
    # в том же event loop, где оно будет использоваться
    return app


def main():
    """Главная функция запуска бота (для локального использования)"""
    # Инициализируем приложение
    app = init_application()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_COUNTRY: [
                CallbackQueryHandler(country_selected, pattern='^country_'),
                CommandHandler('start', start)  # Позволяет перезапустить в любой момент
            ],
            SELECTING_TYPE: [
                CallbackQueryHandler(type_selected, pattern='^type_'),
                CommandHandler('start', start)  # Позволяет перезапустить в любой момент
            ],
            ENTERING_ACCOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, account_received),
                CommandHandler('start', start)  # Позволяет перезапустить в любой момент
            ],
            ENTERING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, amount_received),
                CommandHandler('start', start)  # Позволяет перезапустить в любой момент
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)],
    )
    
    print("Бот запущен...")
    print("Нажмите Ctrl+C для остановки")
    
    try:
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
        # Очищаем данные пользователей при остановке
        user_data.clear()
        print("✅ Бот остановлен. Вы можете запустить его снова.")
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
        print(f"❌ Произошла ошибка: {e}")


if __name__ == '__main__':
    main()

