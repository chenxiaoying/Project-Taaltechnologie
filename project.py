# Project Taaltechnologie

import sys
import socket
from lxml import etree

OUTPUT_FILE = 'output.txt'

# Analyseer de vraag: bepaal het soort vraag
# Wanneer? Wie? Wat? Welke? Hoeveel? In welk(e)? Hoe --?
def analyse_question(question):
  # Geef de vraag door naar de alpino parser, verkrijg de XML
  # Zoek naar de keywords als Wie, Wanneer, Wat, etc. mbv xpath
  print(question)
  

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
    
    answers = ['Answer 1', 2, 'Answer 3']
    #TODO: stuur de vraag door voor analyse, SPARQL
    give_output(ID, answers)
    #find_answer(sentence)
    
if __name__ == "__main__":
  main(sys.argv)


  