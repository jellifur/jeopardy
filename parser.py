# Parse J! Archive for Jeopardy Questions
import re
import codecs

# Check for special characters like " ' < > and 
def replaceChar(line):
	line = line.replace('&quot;', '"')
	line = line.replace('\\', '')
	line = line.replace('&lt;', '<')
	line = line.replace('&gt;', '>')
	line = line.replace('&amp;', '&')
	line = line.replace('<i>', '')
	line = line.replace('</i>', '')
	line = line.replace('&lt;i&gt;', '')
	line = line.replace('<br />', ' ')
	return line

# get wagers
def getWagers(line):
	players = re.findall('wrong&quot;.*?&lt;|right&quot;.*?&lt;', line)
	for i in range(0,len(players)):
		players[i] = re.sub('.*?&quot;&gt;', '', players[i])
		players[i] = re.sub('&lt;', '', players[i])

	wagers = re.findall('&lt;td&gt;.*?&lt;/td&gt;', line)
	for i in range(0,len(wagers)):
		wagers[i] = re.sub('&lt.*?gt;', '', wagers[i])
		
	output = 'Wagers: '
	for i, item in enumerate(wagers):
		output = output + '\n' + players[i] + ': ' + item

	return output	
	
def getQuestions(line, final):
	# Get answer
	answer = re.sub('<.*?correct_response.*?&gt;', '', line)
	if re.search('&lt;i&gt;.*?&lt;', answer) != None:
		answer = answer.replace('&lt;i&gt;', '')
		answer = re.sub('&lt;.*?>', '', answer)
	else:
		answer = re.sub('&lt;.*?>', '', answer)
	answer = answer.strip(' ')
	answer = replaceChar(answer)
	
	# Find contestant(s) with right answer
	rightOutput = 'right: '
	right = []
	right = re.findall('right&quot;&gt;.*?&lt;', line)
	isRight = False
	if len(right)!=0:
		for i, item in enumerate(right):
			right[i] = re.sub('right&.*?&gt;', '', item)
			right[i] = right[i].replace('&lt;', '')
		for item in right:
			if isRight:
				rightOutput += ' | '
			rightOutput += item
			isRight = True
	rightOutput+='\n'
	# Find contestant(s) with wrong answers
	wrongOutput = 'Wrong: '
	if not final:
		wrong = []
		wrong = re.findall('wrong&quot;&gt;.*?&lt;', line)

		if len(wrong)!=0:
			for i, item in enumerate(wrong):
				wrong[i] = item.replace('wrong&quot;&gt;', '')
				wrong[i] = wrong[i].replace('&lt;', '')

			for i, item in enumerate(wrong):
				if item == 'Triple Stumper' or item == 'Quadruple Stumper':
					wrongOutput = wrongOutput + item
					wrong.pop(i)

			for item in wrong:
				item = re.sub(r'\W+', '', item)
				match = re.findall(item+':.*?\)', line)
				if len(match) != 0:
					tmp = re.sub('\)', '', match[0])
					tmp = tmp.strip('\n')
					tmp = replaceChar(tmp)
					wrongOutput = wrongOutput + '\n' + tmp	
	else:
		wrong = []
		wrong = re.findall('wrong&quot;&gt;.*?&lt;/td&gt;.*?&lt;/td&gt;', line)
		if len(wrong)!=0:
			for i, item in enumerate(wrong):
				wrong[i] = item.replace('wrong&quot;&gt;', '')
				wrong[i] = re.sub('&lt;.*?top&quot;&gt;', ': ', wrong[i])
				wrong[i] = wrong[i].replace('&lt;/td&gt;', '')
				wrong[i] = replaceChar(wrong[i])
				wrongOutput = wrongOutput + '\n' + wrong[i]
	
	# Get the question
	quest = re.sub(".*?_stuck', '", '', line)
	quest = re.sub("'\).*>", '', quest)
	# Check for URLs
	quest = replaceChar(quest)
	quest = quest.replace('a href="', '')
	quest = quest.replace('">', '> ')
	quest = quest.replace('</a>', '')
	quest = re.sub('" target=.*?>', '>', quest)
	quest = quest.replace('\n', '')

	newLine = quest + ' | ' + answer + rightOutput + wrongOutput
	return newLine

