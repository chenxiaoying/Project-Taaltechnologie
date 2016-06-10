import re
import sys
import socket
from lxml import etree
from SPARQLWrapper import SPARQLWrapper, JSON

## Find Synonyms for the property using the file similarwords
def similar_words(property_uri):
	word_list = []
	word_list.append(property_uri[0])
	similarwords_file = open('similarwords','r')
	for line in similarwords_file:
		words = line.split('#')
		if property_uri[0] in words:
			for word in words:
				if re.match("^[a-zA-Z_]*$", word):
					word_list.append(word)
				
	return word_list

# Find the exist URI from the file pairCounts
def gener_concept(conc):
	cont_list = []
	concept = ''
	pairCounts_file = open('pairCounts','r')
	for line in pairCounts_file:
		line = line.rstrip()
		
		# If change the wordgroup "Olympische Spelen" to Olympische Zomerspelen
		## if Olympische Zomerspelen for that year doesn't exist, 
		##change to Olympische Winterspelen
		if "Olympische Spelen" in conc:
			conc = conc.replace("Olympische Spelen","Olympische Zomerspelen")
		if re.search(conc, line):
			context = line.split('	')
			cont_list.append(context)
			if conc == context[0]:
				concept = context[0]
			else:
				if "Olympische Spelen" in conc:
					conc = conc.replace("Olympische Spelen","Olympische Winterspelen")
					if re.search(conc, line):
						context = line.split('	')
						cont_list.append(context)
						if conc == context[0]:
							concept = context[0]
	return concept
							

				
## Create queries using the generated properties and URI		
def create_queries(property_uri,concept):
	
	print("property:",property_uri)
	print("URI:",concept)

	answer_list = []
	
	querie_first = 'select ?answer where { ?concept  rdfs:label "'
	querie_second = '"^^xsd:string. ?concept prop-nl:'
	querie_last = ' ?answer .}'
	
	
	#property_uri = similar_words(property_uri)
    
	for word in property_uri:
		if 'concept' in locals():
			querie_whole = querie_first + concept + querie_second + word + querie_last
			sparql = SPARQLWrapper("http://nl.dbpedia.org/sparql")
			sparql.setQuery(querie_whole)
			sparql.setReturnFormat(JSON)
			results = sparql.query().convert()
			if results["results"]["bindings"] != []:
				for result in results["results"]["bindings"]:
					for arg in result:
						erase_url = result[arg]["value"].rsplit('/')
						answer = arg + " : " + erase_url[-1]
						answer_list.append(answer)
						print(answer_list[0],'\n\n')
						return answer_list[0]
				break
				
	if answer_list == []:
		print("Geen antwoord gevonden")
	return answer_list


## Alpino Parser
def alpino_parse(sent, host='zardoz.service.rug.nl',port=42424):
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	s.connect((host,port))
	sent = sent + "\n\n"
	sentbytes = sent.encode('utf-8')
	s.sendall(sentbytes)
	bytes_received = b''
	while True:
		byte = s.recv(8192)
		if not byte:
			break
		bytes_received += byte
	#print(bytes_received.decode('utf-8'), file=sys.stderr)
	xml = etree.fromstring(bytes_received)
	return xml			

def tree_yield(xml):
	leaves = xml.xpath('descendant-or-self::node[@word]')
	words = []
	for l in leaves:
		words.append(l.attrib["word"])
	return " ".join(words)

## Find the object for the questions
## and use it as concept to search for exist URI
def get_concept(get_question):
	xml = alpino_parse(get_question)
	concept = []
	names = xml.xpath('//node[@spectype="deeleigen"]')
	year = xml.xpath('//node[@pt="tw"]')
	for name in names:
		concept.append(name.attrib["word"])
	for i in year:
		yearnumb = i.attrib["word"]
		if yearnumb.isdigit() == True:
			concept.append(yearnumb)
	conc = " ".join(concept)
	
	return conc


def get_nouns(get_question,conc):
	xml = alpino_parse(get_question)
	uri = []
	names = xml.xpath('//node[@ntype]')	
	for name in names:
		uri.append(name.attrib["word"])
	bijv_nw = xml.xpath('//node[@vform]')
	if bijv_nw != []:
		for i in bijv_nw:
			uri.append(i.attrib["word"])
		create_queries(uri,conc)
	return uri

## Vind subject van de vraag
## gebruik het als property
def get_prop(get_question):
	
	xml = alpino_parse(get_question)
	uri_prop = []
	
	## soms is het subject een zelfstandig naamwoord
	names = xml.xpath('//node[@ntype]')
	for name in names:
		uri_prop.append(name.attrib["word"])
		
	## als een bijvoegelijk naamwoord voorkomt
	bijvnw = xml.xpath('//node[@pt="adj"]')
	for word in bijvnw:
		uri_prop.append(word.attrib['word'])
	
	## vind het werkwoord en vraagtype(wie/waar/wanneer)		
	verb = xml.xpath('//node[@pt="ww"]')
	q_type = xml.xpath('//node[@vwtype]')

	for pp in q_type:
		if 'word' in pp.attrib:
			question_type = pp.attrib["word"]
			for v in verb:
				if question_type == "Waar" and v.attrib["word"] == "geboren":
					uri_prop.append("geboorteplaats")
				elif question_type == "Wanneer" and v.attrib["word"] == "geboren":
					uri_prop.append("geboortedatum")
				elif question_type == "Waar":
					uri_prop.append("plaats")
				else:
					uri_prop.append(v.attrib["root"])
			for i in verb:
				werkw = i.attrib["root"]
				
				#als vraagt naar een persoon(begin met wie)
				##verander werkwoord naar zelfstandig nw (bij +er)
				#voorbeeld open wordt opener
				if question_type == "Wie" or question_type == "wie":
					persoon = werkw + "er"
					uri_prop.append(persoon)
					
	noun = xml.xpath('//node[@lcat="np" and @rel="hd"]')
	for n in noun:
		if 'word' in n.attrib:
			uri_prop.append(n.attrib["root"])			

	return uri_prop
	
## als gevraagt naar medailles
def get_medailles(property_uri,conc):
	
	wn = 0
	
	##als gouden,goude enzovoort voorkomt in de vraag
	##property wordt brons,goud,zilver
	for word in property_uri:
		if 'bron' in word:
			property_uri[wn] = 'brons' 
		elif 'goud' in word:
			property_uri[wn] = 'goud'
		elif 'zilver' in word:
			property_uri[wn] = 'zilver'
		wn = wn + 1
	
	## als medailles gevraag van een land, zoek naar de juste URI
	## dbpedia page: land_op_de_hoeveelste spelen
	## voorbeeld: Nederland_op_de_Olympische_Zomerspelen_2012
	for word in property_uri:
		if "medaille" in word:
			for i in property_uri:
				if i[0].isupper() == True:
					conc = i + ' op ' + 'de ' + conc
		break
					
	create_queries(property_uri,conc)

def main(argv):
	get_question = open("olympics_questions.txt","r")
	queries_num = 0
	for question in get_question:
		if '\t' in question: 
			question = question[question.index('\t')+1:]
			print(question)
			conc = get_concept(question)
			newc = gener_concept(conc)
			#ana_first = get_nouns(question,conc)
			property_uri = get_prop(question)
			
			me = get_medailles(property_uri,newc)
	
if __name__ == "__main__":
	main(sys.argv)
	
