# Assignment 4
# Het analyseren van vragen door Alpino, hier queries van maken en doorsturen naar dbpedia.
# Roald Baas (s1879642)

import socket
import sys
from lxml import etree
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://nl.dbpedia.org/sparql")

# Definieer de voorbeeldvragen in een array
vragen = ["Wie ontstak de vlam tijdens de Olympische Winterspelen 2006?",
  "Welke lengte heeft Usain Bolt?",
  "Wie was de opener van de Olympische Winterspelen 2014?",
  "Wat is de plaats van de Olympische Winterspelen 2006?",
  "Wanneer was de eerste Olympische Zomerspelen?",
  "Wat is de bijnaam van Wayne Gretzky?",
  "In welke plaats bevind de Olympische Zomerspelen 2016 zich?",
  "Wat is de geboorteplaats van Brigitte McMahon?",
  "Wat voor soort is Snelwandelen?",
  "Wie zijn voorzitter van de Koninklijke Belgische Atletiekbond?"]

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

# Stuur de SPARQL query naar dbpedia
def send_query(query):
  sparql.setQuery(query)
  sparql.setReturnFormat(JSON)
  results = sparql.query().convert()
  return results

# Print voorbeeldvragen
def print_example_queries():
  for vraag in vragen:
    print(vraag)

# Krijg de deeleigen uit de geparsde zin
def get_deeleigen(xml):
#  xml = alpino_parse(line)
  names = xml.xpath('//node[@spectype="deeleigen"]')
  deeleigen = []
  for name in names:
    deeleigen.append(name.attrib["word"])
    #print(name.attrib)
  return deeleigen

# Krijg de NPs uit de geparsde zin
def get_np(xml):
  names = xml.xpath('//node[@lcat="np"]')
  deel = []
  for name in names:
    deel.append(name.attrib["word"])
    #print(name.attrib)
  np = deel #' '.join(map(str, deel))
  return np

# Maak en geeft het antwoord op de query op basis van X en Y
def sparquery(X, Y):
  answer = 'Geen antwoord gevonden'
  query = """
    SELECT STR(?naam)
    WHERE {
      ?onderwerp foaf:isPrimaryTopicOf wiki-nl:""" + Y + """ .
      ?onderwerp prop-nl:""" + X + ' ?' + 'naam' + """ .
    }
    ORDER BY DESC(?naam)
    """
    
  # Geef de query door met SPARQLWrapper.
  results = send_query(query)
  
  if len(results["results"]["bindings"]) is 0:
    answer = 'Geen antwoord gevonden'
    print(answer)
    return
  else:
    # Print het antwoord.
    for result in results["results"]["bindings"]:
      for arg in result :
        answer = result[arg]["value"]
        # Maak van de link een naam (deze gewoon via SPARQL opvragen zorgt er voor dat hij string-waarden niet meer als antwoord vind)
        if 'http://' in answer:
          answer = answer[31:].replace('_', ' ')
        print(answer)

#TODO: remove debug prints
def main(argv):
  print_example_queries()
  answer = "Geen antwoord"
  for line in sys.stdin:
    line = line.rstrip()
    xml = alpino_parse(line)
    np = get_np(xml)
    if 'Wie' in np:
      np.remove('Wie')
    if 'Wat' in np:
      np.remove('Wat')
    X = np
    Y = get_deeleigen(xml)
    if(len(Y) > 0):
      for i in Y:
        X.remove(i)
    if len(Y) is 0:
      X = X[0]
      Y = np
      Y.remove(X)
    Y = '_'.join(map(str, Y))
    X = ''.join(map(str, X))
    sparquery(X, Y)
  
  
if __name__ == "__main__":
  main(sys.argv)


  