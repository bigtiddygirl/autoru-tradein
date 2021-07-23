import config
import logging
import asyncio
import gspread
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from sql_bd import SQLite


# логи
logging.basicConfig(level=logging.INFO)

# бот
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)

# БД
db = SQLite('db.db')


# Команда активации подписки
@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
	if(not db.subscriber_exists(message.from_user.id)):
		# если юзера нет в базе, добавляем его
		db.add_subscriber(message.from_user.id)
	else:
		# если он уже есть, то просто обновляем ему статус подписки
		db.update_subscription(message.from_user.id, True)
	
	await message.answer("Вы успешно подписались на рассылку!")

# Команда отписки
@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
	if(not db.subscriber_exists(message.from_user.id)):
		# если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
		db.add_subscriber(message.from_user.id, False)
		await message.answer("Вы итак не подписаны.")
	else:
		# если он уже есть, то просто обновляем ему статус подписки
		db.update_subscription(message.from_user.id, False)
		await message.answer("Вы успешно отписаны от рассылки.")
		
async def scheduled(wait_for):
	while True:
		await asyncio.sleep(wait_for)
		gc = gspread.service_account(filename='fluid-gamma-319906-a4ea6dcfcfee.json')
		url = 'https://docs.google.com/spreadsheets/d/1aRAa35d9nYyksSFd-NmqBZlnAFFYt08K3M-wRvFPsbo/'
		sh = gc.open_by_url(url)
		worksheet = sh.get_worksheet(2)
		list_of_lists = worksheet.get_all_values()
		lol = len(worksheet.col_values(2))

		subs = db.get_subscriptions()

		rows = open('lastkey.txt', 'r').read()
		if lol == int(rows):
			pass
		else:
			diff = lol - int(rows)
			for s in subs:
				message = ''
				for i in range(int(rows), lol):
					message += f' * {list_of_lists[i][2]} {list_of_lists[i][3]} {list_of_lists[i][5]}, оценка: {list_of_lists[i][11]}, {list_of_lists[i][12]}\n'
				await bot.send_message(s[1], f'В таблицу по трейдину добавлены записи\nКоличество: {diff}\n{message}', disable_notification=True)
				with open('lastkey.txt', 'w') as f:
					f.write(str(lol))
					f.close()



if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.create_task(scheduled(10))
	executor.start_polling(dp, skip_updates=True)



