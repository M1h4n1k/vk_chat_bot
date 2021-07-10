import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import sqlite3
import re
import traceback
import json



token = 'токен'
vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()
lp = VkBotLongPoll(vk_session, 'группа')

conn = sqlite3.connect('main_table.db')
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS muted_pigs (
							user_id INTEGER,
							chat_id INTEGER
						);''')
cur.execute('''CREATE TABLE IF NOT EXISTS admins (
							user_id INTEGER,
							chat_id INTEGER
						);''')


def mute_pig(user_id, chat_id):
	cur.execute('''INSERT INTO muted_pigs (user_id, chat_id) 
					VALUES(?, ?)''', (user_id, chat_id))
	conn.commit()


def unmute_pig(user_id, chat_id):
	cur.execute('''DELETE FROM muted_pigs 
				WHERE user_id=? AND chat_id=?''', (user_id, chat_id))
	conn.commit()


def check_muted_pig(user_id, chat_id):
	cur.execute('''SELECT 1 FROM muted_pigs WHERE user_id=? AND chat_id=?''', (user_id, chat_id))
	return cur.fetchone() is not None


def get_user_id(raw_id):
	user_id = raw_id.split()[1].split('|')[0].replace('[', '')
	raw_user_id = vk.utils.resolveScreenName(v='5.131', screen_name=user_id)
	user_id = raw_user_id.get('object_id')
	if raw_user_id.get('type') == 'group':
		user_id *= -1
	return user_id



def add_admin(user_id, chat_id):
	cur.execute('''INSERT INTO admins (user_id, chat_id) 
						VALUES(?, ?)''', (user_id, chat_id))
	conn.commit()


def delete_admin(user_id, chat_id):
	cur.execute('''DELETE FROM admins 
					WHERE user_id=? AND chat_id=?''', (user_id, chat_id))
	conn.commit()


def check_admin(user_id, chat_id):
	cur.execute('''SELECT 1 FROM admins WHERE user_id=? AND chat_id=?''', (user_id, chat_id))
	return cur.fetchone() is not None or user_id == 575312782



def swap_layout(text: str):
	start_text = text
	eng_chars = u"~!@#$%^&qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
	rus_chars = u"ё!\"№;%:?йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,"
	for e, r in zip(eng_chars, rus_chars):
		text = text.replace(e, r)
	if text == start_text:
		for e, r in zip(rus_chars, eng_chars):
			text = text.replace(e, r)
	return text


def main():
	for event in lp.listen():
		if event.type != VkBotEventType.MESSAGE_NEW:
			continue
		if check_admin(event.message.from_id, event.message.peer_id):
			if re.match(r'/mute @?[0-9A-z_.]*', event.message.text):
				user_id = get_user_id(event.message.text)
				mute_pig(user_id, event.message.peer_id)
			elif re.match(r'/unmute @?[0-9A-z_.]*', event.message.text):
				user_id = get_user_id(event.message.text)
				unmute_pig(user_id, event.message.peer_id)
			elif re.match(r'/addadm @?[0-9A-z_.]*', event.message.text):
				user_id = get_user_id(event.message.text)
				add_admin(user_id, event.message.peer_id)
			elif re.match(r'/deladm @?[0-9A-z_.]*', event.message.text):
				user_id = get_user_id(event.message.text)
				delete_admin(user_id, event.message.peer_id)
			elif event.message.text == '/del':
				for msg in event.message.fwd_messages:
					try:
						vk.messages.delete(v='5.131', delete_for_all=1,
										conversation_message_ids=msg.get('conversation_message_id'),
										peer_id=event.message.peer_id)
					except vk_api.exceptions.ApiError:
						traceback.print_exc()
				vk.messages.delete(v='5.131', delete_for_all=1,
								conversation_message_ids=event.message.conversation_message_id,
								peer_id=event.message.peer_id)
				vk.messages.send(message=f'Удалил {len(event.message.fwd_messages)} беброчек',
								v='5.131',
								peer_id=event.message.peer_id,
								random_id=0)
		if event.message.text == '/swap':
			try:
				vk.messages.send(message=swap_layout(event.message.reply_message.get('text')),
								v='5.131',
								peer_id=event.message.peer_id,
								random_id=0,
								forward=json.dumps({
									'peer_id': event.message.peer_id,
									'conversation_message_ids': event.message.reply_message.get('conversation_message_id'),
									'is_reply': True
								}))
				vk.messages.delete(v='5.131', delete_for_all=1,
								conversation_message_ids=event.message.conversation_message_id,
								peer_id=event.message.peer_id)
			except vk_api.exceptions.ApiError:
				traceback.print_exc()
		if check_muted_pig(event.message.from_id, event.message.peer_id):
			try:
				vk.messages.delete(v='5.131', delete_for_all=1,
								conversation_message_ids=event.message.conversation_message_id,
								peer_id=event.message.peer_id)
			except vk_api.exceptions.ApiError:
				traceback.print_exc()


if __name__ == '__main__':
	main()
