#!/usr/bin/python -w
# -*- coding: utf8 -*-

import re
import sys
from collections import defaultdict

ignore1 = {"minä", "mä", "mikin", "minäkin", "sinä", "sä", "sinäkin", "hän", "hänkin", "me", "mekin", "te", "tekin", "he", "hekin", "ei", "olla", "alla", "kanssa", "verran", "oma", "itse", "että", "kin"} # lemla
ignore2 = {"mina", "ma", "sina", "sa", "tema", "ta", "meie", "me", "teie", "te", "nemad", "nad", "ei", "mitte", "olema", "all", "võrra", "oma", "ise", "et", "ka"} 
ignorepos = {"post", "pr", "adp"} # vs adv

sb = dict({"ja":["ja", "ning"], "tai":["või"], "eli":["ehk"], "että":["et"], "mutta":["aga"], "entä":["aga"], "vaikka":["kuigi"], "minä":["mina", "ma"], "mä":["mina", "ma"], "mikin":["mina", "ma"], "minäkin":["mina", "ma"], "sinä":["sina", "sa"], "sä":["sina", "sa"], "sinäkin":["sina", "sa"], "hän":["tema", "ta"], "hänkin":["tema", "ta"], "me":["meie", "me"], "mekin":["meie", "me"], "te":["teie", "te"], "tekin":["teie", "te"], "he":["nemad", "nad"], "hekin":["nemad", "nad"], "ei":["ei", "mitte"], "olla":["olema"], "alla":["all"], "kanssa":["koos"], "verran":["võrra"], "oma":["oma"], "itse":["ise"], "kin":["ka"]})

ps = dict({"vblex":["vblex"], "cnjsub":["cnjsub"], "cnjcoo":["cnjcoo"], "ij":["ij"], "num":["num"], "n":["n", "np", "acr"], "np":["n", "np"], "acr":["n", "np", "acr"], "prn":["adj", "prn", "adv"], "adj":["adj", "prn"], "adv":["adv", "prn", "part"], "part":["adv", "part"]})

pstr = dict({"<n><np>":"n", "<vblex><der><der_mine><n>":"n", "<vblex><der><der_ja><n>":"n", "<n><der><der_lik><adj>":"adj",  "<vblex><der><der_v><adj>":"adj", "<vblex><der><der_tav><adj>":"adj", "<n><der><der_lt><adv>":"adv", "<adj><der><der_lt><adv>":"adv"})

altmor = [{"ill", "all"}, {"ine", "ade"}, {"ela", "abl"}, {"acc", "par"}]

class Wordform:
  def __init__(self, w="", l="", m=""):
    self.word = w 	 # empty in biltrans and postchnk
    self.wold = w.lower().replace('Ä', 'ä').replace('Ö', 'ö').replace('Ü', 'ü').replace('Õ', 'õ')
    self.lemma = l
    self.lemla = l.lower().replace('Ä', 'ä').replace('Ö', 'ö').replace('Ü', 'ü').replace('Õ', 'õ') #.replace("¹", "").replace("²", "").replace("³", "")
    self.morph = m
    self.pos = "?"
    morstr = m
    for key in pstr.keys():
      if key in m:           # v, mine, ja, lik, lt, sti pos & lemmas! (täpse+lt)
        self.pos = pstr[key] # but wrong lemma - cannot be used for dict, but at least for relation
        morstr = m[len(key)+1:]
    i = m.find('>')
    if self.pos == "?" and i > 1:
      self.pos = m[1:i]
      morstr = m[i+1:]
    self.morset = morstr.replace('<', '').split('>')
    self.altmor = []
    for st in altmor: 
      for mr in self.morset:
        if mr in st:
          self.altmor.append(st)

  def prints(self):
    if self.word == "":  # empty in biltrans and postchnk
      return self.lemma + self.morph
    else:
      return self.lemma + self.morph
      #return self.word + '/' + self.lemma + self.morph - word in wordunit

