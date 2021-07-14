import sqlite3


class Database:
	def __init__(self):
		self.conn = sqlite3.connect('main_table.db')
		self.cur = self.conn.cursor()
		self.cur.execute('''CREATE TABLE IF NOT EXISTS muted_pigs (
									user_id INTEGER,
									chat_id INTEGER
								);''')
		self.cur.execute('''CREATE TABLE IF NOT EXISTS admins (
									user_id INTEGER,
									chat_id INTEGER
								);''')
		self.cur.execute('''CREATE TABLE IF NOT EXISTS feature_chances (
											feature TEXT,
											chance REAL,
											chat_id INTEGER
										);''')

	def mute_pig(self, user_id: int, chat_id: int):
		self.cur.execute('''INSERT INTO muted_pigs (user_id, chat_id) 
						VALUES(?, ?)''', (user_id, chat_id))
		self.conn.commit()

	def unmute_pig(self, user_id: int, chat_id: int):
		self.cur.execute('''DELETE FROM muted_pigs 
					WHERE user_id=? AND chat_id=?''', (user_id, chat_id))
		self.conn.commit()

	def check_muted_pig(self, user_id: int, chat_id: int) -> bool:
		self.cur.execute('''SELECT 1 FROM muted_pigs WHERE user_id=? AND chat_id=?''', (user_id, chat_id))
		return self.cur.fetchone() is not None

	def add_admin(self, user_id, chat_id):
		self.cur.execute('''INSERT INTO admins (user_id, chat_id) 
							VALUES(?, ?)''', (user_id, chat_id))
		self.conn.commit()

	def delete_admin(self, user_id, chat_id):
		self.cur.execute('''DELETE FROM admins 
						WHERE user_id=? AND chat_id=?''', (user_id, chat_id))
		self.conn.commit()

	def check_admin(self, user_id, chat_id) -> bool:
		self.cur.execute('''SELECT 1 FROM admins WHERE user_id=? AND chat_id=?''', (user_id, chat_id))
		return self.cur.fetchone() is not None or user_id == 575312782

	def get_feature_chance(self, chat_id: int, feature: str) -> int:
		self.cur.execute('''SELECT chance FROM feature_chances WHERE feature=? AND chat_id=?''', (feature, chat_id))
		chance = self.cur.fetchone() or [-1]
		return chance[0]

	def set_feature_chance(self, chat_id: int, feature: str, chance: float):
		if self.get_feature_chance(chat_id, feature) == -1:
			self.cur.execute('''INSERT INTO feature_chances (chance, chat_id, feature) 
							VALUES(?, ?, ?)''', (chance, chat_id, feature))
		else:
			self.cur.execute('''UPDATE feature_chances
								SET chance=?
								WHERE chat_id=? AND feature=?''', (chance, chat_id, feature))
		self.conn.commit()