def loopQuestions(iFile, oFile, categories, condition):
	oFile.write('\n')
	i = -1 # index for categories
	for line in iFile:
		if line.find('<td class="clue">') != -1:
			if i == 5:
				i = 0
			else:
				i+=1
		elif line.find('<div onmouseover=') != -1:
			newLine = getQuestions(line, False)
			oFile.write(categories[i]+' | '+newLine+'\n')
		# Get the question's value
		elif line.find('<td class="clue_value') != -1:
			line = re.sub('<.*?>', '', line)
			line = line.strip(' ')
			oFile.write('Value: '+line)
		# Get the question's number
		elif line.find('<td class="clue_order_number') != -1:
			line = re.sub('<.*?>', '', line)
			line = line.strip(' ')
			oFile.write('Number: '+line)

		if line.find(condition) != -1:
				return
	
def parse(number, iFile):
	oFile = codecs.open('questions/'+str(number)+'_Qs.txt', 'w', 'utf-8')
	print number
	# Get show number and date
	for line in iFile:
		if line.find('game_title') != -1:
			line = re.sub('<.*?>', '', line)
			line = line.strip('Show #')
			oFile.write(line)
			break
	
	# Get show comments
	for line in iFile:
		if line.find('<div id="game_comments"></div>') != -1:
			break
		elif line.find('game_comments') != -1:
			comment = re.sub('<div.*?>', '', line)
			comment = comment.strip(' ')
			if comment.find('</div>') != -1:
				comment = comment.replace('</div>', '')
				oFile.write('Comments: ' + comment)
				break
			elif comment.find('<br />') != -1:
				comment = comment.replace('<br />', '  ')
				comment = comment.strip('\n').strip('\r')
		elif line.find('</div>'):
			line = line.replace('</div>', '')
			comment+=line
			oFile.write('Comments: ' + comment)
			break
		else:
			line = line.replace('<br />', '  ')
			line = line.strip('\n').strip('\r')
			comment+=line
			
	# Get name of contestants
	firstRound = False
	secondRound = False
	oFile.write('Contestants:\n')
	for line in iFile:
		if line.find('p class="contestants"') != -1:
			line = line.replace('</a>,', ':')
			line = re.sub('<.*?>', '', line)
			line = line.strip(' ')
			oFile.write(line)
		if line.find('<div id="jeopardy_round">') != -1:
			firstRound = True
			break
		elif line.find('<div id="double_jeopardy_round">') != -1:
			secondRound = True
			break
	
	if firstRound:
		# Get the first set of categories
		categories = []
		counter = 0 # count number of categories (6)
		for line in iFile:
			if line.find('category_name') != -1:
				counter+=1
				line = re.sub('<.*?>', '', line)
				line = line.strip(' ').strip('\n')
				line = replaceChar(line)
				categories.append(line)
			if counter == 6:
				break

		if len(categories)==0:
			return
			
		# Output categories
		oFile.write('First Jeopardy! Round: ' + categories[0])
		for i in range(1,len(categories)):
			oFile.write(', ' + categories[i])
			
		# Get questions
		loopQuestions(iFile, oFile, categories, 'Scores at the first commercial break')

		# Get scores
		players = []
		scores = []
		for line in iFile:
			if line.find('score_player_nickname') != -1:
				line = re.sub('<.*?>', '', line)
				line = line.strip('\n').strip(' ')
				players.append(line)
			elif line.find('score_positive') != -1 or line.find('score_negative') != -1:
				line = re.sub('<.*?>', '', line)
				line = line.strip('\n').strip(' ')
				scores.append(line)
			elif line.find('Scores at the end of the Jeopardy! Round:') != -1:
				break;
				
		oFile.write('Scores at the first commercial break (after clue 15)\n')
		for i in range(0, len(players)):
			oFile.write(players[i]+': ')
			oFile.write(scores[i]+'\n')
			
		scores = []
		for line in iFile:
			if line.find('score_positive') != -1 or line.find('score_negative') != -1:
				line = re.sub('<.*?>', '', line)
				line = line.strip('\n').strip(' ')
				scores.append(line)
			elif line.find('double_jeopardy_round') != -1:
				secondRound = True
				break;
				
		oFile.write('Scores at the end of the Jeopardy! Round:\n')
		for i in range(0, len(players)):
			oFile.write(players[i]+': ')
			oFile.write(scores[i]+'\n')
		
	if secondRound:
		# Get the first set of categories
		categories=[]
		counter = 0 # count number of categories (6)
		for line in iFile:
			if line.find('category_name') != -1:
				counter+=1
				line = re.sub('<.*?>', '', line)
				line = line.strip(' ').strip('\n')
				line = replaceChar(line)
				categories.append(line)
			if counter == 6:
				break

		if len(categories)==0:
			return
	
		# Output categories.
		oFile.write('Second Jeopardy! Round: ' + categories[0])
		for i in range(1,len(categories)):
			oFile.write(', ' + categories[i]) # Output categories
			
		# Get questions
		loopQuestions(iFile, oFile, categories, 'Scores at the end of the Double Jeopardy!')

		# Get scores
		players = []
		scores = []
		for line in iFile:
			if line.find('score_player_nickname') != -1:
				line = re.sub('<.*?>', '', line)
				line = line.strip('\n').strip(' ')
				players.append(line)
			elif line.find('score_positive') != -1 or line.find('score_negative') != -1:
				line = re.sub('<.*?>', '', line)
				line = line.strip('\n').strip(' ')
				scores.append(line)
			elif line.find('Final Jeopardy! Round') != -1:
				break
		
		oFile.write('Scores at the end of the Double Jeopardy! Round:\n')
		for i in range(0, len(players)):
			oFile.write(players[i]+': ')
			oFile.write(scores[i]+'\n')
			
	# Final Jeopardy
	oFile.write('\n')
	category = ''
	for line in iFile:
		if line.find('<div onmouseover=') != -1:
			newLine = getQuestions(line, True)
			value = getWagers(line)
		elif line.find('category_name') != -1:
			category = re.sub('<.*?>', '', line)
			category = category.strip(' ').strip('\n')
			category = replaceChar(category)
		elif line.find('Final scores:') != -1:
			break

	if len(category) == 0:
		return

	oFile.write('Final Jeopardy! Round\n')
	oFile.write(category + ' | ' + newLine)
	oFile.write('\n'+value)	
		
	# Get Final scores
	scores = []
	remarks = []
	for line in iFile:
		if line.find('score_positive') != -1 or line.find('score_negative') != -1:
			line = re.sub('<.*?>', '', line)
			line = line.strip('\n').strip(' ')
			scores.append(line)
		elif line.find('score_remarks') != -1:
			line = re.sub('<.*?>', '', line)
			line = line.strip(' ').strip('\n')
			remarks.append(line)
		elif line.find('Game dynamics:') != -1:
			break;

	oFile.write('\nFinal scores:\n')
	for i, item in enumerate(players):
		oFile.write(item+': ')
		oFile.write(scores[i])
		oFile.write(' ('+remarks[i]+')\n')
	
	# Get coryat scores
	players = []
	scores = []
	remarks = []
	for line in iFile:
		if line.find('score_player_nickname') != -1:
			line = re.sub('<.*?>', '', line)
			line = line.strip('\n').strip(' ')
			players.append(line)
		elif line.find('score_positive') != -1 or line.find('score_negative') != -1:
			line = re.sub('<.*?>', '', line)
			line = line.strip('\n').strip(' ')
			scores.append(line)
		elif line.find('score_remarks') != -1:
			line = re.sub('<.*?>', '', line)
			line = line.strip(' ').strip('\n')
			remarks.append(line)
		elif line.find('Game dynamics:') != -1:
			break;
			
	oFile.write('\nCoryat scores\n')
	for i, item in enumerate(players):
		oFile.write(item+': ')
		oFile.write(scores[i])
		oFile.write(' ('+remarks[i]+')\n')

	oFile.close()
	return
	
def main():
	print 'working...'
	for i in range(1,4118): # Open files
		fileName = str(i)+'.txt'
		try:
			iFile = codecs.open('game_pages/'+fileName, 'r', 'cp1252')
			parse(i, iFile)
			iFile.close()
		except IOError:
			print "Can't open", fileName

	print 'done.'
	return

main()