class Wordunit:
  def __init__(self, unit="", ab='a'): # ab=a analysed, ab=b biltrans
    self.biltr = ab
    self.main = Wordform()
    self.readings = []
    self.cat = "notfound" # category
    self.tosource = -1 # index of SOURAN wordunit
    self.totransl = -1 # index of TRANAN wordunit
    self.totarget = -1 # index of TARGAN wordunit
    self.tobiltrs = -1 # index of BILTRS wordunit
    self.compound = False
    self.mwe = False
    self.guess = ""
    self.color = ""
    self.nospace = False
    #print str(ord(unit[0])), unit[0], str(ord(unit[-1])), unit[-1] # chr
    #print str(ord(unit[0])), str(ord(unit[-1])), len(unit) # chr
    if len(unit) > 0:
      while ord(unit[0]) == 93:
        if unit[1] == '(':
          unit = unit[1:]
        else:
          unit = unit[2:]
      while ord(unit[-1]) == 91 or ord(unit[-1]) == 93:
        unit = unit[:-1]
      if unit.find("¤") == 0: # 194+
        unit = unit[2:]
        self.compound = True
        self.nospace = True
    if len(unit) > 0:
      if unit[0] == '^':
        if unit[-1] == '$':
          inl = unit[1:-1]
        else:
          inl = unit[1:]
      elif unit[-1] == '$':
        inl = unit[:-1]
      else:
        inl = unit
      wf = ""
      lem = ""
      mrf = ""
      j = -1
      for item in inl.split('/'):
        j += 1
        i = item.find('<') # start of morph
        if i > 0:
          if '+' in item:
            k = len(item)-3
            while k > 1: 
              if item[k] == '<' and item[k-1] != '>':
                i = k
                break
              k -= 1
          lem = item[:i]
          mrf = item[i:]
        elif len(item) > 0:
          if item[0] == '#': # maybe not a correct form
            self.guess = "#"
            lem = item[1:]
          elif item[0] == '*': # not a lemma in fact, but accidentally may be
            self.guess = "*"
            lem = item[1:]
          else:        
            lem = item
          if lem[-1] == '#':
            lem = lem[:-1] 
          if '/' not in inl: # txt or pchnk "gümnaasiumi ^lõpetanu/lõpetanu<n><pl><gen>$"
            wf = lem
            lem = ""
          mrf = ""
        if j == 0: # diff in an and bi
          if ab != 'b': # analysed
            if '/' in inl:
              wf = item
            else: # else postchnk
              self.main = Wordform(wf, lem, mrf)
              self.readings.append(self.main)
          else: # biltrans
            #if '(' in unit:
            #  print "\n", unit, wf,  lem, "\n"
            self.main = Wordform(wf, lem, mrf)
            #if '/' not in unit: # ^ylioppilas<n><pl><gen>/gümnaasiumi$ ^lõpetanu<n><pl><gen>$
            #  self.mwe = True # + more
        elif j == 1 and ab != 'b': # analysed, 1st reading
          self.main = Wordform(wf, lem, mrf)
          self.readings.append(self.main)
        else: # all readings (analysed) or translations (biltrans)
          self.readings.append(Wordform(wf, lem, mrf))
    if len(self.main.lemma) > 0 and self.main.lemma[0] in '...,:;()?..!.."/@\'+=\\#¤%&[]£${}^|<>0123456789' or (len(self.main.lemma) > 1 and self.main.lemma[0] in "*-" and self.main.lemma[1] in "/<") or (len(self.main.word) == 1 and self.main.word[0] in "*-") or "<cm>" in self.main.morph or "<sent>" in self.main.morph or "<punct>" in self.main.morph or "<guio>" in self.main.morph or "<quot>" in self.main.morph or len(self.main.lemma) == 0 and len(self.main.word) > 0 and self.main.word[0] in '...,:;()?..!.."/@\'+=\\¤%&[]£${}^|<>0123456789':
      # filter numbers & punctuation
      self.cat = "punct"
      if self.main.lemma !='-' or "<guio>" not in self.main.morph and "<guio>" not in self.main.word:
        self.compound = False 
    elif self.main.lemla in ignore1 or self.main.lemla in ignore2 or self.main.pos in ignorepos:
      self.cat = "ignore"

  def printr(self):
    readingstr = ""
    for rd in self.readings:
      readingstr = readingstr + '/' + self.guess + rd.prints()
    return readingstr

  def prints(self, no=False, comm=True):
    prefix = "^"
    if self.compound == True:
      prefix = "+^"
    elif self.mwe == True:
      prefix = "++^"
    postfix = "$"
    if self.totarget >= 0:
      postfix = "$tar" + str(self.totarget)
    if self.tobiltrs >= 0:
      postfix = postfix + "bi" + str(self.tobiltrs)
    if self.totransl >= 0:
      postfix = postfix + "tr" + str(self.totransl)
    if self.tosource >= 0:
      postfix = postfix + "s" + str(self.tosource)
    if self.color != "":
      postfix = postfix + self.color
    if self.biltr == 'b':  # biltrans
      if comm == True: 
        return prefix + self.main.prints() + self.printr() + postfix
      else: 
        if len(self.main.word) == 1 and (self.main.word[0] == '(' or self.main.word[0] == ')' or self.main.word[0] == '+' or self.main.word[0] == '='):  
          return self.main.word
        #elif self.main.lemma[0] == '*':  
        #  return "^" + self.main.prints() + self.printr() + "$"
        else:  
          rs = "^" + self.guess + self.main.prints() + self.printr() + "$"
          return rs.replace('^"^', '"^').replace('$"$', '$"').replace('$%$', '$%').replace('($', '(').replace('&&', ' ')
    elif self.main.word == "":  # postchnk
      if no == False:
        return prefix + self.main.prints() + postfix
      else:
        return prefix + self.main.prints() + '#' + str(self.tobiltrs) + self.cat + postfix
    elif self.main.lemma == "":  # txt
      return self.main.word 
    else:                 # mrf analysed
      return prefix + self.main.word + self.printr() + postfix

