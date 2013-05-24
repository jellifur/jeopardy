import sqlite3
import re
import codecs

class GenId:
	def __init__(self):
		self.Qid = 0 # Question ID
		self.Aid = 0 # Answer ID

class QnA:
	def __init__(self, Q_id, show_Id, aBoard):
		self.Qid = Q_id
		self.showId = show_Id
		self.board = aBoard
		self.value = None
		self.numAsked = None
		self.category = None
		self.question = None
		self.is_dailyDouble = 0
		self.is_answered = 0
		self.tripleStumper = 0
		self.Aid = None
		self.name = None
		self.answer = None
		self.is_right = None
		self.bet = None

def makeDB(jeopardy):
	j = jeopardy.cursor()

	j.execute('DROP TABLE IF EXISTS Shows')
	j.execute('''CREATE TABLE Shows
	               (showId       int PRIMARY KEY,
	             	showDate     date,
	             	day          varchar(10),
	             	description  varchar(200),
                    gameID       int NOT NULL,
	                season       varchar(10))''')

	j.execute('DROP TABLE IF EXISTS Contestants')
	j.execute('''CREATE TABLE Contestants
	               (name            varchar(50) NOT NULL,
	             	description     varchar(200),
	                showId          int NOT NULL REFERENCES Shows(showId),

					PRIMARY KEY (name, showId))''')

	j.execute('DROP TABLE IF EXISTS Scores')
	j.execute('''CREATE TABLE Scores
				   (name			varchar(50) NOT NULL,
					showId			int NOT NULL REFERENCES Shows(showId),
	                scoreCommBreak  int,
	                score1          int,
	                score2          int,
	                finalScore      int,
	                coryat          int,
	                place           int,
	                winnings        int,

	                PRIMARY KEY (name, showID))''')

	j.execute('DROP TABLE IF EXISTS Questions')
	j.execute('''CREATE TABLE Questions
	               (Qid             int NOT NULL PRIMARY KEY,
	             	showId          int REFERENCES Shows(showId),
	             	board			int CHECK (board > 0 AND board < 4), 
	                value           int,
	                numAsked        int,
	                category        varchar(80),
	                question        varchar(1000) NOT NULL,
	                is_dailyDouble  bit,
	                is_answered     bit,
	                tripleStumper	bit)''')

	j.execute('DROP TABLE IF EXISTS Answers')
	j.execute('''CREATE TABLE Answers
	               (Aid        int NOT NULL PRIMARY KEY,
	               	Qid        int NOT NULL REFERENCES Questions(Qid),
	             	showId     int REFERENCES Shows(showId),
	             	name       varchar(50),
	                answer     varchar(200),
	                is_right   bit,
	                bet        int)''')

def insertQs(j, data):
	j.execute('INSERT INTO Questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
			(data.Qid, data.showId, data.board, data.value, data.numAsked, \
				data.category, data.question, data.is_dailyDouble, \
				data.is_answered, data.tripleStumper))

def insertAs(j, data):
	j.execute('INSERT INTO Answers VALUES (?, ?, ?, ?, ?, ?, ?)', 
			(data.Aid, data.Qid, data.showId, data.name, data.answer, \
				data.is_right, data.bet))
				
def getQs(f, jeopardy, showId, genId, board, condition):
	j = jeopardy.cursor()

	line = f.readline()
	while line.find(condition) == -1:
		genId.Qid+=1
		data = QnA(genId.Qid, showId, board)

		# get category, question and answer
		parsedLine = line.split(' | ')
		data.category = parsedLine[0]
		data.question = parsedLine[1]
		data.answer = parsedLine[2].strip('\n')
		
		# find the person who got the answer right
		line = f.readline()
		line = line.strip('\n')
		if len(line) > 8:
			data.is_answered = 1
			data.name = re.sub('right: ', '', line)

		# Get the wrong answer and value
		wrongAnswers = []
		if f.readline().find('Triple Stumper') != -1:
			data.tripleStumper = 1

		value = ''
		while True:
			line = f.readline()
			if line.find('Value: ') != -1: # find value
				value =  re.sub(r'[\W_]+', '', line)
				value = value.strip('Value')
				break
			else:
				wrongAnswers.append(line)

		if value.find('DD') != -1:
			data.value = value.strip('DD')
			data.is_dailyDouble = 1

		numAsked = f.readline()
		data.numAsked = numAsked.strip('Number: ').strip('\n')
		insertQs(j, data) # Insert Questions
		
		# Insert into Answers (right)
		if data.is_answered == 1:
			data.is_right = 1
			genId.Aid+=1
			data.Aid = genId.Aid
			insertAs(j, data)
		# Insert into Answers (wrong)
		if len(wrongAnswers) > 0:
			data.is_right = 0
			for item in wrongAnswers:
				wrong = item.split(':')
				genId.Aid+=1
				data.Aid = genId.Aid
				data.name = wrong[0]
				data.answer = wrong[1].strip('\n').strip(' ')
				insertAs(j, data)

		line = f.readline()
		
