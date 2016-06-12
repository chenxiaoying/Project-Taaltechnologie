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

# Parse een 'Wie/Wat is de/het X van Y?' vraag
def parseXofYQuestion(xml, question):
  # Lijst waar de antwoorden in komen te staan
  ans = []
  # Vind de subject
  subject = xml.xpath('//node[@rel="su"]')
  #directObject = xml.xpath('//node[@cat="np" and @rel="obj1"]')
  #if directObject is not []:
  #  for word in directObject:
  #    ding = tree_yield(word)
  #    print(ding)
  if subject is not []:
    subSentence = subStr((int(subject[0].attrib["begin"]), int(subject[0].attrib["end"])), question)
    subject = noPrepositions(subSentence)
  
  #print('\tSUBJECT:\t' + subject)
  
  if ' van ' in subject:
    X = subject[0:subject.index(' van ')]
    X = X.rsplit()
    #print(X)
    
    #X kijken naar similar words
    Y = subject[subject.index(' van ')+5:]
    Y = noPrepositions(Y)
    #print(Y)
  else:
    # Hij heeft het niet goed herkend
    #TODO: andere oplossing bedenken.
    return None
  
  #TODO: Y bepalen aan de hand van deeleigen in plaats van checken wat er na ' van ' komt
  Y2 = []
  deeleigen = xml.xpath('//node[@spectype="deeleigen"]')
  for name in deeleigen:
    Y2.append(name.attrib["word"])
  Y2 = ' '.join(Y2)
  print(Y2)
  
  
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
    #print(query)
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
        
  print('---------------')
  print(ans)
  print('---------------')
  return ans

# Analyseer de vraag: bepaal het soort vraag
# Wanneer? Wie? Wat? Welke? Hoeveel? In welk(e)? Hoe --?
# Wie/wat is de/het X van Y
# List-questions (Welke landen...)
# Count-questions (Hoeveel landen...)
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
    #print('\tWHD:\t' + whd)
    #TODO: check of woorden als 'wie', 'wat', etc in de whd zitten en aan de hand hiervan het vraagtype bepalen
    questionType = getQuestionType(whd)
    # Nu weten we het vraagtype:
    
  #if questionType is not None:
    #print('\tQUESTION TYPE:\t' + questionType)
  #else:
    # Als q type None is even extra aandacht aan schenken.
    #print('\tQUESTION TYPE:\t None!!!!!!!!!!!!')
    
  # Wie/Wat is de/het X van Y
  if questionType == 'wie' or questionType == 'wat':
    #print('\tWIE/WAT')
    # Check of het om een wie/wat is vraag gaat
    if xml.xpath('//node[@stype="whquestion" and @root="ben"]'):
      #print('\tWIE/WAT IS DE X VAN Y')
      ans = parseXofYQuestion(xml, question)
      return ans
  
  # Hoe -- vraag
  if questionType == 'hoe':
    print('\tHOE')
    Y = []
    deeleigen = xml.xpath('//node[@spectype="deeleigen"]')
    for name in deeleigen:
      Y.append(name.attrib["word"])
    Y = ' '.join(Y)
    print(Y)
    
  # Wanneer-vraag
  if questionType == 'wanneer':
    print('\tWANNEER')
    Y = []
    deeleigen = xml.xpath('//node[@spectype="deeleigen"]')
    for name in deeleigen:
      Y.append(name.attrib["word"])
    Y = ' '.join(Y)
    #TODO: Y gebruiken om URI te vinden
    print(Y)
    # Vind de werkwoorden, en gebruik dit om de property te vinden
    X = []
    werkwoorden = xml.xpath('//node[@pt="ww"]')
    for name in werkwoorden:
      X.append(name.attrib["word"])
    print(X)
    # Als een werkwoord 'geboren' is, gaat het om een geboortedatum
    if 'geboren' in X:
      X = ['geboortedatum']
    else:
      #Het gaat niet om een geboortedatum, probeer wat anders
      print('Geen geboortedatum')
    # Als X uit meerdere woorden bestaat, probeer ze allemaal
    ans = []
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
    print('---------------')
    print(ans)
    print('---------------')
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
    


# Find the exist URI from the file pairCounts
def gener_concept(conc):
    cont_list = []
    concept = ''
    #pairCounts_file = open('pairCounts','r')
    for line in pairCounts:
        line = line.rstrip()
        
        # change the wordgroup "Olympische Spelen" to Olympische Zomerspelen
        #TODO: hier gaat hij meteen de fout in bij de eerste vraag; hij zou Olympische Spelen moeten pakken als URI, niet Olympische Zomerspelen
        ## if Olympische Zomerspelen for that year doesn't exist, 
        ##change to Olympische Winterspelen
        if "Olympische Spelen" in conc:
            conc = conc.replace("Olympische Spelen","Olympische Zomerspelen")
        if re.search(conc, line):
            context = line.split('  ')
            cont_list.append(context)
            if conc == context[0]:
                concept = context[0]
            else:
                if "Olympische Spelen" in conc:
                    conc = conc.replace("Olympische Spelen","Olympische Winterspelen")
                    if re.search(conc, line):
                        context = line.split('  ')
                        cont_list.append(context)
                        if conc == context[0]:
                            concept = context[0]
    return concept
    
    
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
                    persoon = werkw + "or"
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

   
## Create queries using the generated properties and URI        
def create_queries(property_uri,concept):
    
    print("property:",property_uri)
    print("URI:",concept)

    answer_list = []
    
    querie_first = 'select ?answer where { ?concept  rdfs:label "'
    querie_second = '"^^xsd:string. ?concept prop-nl:'
    querie_last = ' ?answer .}'
    
    #kijken naar similar woord nog niet gelukt
    for word in property_uri:
        if getAlt(word) != None:
            property_uri.append(getAlt(word))
            break
    #print(property_uri)
    
    for word in property_uri:
        try:
            for i, j in {'*':'_','&':'_','$':'_','@':'_','/':'_','(':'', ')':''}.items():
                word = word.replace(i, j)
            #print(word)
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
                            print(answer_list,'\n\n')
        except Exception as e:
            sys.stderr.write(e)
            pass        
    if answer_list == []:
        print("Geen antwoord gevonden\n")
    return answer_list



## haal alle properties uit relevante dbpedia pagina die hoort bij categorie sporten, personen en olympics
def prop_list():
    word_list = ["Sport","Person","Olympics"]
    answer_list = []
    for word in word_list:
        query = """select distinct ?property where {
        ?instance a <http://dbpedia.org/ontology/"""+ word + """> . 
        ?instance ?property ?obj . }"""
        results = send_query(query)
        if results["results"]["bindings"] != []:
            for result in results["results"]["bindings"]:
                for arg in result:
                    erase_url = result[arg]["value"].rsplit('/')
                    answer_list.append(erase_url[-1])
                    #print(answer_list,'\n\n')
    
    return answer_list
            





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
  if answers == [] or answers is None:
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
        #print(m.group('new'))
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
  sys.stdin = open('olympics_questions.txt', 'r', encoding='utf-8')
  
  prop_list()
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

    uri = get_concept(question)
    new_uri = gener_concept(uri)
    property_q = get_prop(question)
    get_medailles(property_q,new_uri)

    give_output(ID, answers)






sparql = SPARQLWrapper("http://nl.dbpedia.org/sparql")
sparql.setReturnFormat(JSON)
pairCounts = open('pairCounts', 'r', encoding='utf-8')
#counts = re.split("\n+", pairCounts.read())
similarWords = re.split("\n+", open('similarwords', 'r', encoding='utf-8').read())
    
if __name__ == "__main__":
  main(sys.argv)


  