L1 = "FIN"
L2 = "EST"

SOURCE = 0
TARGET = 1
TRANSL = 2
BILTRS = 3
SOURAN = 4
TARGAN = 5
TRANAN = 6

def get_sentence(infile, cmp_file, ab='a'):
  # one from infiles: [source, target, transl, biltrans, source_an, target_an, transl_an] 
  def repl(sm):
    return sm.group(1) + "&&" + sm.group(2) 
  txt = infile.readline().strip()
  #txt = sys.stdin.readline().strip()
  if not txt or len(txt) < 3: # or txt == "":
    return None, None, None
  if txt[0] == '^' or txt[1] == '^' or txt[-1] == '$' or ab == 'b':
    if ab == 'b':
      txt, n = re.subn('([^$]) ([^^])', repl, txt) # multiword dix, change '&&'->' ' in output 
      #if n > 0:
      #  print txt
    txt = txt.replace("$^", "$ ¤^").replace("(^", "( ¤^").replace("$(", "$ ¤(").replace("$)", "$ ¤)").replace(")^", ") ¤^").replace("^ -/ <", " ^-/<")
  else: # txt
    txt = txt.replace('.', " ¤.").replace(',', " ¤,").replace('# ,', " ¤#,").replace(':', " ¤:").replace(';', " ¤;").replace('!', " ¤!").replace('?', " ¤?").replace(")#", ")").replace("(", " ( ").replace(")", " ) ") .replace("-", " - ").replace(" -  ", "- ").replace("  - ", " -").replace(" *", " ").replace(" #", " ")
  sentence = []
  borders = []
  lemmas = []
  i = -1
  for item in txt.split():
    if len(item) < 1:
      continue
    #print '&' +item + ' '+str(ord(item[0])) + ' '+str(len(item))+ '&'
    i += 1
    #if ab == 'b' and '/' not in item and "<" in item:
    #  item = "wordix/" + item
    if ab == 'a' and '/' in item and ">+" in item:
      ites = item.split('/')
      beg = ites[0] # don't change at the moment
      j = 0
      for cp in ites[1].split('+'):
        sentence.append(Wordunit(beg + "/" + cp, ab))
        #cmp_file.write("\ncmp " + item + "\t" + beg + "/" + cp + "\t" + sentence[-1].prints())
        if j > 0:
          sentence[-1].compound = True 
          i += 1
        j += 1
    elif len(item) > 2 or ord(item[0]) != 93 or '(' in item:
      wu = Wordunit(item, ab)
      sentence.append(wu)
      if len(sentence) > 1: 
        prwu = sentence[-2]
        if prwu and wu.compound == True and "punct" in prwu.cat and prwu.compound == False:
          wu.compound = False
    else:
      continue

    newu = sentence[-1]
    #if ab == 'a' and len(sentence) > 1 and sentence[-2].main.morph == "" and sentence[-2].main.word == "" and "punct" not in sentence[-2].cat and "punct" not in newu.cat and ">+" in txt: 
    #  sentence[-1].compound = True # pchnk "gümnaasiumi ^lõpetanu/lõpetanu<n><pl><gen>$", in some cases, check 

    neww = newu.main
    if neww.word == "": 
      newl = neww.lemma
    else:
      newl = neww.word
    if (len(newl) == 1 or len(newl) > 1 and newl[1] in '<0123456789') and newl[0] in ':;,':
      borders.append(i)

    if ab == 'b':
      j = -2
      while "punct" not in newu.cat and "ignore" not in newu.cat and newu.compound == True:
        if newu.main.lemma != "" and newu.main.pos in "vblexnadj":
          lemmas.append(newu.main.lemla)
        j -= 1
        if -j < len(sentence):
          newu = sentence[j]
        else:
          break
      if "punct" not in newu.cat and "ignore" not in newu.cat and newu.main.lemma != "" and newu.main.pos in "vblexnadj":
        lemmas.append(newu.main.lemla)

  return sentence, borders, lemmas

