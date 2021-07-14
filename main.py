import config
import json
import random
import re
import traceback
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

import database_api


vk_session = vk_api.VkApi(token=config.token)
vk = vk_session.get_api()
lp = VkBotLongPoll(vk_session, config.group_id)

db = database_api.Database()


def get_user_id(raw_id):  # TODO hueta perepisat'
	user_id = raw_id.split()[1].split('|')[0].replace('[', '')
	raw_user_id = vk.utils.resolveScreenName(v='5.131', screen_name=user_id)
	user_id = raw_user_id.get('object_id')
	if raw_user_id.get('type') == 'group':
		user_id *= -1
	return user_id


def get_layout(text: str) -> str:
	eng_chars = u"~!@#$%^&qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
	rus_chars = u"ё!\"№;%:?йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,"
	letters = {
		'eng_letters': 0,
		'rus_letters': 0
	}
	for i in text:
		if i in eng_chars:
			letters['eng_letters'] += 1
		if i in rus_chars:
			letters['rus_letters'] += 1
	return 'eng' if letters['eng_letters'] > letters['rus_letters'] else 'rus'


def swap_layout(text: str):
	eng_chars = u"~!@#$%^&qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
	rus_chars = u"ё!\"№;%:?йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,"
	if get_layout(text) == 'eng':
		for e, r in zip(eng_chars, rus_chars):
			text = text.replace(e, r)
	else:
		for e, r in zip(rus_chars, eng_chars):
			text = text.replace(e, r)
	return text


def make_rip(text: str):  # ахуевшая, гениальная фича  # TODO хуевый, надо по ударениям искать. Найти открытое апи для ударения в слове
	last_word = text.split()[-1].lower()
	vowels = 'аеиоуёэюяы'
	last_pos1 = last_pos2 = last_pos3 = -1
	for i in range(len(last_word)):
		if last_word[i] in vowels:
			last_pos3 = last_pos2
			last_pos2 = last_pos1
			last_pos1 = i
	if last_pos1 - last_pos2 == 1 and last_pos3 != -1:
		xd_word = last_word[last_pos3:]
	elif last_pos2 == -1:
		xd_word = last_word[last_pos1:]
	else:
		xd_word = last_word[last_pos2:]

	swaps = {
		'а': 'я',
		'о': 'ё',
		'у': 'ю',
		'э': 'е'
	}
	xd_word = 'ху' + swaps.get(xd_word[0], xd_word[0]) + xd_word[1:]
	return xd_word



FEATURES = ['rip']  # гениальное решение (я еблан)



def main():
	for event in lp.listen():
		if event.type != VkBotEventType.MESSAGE_NEW:
			continue
		if db.check_admin(event.message.from_id, event.message.peer_id):  # в теории юзера можно вынести
			if re.match(r'/mute @?[0-9A-z_.]*', event.message.text):
				user_id = get_user_id(event.message.text)
				db.mute_pig(user_id, event.message.peer_id)
			elif re.match(r'/unmute @?[0-9A-z_.]*', event.message.text):
				user_id = get_user_id(event.message.text)
				db.unmute_pig(user_id, event.message.peer_id)
			elif re.match(r'/addadm @?[0-9A-z_.]*', event.message.text):
				user_id = get_user_id(event.message.text)
				db.add_admin(user_id, event.message.peer_id)
			elif re.match(r'/deladm @?[0-9A-z_.]*', event.message.text):
				user_id = get_user_id(event.message.text)
				db.delete_admin(user_id, event.message.peer_id)
			elif re.match(r'/chance [A-z0-9] [01]?\.[0-9]*', event.message.text):
				db.set_feature_chance(feature=event.message.text.split()[1],
										chat_id=event.message.peer_id,
										chance=float(event.message.text.split()[2]))
			elif re.match(r'/del', event.message.text):
				for msg in event.message.fwd_messages:
					try:
						vk.messages.delete(v='5.131', delete_for_all=1,
										conversation_message_ids=msg.get('conversation_message_id'),
										peer_id=event.message.peer_id)
					except vk_api.exceptions.ApiError:
						traceback.print_exc()
				try:
					vk.messages.delete(v='5.131', delete_for_all=1,
									conversation_message_ids=event.message.conversation_message_id,
									peer_id=event.message.peer_id)
					vk.messages.send(message=f'Удалил {len(event.message.fwd_messages)} беброчек',
									v='5.131',
									peer_id=event.message.peer_id,
									random_id=0)
				except vk_api.exceptions.ApiError:
					traceback.print_exc()
		if db.check_muted_pig(event.message.from_id, event.message.peer_id):
			try:
				vk.messages.delete(v='5.131', delete_for_all=1,
								conversation_message_ids=event.message.conversation_message_id,
								peer_id=event.message.peer_id)
			except vk_api.exceptions.ApiError:
				traceback.print_exc()
			continue  # мнение замученных свиней не учитывается => их команды идут нахуй
		if re.match(r'/swap', event.message.text):  # TODO объединить эту хуйню и хуйню ниже, чтобы меньше строк было
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
		elif re.match(r'/rip', event.message.text):
			try:
				vk.messages.send(message=make_rip(event.message.reply_message.get('text')),
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
		feature_random = random.random()
		for f in FEATURES:
			if feature_random < db.get_feature_chance(event.message.peer_id, f):
				# сделать словарь с фичами и функциями к ним и запускать функцию из словаря сразу, только для этого сначала еще все пиреписать надо на функции будет
				try:
					vk.messages.send(message=make_rip(event.message.text),
										v='5.131',
										peer_id=event.message.peer_id,
										random_id=0,
										forward=json.dumps({
											'peer_id': event.message.peer_id,
											'conversation_message_ids': event.message.conversation_message_id,
											'is_reply': True
										}))
				except vk_api.exceptions.ApiError:
					traceback.print_exc()


if __name__ == '__main__':
	main()
