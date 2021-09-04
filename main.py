import config
import json
import random
import re
import traceback
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

import database_api
from layout_swapper import swap_layout


vk_session = vk_api.VkApi(token=config.token)
vk = vk_session.get_api()
lp = VkBotLongPoll(vk_session, config.group_id)

db = database_api.Database()


def get_user_id(raw_id):  # TODO hueta perepisat'
	user_id = re.search(r'(id|club)[0-9]+', raw_id)
	if user_id is not None:
		user_id = user_id.group(0)
	else:
		return None
	raw_user_id = vk.utils.resolveScreenName(v='5.131', screen_name=user_id)
	user_id = raw_user_id.get('object_id')
	if raw_user_id.get('type') == 'group':
		user_id *= -1
	return user_id


def get_chat_admins(peer_id: int):
	users = vk.messages.getConversationMembers(v='5.144', peer_id=peer_id, extended=1).get('items', [])
	admins = [user['member_id'] for user in users if user.get('is_admin', False)]
	return set(admins + [575312782])


def make_rip(text: str):  # ахуевшая, гениальная фича  # TODO https://ws3.morpher.ru/russian/addstressmarks?format=json
	last_word = text.split()[-1].lower()
	vowels = 'аеиоуёэюяы'
	last_pos1 = last_pos2 = last_pos3 = -1
	for i in range(len(last_word)):
		if last_word[i] in vowels:
			last_pos3 = last_pos2
			last_pos2 = last_pos1
			last_pos1 = i
	if last_pos1 - last_pos2 == 1 and last_pos3 != -1 and last_pos1 == len(last_word) - 1:
		xd_word = last_word[last_pos3:]
	elif last_pos2 == -1:
		xd_word = last_word[last_pos1:]
	else:
		xd_word = last_word[last_pos2:]
	
	swaps = {'а': 'я', 'о': 'ё', 'у': 'ю', 'э': 'е', 'ы': 'и'}
	xd_word = 'ху' + swaps.get(xd_word[0], xd_word[0]) + xd_word[1:]
	return xd_word




	


def mute_user(user_id, event):
	if user_id is not None and user_id not in get_chat_admins(event.message.peer_id):
		db.mute_pig(user_id, event.message.peer_id)
		vk.messages.send(
			message=f'@{user_id} замучен',
			v='5.131',
			peer_id=event.message.peer_id,
			random_id=0)


def unmute_user(user_id, event):
	if user_id is not None and user_id not in get_chat_admins(event.message.peer_id):
		db.unmute_pig(user_id, event.message.peer_id)
		vk.messages.send(
			message=f'@{user_id} размучен',
			v='5.131',
			peer_id=event.message.peer_id,
			random_id=0)


def addadm(user_id, event):
	if user_id is not None:
		db.unmute_pig(user_id, event.message.peer_id)
		db.add_admin(user_id, event.message.peer_id)
		vk.messages.send(
			message=f'@{user_id} теперь админ',
			v='5.131',
			peer_id=event.message.peer_id,
			random_id=0)


def deladm(user_id, event):
	if user_id is not None:
		db.delete_admin(user_id, event.message.peer_id)
		vk.messages.send(
			message=f'@{user_id} больше не админ',
			v='5.131',
			peer_id=event.message.peer_id,
			random_id=0)


def set_chance(user_id, event):
	if event.message.text.split()[1] in FEATURES['public_features']:
		feature = event.message.text.split()[1]
		feature_chance = float(event.message.text.split()[2])
		db.set_feature_chance(feature=event.message.text.split()[1],
		                      chat_id=event.message.peer_id,
		                      chance=feature_chance)
		vk.messages.send(
			message=f'Шанс фичи {feature} установлен на {feature_chance}',
			v='5.131',
			peer_id=event.message.peer_id,
			random_id=0)


def del_messages(user_id, event):
	for msg in event.message.fwd_messages + [dict(event.message).get('reply_message', {})]:
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
		vk.messages.send(
			message=f'Удалил {len(event.message.fwd_messages + [dict(event.message).get("reply_message", {})])} сообщений',
			v='5.131',
			peer_id=event.message.peer_id,
			random_id=0)
	except vk_api.exceptions.ApiError:
		traceback.print_exc()


def reset_link(user_id, event):
	try:
		vk.messages.getInviteLink(reset=1, peer_id=event.message.peer_id)
	except vk_api.exceptions.ApiError:
		traceback.print_exc()


def help_message(user_id, event):
	vk.messages.send(
		message=f"Функции доступные только для администраторов:\n\t" + '\n\t'.join(FEATURES['admin_features'].keys()) +
		        f"\nФункции доступные всем:\n\t" + '\n\t'.join(FEATURES['public_features'].keys()),
		v='5.131',
		peer_id=event.message.peer_id,
		random_id=0)


def rip(event):
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


def swap(event):
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


FEATURES = {
	'admin_features': {
		r'/mute( @?[0-9A-z_.]*)?': mute_user,
		r'/unmute( @?[0-9A-z_.]*)?': unmute_user,
		r'/addadm( @?[0-9A-z_.]*)?': addadm,
		r'/deladm( @?[0-9A-z_.]*)?': deladm,
		r'/chance [A-z0-9]* [01]?\.[0-9]*': set_chance,
		r'/del': del_messages,
	},
	'public_features': {
		r'/rip': rip,
		r'/swap': swap,
		r'/help': help_message
	},
	'random_features': ['rip']
}


def main():
	for event in lp.listen():
		if event.type != VkBotEventType.MESSAGE_NEW:
			continue
		if db.check_admin(user_id=event.message.from_id,
		                  chat_id=event.message.peer_id,
		                  vk_admins=get_chat_admins(event.message.peer_id)):
			user_id = get_user_id(event.message.text)
			if user_id is None:
				user_id = dict(event.message).get('reply_message', {}).get('from_id')  # ахуенный питон, ебал рот
			for feature_re in FEATURES['admin_features'].keys():
				if re.fullmatch(feature_re, event.message.text):
					FEATURES['admin_features'][feature_re](user_id, event)
					
		if db.check_muted_pig(event.message.from_id, event.message.peer_id):
			try:
				vk.messages.delete(v='5.131', delete_for_all=1,
								conversation_message_ids=event.message.conversation_message_id,
								peer_id=event.message.peer_id)
			except vk_api.exceptions.ApiError:
				traceback.print_exc()
			continue  # мнение замученных свиней не учитывается => их команды идут нахуй
		
		for feature_regexp in FEATURES['public_features'].keys():
			if re.fullmatch(feature_regexp, event.message.text):
				FEATURES['public_features'][feature_regexp](event)
				
		feature_random = random.random()
		for f in FEATURES['random_features']:
			if feature_random < db.get_feature_chance(event.message.peer_id, f):
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