def get_phrases(infilenames, cmp_file):
  # infiles: [source, target, transl, biltrans, source_an, target_an, transl_an]
  # infiles: ignored here
  #infiles = []
  #for i in range(len(infilenames)):
  #  infiles.append(file(infilenames[i]))
  
  sentno = 0
  #borders = []
  sentences = []
  lemmas = []
  #sentence, border, lemmas = get_sentence(infiles[SOURCE], cmp_file)
  sentence, border, lemmas = get_sentence(sys.stdin, "", 'b')
  while sentence:
    sentno += 1
    #borders = [border]
    sentences = [sentence]
    """for i in range(len(infiles)-1):
      if i+1 == BILTRS:
        sentence, border, lemmas = get_sentence(infiles[i+1], cmp_file, 'b')
      else:
        sentence, border, lemmas = get_sentence(infiles[i+1], cmp_file)
      if sentence:
        sentences.append(sentence)
        borders.append(border)"""
    yield sentences, lemmas # here want whole sentences, so need only 1 last line after this
    
    """if len(borders[SOURAN]) == 0 or len(borders[TARGAN]) == 0:
      yield sentences, lemmas
    else:
      diff = len(borders[TARGAN]) - len(borders[SOURAN])
      if diff > 0: # change target, targan
        #cmp_file.write("\n" + str(borders))
        for i in range(len(borders[SOURAN])):
          if abs(abs(borders[TARGAN][i] - borders[SOURAN][i]) - abs(borders[TARGAN][i+1] - borders[SOURAN][i])) < 3: # check
            if borders[SOURAN][i] > 0 and len(sentences[BILTRS][borders[BILTRS][i]-1].readings) > 0 and sentences[SOURAN][borders[SOURAN][i]-1].main.lemma in sentences[BILTRS][borders[BILTRS][i]-1].main.lemma and sentences[TARGAN][borders[TARGAN][i+1]-1].main.lemma in sentences[BILTRS][borders[BILTRS][i]-1].readings[0].lemma or borders[SOURAN][i] < len(sentences[SOURAN])-1 and sentences[SOURAN][borders[SOURAN][i]+1].main.lemma in sentences[BILTRS][borders[BILTRS][i]+1].main.lemma and sentences[TARGAN][borders[TARGAN][i+1]+1].main.lemma in sentences[BILTRS][borders[BILTRS][i]+1].readings[0].lemma:
              sentences[TARGAN][i].color = "grey"
              borders[TARGAN].pop(i)
              borders[TARGET].pop(i)
          elif abs(borders[TARGAN][i] - borders[SOURAN][i]) > abs(borders[TARGAN][i+1] - borders[SOURAN][i]):
            sentences[TARGAN][i].color = "grey"
            borders[TARGAN].pop(i)
            borders[TARGET].pop(i)
          if len(borders[TARGAN]) == len(borders[SOURAN]):
            break
        i = -1
        while len(borders[TARGAN]) > len(borders[SOURAN]): 
            sentences[TARGAN][i].color = "grey"
            borders[TARGAN].pop()
            borders[TARGET].pop()
            i -= 1
        #cmp_file.write("\n" + str(borders))
      elif diff < 0: # change source, souran, transl, tranan, biltrs
        #cmp_file.write("\n" + str(borders))
        for i in range(len(borders[TARGAN])):
          if abs(abs(borders[TARGAN][i] - borders[SOURAN][i]) - abs(borders[TARGAN][i] - borders[SOURAN][i+1])) < 3: # check
            if borders[TARGAN][i] > 0 and len(sentences[BILTRS][borders[BILTRS][i]-1].readings) > 0 and sentences[SOURAN][borders[SOURAN][i+1]-1].main.lemma in sentences[BILTRS][borders[BILTRS][i+1]-1].main.lemma and sentences[TARGAN][borders[TARGAN][i]-1].main.lemma in sentences[BILTRS][borders[BILTRS][i+1]-1].readings[0].lemma or borders[SOURAN][i] < len(sentences[SOURAN])-1 and sentences[SOURAN][borders[SOURAN][i+1]+1].main.lemma in sentences[BILTRS][borders[BILTRS][i+1]+1].main.lemma and sentences[TARGAN][borders[TARGAN][i]+1].main.lemma in sentences[BILTRS][borders[BILTRS][i+1]+1].readings[0].lemma:
              sentences[TRANAN][i].color = "grey"
              borders[SOURCE].pop(i)
              borders[SOURAN].pop(i)
              borders[TRANSL].pop(i)
              borders[TRANAN].pop(i)
              borders[BILTRS].pop(i)
          elif abs(borders[TARGAN][i] - borders[SOURAN][i]) > abs(borders[TARGAN][i] - borders[SOURAN][i+1]):
              sentences[TRANAN][i].color = "grey"
              borders[SOURCE].pop(i)
              borders[SOURAN].pop(i)
              borders[TRANSL].pop(i)
              borders[TRANAN].pop(i)
              borders[BILTRS].pop(i)
          if len(borders[TARGAN]) == len(borders[SOURAN]):
            break
        i = -1
        while len(borders[TARGAN]) < len(borders[SOURAN]): 
            sentences[TRANAN][i].color = "grey"
            borders[SOURCE].pop()
            borders[SOURAN].pop()
            borders[TRANSL].pop()
            borders[TRANAN].pop()
            borders[BILTRS].pop()
            i -= 1
        #cmp_file.write("\n" + str(borders))

      if len(borders[SOURAN]) == 0 or len(borders[TARGAN]) == 0:
        yield sentences, lemmas
      else:
        for j in range(len(borders[SOURAN])+1):
          phrases = []
          for i in range(len(infiles)):
            if j == 0:
             newph = sentences[i][:borders[i][0]]
            elif j < len(borders[i]):
              newph = sentences[i][borders[i][j-1]+1:borders[i][j]]
            else:
              newph = sentences[i][borders[i][-1]+1:]
            phrases.append(newph)
          if j == 0: # once per sentence 
            yield phrases, lemmas
          else:
            yield phrases, []"""
    
    #sentence, border, lemmas = get_sentence(infiles[SOURCE], cmp_file)
    sentence, border, lemmas = get_sentence(sys.stdin, "", 'b')
