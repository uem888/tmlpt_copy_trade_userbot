import re
import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

# Конфигурация клиента Telegram
# api_id, api_hash получаем здесь: my.telegram.org
api_id = 1234567
api_hash = 'api_hash'
phone_number = '+79997775533'
password = 'password'  # Пароль от 2FA, если включен

# ID пользователя, чьи сообщения отслеживаем
SOURCE_USER_ID = 123456789  # Замените на реальный ID пользователя

# Получатель (лучше использовать @username)
TARGET_BOT = '@SomeTargetBot'  # Замените на username бота-получателя, где у вас настроены автопокупка и автопродажа по критериям (можно Fasol)

# Паттерн для поиска адреса контракта Solana
SOLANA_ADDRESS_PATTERN = r'[1-9A-HJ-NP-Za-km-z]{32,44}[^\s\n]*'

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot.log',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# Инициализация клиента Telegram
client = TelegramClient('bot_session', api_id, api_hash)

@client.on(events.NewMessage(from_users=SOURCE_USER_ID))
async def handle_new_message(event):
    """Обрабатывает новые сообщения от указанного пользователя"""
    try:
        message_text = event.message.message
        
        if not message_text:
            return
        
        logger.info(f"Получено сообщение от пользователя: {message_text[:100]}...")
        
        # Ищем адреса контрактов Solana
        solana_addresses = re.findall(SOLANA_ADDRESS_PATTERN, message_text)
        logger.info(f"Найдены адреса: {solana_addresses}")
        
        for raw_address in solana_addresses:
            # Очищаем адрес от спецсимволов в конце
            address = re.sub(r'[^1-9A-HJ-NP-Za-km-z]', '', raw_address)
            
            # Пропускаем слишком короткие строки
            if len(address) < 32:
                continue
                
            # Отправка адреса целевому боту
            await client.send_message(
                TARGET_BOT,
                address,
                parse_mode='md'
            )
            
            logger.info(f"Отправлен адрес боту {TARGET_BOT}: {address}")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}", exc_info=True)

async def main():
    try:
        logger.info("Запуск бота...")
        await client.connect()
        
        if not await client.is_user_authorized():
            logger.info("Требуется авторизация...")
            await client.send_code_request(phone_number)
            try:
                await client.sign_in(phone_number, input('Введите код подтверждения: '))
            except SessionPasswordNeededError:
                await client.sign_in(password=password)
        
        me = await client.get_me()
        logger.info(f"Авторизация успешна! Пользователь: {me.first_name} (ID: {me.id})")
        logger.info(f"Отслеживаем сообщения от пользователя: {SOURCE_USER_ID}")
        logger.info(f"Отправляем адреса боту: {TARGET_BOT}")
        
        await client.run_until_disconnected()
    except Exception as e:
        logger.critical(f"Ошибка при запуске: {str(e)}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную.")
    finally:
        logger.info("Завершение работы.")
