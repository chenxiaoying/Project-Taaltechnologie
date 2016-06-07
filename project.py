# Project Taaltechnologie

import sys
import socket
from lxml import etree

# Analyseer de vraag: bepaal het soort vraag
def analyse_question(question):
  print(question)
  # Wanneer? Wie? Wat? Welke? Hoeveel?
  
  # Indien van de .txt file een vraag gelezen: haal de vraag uit de regel
  if '\t' in question: 
    question = question[question.index('\t')+1:]
  
  print(question)
  # Parse de vraag met Alpino
  #xml = alpino_parse(question)

# Output format: ID \t Answer1 \t Answer2...

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
  print("Type een vraag")
  for sentence in sys.stdin:
    analyse_question(sentence)
    #find_answer(sentence)
    
if __name__ == "__main__":
  main(sys.argv)


  