#  #for i in range(len(infiles)):
  #  infiles[i].close()


def print_phrase(phrase, no=False):
  phrasestr = ""
  for i in range(len(phrase)):
    phrasestr = phrasestr + phrase[i].prints(no) + ' '
  return phrasestr + '\n'
  
def print_phrases(phrases):
  phrasestr = ""
  for i in range(len(phrases)):
    phrasestr = phrasestr + print_phrase(phrases[i], False)
  print phrasestr + '\n'
  #return phrasestr + '\n'

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

vset = ["prevlemma", "prevmorph", "nextlemma", "nextmorph", "near", "middle", "far"]

class Wordtritem:
  def __init__(self, bwur): # bwur - L2 biltrans wordunit reading (main in Wordunit)
    if isinstance(bwur, Wordform):
      self.lemma = bwur.lemma
      self.lemla = bwur.lemla
      self.pos = bwur.pos
      self.old = False
      self.count = 0
      if bwur.morph == "":
        self.morph = "?"
      else:
        self.morph = bwur.morph
      self.wlist = defaultdict(str)
      self.wcount = defaultdict(str)
      for v in vset:
        self.wlist[v] = []
        self.wcount[v] = []
      # lang2?
    else: # bwur - txt
      items = bwur.split()
      self.lemma = items[0]
      self.lemla = self.lemma.lower().replace('Ä', 'ä').replace('Ö', 'ö').replace('Ü', 'ü').replace('Õ', 'õ')
      self.pos = items[1]
      self.morph = items[2]
      self.old = True
      self.count = 0
      if items[3] != "":
        self.count = int(items[3])
      self.wlist = defaultdict()
      self.wcount = defaultdict()
      lists = items[4].split(';')
      i = 0
      for l in lists:
        self.wlist[vset[i]] = []
        self.wcount[vset[i]] = []
        if l != "":
          for li in l.split(','):
            lis = li.split(':')
            if len(lis) == 2:
              self.wlist[vset[i]].append(lis[0])
              self.wcount[vset[i]].append(int(lis[1]))
        i += 1

  def to_txt(self):
    if self.lemma == "":
      return ""
    txtstr = self.lemma + ' ' + self.pos + ' ' + self.morph + ' ' + str(self.count) + ' '
    for v in vset:
      wl = []
      for i in range(len(self.wlist[v])):
        wl.append(self.wlist[v][i] + ':' + str(self.wcount[v][i]))
      txtstr = txtstr + ','.join(wl)
      if v != "far":
        txtstr = txtstr + ';'
    return txtstr

