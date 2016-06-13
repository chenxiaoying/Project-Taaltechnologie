# Project Taaltechnologie
# Group 13: Roald Baas, Xiaoying Chen, Anne Wanningen
# We nemen aan dat de bestanden pairCounts en similarwords aanwezig zijn in dezelfde directory als dit bestand

from SPARQLWrapper import SPARQLWrapper, JSON
from operator import itemgetter, attrgetter, methodcaller
import sys
import re
import socket
from  lxml import etree

VERBOSE_LEVEL = 3
MAXITERS = 10
OUTPUT_FILE = 'output.txt'
QUESTIONTYPES = ['wat', 'wie', 'waar', 'wanneer', 'hoeveel', 'welke', 'hoe'] #TODO: questiontypes uitbreiden. 'hoe' moet helemaal aan het eind (zodat 'hoeveel' eerst komt). Dan kunnen we verder zoeken: hoe lang, hoe vaak, etc.
usedAltWords = []



def printP(string, verbose=3, tabs=0, append=False):
  if verbose > VERBOSE_LEVEL: return
  for _ in  range(tabs): print("\t", end="")
  if append: print(string, end="")
  else: print(string)


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
  # Krijg de uri
  uri = get_concept(question)
  uri = gener_concept(uri)
  
  #directObject = xml.xpath('//node[@cat="np" and @rel="obj1"]')
  #if directObject is not []:
  #  for word in directObject:
  #    ding = tree_yield(word)
  #    print(ding)
  if subject is not []:
    subSentence = subStr((int(subject[0].attrib["begin"]), int(subject[0].attrib["end"])), question)
    subject = noPrepositions(subSentence)
  
  #print('\tSUBJECT:\t' + subject)
  
  X = get_prop(question)
  # Haal dubbelen uit X
  X = list(set(X))
  print('----prop---')
  print(X)
  print('----------')
  
  Y = uri
  print('----URI---')
  print(Y)
  print('----------')
  
  
  
  # Als X uit meerdere woorden bestaat, probeer ze allemaal
  for j in X:
    query = """
      SELECT STR(?naam)
      WHERE {
        ?onderwerp foaf:isPrimaryTopicOf wiki-nl:""" + Y.replace(' ', '_').replace('*', '_') + """ .
        ?onderwerp prop-nl:""" + j.replace('*', '_') + ' ?' + 'naam' + """ .
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
def analyse_question_firstPass(question):
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
    
  # Wie/Wat is de/het X van Y
  if questionType == 'wie' or questionType == 'wat':
    #print('\tWIE/WAT')
    # Check of het om een wie/wat is vraag gaat
    if xml.xpath('//node[@stype="whquestion" and @root="ben"]'):
      #print('\tWIE/WAT IS DE X VAN Y')
      ans = parseXofYQuestion(xml, question)
      return ans
  
  # Waar-vraag
  # Deze wordt beantwoord door de default-case onderaan de functie
  
  # Hoeveel-vraag
  if questionType == 'hoeveel':
    #TODO: als iets van '...Zomerspelen van 2008' er in voor komt is uri mogelijk '2008'
    uri = get_concept(question)
    uri = gener_concept(uri)
    print('uri---------------')
    print(uri)
    print('---------------')
    X = get_prop(question)
    print('prop---------------')
    print(X)
    print('---------------')
    # In principe wordt deze opgepakt door de default-case (zie onderaan deze functie)
    #get_medailles(X,uri)
  
  # Hoe -- vraag
  if questionType == 'hoe':
    uri = get_concept(question)
    uri = gener_concept(uri)
    print(uri)
    X = get_prop(question)
    print(X)
    # Als het om lengte gaat
    if 'lang' in X:
      X.append('lengte')
    ans = []
    for j in X:
      query = """
        SELECT STR(?naam)
        WHERE {
          ?onderwerp foaf:isPrimaryTopicOf wiki-nl:""" + uri.replace(' ', '_').replace('*', '_') + """ .
          ?onderwerp prop-nl:""" + j.replace('*', '_') + ' ?' + 'naam' + """ .
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
    
    
  # Wanneer-vraag
  if questionType == 'wanneer':
    uri = get_concept(question)
    uri = gener_concept(uri)
    #TODO: Y gebruiken om URI te vinden
    print(uri)
    # Vind de werkwoorden, en gebruik dit om de property te vinden
    X = []
    werkwoorden = xml.xpath('//node[@pt="ww"]')
    for name in werkwoorden:
      X.append(name.attrib["word"])
    # Als een werkwoord 'geboren' is, gaat het om een geboortedatum
    if 'geboren' in X:
      X.append('geboortedatum')
    # Het is een wanneer-vraag, dus er zal vast naar een jaar gevraagd worden indien "Olympisch" aanwezig is (en er niet naar de sluiting gevraagd wordt)
    if 'Olympisch' in uri and 'sluiting' not in X:
      X.append('opening')
    print(X)
    # Als X uit meerdere woorden bestaat, probeer ze allemaal
    ans = []
    for j in X:
      query = """
        SELECT STR(?naam)
        WHERE {
          ?onderwerp foaf:isPrimaryTopicOf wiki-nl:""" + uri.replace(' ', '_').replace('*', '_') + """ .
          ?onderwerp prop-nl:""" + j.replace('*', '_') + ' ?' + 'naam' + """ .
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
    
  
  # Default: geen vraagtype gevonden, probeer een antwoord te vinden aan de hand van de property en uri
  uri = get_concept(question)
  uri = gener_concept(uri)
  print(uri)
  X = get_prop(question)
  print(X)
  ans = []
  for j in X:
    query = """
      SELECT STR(?naam)
      WHERE {
        ?onderwerp foaf:isPrimaryTopicOf wiki-nl:""" + uri.replace(' ', '_').replace('*', '_') + """ .
        ?onderwerp prop-nl:""" + j.replace('*', '_') + ' ?' + 'naam' + """ .
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

def analyse_question(question):
  # Seems to work better for finding Nouns:
  for i, j in {'Winter':'winter','Zomer':'zomer','Olympi':'olympi','Spele':'spele','Jeugd':'jeugd'}.items():
                question = question.replace(i, j)


  # Geef de vraag door naar de alpino parser, verkrijg de XML
  # Zoek naar de keywords als Wie, Wanneer, Wat, etc. mbv xpath
  printP("\n\n"+question, 1)
  xml = alpino_parse(question)
  questionType = None
  usedAltWords.clear()

  words = re.sub("[^\w]", " ",  question).split()
  
  # Vind de whd (wat, wie, hoeveel --, wanneer, hoe --, etc)
  #TODO: misschien checken of deze leeg is voordat hij verder gaat.
  whd = xml.xpath('//node[@rel="whd"]')
  # Als whd leeg is, is het vraagtype niet goed te bepalen
  if whd == []:
    printP('\tWHD IS LEEG!!!')
  # De whd is niet leeg, we kunnen een vraagtype bepalen
  else:
    whd = tree_yield(whd[0])
    #printP('\tWHD:\t' + whd)
    #TODO: check of woorden als 'wie', 'wat', etc in de whd zitten en aan de hand hiervan het vraagtype bepalen
    questionType = getQuestionType(whd)
    # Nu weten we het vraagtype:
    
  #if questionType is not None:
    #printP('\tQUESTION TYPE:\t' + questionType)
  #else:
    # Als q type None is even extra aandacht aan schenken.
    #printP('\tQUESTION TYPE:\t None!!!!!!!!!!!!')
    
  # find the subject
  #subject = xml.xpath('//node[@rel="su"]')
  #subSentence = subStr((int(subject[0].attrib["begin"]), int(subject[0].attrib["end"])), question)
  #subject = noPrepositions(subSentence)

  # Finding all the nouns
  nodes = xml.xpath('//node[@pt="n"]') #spectype="deeleigen"]')
  nouns = []
  for node in nodes :
    word = node.attrib["word"]
    lemma = node.attrib["lemma"]
    if lemma != None:
      nouns.append(lemma)
    if word != None:
      nouns.append(word)
      printP("\t\tFound noun:\t" + word)
  printP("\n", 3)

  # Finding all adjectives for those nouns
  nodes = xml.xpath('//node[@pt="adj"]') #spectype="deeleigen"]')
  nounsWithAdj = []
  for node in nodes :
    word = node.attrib["word"]
    if word != None:
      for noun in nouns:
        nounAndAdj = str(word + " " + noun)
        if nounAndAdj in question:
          nounsWithAdj.append(nounAndAdj)
          printP("\t\tFound an adjective for noun:\t" + nounAndAdj)

  printP("\n", 3)

  # Finding all the NPs:
  nodes = xml.xpath('//node[@cat="np"]') #spectype="deeleigen"]')
  nps = []
  for node in nodes :
    subSentence = getSubStringFromNode(node, question)
    if subSentence != None:
      nps.append(subSentence)
      printP("\t\tFound NP:\t" + subSentence)

  printP("\n", 3)

  # Extracting important POSs:
  importantPOSs = []
  for noun in nouns:
    for np in nps:
      if noun in np: 
        importantPOSs.append(noun)
        printP("\t\tFound Important POS:\t" + noun)
        for nounWithAdj in nounsWithAdj:
          if noun in nounWithAdj:
            importantPOSs.append(nounWithAdj)
            printP("\t\t  Also added by extent:\t" + nounWithAdj)

  printP("\n", 3)

  # Find URIs using important POSs:
  #printP("Looking for URIs:", 2, 1)
  #for pos in importantPOSs:
  #  (prop, uri) = findURI(pos, 10)
  #  if prop != None: printP("Found PROPRTY:\t" + prop + "\t@: " + uri, 2, 2)
 
  # Find Subject:
  nodes = xml.xpath('//node[@rel="su"]') #spectype="deeleigen"]')
  if nodes != None and len(nodes) > 0: subject = getSubStringFromNode(nodes[0], question)
  else: subject = None
  printP("Subject:\t" + str(subject), 2, 2)

  # Find countable attribute:
  objectToCount = None
  for pos in (nouns + nounsWithAdj):
    if str("oeveel " + pos) in question:
      objectToCount = pos

  if objectToCount != None: printP("Object to Count:\t" + objectToCount, 2, 2)

  
  # Find Object for attribute:
  objectToCountOn = None
  nodes = xml.xpath('//node[@rel="obj1"]') #spectype="deeleigen"]')
  if nodes != None: 
    if isinstance(nodes, list) and len(nodes) != 0: objectToCountOn = getSubStringFromNode(nodes[0], question)
    else: objectToCountOn = getSubStringFromNode(nodes, question)
  # Ugly Hacks:
    if objectToCountOn != None and "oeveel" in objectToCountOn and len(nodes)>1: objectToCountOn = getSubStringFromNode(nodes[1], question)
    if objectToCountOn != None and "spelen" in objectToCountOn and "lympisch" not in objectToCountOn: objectToCountOn += " olympische"

  printP("On Object:\t" + str(objectToCountOn), 2, 2)

  printP("\n", 3)

  keywords = []
  if objectToCount != None: keywords.append(objectToCount)
  if nouns != None: keywords += nouns
  keywords = ' '.join(str(keyword) for keyword in keywords)

  # More Ugly Hacks:
  questionLower = question.lower()
  if "open" in questionLower: 
    if "wie" in questionLower: keywords = "opener " + keywords
    if "wanneer" in questionLower or "datum" in questionLower: keywords = "start opening " + keywords
  if "organis" in questionLower and "wie" in questionLower: keywords = "organisator "+keywords
  if "waar" in questionLower or "land " in questionLower or "plaats" in questionLower: keywords = "location plaats " + keywords
  if "eerste" in questionLower: keywords = keywords + " eerste"
  if "geboren" in questionLower or "geboorte" in questionLower: 
    if "waar" in questionLower or "plaats" in questionLower or "stad" in questionLower: keywords = "geborenIn geboorteplaats geboortestad " + keywords
    if "wanneer" in questionLower: keywords = "geboren geboortedatum geboorte " + keywords
  if "vorige" in questionLower: keywords = "vorige " + keywords
  if "lang" in questionLower or "lengte" in questionLower: keywords = "lang lengte " + keywords
  if "laatste" in questionLower or "afgelopen" in questionLower or "vorige" in questionLower:
    if "zomer" in questionLower: keyword = "2012 " + keywords
    elif "winter" in questionLower: keyword = "2014 " + keywords
    else: keyword = "2014 " + keywords
  if "volgende" in questionLower or "aankomende" in questionLower or "deze" in questionLower:
    if "zomer" in questionLower: keyword = "2016 " + keywords
    elif "winter" in questionLower: keyword = "2018 " + keywords
    else: keyword = "2016 " + keywords
  if "fakkel" in questionLower: keywords = "vlam "+keywords
  if "vlaggendrager" in questionLower: keywords = "vlam "+keywords


  answer = None

  for word in list(set(re.split(' ', keywords))):
    if word in nouns: 
      if objectToCountOn != None: objectToCountOn.replace(word, '')
      if subject != None: subject.replace(word, '')

  if "hoeveel" in questionLower and answer == None: answer = tryKeywordsOnURIs(keywords, findURIs(objectToCountOn))
  if "wie" in questionLower and answer == None: answer = tryKeywordsOnURIs(keywords, findURIs(subject))
  if "geboren" in questionLower and answer == None: answer = tryKeywordsOnURIs(keywords, findURIs(subject))

  if answer == None:
    answer = tryKeywordsOnURIs(keywords, findURIs(objectToCountOn))
  if answer == None:
    answer = tryKeywordsOnURIs(keywords, findURIs(subject))
  if answer == None:
    for pos in importantPOSs:
      answer = tryKeywordsOnURIs(keywords, findURIs(pos))
      if answer != None: return answer
    for noun in nouns:
      answer = tryKeywordsOnURIs(keywords, findURIs(nouns))
      if answer != None: return answer
  return answer  
  #printP("\n", 3)
  #objectToCountURIs = findURIs(objectToCount)

  #printP("\n", 3)

  #for uri in objectToCountOnURIs:
  #  print(getAllProps(uri[1]))





def tryKeywordsOnURIs(keywords, uris):

  if keywords == None or len(keywords) == 0 or uris == None or len(uris) == 0 or uris[0] == None: 
    if uris != None: print(len(uris))
    return None
  uri = None
  prop = None
  i = 0

  while True and len(uris) > i and len(keywords) > 0:
    if len(uris[i]) > 1:
      uri = uris[i][1]
    properties = getAllProps(uri)
    for idx in range(len(properties)):
      properties[idx].append(0)
      for word in list(set(re.split(' ', keywords))):
        if word.lower() in str(properties[idx][0]).lower():
          printP("Found keyword  "+word+"  in Property: " + properties[idx][0], 3, 3)
          properties[idx][2] += 1
          prop = properties[idx][0]
          result = getPropValAtURI(prop, uri)
          if result != None:
            answer = []
            for part in result['results']['bindings']:
              answer.append(part['callret-0']['value'])
            return answer
          else: printP("Nothing for    " +prop,3,3) 
        else: printP("No Prop  " + word + "  in  " + str(properties[idx][0]).lower(), 4, 4)

    if properties != None and len(properties) > 0:    
      properties.sort(key=lambda x: x[2], reverse=True)
      prop = properties[0][0]
    if properties != None and len(properties) > 0 and properties[0][2] > 0: 
      break
    if i >= min(50, len(uris)): 
      break
    i += 1

  result = getPropValAtURI(prop, uri)
  if result != None:
    answer = []
    for part in result['results']['bindings']:
      answer.append(part['callret-0']['value'])
    return answer
  else: return None






 
def getPropValAtURI(prop, uri):
  if prop != None and uri != None and "rdf-" not in prop:
    printP("Trying Query for "+prop+"\t@\t"+uri, 2, 2)
    sparql.setQuery("""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX prop-nl: <http://nl.dbpedia.org/property/>
                PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
                SELECT str(?y)
                WHERE  {
                <"""+uri+"""> prop-nl:"""+prop+""" ?y
                }"""
    )
    try:
      results = sparql.query().convert()
    except:
      printP("Query Failed.", 3, 1)
      return None
  else: return None
  if len(results['results']['bindings']) == 0: return None
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
  results = sparql.query().convert()['results']['bindings']
  properties = []

  for result in results:
    foundURI = result['property']['value']
    tmpList = re.split('/', foundURI)
    properties.append([tmpList[-1], foundURI])

  return properties



def findURIs(string, it=0):
  if string == None: return None

#  words = re.sub("[^\w]", " ",  string).split()
  if isinstance(string, list): words = string
  else: words = re.split(' ', string)
  if words == None or len(words) == 0: return None

  results = []

  for word in words:
    printP("TESTING FOR:  " + word, 3, 2)
    uri = None

    for element in counts:
      m = re.match(r"("+word+")\s"+".*", element, re.I)
      if (m != None):
        parts = re.split("\t", element)
        if len(parts) == 3: results.append([parts[0], parts[1], int(parts[2]), 0])
 
  for idx in range(len(results)):
    resultWords = re.split(' ',results[idx][0].lower())
    #resultWords = re.split('_',results[idx][1].lower())
    for word in words:
      if word.lower() in resultWords:
        results[idx][3] += 75
    results[idx][3] -= len(resultWords)*10 
    results[idx][3] -= len(results[idx][1])
    
  updatedResults = results

#  for idx1 in range(len(results)):
#    for idx2 in range(idx1, len(results)):
#      if results[idx1][1] == results[idx2][1]:
#        updatedResults[idx1][3] += results[idx2][3]

  updatedResults.sort(key=lambda x: x[3], reverse=True)
  if VERBOSE_LEVEL > 2:
    for i in range(min(len(updatedResults), 10)):
      printP(updatedResults[i][0] + "\t" + updatedResults[i][1] + "\t" + str(updatedResults[i][2]) + "\t" + str(updatedResults[i][3]), 3, 2)

  return updatedResults




def getSubStringFromNode(node, question):
    subSentence = None
    if isinstance(node, list):
      for j in range(len(node)):
        subSentence = subStr((int(node[j].attrib["begin"]), int(node[j].attrib["end"])), question)
    else: subSentence = subStr((int(node.attrib["begin"]), int(node.attrib["end"])), question)
    return subSentence
 

# Try to find a substring that matches a URI
def findURI_OLD(words, it=0):
  if (words == None) or (it > MAXITERS) or len(words) == 0: return (None, None)   

  (prop, uri) = testForURI(words)
  if (uri != None): return (prop,uri)

  words = re.sub("[^\w]", " ",  words).split()
  if words == None or len(words) == 0: return (None, None)

  for i, word in enumerate(words):
    tmpList =  words
    altWord = getAlt(word)
    if (altWord != None): tmpList[i] = altWord
    else: tmpList.pop(i)
    if (len(tmpList) > 0): (prop, uri) = findURI(' '.join(tmpList))
    if (uri != None): return (prop,uri)
    
  findURI(' '.join(words[1:]))
  return(None, None)


# Find a URI given a string
def testForURI(string):
  if string == None: return (None,None)
  printP("TESTING FOR:  " + string, 3, 2)
  uri = None
  results = []

  for element in counts:
    m = re.match(r"(^"+string+")\s"+".*", element, re.I)
    if (m != None):
      # printP(m.group(0))
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
    
    ## ik weet niet waarom als dit niet hier staat, kan hij geen URI vinden behalve Olympische Spelen
    pairCounts_file = open('pairCounts','r',encoding='utf-8')

    for line in pairCounts_file:
        line = line.rstrip()
        context = line.split('\t')
        
        ## verbetert naar als achter de Olympische Spelen een number(meestal is het een jaargetal) volgt, zoekt naar juste olympisch winter/zomer spelen
        ## als geen jaar achter volgt, pakt URI van olympische spelen
        if "Olympische Spelen" in conc and re.search('\d',conc) != None:
            conc = conc.replace("Olympische Spelen","Olympische Zomerspelen")
            if conc == context[0]:
                concept = context[0]
            else:
                conc = conc.replace("Olympische Spelen","Olympische Winterspelen")
                if conc == context[0]:
                    concept = context[0]
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

   
## Create queries using the generated properties and URI        
def create_queries(property_uri,concept):
    
    printP("property:",property_uri)
    printP("URI:",concept)

    answer_list = []
    
    querie_first = 'select ?answer where { ?concept  rdfs:label "'
    querie_second = '"^^xsd:string. ?concept prop-nl:'
    querie_last = ' ?answer .}'
    
    #kijken naar similar woord nog niet gelukt
    for word in property_uri:
        alt = getAlt(word)
        if alt != None:
            property_uri.append(alt)
            break

    #printP(property_uri)
    
    for word in property_uri:
        try:
            for i, j in {'*':'_','&':'_','$':'_','@':'_','/':'_','(':'', ')':''}.items():
                word = word.replace(i, j)
            #printP(word)
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
                            printP(answer_list,'\n\n')
        except Exception as e:
            sys.stderr.write(e)
            pass        
    if answer_list == []:
        printP("Geen antwoord gevonden\n")
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
                    #printP(answer_list,'\n\n')
    
    return answer_list
            





# Find a URI given a keyword
#def findURI(word, it=0):
#  uri = None
#  results = []
#
#  for element in counts:
#    m = re.match(r"(^"+word+")\s"+".*", element, re.I)
#    if (m != None):
#      # printP(m.group(0))
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
    # Indien het antwoord een URI is: maak er een naam van
    if isinstance(answers, list): line = '\t'.join(str(answer.replace('http://nl.dbpedia.org/resource/','').replace('_',' ')) for answer in answers)
    else: line = answers
  
    
  line = str(ID) + '\t' + line
  # Append de regel aan de output file, gescheiden met een newline
  f.write(line + '\n')
  printP(line, 1)



# Input format: ID \t Question
def find_answer(sentence):
  printP(sentence)



# Get a single alternative word from similarWords
def getAlt(word):
  usedAltWords.append(word)
  for element in similarWords:
    m = re.match(r"(?P<original>^"+word+r")\#(?P<new>[^#]+)", element)
    if (m != None and m.group('new') not in usedAltWords):
        return m.group('new')
  return None



# Get rid of prepositions
def noPrepositions(sentence):
    if sentence == None: return None
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
#  printP(bytes_received.decode('utf-8'), file=sys.stderr)
  xml = etree.fromstring(bytes_received)
  return xml

def main(argv):
  # Maak de output.txt file eerst leeg voordat de antwoorden er bij in komen
  open(OUTPUT_FILE, 'w').close()
  # Hoog ID op met 1 elke iteratie over sys.stdin. Vervang ID door het ID van de vraag indien aanwezig.
  ID = 0
  #TODO: tijdelijk gewoon meteen de vragen txt meegeven voor het gemak
  sys.stdin = open('olympics_questions.txt', 'r', encoding='ISO-8859-1')
#  sys.stdin = open('questions_hoeveel.txt', 'r', encoding='utf-8')
  
#  prop_list()
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

    # Eerst snellere methode om antwoorden te vinden
    answers = analyse_question_firstPass(question)
    # Als er geen antwoord is gevonden, probeer de langzamere methode
    if answers == [] or answers is None:
      answers = analyse_question(question)
      
    
    # Haal dubbelen uit de antwoorden-lijst
    answers = list(set(answers))
    give_output(ID, answers)






sparql = SPARQLWrapper("http://nl.dbpedia.org/sparql")
sparql.setReturnFormat(JSON)
pairCounts = open('pairCounts', 'r', encoding='utf-8')
counts = re.split("\n+", pairCounts.read())
similarWords = re.split("\n+", open('similarwords', 'r', encoding='utf-8').read())
    
if __name__ == "__main__":
  main(sys.argv)


  
