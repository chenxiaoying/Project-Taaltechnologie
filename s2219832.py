from SPARQLWrapper import SPARQLWrapper, JSON
from operator import itemgetter, attrgetter, methodcaller
import sys
import re
import socket
from  lxml import etree

MAXITERS = 10


def print_example_queries():
	print("Wat is de bijnaam van Mike Tyson?")
	print("Wie is de coach van Anastasia Tsjaun?")
	print("Wat is het discipline van Pieter van den Hoogenband?")
	print("Wat is de positie van Rogier Jansen?")
	print("Wat is het discipline van Hans Elzerman?")
	print("Wat is de organisatie van gewichtheffen?")
	print("Wat is de bijnaam van Emma Snowsill?")
	print("Wie is de eigenaar van het Yankee Stadium?")
	print("Wat is het gewicht van Mark LoMonaco?")
	print("Wie is de trainer van Jimmy Snuka?")




# parse input sentence and return alpino output as an xml element tree
def alpino_parse(sent, host="zardoz.service.rug.nl", port=42424):
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	s.connect((host,port))
	sent = sent + "\n\n"
	sentbytes= sent.encode("utf-8")
	s.sendall(sentbytes)
	bytes_received= b''
	while True:
		byte = s.recv(8192)
		if not byte:
			break
		bytes_received += byte
	# print(bytes_received.decode(’utf-8’), file=sys.stderr)
	xml = etree.fromstring(bytes_received)
	return xml




def getAlt(word):
	for element in similarWords:
		m = re.match(r"(?P<original>^"+word+r")\#(?P<new>[^#]+)", element)
		if (m != None):
#			sys.stderr.write("Found similar word for " + m.group('original') + ":\t" + m.group('new') + "\n")
			return m.group('new')
	return None




def findURI(sentence, it=0):
	words = re.sub("[^\w]", " ",  sentence).split()
	#	print("Finding URI for: "+subj)
	results = findMatches(sentence, it)
	for (prop, uri, count) in results:
		if uri != None:
			return (prop,uri)	
		while (uri==None)and(it<MAXITERS):
			newWord = getAlt(subj)
			if (newWord != subj and newWord != None):
				(prop, uri) = findURI(newWord, it+1)
				return (prop, uri)
#	else:
#		allResults = []
#		for word in words:
#			print("Finding matches for: "+word)
#			results = findMatches(word, it)
#			if results != None: allResults += results
#		for result in allResults:
#			for resultComp in allResults:
#				if result != resultComp:
#					if result[1]==resultComp[1]:
#						result[2] += resultComp[2]
#						print("Found match!\t" + result[0] + "\tAND\t" + resultComp[0])
#		finalResults = sorted(allResults, key=lambda elem: int(elem[2]), reverse = True)
#		#print(finalResults)
#		for (prop, uri, count) in finalResults:
#			if uri != None:
#				return (prop,uri)	
	return (None, None)



def findMatches(subj, it=0):
	uri = None
	results = []

	for element in counts:
		m = re.match(r"(^"+subj+")\s"+".*", element, re.I)
		if (m != None):
		#       print(m.group(0))
			parts = re.split("\t", m.group(0))
			results.append([parts[0], parts[1], parts[2]])

	return sorted(results, key=lambda elem: int(elem[2]), reverse = True)









def create_and_fire_query(question):

#	m = re.match(r"((?P<qType>((Wie)|(Wat)){1}) is(?P<pn1>(( )|( de )|( het )))(?P<subj1>.*) van(?P<pn2>(( )|( de )|( het )){1})){1}(?P<subj2>(?!(de )|(het ))+.*[^?]{1})\??$", question)
	m = re.match(r"((Wie|Wat) is( de| het)? (?P<subj1>.+?))+? van(( de| het)? (?P<subj2>.*))+\?", question)
	if (m == None):
		print("Could not parse the question. Please strictly adhere to the above format.")
		sys.exit()

#	print(m.group(0))

	subj1=(m.group('subj1'))
#	print(subj1)
	subj2=(m.group('subj2'))
#	print(subj2)

	term = m.group('subj1')
	name = "\"" + m.group('subj2') + "\""

	prop = findURI(subj1)[0]
	uri = findURI(subj2)[1]
	results = None

	if prop != None and uri != None:
		sparql.setQuery("""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
		PREFIX prop-nl: <http://nl.dbpedia.org/property/>
		PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
		SELECT str(?y)
		WHERE  {
		<"""+uri+"""> prop-nl:"""+prop+""" ?y
		}"""
		)
		results = sparql.query().convert()

	i = 0
	while (results == None or len(results["results"]["bindings"])==0) and i < MAXITERS:
		i += 1