class Wordtrans:
  def __init__(self, bwu): # bwu - biltrans Wordunit
    if isinstance(bwu, Wordunit):
      #self.main = Wordtritem(bwu.main) L1 main
      self.lemma = bwu.main.lemma
      self.lemla = bwu.main.lemla
      self.morph = bwu.main.morph
      self.pos = bwu.main.pos
      self.translations = [] # L2
      for rd in bwu.readings: 
        self.translations.append(Wordtritem(rd))
      self.default = -1 # index of default translation
      self.alternate = 0
      self.onlymorph = 0
      self.wordcount = 0
    else: # bwu - txt
      #print bwu
      iters = bwu.replace('  ', ' _ ').split('\t')
      i = 0
      self.translations = [] # L2
      for r in iters:
        if i == 0:
          items = r.split()
          self.lemma = items[0]
          self.lemla = self.lemma.lower().replace('Ä', 'ä').replace('Ö', 'ö').replace('Ü', 'ü').replace('Õ', 'õ')
          self.wordcount = int(items[1])
          self.pos = items[2]
          self.morph = items[3]
          self.default = int(items[4])
          self.alternate = int(items[5])
          self.onlymorph = int(items[6])
          self.translations = []
        else:
          if len(r) > 3:
            self.translations.append(Wordtritem(r))
        i += 1

  def add_context(self, word, targettr, prevlemma, prevmorph, nextlemma, nextmorph, near):
      # word - biltrans Wordunit, targettr - phrases[TARGAN] transl Wordunit
      transrule = None   
      self.wordcount += 1
      for tr in self.translations:
          if tr.lemla == targettr.main.lemla:
              transrule = tr
              break
          for rd in word.readings:
              if (tr.lemla == rd.lemla or tr.lemla == rd.lemma) and tr.lemla.find(targettr.main.lemla+'<') == 0:
                  transrule = tr
                  break
          if transrule != None: break
      if transrule == None: # new translation
          self.translations.append(Wordtritem(targettr.main))
          transrule = self.translations[-1]
      transrule.count += 1
      
      if prevlemma != "":
          if prevlemma in transrule.wlist['prevlemma']:
              i = transrule.wlist['prevlemma'].index(prevlemma)
              transrule.wcount['prevlemma'][i] += 1
          else:
              transrule.wlist['prevlemma'].append(prevlemma)
              transrule.wcount['prevlemma'].append(1)
      if prevmorph != "":
          if prevmorph in transrule.wlist['prevmorph']:
              i = transrule.wlist['prevmorph'].index(prevmorph)
              transrule.wcount['prevmorph'][i] += 1
          else:
              transrule.wlist['prevmorph'].append(prevmorph)
              transrule.wcount['prevmorph'].append(1)
      if nextlemma != "":
          if nextlemma in transrule.wlist['nextlemma']:
              i = transrule.wlist['nextlemma'].index(nextlemma)
              transrule.wcount['nextlemma'][i] += 1
          else:
              transrule.wlist['nextlemma'].append(nextlemma)
              transrule.wcount['nextlemma'].append(1)
      if nextmorph != "":
          if nextmorph in transrule.wlist['nextmorph']:
              i = transrule.wlist['nextmorph'].index(nextmorph)
              transrule.wcount['nextmorph'][i] += 1
          else:
              transrule.wlist['nextmorph'].append(nextmorph)
              transrule.wcount['nextmorph'].append(1)
      if len(near) > 0:
        for el in near:
          if el in transrule.wlist['near']:
              i = transrule.wlist['near'].index(el)
              transrule.wcount['near'][i] += 1
          else:
              transrule.wlist['near'].append(el)
              transrule.wcount['near'].append(1)


  def to_txt(self):
    if self.lemma == "":
      return ""
    txtstr = self.lemma + ' ' + str(self.wordcount) + ' ' + self.pos + ' ' + self.morph + ' ' + str(self.default) + ' ' + str(self.alternate) + ' ' + str(self.onlymorph) + '\t'
    for tr in self.translations:
      txtstr = txtstr + tr.to_txt() + '\t'
    return txtstr + '\n\n'

