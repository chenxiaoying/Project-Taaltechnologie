# Project Taaltechnologie
# Group 13: Roald Baas, Xiaoying Chen, Anne Wanningen
# We nemen aan dat de bestanden pairCounts en similarwords aanwezig zijn in dezelfde directory als dit bestand

from SPARQLWrapper import SPARQLWrapper, JSON
from operator import itemgetter, attrgetter, methodcaller
import sys
import re
import socket
from  lxml import etree

MAXITERS = 10
OUTPUT_FILE = 'output.txt'
QUESTIONTYPES = ['wat', 'wie', 'waar', 'wanneer', 'hoeveel', 'welke', 'hoe'] #TODO: questiontypes uitbreiden. 'hoe' moet helemaal aan het eind (zodat 'hoeveel' eerst komt). Dan kunnen we verder zoeken: hoe lang, hoe vaak, etc.

# Stuur de SPARQL query naar dbpedia
def send_query(query):
  sparql.setQuery(query)
  sparql.setReturnFormat(JSON)
  results = sparql.query().convert()
  return results

# Bepaal het vraagtype van een lijst woorden aan de hand van QUESTIONTYPES
def getQuestionType(words):
  for type in QUESTIONTYPES:
    # Als een bepaald type (uit QUESTIONTYPES) in de gegeven woorden aanwezig is gaat het om dit type
    if isIn(type, words):
      return type
  # Als er niets is gevonden is het type None
  return None

# Zit x in y?
def isIn(x, y):
  # Haal hoofdletters er uit voor elk element
  if x.lower() in y.lower():
    return True
  else:
    return False

# tree_yield: gegeven bij assignment 4
# The function tree_yield appends the value of the word-attribute for all nodes that are dominated by the node 'xml' that is the argument of the function, and returns this a single string....
def tree_yield(xml):
  leaves = xml.xpath('descendant-or-self::node[@word]')
  words = []
  for l in leaves :
      words.append(l.attrib["word"])
  return " ".join(words)

# Analyseer de vraag: bepaal het soort vraag
# Wanneer? Wie? Wat? Welke? Hoeveel? In welk(e)? Hoe --?
def analyse_question(question):
  # Geef de vraag door naar de alpino parser, verkrijg de XML
  # Zoek naar de keywords als Wie, Wanneer, Wat, etc. mbv xpath
  print(question)
  xml = alpino_parse(question)
  questionType = None
  
  # Vind de whd (wat, wie, hoeveel --, wanneer, hoe --, etc)
  #TODO: misschien checken of deze leeg is voordat hij verder gaat.
  whd = xml.xpath('//node[@rel="whd"]')
  # Als whd leeg is, is het vraagtype niet goed te bepalen
  if whd == []:
    print('\tWHD IS LEEG!!!')
  # De whd is niet leeg, we kunnen een vraagtype bepalen
  else:
    whd = tree_yield(whd[0])
    print('\tWHD:\t' + whd)
    #TODO: check of woorden als 'wie', 'wat', etc in de whd zitten en aan de hand hiervan het vraagtype bepalen
    questionType = getQuestionType(whd)
    # Nu weten we het vraagtype:
    
  if questionType is not None:
    print('\tQUESTION TYPE:\t' + questionType)
  else:
    # Als q type None is even extra aandacht aan schenken.
    print('\tQUESTION TYPE:\t None!!!!!!!!!!!!')
    
  # Als whd 'hoeveel' is weten we direct waar het om gaat: de woorden die erna komen.
  if questionType == 'hoeveel':
    print(whd[8:])
    
  # Wie/Wat is de/het X van Y
  #TODO: werkt nog niet zoals het moet
  if questionType == 'wie' or questionType == 'wat':
    print('\tWie/Wat')
    # Als 'is' op de juiste plek staat
    if 'is' in question[4:6]:
      print('\tWie/Wat is...')
      subject = xml.xpath('//node[@rel="su"]')
      if subject is not []:
        subSentence = subStr((int(subject[0].attrib["begin"]), int(subject[0].attrib["end"])), question)
        subject = noPrepositions(subSentence)
      
      X = subject[0:subject.index(' van ')]
      X = X.rsplit()
      print(X)
      
      # X kijken naar similar words
      Y = subject[subject.index(' van ')+5:]
      Y = noPrepositions(Y)
      print(Y)
      
      # Lijst waar de antwoorden in komen te staan
      ans = []
      # Als X uit meerdere woorden bestaat, probeer ze allemaal
      for j in X:
        query = """
          SELECT STR(?naam)
          WHERE {
            ?onderwerp foaf:isPrimaryTopicOf wiki-nl:""" + Y.replace(' ', '_') + """ .
            ?onderwerp prop-nl:""" + j + ' ?' + 'naam' + """ .
          }
          ORDER BY DESC(?naam)
          """
        print(query)
        # Geef de query door met SPARQLWrapper.
        results = send_query(query)
        
        # Print het antwoord.
        for result in results["results"]["bindings"]:
          for arg in result :
            answer = result[arg]["value"]
            # Maak van de link een naam (deze gewoon via SPARQL opvragen zorgt er voor dat hij string-waarden niet meer als antwoord vind)
            if 'http://' in answer:
              answer = answer[31:].replace('_', ' ')
            #print(answer)
            ans.append(answer)
            print(ans)
      return ans
      
  
  # Anders niks returnen
  return None
  
  # Vind de subject
#  subject = xml.xpath('//node[@rel="su"]')
#  subSentence = subStr((int(subject[0].attrib["begin"]), int(subject[0].attrib["end"])), question)
#  subject = noPrepositions(subSentence)

#  if (subject != None): print("\tSUBJECT:\t" + subject)

