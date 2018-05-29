import csv
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from stanfordcorenlp import StanfordCoreNLP


#Create lists with post titles from csv files. 
with open('ccdi_investigations.csv', newline='') as ccdi:
	reader = csv.DictReader(ccdi)
	c_title = []
	c_text = []
	for row in reader:
		c_title.append(row['title'])
		c_text.append(row['text'])

with open('sichuan_cdi_data.csv', newline='') as sichuan:
	reader = csv.DictReader(sichuan)
	s_title = []
	s_text = []
	for row in reader:
		s_title.append(row['title'])
		s_text.append(row['text'])

with open('yunnan_cdi_data.csv', newline='') as yunnan:
	reader = csv.DictReader(yunnan)
	y_title = []
	y_text = []
	for row in reader:
		y_title.append(row['title'])
		y_text.append(row['text'])

##Compare titles and text to find 100% matches and print results.
#sichuan_ccdi_title_matches = set(c_title) & set(s_title)
#print('Matching post titles between sichuan cdi and ccdi: ' + str(len(sichuan_ccdi_title_matches)))
#print(sichuan_ccdi_title_matches)
#
#sichuan_ccdi_text_matches = set(c_text) & set(s_text)
#print('Matching post text between sichuan cdi and ccdi: ' + str(len(sichuan_ccdi_text_matches)))
#print(sichuan_ccdi_text_matches)
#
#yunnan_ccdi_title_matches = set(c_title) & set(y_title)
#print('Matching post titles between yunnan cdi and ccdi: ' + str(len(yunnan_ccdi_title_matches)))
#print(yunnan_ccdi_title_matches)
#
#yunnan_ccdi_text_matches = set(c_text) & set(y_text)
#print('Matching post text between yunnan cdi and ccdi: ' + str(len(yunnan_ccdi_text_matches)))
#print(yunnan_ccdi_text_matches)



#Compare sichuan cdi and ccdi titles and find %80+ matches.
matches_sc = []
for st in s_title:
	for ct in c_title:
		ratio = fuzz.ratio(st,ct)
		if ratio >= 80:
			match = {
			'sichuan_title': st,
			'ccdi_title': ct,
			'match_ratio': ratio,
			}
			matches_sc.append(match)

print('Number of likely matches found between sichuan cdi and ccdi: ' + str(len(matches_sc)))
#for row in matches_sc:
#	print(row)
#	
#
##Write sichuan matches to a csv.
#with open('sichuan_vs_ccdi_test.csv', 'w', newline='') as output_file1:
#	fieldnames = ['sichuan_title', 'ccdi_title', 'match_ratio']
#	dict_writer = csv.DictWriter(output_file1, fieldnames=fieldnames)
#
#	dict_writer.writeheader()
#	dict_writer.writerows(matches_sc)


#Use nested loop to compare yunnan cdi and ccdi titles and find %80+ matches.
matches_yc = []
for yt in y_title:
	for ct in c_title:
		ratio = fuzz.ratio(yt,ct)
		if ratio >= 80:
			match = {
			'yunnan_title': yt,
			'ccdi_title': ct,
			'match_ratio': ratio,
			}
			matches_yc.append(match)

print('Number of likely matches found between yunnan cdi and ccdi: ' + str(len(matches_yc)))
#for item in matches_yc:
#	print(item)
#
##Write yunnan matches to a csv.
#with open('yunnan_vs_ccdi_test.csv', 'w', newline='') as output_file2:
#	fieldnames = ['yunnan_title', 'ccdi_title', 'match_ratio']
#	dict_writer = csv.DictWriter(output_file2, fieldnames=fieldnames)
#
#	dict_writer.writeheader()
#	dict_writer.writerows(matches_yc)

# Get names from fuzzywuzzy matches using Stanford
# Named Entity Recognizer (NER) and verify match.

# connect to corenlp server
nlp = StanfordCoreNLP('http://corenlp.run', lang='zh', port=80)

verified_matches_sc = []
for match in matches_sc:
	# Get name from first match string
	sentence = match['sichuan_title']
	ner = nlp.ner(sentence)
	name1 = [item[0] for item in ner if 'PERSON' in item]
	
	# Get name from second match string
	sentence = match['ccdi_title']
	ner = nlp.ner(sentence)
	name2 = [item[0] for item in ner if 'PERSON' in item]

	if name1 == name2:
		print('match')
		match['name'] = name1
		verified_matches_sc.append(match)

verified_matches_yc = []
for match in matches_yc:
	# Get name from first match string
	sentence = match['yunnan_title']
	ner = nlp.ner(sentence)
	name1 = [item[0] for item in ner if 'PERSON' in item]
	
	# Get name from second match string
	sentence = match['ccdi_title']
	ner = nlp.ner(sentence)
	name2 = [item[0] for item in ner if 'PERSON' in item]

	if name1 == name2:
		print('match')
		match['name'] = name1
		verified_matches_yc.append(match)

# Close corenlp server connection.
nlp.close()

print('sichuan and ccdi fuzzywuzzy verified matches: ' + str(len(verified_matches_sc)))
print('yunnan and ccdi fuzzywuzzy verified matches: ' + str(len(verified_matches_yc)))

#Write verified yunnan matches to a csv.
with open('yunnan_vs_ccdi_name_verification_test.csv', 'w', newline='') as output_file2:
	fieldnames = ['yunnan_title', 'ccdi_title', 'match_ratio', 'name']
	dict_writer = csv.DictWriter(output_file2, fieldnames=fieldnames)

	dict_writer.writeheader()
	dict_writer.writerows(verified_matches_yc)
#Write verified sichuan matches to a csv.
with open('sichuan_vs_ccdi_name_verification_test.csv', 'w', newline='') as output_file1:
	fieldnames = ['sichuan_title', 'ccdi_title', 'match_ratio', 'name']
	dict_writer = csv.DictWriter(output_file1, fieldnames=fieldnames)

	dict_writer.writeheader()
	dict_writer.writerows(verified_matches_sc)
	