#		sys.stderr.write("Could not find an entry for \"" + subj1 + "\".\n")
		subj1 = getAlt(subj1)
		if subj1 == None:
			break
#		sys.stderr.write("Trying for \"" + subj1 + "\"..\n")
		prop = findURI(subj1)[0]
		if prop != None and uri != None:
			sparql.setQuery("""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
			PREFIX prop-nl: <http://nl.dbpedia.org/property/>
			PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
			SELECT str(?y)
			WHERE  {
			<"""+uri+"""> prop-nl:"""+prop+""" ?y
			}"""
			)
			results = sparql.query().convert()
#	print(prop)
#	print(uri)
	if results == None or len(results["results"]["bindings"])==0 or prop == None or uri == None:
#		sys.stderr.write("Could not find an entry..\n")
		return None
	return results["results"]["bindings"][0]["callret-0"]["value"]




def subStr(interval, sentence):
	words = re.sub("[^\w]", " ",  sentence).split()
	answer = words[interval[0]]
	for word in words[interval[0]+1:interval[1]]:
		answer += " " + word
	return answer


def noPrepositions(sentence):
	m = re.match(r"(de |het |een )?(?P<result>.+)", sentence)
	return m.group('result')


def tryProp(prop, uri):
	print("Trying:\t" + prop + "\t" + uri)
	if prop != None and uri != None:
		sparql.setQuery("""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
		PREFIX prop-nl: <http://nl.dbpedia.org/property/>
		PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
		SELECT str(?y)
		WHERE  {
		<"""+uri+"""> prop-nl:"""+prop+""" ?y
		}"""
		)
		results = sparql.query().convert()
	if results == None or len(results["results"]["bindings"])==0 or prop == None or uri == None:
		return None
	return results


def getAllProps(uri):
	sparql.setQuery("""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX prop-nl: <http://nl.dbpedia.org/property/>
	PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
	SELECT distinct ?property
	WHERE  {
	<"""+uri+"""> ?property ?val
	}"""
	)
	return sparql.query().convert()


def main(argv):
#	print_example_queries()
#	for line in sys.stdin:
#		line = line.rstrip()
#		answer = create_and_fire_query(line)
#		if answer == None:
#			print("Could not find an answer.")
#		else:
#			print(answer)
	sentence = "Welke organisatie is van de Olympische Spelen?"
	words = re.sub("[^\w]", " ",  sentence).split()

	xml = alpino_parse(sentence)
	#sentence = xml.xpath('//sentence')
	#print(xml.xpath('sentence')[0].text)
	
	names = xml.xpath('//node[@rel="su"]') #spectype="deeleigen"]')
#	names = xml.xpath('//node[@cat="np"]') #spectype="deeleigen"]')
	for name in names :
		#print(name.attrib)
		subSentence = subStr((int(name.attrib["begin"]), int(name.attrib["end"])), sentence)
		print(noPrepositions(subSentence))
		(prop, uri) = findURI(noPrepositions(subSentence))
		if uri != None: print(prop + ":\t" + uri)
		print("\n\n")
	
	names = xml.xpath('//node[@pt="n"]') #spectype="deeleigen"]')
#	names = xml.xpath('//node[@cat="np"]') #spectype="deeleigen"]')
	nouns = []
	for name in names :
		word = name.attrib["lemma"]
		if word != None:
			nouns.append(word)
			print(word)
		print("\n\n")
	
	props = getAllProps(uri)
	results = []
	for res in props['results']['bindings']:
		result = str(res['property']['value'])
		m = re.match(r"http://nl.dbpedia.org/property/(?P<res>.*)$", result)
		if m != None:
			results.append(m.group('res'))
	
	for prop in results:
		#print(prop)
		for word in nouns:
			#print("\t" + word)
			#m = re.match("(" + word + ")+", prop, re.I) 
			if word.lower() in prop.lower():
				result = tryProp(prop, uri)
				if result != None:
					print(result["results"]["bindings"][0]["callret-0"]["value"])
				
#	print("\n\n\n\n")

#	for word in nouns:
#		(prop2, uri2) = findURI(word, 10)
#		if prop2 != None:
#			print(uri2 + ":")
#			if " " in prop2:
#				m = re.match(r"(?P<result>[^/]*)$", uri2)
#				if m != None:
#					print(m.group('result') + ":")
#					print(tryProp(m.group('result'), uri))
#			else:
#				print(tryProp(prop2, uri))





sparql = SPARQLWrapper("http://nl.dbpedia.org/sparql")
sparql.setReturnFormat(JSON)
pairCounts = open('pairCounts', 'r')
counts = re.split("\n+", pairCounts.read())
similarWords = re.split("\n+", open('similarwords', 'r').read())

if __name__ == "__main__":
	main(sys.argv)

