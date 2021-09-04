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