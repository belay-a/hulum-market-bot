import asyncio
from aiogram import Bot

# የራስዎን Token እዚህ ያስገቡ
API_TOKEN = '8411154664:AAEJu7xKKVHQYnXsAM-PGtpzg-ULMdvI3xk'

async def delete_wb():
    bot = Bot(token=API_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook በተሳካ ሁኔታ ተሰርዟል! አሁን bot.py ን መጀመር ይችላሉ።")
    await bot.session.close()

if __name__ == '__main__':
    asyncio.run(delete_wb())