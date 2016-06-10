# Project Taaltechnologie

import sys
import socket
from lxml import etree

# Analyseer de vraag: bepaal het soort vraag
def analyse_question(question):
  print(question)
  # Wanneer? Wie? Wat? Welke? Hoeveel?

# Output format: ID \t Answer1 \t Answer2...
def give_output(ID, answers):
  #TODO: zorg dat answers een lijst antwoorden kan zijn
  #TODO: Als er geen antwoorden in zitten, meld dit.
  #if answers is None:
  
  line = str(ID) + '\t' + answers
  
  print(line)

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
    
    #TODO: stuur de vraag door voor analyse, SPARQL
    give_output(ID, question)
    #find_answer(sentence)
    
if __name__ == "__main__":
  main(sys.argv)


  