def insertDB(games, f, gameId, jeopardy, genId):
	j = jeopardy.cursor()
	games.seek(0) # Go to the beginning of the file	
	
	# Get show number, day, and date
	firstLine = f.readline()
	firstLine = firstLine.split(' - ')
	showId = firstLine[0]
	date = firstLine[1].split(', ')
	showDay = date[0]
	showDate = date[1] + ', ' + date[2].strip('\n')

	# find season by looking at list of games (another file)
	showSeason = ''
	for line in games:
		tmpLine=[]
		for item in line.split('\t'):
			tmpLine.append(item)
		if tmpLine[1] == str(gameId):
			showSeason = tmpLine[0]

	# Get comments if there comments
	line = f.readline()
	showInfo = ''
	if line.find('Comments:') != -1:
		line = line.split(': ')
		showInfo = line[1].strip('\n')
		f.readline()
	
	# Insert into Shows TABLE
	j.execute('INSERT INTO Shows VALUES (?, ?, ?, ?, ?, ?)',
		(showId, showDate, showDay, showInfo, gameId, showSeason))
	
	board = 0 # Get board number
	# Insert into Contestants
	line = f.readline()
	playerCount = 0
	while True:
		name = re.sub(':.*', '', line)
		name = name.strip('\n')
		first_last = name.split()
		playerInfo = re.sub('.*?:', '', line)
		playerInfo = playerInfo.strip('\n')
		playerCount+=1
		j.execute('INSERT INTO Contestants(name, description, showID) VALUES (?, ?, ?)',
				(name, playerInfo, showId))
		line = f.readline()
		if len(line) == 0:
			return

		if line.find('First Jeopardy!') != -1:
			board = 1
			break
		elif line.find('Second Jeopardy!') != -1:
			board = 2
			break

	if board == 1:
		getQs(f, jeopardy, showId, genId, 1, 'Scores at the first commercial break')
		
		# Insert scores for first commercial break
		for i in range(0, playerCount):
			line = f.readline()
			score = line.split(': ')
			aScore = score[1].replace('$', '')
			aScore = aScore.replace(',', '')
			j.execute('INSERT INTO Scores(name, showID, scoreCommBreak) VALUES (?, ?, ?)',
						(score[0], showId, aScore))
		# Insert scores after the first Jeopardy game
		f.readline() # read in the description of the title
		for i in range(0, playerCount):
			line = f.readline()
			score = line.split(': ')
			aScore = score[1].replace('$', '')
			aScore = aScore.replace(',', '')
			j.execute('UPDATE Scores SET score1=? WHERE name=? AND showId=?',
						(aScore, score[0], showId))

		line = f.readline() # read in the title for the second round
		if line.find('Second Jeopardy!') != -1:
			board = 2

	if board == 2:
		getQs(f, jeopardy, showId, genId, 2, 'Scores at the end of the Double Jeopardy')

		# Insert scores after Double Jeopardy
		for i in range(0, playerCount):
			line = f.readline()
			score = line.split(': ')
			aScore = score[1].replace('$', '')
			aScore = aScore.replace(',', '')
			j.execute('UPDATE Scores SET score2=? WHERE name=? AND showId=?', 
					(aScore, score[0], showId))	

	# ======================== Get FINAL JEOPARDY =============================
	f.readline() # Empty line
	line = f.readline() # Title line
	if line.find('Final Jeopardy!') != -1:
		line = f.readline() # Q and A
		parsedLine = line.split(' | ')
		answer = parsedLine[2].strip('\n')

		# find the person who got the answer right
		line = f.readline()
		line = line.strip('\n')
		is_answered = 0
		if len(line) > 8:
			is_answered = 1
			line = re.sub('right: ', '', line)
			rightNames = line.split(' | ')

		genId.Qid+=1
		j.execute('INSERT INTO Questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
					(genId.Qid, showId, 3, None, None, parsedLine[0], parsedLine[1], 0, \
						is_answered, None))
	
		# Wrong answers
		f.readline()
		wrongAnswers = []
		line = f.readline()
		while line.find('Wagers: ') == -1:
			wrongAnswers.append(line)
			line = f.readline()

		# Get wagers
		wagers = {}
		line = f.readline()
		while line.find('Final scores:') == -1:
			tmp = line.split(': ')
			wagers[tmp[0]] = tmp[1]
			line = f.readline()
		
		if len(wagers) == 0:
			print str(gameId) + ' Has a tiebreaker round (will fix later)'
			return

		# INSERT into Answers (right)
		if is_answered == 1:
			for item in rightNames:
				genId.Aid+=1
				bet = wagers[item]
				bet = bet.replace('$', '')
				bet = bet.replace(',', '')
				j.execute('INSERT INTO Answers VALUES (?, ?, ?, ?, ?, ?, ?)', 
							(genId.Aid, genId.Qid, showId, item, answer, 1, bet))

		# Insert into Answers (wrong)
		if len(wrongAnswers) > 0:
			for item in wrongAnswers:
				wrong = item.split(': ')
				genId.Aid+=1
				answer = wrong[1].strip('\n')
				bet = wagers[wrong[0]]
				bet = bet.replace('$', '')
				bet = bet.replace(',', '')
				j.execute('INSERT INTO Answers VALUES (?, ?, ?, ?, ?, ?, ?)', 
							(genId.Aid, genId.Qid, showId, wrong[0], answer, 0, bet))

		# Get Final Scores
		for i in range(0, playerCount):
			line = f.readline()
			newline = re.sub('\(.*\)', '', line)
			score = newline.split(': ')
			aScore = score[1].replace('$', '')
			aScore = aScore.replace(',', '')
			j.execute('UPDATE Scores SET finalScore=? WHERE name=? AND showId=?', 
						(aScore, score[0], showId))

			# Get place and winnings
			if line.find('(') != -1:
				place = 0
				line = re.sub('.*?\(', '', line)
				places = line.split(': ')
				if line.find('champion') != -1 or line.find('Semifinalist') != -1:
					place = 1
				else:
					place = re.sub(r'\D', '', places[0])
				#get winnings, sometimes they don't have winnings, but move onto next round
				winnings = 0
				if line.find('$') != -1:
					winnings = re.sub('.*?\$', '', line)
					winnings = winnings.strip(')\n')
					winnings = winnings.replace(',', '')
					winnings = re.sub(r'\D', '', winnings)
				j.execute('UPDATE Scores SET place = ?, winnings=? WHERE name=? AND showId=?', 
							(place, winnings, score[0], showId))

		# Get Coryat Scores
		f.readline() # Empty
		f.readline() # Title
		for i in range(0, playerCount):
			line = f.readline()
			newline = re.sub('\(.*\)', '', line)
			score = newline.split(': ')
			aScore = score[1].replace('$', '')
			aScore = aScore.replace(',', '')
			j.execute('UPDATE Scores SET coryat=? WHERE name=? AND showId=?', 
						(aScore, score[0], showId))
	# =========================================================================

def main():
	jeopardy = sqlite3.connect('jeopardy.db')
	makeDB(jeopardy)
	# Open files
	games = open("games.txt")

	print 'Working...'
	genId = GenId()
	for i in range(1,4118):
		#if i == 3889 or i == 1473 or i == 2172 or i == 3081: # Rounds with Tiebreakers
		#	continue
		fileName = str(i)+'_Qs.txt'
		try:
			f = codecs.open('questions/'+fileName, encoding='utf-8')
			insertDB(games, f, i, jeopardy, genId)
			f.close()
		except IOError:
			print str(i) + ": Can't open", fileName

	# ===================== debugging stuff =========================
	j = jeopardy.cursor()
	#for row in j.execute('SELECT * FROM Shows'):
	#	print row

	#for row in j.execute('SELECT * FROM Contestants'):
	#	print row

	#for row in j.execute('SELECT * FROM Questions'):
	#	print row

	#for row in j.execute('SELECT * FROM Answers'):
	#	print row
	# ================================================================
	games.close()
	jeopardy.commit()
	jeopardy.close()
	print 'done.'
	return

main()
