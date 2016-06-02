import re
import sys
import socket
from lxml import etree
from SPARQLWrapper import SPARQLWrapper, JSON
	

def print_questions():
	questions = ["1. Waar waren de olympische Zomerspelen 2008 gehouden?",
				"2. Waar werd Michael Phelps geboren?",
				"3. Wanneer werd Andy Murray geboren?",
				"4. Wie opende de Olympische Zomerspelen 2012?",
				"5. Wanneer sluiten de Olympische Zomerspelen 2016 ?",
				"6. Hoeveel atleten deden er mee aan de Olympische Zomerspelen 2004?",
				"7. Door hoeveel landen werd er deelgenomen aan de Olympische Zomerspelen van 2000 ?",
				"8. Wat is het gewicht van Katie Ledecky ?",
				"9. Wat is de club van Missy Franklin ?",
				"10. Wat is de nationaliteit van Andy Murray ?"]
	
	for i in questions:
		print(i)
		
	return questions
	
	
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
	

def create_queries(property_uri,conc):

	querie_first = 'select ?answer where { ?concept  rdfs:label "'
	querie_second = '"^^xsd:string. ?concept prop-nl:'
	querie_last = ' ?answer .}'

	cont_list = []
	pairCounts_file = open('pairCounts','r')
	for line in pairCounts_file:
		line = line.rstrip()
		if re.search(conc, line):
			context = line.split('	')
			cont_list.append(context)
			if conc == context[0]:
				concept = context[0]
			
	word_list = similar_words(property_uri)
	answer_list = []


	for word in word_list:
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
					print(answer_list[0])
			break
	if answer_list == []:
		print("Can't find answer")

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

	xml = etree.fromstring(bytes_received)
	return xml			

def tree_yield(xml):
	leaves = xml.xpath('descendant-or-self::node[@word]')
	words = []
	for l in leaves:
		words.append(l.attrib["word"])
	return " ".join(words)
	
def get_concept(get_question):
	xml = alpino_parse(get_question)
	concept = []
	names = xml.xpath('//node[@spectype="deeleigen"]')
	names_pp = xml.xpath('//node[@neclass="year"]')
	for name in names:
		concept.append(name.attrib["word"])
	for pp in names_pp:
		concept.append(pp.attrib["word"])
	conc = " ".join(concept)
	return conc

def get_prop(get_question):
	xml = alpino_parse(get_question)
	uri_prop = []
	names = xml.xpath('//node[@genus="zijd"]')
	verb = xml.xpath('//node[@infl="psp"]')
	names_pp = xml.xpath('//node[@rel="whd"]')
	werkwoord = xml.xpath('//node[@pos="verb"]')
	for name in names:
		uri_prop.append(name.attrib["word"])
	for pp in names_pp:
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
			for i in werkwoord:
				werkw = i.attrib["root"]
				if question_type == "Wie":
					persoon = werkw + "er"
					uri_prop.append(persoon)
				else:
					nw = werkw + "ing"
					uri_prop.append(nw)
	noun = xml.xpath('//node[@lcat="np" and @rel="hd"]')
	for n in noun:
		if 'word' in n.attrib:
			uri_prop.append(n.attrib["word"])			

	return uri_prop
		
def main(argv):
	questions = print_questions()
	get_question = input("Stel een vraag:")
	conc = get_concept(get_question)
	property_uri = get_prop(get_question)
	queries = create_queries(property_uri,conc)
	
if __name__ == "__main__":
	main(sys.argv)
	