#  (prop, uri) = findURI(subject, 10)
#  if (uri != None): print("\tFOUND:\t\t" + prop + "\n\tURI:\t\t" + uri)
#  print()



# Try to find a substring that matches a URI
def findURI(words, it=0):
  if (words == None) or (it > MAXITERS): return (None, None)   

  (prop, uri) = testForURI(words)
  if (uri != None): return (prop,uri)

  words = re.sub("[^\w]", " ",  words).split()

  for i, word in enumerate(words):
    tmpList =  words
    altWord = getAlt(word)
    if (altWord != None): tmpList[i] = altWord
    else: tmpList.pop(i)
    if (len(tmpList) > 0): (prop, uri) = findURI(' '.join(tmpList))
    if (uri != None): return (prop,uri)
    
  findURI(' '.join(words[1:]))



# Find a URI given a string
def testForURI(string):
  print("\t\t\tTESTING FOR:  " + string)
  uri = None
  results = []

  for element in counts:
    m = re.match(r"(^"+string+")\s"+".*", element, re.I)
    if (m != None):
      # print(m.group(0))
      parts = re.split("\t", m.group(0))
      results.append([parts[0], parts[1], parts[2]])

  for (prop, uri, count) in results:
    if uri != None:
      return (prop,uri)

  return (None, None)



 







# Find a URI given a keyword
#def findURI(word, it=0):
#  uri = None
#  results = []
#
#  for element in counts:
#    m = re.match(r"(^"+word+")\s"+".*", element, re.I)
#    if (m != None):
#      # print(m.group(0))
#      parts = re.split("\t", m.group(0))
#      results.append([parts[0], parts[1], parts[2]])
#
#  for (prop, uri, count) in results:
#    if uri != None:
#      return (prop,uri)
#
#  while (uri==None)and(it<MAXITERS):
#    newWord = getAlt(word)
#    if (newWord != word and newWord != None):
#      (prop, uri) = findURI(newWord, it+1)
#      return (prop, uri)
#
#  words = re.sub("[^\w]", " ",  word).split()
#
#  if (len(words) > 1): findURI(' '.join(words[1:]), it+1)
#
#  return (None, None)
  
  

# Output format: ID \t Answer1 \t Answer2...
def give_output(ID, answers):
  f = open(OUTPUT_FILE, 'a')
  # Als answers leeg is, geef aan dat er geen antwoord is gevonden
  if answers == []:
    line = 'Geen antwoord gevonden'
  else:
    # Er zijn 1 of meer antwoorden: maak van de lijst een string gescheiden door tabs
    line = '\t'.join(str(answer) for answer in answers)
    
  line = str(ID) + '\t' + line
  # Append de regel aan de output file, gescheiden met een newline
  f.write(line + '\n')
  #print(line)



# Input format: ID \t Question
def find_answer(sentence):
  print(sentence)



# Get a single alternative word from similarWords
def getAlt(word):
  for element in similarWords:
    m = re.match(r"(?P<original>^"+word+r")\#(?P<new>[^#]+)", element)
    if (m != None):
      return m.group('new')
  return None



# Get rid of prepositions
def noPrepositions(sentence):
    m = re.match(r"(de |het |een )?(?P<result>.+)", sentence)
    return m.group('result')



# Get a substring
def subStr(interval, sentence):
  words = re.sub("[^\w]", " ",  sentence).split()
  answer = words[interval[0]]
  for word in words[interval[0]+1:interval[1]]:
    answer += " " + word
  return answer



# parse input sentence and return alpino output as an xml element
def alpino_parse(sent, host='zardoz.service.rug.nl', port=42424):
  s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  s.connect((host,port))
  sent = sent + "\n\n"
  sentbytes = sent.encode('utf-8')
  s.sendall(sentbytes)
  bytes_received= b''
  while True:
    byte = s.recv(8192)
    if not byte:
      break
    bytes_received += byte
#  print(bytes_received.decode('utf-8'), file=sys.stderr)
  xml = etree.fromstring(bytes_received)
  return xml



def main(argv):
  # Maak de output.txt file eerst leeg voordat de antwoorden er bij in komen
  open(OUTPUT_FILE, 'w').close()
  # Hoog ID op met 1 elke iteratie over sys.stdin. Vervang ID door het ID van de vraag indien aanwezig.
  ID = 0
  #TODO: tijdelijk gewoon meteen de vragen txt meegeven voor het gemak
  sys.stdin = open('questions.txt', 'r', encoding='utf-8')
  
  for sentence in sys.stdin:
    sentence = sentence.rstrip()
    # Haal het ID en de vraag uit de zin
    if '\t' in sentence:
      ID = sentence[0:sentence.index('\t')]
      question = sentence[sentence.index('\t')+1:]
    # Geen ID voor de vraag: sentence is de gehele vraag, geef het een ID
    else:
      ID = ID + 1
      question = sentence
    
    #TODO: debug antwoorden weghalen
    answers = ['Answer 1', 2, 'Answer 3']
    #TODO: stuur de vraag door voor analyse, SPARQL.
    #Voorlopig zit het SPARQL query gedeelte al in analyse_question. Misschien apart maken
    answers = analyse_question(question)
    #TODO: aan de hand van deze analyse weten we welk soort SPARQL query we moeten maken

    give_output(ID, answers)






sparql = SPARQLWrapper("http://nl.dbpedia.org/sparql")
sparql.setReturnFormat(JSON)
pairCounts = open('pairCounts', 'r', encoding='utf-8')
counts = re.split("\n+", pairCounts.read())
similarWords = re.split("\n+", open('similarwords', 'r', encoding='utf-8').read())
    
if __name__ == "__main__":
  main(sys.argv)


  