def wordtrans_to_txt(wtl, wt_file): # list of Wordtrans
  for wt in wtl:
      #if len(wt.translations) > 1:
      wt_file.write(wt.to_txt())

def wordtrans_from_txt(wt_file):
  wtl = []  # list of Wordtrans
  wll = []  # lict of Wordtrans lemmas
  wd = dict()  # dict of Wordtrans lemmas with counts
  line = wt_file.readline()
  while line:
    if len(line) > 3:
      wtr = Wordtrans(line)
      wtl.append(wtr)
      wll.append(wtr.lemla)
      wd[wtr.lemla] = wtr.wordcount
    line = wt_file.readline()
  return wtl, wll, wd

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def compare(infilenames):
  # Usage: python comp.py [source] [target] [transl] [biltrans] [source_an] [target_an] [transl_an] \n""")
  # python com.py soome.txt eesti.txt soome.tolge soome.biltr soome.mrf eesti.mrf soome.pchnk


  def starts_cmwe(kind, index): 
      if index < 0 or index >= len(phrases[kind]) or phrases[kind][index].compound == True or phrases[kind][index].mwe == True:
        return 'n' # no, not correct index or not starting
      elif index + 1 < len(phrases[kind]): 
        if phrases[kind][index+1].compound == True:
          return 'c' # first in compound
        elif phrases[kind][index+1].mwe == True:
          return 'm' # first in mwe
        else:
          return 'n' # not in compound/mwe
      else:
        return 'n' # wrong index

  def tail_cmwe(kind, index):
      if index < 0 or index >= len(phrases[kind]):
        return 'n' # no, not correct index
      if phrases[kind][index].compound == True:
        return 'c' # in tail of compound
      elif phrases[kind][index].mwe == True:
        return 'm' # in tail of mwe
      else:
        return 'n' # not in tail of compound/mwe



  rul_file = open(infilenames, 'r') # infilenames[TRANSL]+".nrl" - here one file
  lrules, lrlems, lrc = wordtrans_from_txt(rul_file)
  rul_file.close()

  sentno = 0
  lemmas = []
  cmp_file = ""
  phrases_itr = get_phrases(infilenames, cmp_file)
  #plemmas = lemmas
  phrases, lemmas = phrases_itr.next()

  try:
    while phrases: # here: list of one sentence
      sentno += 1
      #print str(sentno)
      #print_phrases(phrases)
      #print str(sentno)

      itr = 0
      sentstr = ""
      s = phrases[0]
      while itr < len(s): # word in sentence
        word = s[itr]
        prev = None
        if itr > 0:
          prev = s[itr-1]
        next = None
        if itr < len(s)-1:
          next = s[itr+1]
        if "punct" not in word.cat and len(word.readings) > 1 and word.main.lemla in lrlems:
          ri = lrlems.index(word.main.lemla)
          wrule = lrules[ri]
          mscore = 0
          mscori = -1
          mcount = 0
          score = [0 for i in range(len(word.readings))]
          for i in range(len(word.readings)):
            # find translation
            tr = None
            for wtr in wrule.translations:
              if wtr.lemla == word.readings[i].lemla:
                tr = wtr
                break
            if tr != None: 
              # find score
              if prev != None and prev.main.lemla in tr.wlist['prevlemma'] and prev.main.lemla not in ignore1:
                lrcount = 1
                if prev.main.lemla in lrc.keys():
                  lrcount = lrc[prev.main.lemla]
                j = tr.wlist['prevlemma'].index(prev.main.lemla)
                score[i] += float(tr.wcount['prevlemma'][j] * 50) / lrcount
              if prev != None and prev.main.morph in tr.wlist['prevmorph']:
                j = tr.wlist['prevmorph'].index(prev.main.morph)
                score[i] += float(tr.wcount['prevmorph'][j]) / 50
                if "*" in tr.wlist['prevlemma']:
                  score[i] += 50
              if next != None and next.main.lemla in tr.wlist['nextlemma'] and next.main.lemla not in ignore1:
                lrcount = 1
                if next.main.lemla in lrc.keys():
                  lrcount = lrc[next.main.lemla]
                j = tr.wlist['nextlemma'].index(next.main.lemla)
                score[i] += float(tr.wcount['nextlemma'][j] * 50) / lrcount
              if next != None and next.main.morph in tr.wlist['nextmorph']:
                j = tr.wlist['nextmorph'].index(next.main.morph)
                score[i] += float(tr.wcount['nextmorph'][j]) / 50
                if "*" in tr.wlist['nextlemma']:
                  score[i] += 50
              if len(lemmas) > 0 and len(tr.wlist['near']) > 0:
                for lemma in lemmas:
                  if lemma in tr.wlist['near']:
                    lrcount = 1
                    if lemma in lrc.keys():
                      lrcount = lrc[lemma]
                    j = tr.wlist['near'].index(lemma)
                    score[i] += float(tr.wcount['near'][j]) / lrcount

              if score[i] > mscore or (score[i] == mscore and tr.count > mcount):
                mscore = score[i]
                mscori = i   
                mcount = tr.count   
          if mscori >= 0:
            word.readings = [word.readings[mscori]]        
        if itr == 0 or word.compound == True or word.nospace == True:
          sentstr = sentstr + word.prints(False, False)
        else:
          sentstr = sentstr + ' ' + word.prints(False, False)
        itr += 1 
      if len(sentstr) > 3:
        print sentstr

      try:
        phrases, lemmas = phrases_itr.next()
      except StopIteration:
        break

  except IndexError:
    sys.stderr.write("Could not read phrase nr %i: \n%s" % (sentno, print_phrases(phrases)))
    sys.exit(1)

  rul_file.close()

def usage():
    sys.stderr.write("""Applies lexical selection rules to biltrans output.  
    Usage: python ls.py [lrules file] < input > output\n""")
    # python ls.py soome.tolge.nrl < soome.biltr > soome.biltrs

if __name__ == "__main__":

    if len(sys.argv)!=2:
        usage()
        sys.exit(1)
    sys.stderr.write("Rules: " + sys.argv[1] + "\n")
    compare(sys.argv[1])

