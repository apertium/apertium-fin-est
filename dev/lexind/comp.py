#!/usr/bin/python -w
# -*- coding: utf8 -*-

import re
import sys
from collections import defaultdict

ignore1 = {"minä", "mä", "mikin", "minäkin", "sinä", "sä", "sinäkin", "hän", "hänkin", "me", "mekin", "te", "tekin", "he", "hekin", "ei", "olla", "alla", "kanssa", "verran", "oma", "itse", "että", "kin"} # lemla
ignore2 = {"mina", "ma", "sina", "sa", "tema", "ta", "meie", "me", "teie", "te", "nemad", "nad", "ei", "mitte", "olema", "all", "võrra", "oma", "ise", "et", "ka"} 
ignorepos = {"post", "pr", "adp"} # vs adv

sb = dict({"ja":["ja", "ning"], "tai":["või"], "eli":["ehk"], "että":["et"], "mutta":["aga"], "entä":["aga"], "vaikka":["kuigi"], "minä":["mina", "ma"], "mä":["mina", "ma"], "mikin":["mina", "ma"], "minäkin":["mina", "ma"], "sinä":["sina", "sa"], "sä":["sina", "sa"], "sinäkin":["sina", "sa"], "hän":["tema", "ta"], "hänkin":["tema", "ta"], "me":["meie", "me"], "mekin":["meie", "me"], "te":["teie", "te"], "tekin":["teie", "te"], "he":["nemad", "nad"], "hekin":["nemad", "nad"], "ei":["ei", "mitte"], "olla":["olema"], "alla":["all"], "kanssa":["koos"], "verran":["võrra"], "oma":["oma"], "itse":["ise"], "kin":["ka"]})

ps = dict({"vblex":["vblex"], "cnjsub":["cnjsub"], "cnjcoo":["cnjcoo"], "num":["num", "n"], "n":["n", "np", "num", "acr", "ij"], "np":["n", "np"], "acr":["n", "np", "acr"], "ij":["n", "ij"], "prn":["adj", "prn", "adv"], "adj":["adj", "prn"], "adv":["adv", "prn", "part"], "part":["adv", "prn", "part"], "adp":["adp", "post", "pre"], "post":["adp", "post", "pre"], "pre":["adp", "post", "pre"]})

pstr = dict({"<n><np>":"n", "<vblex><der><der_mine><n>":"n", "<vblex><der><der_ja><n>":"n", "<n><der><der_lik><adj>":"adj",  "<vblex><der><der_v><adj>":"adj", "<vblex><der><der_tav><adj>":"adj", "<n><der><der_lt><adv>":"adv", "<adj><der><der_lt><adv>":"adv"})

altmor = [{"ill", "all"}, {"ine", "ade"}, {"ela", "abl"}, {"acc", "par", "gen"}]

class Wordform:
  def __init__(self, w="", l="", m=""):
    self.word = w 	 # empty in biltrans and postchnk
    self.wold = w.lower().replace('Ä', 'ä').replace('Ö', 'ö').replace('Ü', 'ü').replace('Õ', 'õ')
    self.lemma = l
    self.lemla = l.lower().replace('Ä', 'ä').replace('Ö', 'ö').replace('Ü', 'ü').replace('Õ', 'õ').replace("¹", "").replace("²", "").replace("³", "")
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
    self.main = Wordform() # main reading
    self.readings = [] # translations for BILTRS
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
      if ab == 't' or inl == '/':
        if len(inl) > 0:
            if inl[0] == '#': 
              self.guess = "#"
              inl = inl[1:]
            elif inl[0] == '*': 
              self.guess = "*"
              inl = inl[1:]
            if inl[-1] == '#':
              inl = inl[:-1] 
        wf = inl
        self.main = Wordform(wf, lem, mrf)
        self.readings.append(self.main)
      else:
        for item in inl.split('/'):
          j += 1

          if len(item) > 0 and item[0] == '*': # not a lemma in fact, but accidentally may be
              self.guess = "*"
              item = item[1:]
          if len(item) > 0 and item[-1] == '#':
              item = item[:-1] 

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
            lem = item
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
              self.main = Wordform(wf, lem, mrf)
          elif j == 1 and ab != 'b': # analysed, 1st reading
            self.main = Wordform(wf, lem, mrf)
            self.readings.append(self.main)
          else: # all readings (analysed) or translations (biltrans)
            self.readings.append(Wordform(wf, lem, mrf))
    if len(self.main.lemma) > 0 and self.main.lemma[0] in '...,:;()?..!.."/@\'+=\\#¤%&[]£${}^|<>0123456789' or (len(self.main.lemma) > 1 and self.main.lemma[0] in "*-" and self.main.lemma[1] in "/<") or (len(self.main.word) == 1 and self.main.word[0] in "*-") or "<cm>" in self.main.morph or "<sent>" in self.main.morph or "<punct>" in self.main.morph or "<guio>" in self.main.morph or "<quot>" in self.main.morph or len(self.main.lemma) == 0 and len(self.main.word) > 0 and self.main.word[0] in '...,:;()?..!.."/@\'+=\\¤%&[]£${}^|<>0123456789':
      # filter numbers & punctuation
      self.cat = "punct"
      if self.main.lemma !='-' and self.main.lemma !='/' and "<guio>" not in self.main.morph and "<guio>" not in self.main.word:
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
    postfix = postfix + self.cat
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
      if len(postfix) < 2  or "notfound" in self.cat or "punct" in self.cat:
        return self.main.word
      else:
        return self.main.word + "$" + postfix[1:]
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
  if not txt or txt == "": #  or len(txt) < 3:
    return None, None, None
  if txt[0] == '^' or txt[1] == '^' or txt[-1] == '$' or ab == 'b' or ab == 'a':
    if ab == 'b':
      txt, n = re.subn('([^$]) ([^^])', repl, txt) # multiword dix
      #if n > 0:
      #  print txt
    txt = txt.replace("^ -/ <punct>+", " ^-/-<punct>+").replace("$^", "$ ¤^").replace("(^", "( ¤^").replace("$(", "$ ¤(").replace("$)", "$ ¤)").replace(")^", ") ¤^").replace("$/^", "$ ¤/ ¤^")
  else: # txt
    txt = txt.replace('.', " ¤.").replace(',', " ¤,").replace('# ,', " ¤#,").replace(':', " ¤:").replace(';', " ¤;").replace('!', " ¤!").replace('?', " ¤?").replace(")#", ")").replace("(", " ( ").replace(")", " ) ") .replace("-", " - ").replace(" -  ", "- ").replace("  - ", " -").replace(" *", " ").replace(" #", " ").replace("/", " ¤/ ¤")
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
  infiles = []
  for i in range(len(infilenames)):
    infiles.append(file(infilenames[i]))
  
  sentno = 0
  borders = []
  sentences = []
  lemmas = []
  sentence, border, lemmas = get_sentence(infiles[SOURCE], cmp_file, 't')
  while sentence:
    sentno += 1
    borders = [border]
    sentences = [sentence]
    for i in range(len(infiles)-1):
      if i+1 == BILTRS:
        sentence, border, lemmas = get_sentence(infiles[i+1], cmp_file, 'b')
      elif i+1 < BILTRS:
        sentence, border, lemmas = get_sentence(infiles[i+1], cmp_file, 't')
      else:
        sentence, border, lemmas = get_sentence(infiles[i+1], cmp_file)
      if sentence:
        sentences.append(sentence)
        borders.append(border)
    #yield sentences, lemmas # if want whole sentences, then need only 3 last lines after this
    
    if len(borders[SOURAN]) == 0 or len(borders[TARGAN]) == 0:
      yield sentences, lemmas
    else:
      diff = len(borders[TARGAN]) - len(borders[SOURAN])
      if diff > 0: # change target, targan
        for i in range(len(borders[SOURAN])):
          if abs(abs(borders[TARGAN][i] - borders[SOURAN][i]) - abs(borders[TARGAN][i+1] - borders[SOURAN][i])) < 3 and borders[SOURAN][i] > 0 and len(sentences[BILTRS][borders[BILTRS][i]-1].readings) > 0 and sentences[SOURAN][borders[SOURAN][i]-1].main.lemma in sentences[BILTRS][borders[BILTRS][i]-1].main.lemma and sentences[TARGAN][borders[TARGAN][i+1]-1].main.lemma in sentences[BILTRS][borders[BILTRS][i]-1].readings[0].lemma or borders[SOURAN][i] < len(sentences[SOURAN])-1 and sentences[SOURAN][borders[SOURAN][i]+1].main.lemma in sentences[BILTRS][borders[BILTRS][i]+1].main.lemma and sentences[TARGAN][borders[TARGAN][i+1]+1].main.lemma in sentences[BILTRS][borders[BILTRS][i]+1].readings[0].lemma:
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
      elif diff < 0: # change source, souran, transl, tranan, biltrs
        for i in range(len(borders[TARGAN])):
          if abs(abs(borders[TARGAN][i] - borders[SOURAN][i]) - abs(borders[TARGAN][i] - borders[SOURAN][i+1])) < 3 and (borders[TARGAN][i] > 0 and len(sentences[BILTRS][borders[BILTRS][i]-1].readings) > 0 and sentences[SOURAN][borders[SOURAN][i+1]-1].main.lemma in sentences[BILTRS][borders[BILTRS][i+1]-1].main.lemma and sentences[TARGAN][borders[TARGAN][i]-1].main.lemma in sentences[BILTRS][borders[BILTRS][i+1]-1].readings[0].lemma or borders[SOURAN][i] < len(sentences[SOURAN])-1 and sentences[SOURAN][borders[SOURAN][i+1]+1].main.lemma in sentences[BILTRS][borders[BILTRS][i+1]+1].main.lemma and sentences[TARGAN][borders[TARGAN][i]+1].main.lemma in sentences[BILTRS][borders[BILTRS][i+1]+1].readings[0].lemma):
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
            yield phrases, []
    
    sentence, border, lemmas = get_sentence(infiles[SOURCE], cmp_file, 't')
  for i in range(len(infiles)):
    infiles[i].close()


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

  def add_context(self, word, targettr, ttr, prevlemma, prevmorph, nextlemma, nextmorph, near):
      # word - biltrans Wordunit, targettr - phrases[TARGAN] transl Wordunit
      if targettr == None:
        return
      transrule = None   
      self.wordcount += 1
      targetlemla = targettr.main.lemla
      if ttr != None:
          targetlemla = targetlemla + targettr.main.morph + "+" + ttr.main.lemla
      for tr in self.translations:
          if tr.lemla == targetlemla:
              transrule = tr
              break
          for rd in word.readings:
              if (tr.lemla == rd.lemla or tr.lemla == rd.lemma) and tr.lemla.find(targetlemla+'<') == 0:
                  transrule = tr
                  break
          if transrule != None: break
      if transrule == None: # new translation
          if ttr != None:  
            self.translations.append(Wordtritem(ttr.main))
          else:  
            self.translations.append(Wordtritem(targettr.main))
          self.translations[-1].lemma = targetlemla
          self.translations[-1].lemla = targetlemla
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
  wll = []  # list of Wordtrans lemmas
  line = wt_file.readline()
  while line:
    if len(line) > 3:
      wtr = Wordtrans(line)
      wtl.append(wtr)
      wll.append(wtr.lemma)
    line = wt_file.readline()
  return wtl, wll

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


  def generate_bidix_entries():

    def get_lemma(wur): # Wordunit.main or reading
      if wur.pos == "np" or wur.pos == "acr" or wur.pos == "?" or len(wur.lemma) <= 3 and wur.pos != "prn" and wur.pos != "adv":
        return wur.lemma
      else:
        return wur.lemla

    def get_lemmamor(wur): # Wordunit.main or reading
      mor = wur.morph.replace('<', '<s n="').replace('>', '"/>') # <s n="adj"/>
      return get_lemma(wur) + mor

    def get_pos(wur): # Wordunit.main or reading
      if wur.pos == "?":
        return "n"
      else:
        #if "<prefix>" in wur.morph: # 1st!
        #  return wur.pos + '"/><s n="prefix' - don't help as don't generate
        #else:
        return wur.pos

    def get_bidixstr(btwu, lemma1, pos1, lemma2, pos2, lemma3="", sep='c'): # sep c-compound, m-mwe
      # btwu - bitranslation Wordunit to add new translation
      lemma23 = lemma2
      if lemma3 != "":
        sp = "" # 'c'
        if sep == 'm':
          sp = "<b/>"
        lemma23 = lemma2+sp+lemma3
      found = 0
      for rd in btwu.readings:
        if cmp(lemma23, rd.wold) == 0 or cmp(lemma23, rd.lemla) == 0:
          found = 1
          break
      if found == 0:
        lm = lemma23.replace('<s n="', '<').replace('"/>', '>')
        btwu.readings.append(Wordform(lm, lm, '<'+pos2+'>')) # wordform not important here
      return '    <e><p><l>'+lemma1.replace('<np>n+', '<s n="np"/><s n="sg"/><s n="gen"/>+')+'<s n="'+pos1+'"/></l><r>'+lemma23+'<s n="'+pos2+'"/></r></p></e>\n'


    # generate_bidix_entries()
    s = -1
    ps = -1
    itr = 0
    while itr < len(phrases[TRANAN]): # word in translated phrase
           trword = phrases[TRANAN][itr]
           if ("syn&wrong" in trword.cat or "spell&new" in trword.cat) and trword.tobiltrs >= 0 and trword.totarget >= 0: # and "ignore" not in phrases[TARGAN][trword.totarget].cat: 
              # compounding exceptions
              cmwe = starts_cmwe(TARGAN, trword.totarget) # is a cmwe start?
              cmwe1 = tail_cmwe(TARGAN, trword.totarget+1) # is in a cmwe tail?
              cmweb = starts_cmwe(BILTRS, trword.tobiltrs) # is biltrs a head of compound?
              if cmweb == 'n':
                cmweb = tail_cmwe(BILTRS, trword.tobiltrs) # or is biltrs a in a tail compound?
              cmwes = starts_cmwe(SOURAN, phrases[BILTRS][trword.tobiltrs].tosource) # is source a head of compound?
              if cmwes == 'n':
                cmwes = tail_cmwe(SOURAN, phrases[BILTRS][trword.tobiltrs].tosource) # or is source a in a tail compound?
              ps = s
              s = phrases[BILTRS][trword.tobiltrs].tosource
              if s >= 0 and ps == s:
                itr += 1  
                continue
              b = phrases[BILTRS][trword.tobiltrs]
              bt = phrases[BILTRS][trword.tobiltrs]
              bpos = get_pos(phrases[BILTRS][trword.tobiltrs].main)
              lembtr = get_lemma(phrases[BILTRS][trword.tobiltrs].main)
              if s >= 0 and cmwe == 'n' and tail_cmwe(TARGAN, trword.totarget) == 'n':
                bt = phrases[SOURAN][s]
                bpos = get_pos(phrases[SOURAN][s].main)
                lembtr = get_lemma(phrases[SOURAN][s].main)
              lt = phrases[TARGAN][trword.totarget]

              jtr = 0
              verb = -1
              targets = [] 
              while jtr < len(phrases[TARGAN]): # word in target phrase
                if phrases[TARGAN][jtr].totransl == itr: # and jtr != trword.totarget:
                  targets.append(jtr)
                  if phrases[TARGAN][targets[-1]].main.pos == "vblex" and "der" not in phrases[TARGAN][targets[-1]].main.morph:
                    verb = jtr 
                jtr += 1
              # compounds from one source&biltrans to 2-3 target words
              ll = len(targets) 
              if ll == 2 and targets[0]+1 == targets[1] and targets[1]+1 < len(phrases[TARGAN]) and phrases[TARGAN][targets[0]].totransl == phrases[TARGAN][targets[1]].totransl and phrases[TARGAN][targets[1]+1].totransl == phrases[TARGAN][targets[1]].totransl+1:
                  if phrases[TARGAN][targets[0]].main.pos == "vblex":
                    llemmas = get_lemmamor(phrases[TARGAN][targets[1]].main)+'+'+get_lemma(phrases[TARGAN][targets[0]].main)
                    lpos = get_pos(phrases[TARGAN][targets[0]].main)
                  else:
                    llemmas = get_lemmamor(phrases[TARGAN][targets[0]].main)+'+'+get_lemma(phrases[TARGAN][targets[1]].main)
                    lpos = get_pos(phrases[TARGAN][targets[1]].main)
                  if (bpos == lpos or bpos in "partadvadj" and lpos in "partadvadj") and '"der"' not in llemmas:
                    lex_file.write(get_bidixstr(b, lembtr, bpos, llemmas, lpos))

              elif ll > 1 and (ll > 2 or starts_cmwe(TRANAN, itr) == 'n') and cmweb == 'n' and (s < 0 or s >= 0 and cmwes == 'n'):
                if verb > -1:
                  llemmas = get_lemma(phrases[TARGAN][verb].main) 
                  for i in range(ll): # target in targets.reverse():
                    if len(phrases[TARGAN][targets[ll-i-1]].main.lemla) > 2 and phrases[TARGAN][targets[ll-i-1]].main.lemla != phrases[TARGAN][verb].main.lemla:
                      llemmas = phrases[TARGAN][targets[ll-i-1]].main.wold + '<b/>' + llemmas
                  lex_file.write(get_bidixstr(b, lembtr, bpos, llemmas, "vblex"))
                elif starts_cmwe(TARGAN, targets[0]) == 'm': # satoi kaatamalla
                  llemmas = get_lemmamor(phrases[TARGAN][targets[ll-1]].main)
                  lpos = get_pos(phrases[TARGAN][targets[ll-1]].main)
                  if targets[ll-1]+1 < len(phrases[TARGAN]) and tail_cmwe(TARGAN, targets[ll-1]+1) == 'c':
                    if phrases[TARGAN][targets[ll-1]].main.pos == "vblex":
                      llemmas = get_lemmamor(phrases[TARGAN][targets[ll-1]+1].main) + '+' + get_lemmamor(phrases[TARGAN][targets[ll-1]].main)                      
                      lpos = get_pos(phrases[TARGAN][targets[ll-1]].main)
                    else:
                      llemmas = get_lemmamor(phrases[TARGAN][targets[ll-1]].main) + '+' + get_lemmamor(phrases[TARGAN][targets[ll-1]+1].main)                      
                      lpos = get_pos(phrases[TARGAN][targets[ll-1]+1].main)
                  for i in range(ll-1): 
                    llemmas = phrases[TARGAN][targets[ll-i-2]].main.wold + '<b/>' + llemmas
                  if (bpos == lpos or bpos in "partadvadj" and lpos in "partadvadj") and '"der"' not in llemmas:
                    lex_file.write(get_bidixstr(b, lembtr, bpos, llemmas, lpos))
                elif targets[0]+1 == targets[1] and tail_cmwe(TARGAN, targets[1]): 
                  llemmas = get_lemmamor(phrases[TARGAN][targets[0]].main)
                  lpos = get_pos(phrases[TARGAN][targets[1]].main)
                  # 3 words: <e><p><l>lanttulaatikko<s n="n"/></l><r>kaalikas<s n="n"/><s n="sg"/><s n="gen"/>+vorm<s n="n"/><s n="sg"/><s n="gen"/>+roog²<s n="n"/></r></p></e>
                  if len(targets) > 2 and targets[1]+1 == targets[2] and tail_cmwe(TARGAN, targets[2]): # add more
                    if phrases[TARGAN][targets[1]].main.pos == "vblex":
                      llemmas = llemmas + '+' + get_lemmamor(phrases[TARGAN][targets[2]].main) + '+' + get_lemma(phrases[TARGAN][targets[1]].main)                    
                      lpos = get_pos(phrases[TARGAN][targets[1]].main)
                    else:
                      llemmas = llemmas + '+' + get_lemmamor(phrases[TARGAN][targets[1]].main) + '+' + get_lemma(phrases[TARGAN][targets[2]].main)                    
                      lpos = get_pos(phrases[TARGAN][targets[2]].main)
                  else: # 2 words
                    llemmas = llemmas + '+' + get_lemma(phrases[TARGAN][targets[1]].main) 
                  if (bpos == lpos or bpos in "partadvadj" and lpos in "partadvadj") and '"der"' not in llemmas:
                    lex_file.write(get_bidixstr(b, lembtr, bpos, llemmas, lpos))


              elif s >= 0 and cmwes == 'n' and (cmwe == 'n' or cmweb == 'n'): # compounds 1 by 1
                lpos = ""
                lemtar = phrases[TARGAN][trword.totarget].main
                if trword.totarget+1 < len(phrases[TARGAN]) and (cmwe1 == 'c' or cmwe1 == 'm'): # and phrases[TARGAN][trword.totarget+1].main.pos == bpos:
                  lemtarr = phrases[TARGAN][trword.totarget+1].main                
                  # specific form? context? (ei mikään)
                  lpos = get_pos(lemtarr)
                  if (bpos == lpos or bpos in "partadvadj" and lpos in "partadvadj") and "der" not in lemtarr.morph:
                    lex_file.write(get_bidixstr(b, lembtr, bpos, get_lemma(lemtar), lpos, get_lemma(lemtarr), cmwe1))
                  itr += 1
                else: # and phrases[TARGAN][trword.totarget+1].main.pos == bpos:
            	  lpos = get_pos(lemtar)
                  if bpos == "np" and lpos == "n":
                    lpos = "np"
                  if (bpos == lpos or bpos in "partadvadj" and lpos in "partadvadj") and "der" not in lemtar.morph:
                    lex_file.write(get_bidixstr(b, lembtr, bpos, get_lemma(lemtar), lpos))

              else: # all 
                for lemtar in phrases[TARGAN][trword.totarget].readings:  # new bidix candidate (dif compounds! pos+form! gaps both ways!)
                  lpos = phrases[TARGAN][trword.totarget].main.pos # +1
            	  lpos = get_pos(lemtar)
                  if (bpos == lpos or bpos in "partadvadj" and lpos in "partadvadj") and "der" not in lemtar.morph:
                    lex_file.write(get_bidixstr(b, lembtr, bpos, get_lemma(lemtar), lpos))
           itr += 1  


  def lemma_word_inbiltr(ind, lemla, wold):
    if ind < 0:
      return 'n'
    for tr in phrases[BILTRS][ind].readings:
      if lemla+'&&' == tr.lemla[:len(lemla)+2] or '&&'+lemla+'&&' in tr.lemla:
        return 'm'
      if '&&'+lemla == tr.lemla[-len(lemla)-2:]:
        return 'w'

      if tr.lemla == lemla or lemla+'<' == tr.lemla[:len(lemla)+1] or '+'+lemla+'<' in tr.lemla or lemla+'<' == tr.lemla[len(tr.lemla)-len(lemla):]:
        return 'y'
      if wold != "" and tr.wold == wold or tr.lemla == wold or wold+'<' == tr.wold[:len(wold)+1] or '>'+wold+'<' in tr.wold:
        return 'y'
    return 'n'


  def relate(j, itr, cat="", gapl=[], trgpl=[], LR='B'): # TARGAN, TRANAN, gapl, trgapl
      if LR != "R":
          phrases[TARGAN][j].totransl = itr
      if LR != "L":
          phrases[TRANAN][itr].totarget = j
      if cat != "":
          phrases[TRANAN][itr].cat = cat 
      if j in gapl:
          gapl.remove(j)
      if itr in trgpl:
          trgpl.remove(itr)
      bilems = []
      if itr+1 < len(phrases[TRANAN]) and phrases[TRANAN][itr].tobiltrs > -1 and phrases[TRANAN][itr].tobiltrs+1 < len(phrases[BILTRS]): # don't have [itr+1].tobiltrs relation at this moment
        for lm in phrases[BILTRS][phrases[TRANAN][itr].tobiltrs+1].readings:
          bilems.append(lm.lemla)

      if tail_cmwe(TARGAN, j) != 'n' and phrases[TARGAN][j-1].totransl == -1  and (itr == 0 or itr > 0 and tail_cmwe(TRANAN, itr) == 'n' and (phrases[TRANAN][itr-1].totarget > -1 or "punct" in phrases[TRANAN][itr-1].cat or "ignore" in phrases[TRANAN][itr-1].cat)):
          phrases[TARGAN][j-1].totransl = itr # jõulusoov
          phrases[TARGAN][j-1].cat = "compound"

      if cat == "wordok1C ":
          phrases[TARGAN][j+1].totransl = itr 
          if j+1 in gapl:
            gapl.remove(j+1)
      elif tail_cmwe(TARGAN, j+1) != 'n' and phrases[TARGAN][j+1].totransl == -1:
        if itr+1 < len(phrases[TRANAN]) and phrases[TARGAN][j+1].main.lemla == phrases[TRANAN][itr+1].main.lemla and phrases[TRANAN][itr+1].totarget == -1:
          gapl, trgpl = relate(j+1, itr+1, "wordokc ", gapl, trgpl)
          phrases[TRANAN][itr+1].compound = True
        elif itr+1 < len(phrases[TRANAN])  and phrases[TARGAN][j+1].main.lemla in bilems and phrases[TRANAN][itr+1].totarget == -1:
          gapl, trgpl = relate(j+1, itr+1, "lexselc ", gapl, trgpl)
          phrases[TRANAN][itr+1].compound = True
        elif itr+1 < len(phrases[TRANAN])  and phrases[TRANAN][itr].tobiltrs > -1 and tail_cmwe(BILTRS, phrases[TRANAN][itr].tobiltrs+1) != 'n' and phrases[TRANAN][itr+1].totarget == -1:
          gapl, trgpl = relate(j+1, itr+1, "syn&wrongc ", gapl, trgpl)
          phrases[TRANAN][itr+1].compound = True
        elif itr+1 < len(phrases[TRANAN]) and phrases[TARGAN][j+1].main.morph == phrases[TRANAN][itr+1].main.morph and phrases[TARGAN][j+1].main.morph != phrases[TRANAN][itr].main.morph and phrases[TRANAN][itr+1].totarget == -1:
          gapl, trgpl = relate(j+1, itr+1, "syn&wrongc ", gapl, trgpl)
          phrases[TRANAN][itr+1].compound = True
        elif tail_cmwe(TRANAN, itr+1) != 'n' and phrases[TARGAN][j+1].main.lemla == phrases[TRANAN][itr+1].main.lemla and phrases[TRANAN][itr+1].totarget == -1:
          gapl, trgpl = relate(j+1, itr+1, "syn&wrongc1 ", gapl, trgpl)
        elif j+1 < len(phrases[TARGAN]):
          gapl, trgpl = relate(j+1, itr, "", gapl, trgpl, 'L')
      elif itr+1 < len(phrases[TRANAN]) and tail_cmwe(TRANAN, itr+1) != 'n' and phrases[TRANAN][itr+1].totarget == -1:
          gapl, trgpl = relate(j, itr+1, "syn&wrongc2 ", gapl, trgpl, 'R')

      if itr > 0:
        if phrases[TRANAN][itr-1].totarget == -1 and "notfound" in phrases[TRANAN][itr-1].cat and phrases[TRANAN][itr].tobiltrs > 0: # compare previous with current
          pbiltr = phrases[BILTRS][phrases[TRANAN][itr].tobiltrs-1]
          if phrases[TRANAN][itr].main.pos in {"n", "np"} and phrases[TRANAN][itr].totarget > 0 and (phrases[TRANAN][itr-1].main.pos in {"adj", "prn"} or pbiltr.tosource > -1 and phrases[SOURAN][pbiltr.tosource].main.pos in {"adj", "prn"}): # attr?
            targ = phrases[TARGAN][phrases[TRANAN][itr].totarget-1]
            if targ.totransl == -1 and (targ.main.pos in {"adj", "prn"} and pbiltr.main.pos in {"adj", "prn"} or pbiltr.tosource > -1 and phrases[SOURAN][pbiltr.tosource].main.pos in {"adj", "prn"}): 
              phrases[TRANAN][itr-1].totarget = phrases[TRANAN][itr].totarget - 1
              targ.totransl = itr - 1
              phrases[TRANAN][itr-1].cat = "syn&wrongA " 
            elif targ.main.morph == "":
              phrases[TRANAN][itr-1].totarget = phrases[TRANAN][itr].totarget
              phrases[TRANAN][itr-1].cat = "syn&wrongAx "     
            elif targ.totransl > -1:
              phrases[TRANAN][itr-1].totarget = phrases[TRANAN][itr].totarget
              phrases[TRANAN][itr-1].cat = "syn&wrongA "     

          if itr+1 < len(phrases[TRANAN]) and phrases[TRANAN][itr+1].totarget == -1 and phrases[TRANAN][itr+1].main.pos in {"n", "np"} and phrases[TRANAN][itr].totarget > 0 and phrases[TRANAN][itr].main.pos in {"adj", "prn"} and phrases[TRANAN][itr].totarget+1 < len(phrases[TARGAN]): # compare current with next
            targ = phrases[TARGAN][phrases[TRANAN][itr].totarget+1]
            if targ.totransl == -1 and targ.main.pos in {"n", "np"}: 
              phrases[TRANAN][itr+1].totarget = phrases[TRANAN][itr].totarget + 1
              targ.totransl = itr + 1
              phrases[TRANAN][itr+1].cat = "syn&wrongAn " 
            elif targ.totransl > -1:
              phrases[TRANAN][itr+1].totarget = phrases[TRANAN][itr].totarget + 1
              phrases[TRANAN][itr+1].cat = "syn&wrongAn "             

          if itr > 1 and phrases[TRANAN][itr-1].totarget == -1: # compare previous with one before that
            if phrases[TRANAN][itr-2].totarget > -1 and phrases[TRANAN][itr-2].main.pos in {"adj", "prn"} and phrases[TRANAN][itr-1].main.pos in {"n", "np"} and phrases[TRANAN][itr-2].tobiltrs >= 0 and phrases[TRANAN][itr-2].totarget >= 0: # attr?
              pbiltr = phrases[BILTRS][phrases[TRANAN][itr-2].tobiltrs+1]
              targ = phrases[TARGAN][phrases[TRANAN][itr-2].totarget+1]
              if targ.main.pos in {"n", "np"} and pbiltr.main.pos in {"n", "np"} and targ.totransl == -1: 
                if phrases[TRANAN][itr].totarget-1 == phrases[TRANAN][itr-2].totarget+1:
                  phrases[TRANAN][itr-1].totarget = phrases[TRANAN][itr-2].totarget + 1
                  targ.totransl = itr - 1
                else:
                  targ.totransl = itr - 2
                phrases[TRANAN][itr-1].cat = "syn&wrongAz " 
              elif targ.totransl > -1:
                phrases[TRANAN][itr-1].totarget = phrases[TRANAN][itr-2].totarget
                phrases[TRANAN][itr-1].cat = "syn&wrongAz "             

      return gapl, trgpl

  def continuation(gapl, trgapl):
      itr = 0
      while itr < len(phrases[TRANAN]): # word in phrase (2, len-1)
        if phrases[TRANAN][itr].totarget == -1 and "notfound" in phrases[TRANAN][itr].cat:
          i1 = -1
          i2 = -2
          if itr == 0:
            i1 = itr
          if itr == len(phrases[TRANAN])-1:
            i2 = len(phrases[TARGAN])-1
          if i1 < 0 and itr > 0 and phrases[TRANAN][itr-1].totarget > -1 and phrases[TRANAN][itr-1].totarget + 1 < len(phrases[TRANAN]):
            i1 = phrases[TRANAN][itr-1].totarget + 1
          if i2 < 0 and itr+1 < len(phrases[TRANAN]) and phrases[TRANAN][itr+1].totarget > -1 and phrases[TRANAN][itr+1].totarget - 1 >= 0:
            i2 = phrases[TRANAN][itr+1].totarget - 1
          if i1 < 0 and i2 > 0 and (phrases[TARGAN][i2-1].main.lemma == phrases[TRANAN][itr-1].main.lemma or phrases[TARGAN][i2-1].main.lemma in sb.keys() and phrases[TRANAN][itr-1].main.lemma in sb[phrases[TARGAN][i2-1].main.lemma]):
            i1 = i2
          if i2 < 0 and i1 > -1 and i1+1 < len(phrases[TARGAN]) and (phrases[TARGAN][i1+1].main.lemma == phrases[TRANAN][itr+1].main.lemma or phrases[TARGAN][i1+1].main.lemma in sb.keys() and phrases[TRANAN][itr+1].main.lemma in sb[phrases[TARGAN][i1+1].main.lemma]):
            i2 = i1
          if i1 == i2 and phrases[TARGAN][i1].totransl < 0 and "notfound" in phrases[TARGAN][i1].cat:
              phrases[TARGAN][i1].totransl = itr
              if phrases[TARGAN][i1].main.pos == "adv" and phrases[TRANAN][itr].main.pos == "vblex":
                j = i1-1
                while j >= 0:
                  if phrases[TARGAN][j].totransl == -1 and "ignore" not in phrases[TARGAN][i1].cat and phrases[TARGAN][j].main.pos == "vblex":
                    gapl, trgapl = relate(j, itr, "syn&wrongIV ", gapl, trgapl)
                  j -= 1
              if phrases[TRANAN][itr].totarget == -1:
                phrases[TRANAN][itr].totarget = i1
                phrases[TRANAN][itr].cat = "syn&wrongI " 
                if itr in trgapl: trgapl.remove(itr)
          if i1+1 == i2 and phrases[TARGAN][i1].totransl < 0 and "notfound" in phrases[TARGAN][i1].cat and phrases[TARGAN][i2].totransl < 0 and "notfound" in phrases[TARGAN][i2].cat and starts_cmwe(TARGAN, i1) != 'n':
              gapl, trgapl = relate(i1, itr, "syn&wrongIC ", gapl, trgapl)
              phrases[TARGAN][i2].totransl = itr
              if i2 in gapl: gapl.remove(i2)
        itr += 1  
      return gapl, trgapl

  nrr = infilenames[-1]
  cmp_file = open(infilenames[TRANSL]+nrr+".log", 'w')
  lex_file = open(infilenames[TRANSL]+nrr+".dix", 'w')

  rul_file = open(infilenames[-2], 'r') # (infilenames[TRANSL]+".nrl", 'r')
  lrules, lrlems = wordtrans_from_txt(rul_file)
  rul_file.close()

  cmp_file.write("Category\t  MT translation\t- Human translation\t- Inner bitranslation\n\n")

  all_words = 0
  nf_words = 0
  ignore_words = 0
  comp_parts = 0

  cor_words = 0
  diff_form = 0
  diff_lemma = 0
  sel_words = 0
  selr_words = 0
  selc_words = 0
  inc_words = 0
  spn_words = 0
  punct = 0
  other = ""

  sentno = 0
  lemmas = []
  phrases_itr = get_phrases(infilenames[:-2], cmp_file)
  plemmas = lemmas
  phrases, lemmas = phrases_itr.next()

  try:
    while phrases:
      sentno += 1

      # # # # # # # # # # # #
      cr = "CORR"
      rd = ""
      jor = 0 # first unattached in source (biltrans)
      cor = 0 # first unattached in target (est_mrf)
      itr = 0
      pos = ""
      itrsl = 0
      while itr < len(phrases[TRANAN]): # word in phrase I
        if itrsl < len(phrases[TRANSL]) and "punct" not in phrases[TRANAN][itr].cat and "<guio>" not in phrases[TRANAN][itr].main.morph:
          if itrsl < len(phrases[TRANSL]) and phrases[TRANAN][itr].guess == '*' and phrases[TRANSL][itrsl].main.wold == phrases[TRANAN][itr].main.wold and "punct" not in phrases[TRANSL][itrsl].cat: 
            itrsl += 1 
          else:
            ls = phrases[TRANAN][itr].main.lemla
            if itrsl > 0 and itrsl-1 < len(phrases[TRANSL]) and len(ls) > 0 and phrases[TRANSL][itrsl].main.wold[0] != ls[0] and phrases[TRANSL][itrsl-1].main.wold[0] == ls[0]: 
              phrases[TRANAN][itr].main.word = phrases[TRANSL][itrsl-1].main.word  
              phrases[TRANAN][itr].main.wold = phrases[TRANSL][itrsl-1].main.wold 
            while itrsl < len(phrases[TRANSL]) and ("punct" in phrases[TRANSL][itrsl].cat and "<guio>" not in phrases[TRANSL][itrsl].main.morph or phrases[TRANAN][itr].guess == '*' and phrases[TRANSL][itrsl].main.wold == phrases[TRANAN][itr].main.wold or itrsl+1 < len(phrases[TRANSL]) and phrases[TRANSL][itrsl+1].main.wold.find(phrases[TRANAN][itr].main.lemla[:-2]) == 0 and phrases[TRANAN][itr].main.lemla[:-2] not in phrases[TRANSL][itrsl].main.wold): #  not phrases[TRANSL][itrsl].compound and
              itrsl += 1 
            if itrsl < len(phrases[TRANSL]) and len(ls) > 0 and phrases[TRANSL][itrsl].main.wold[0] == ls[0]: 
              phrases[TRANAN][itr].main.word = phrases[TRANSL][itrsl].main.word 
              phrases[TRANAN][itr].main.wold = phrases[TRANSL][itrsl].main.wold 
              itrsl += 1 
        
        for sousent in phrases[SOURAN]: # find mrf correspondence in source
          if phrases[TRANAN][itr].main.wold == sousent.main.wold:
            if phrases[TRANAN][itr].main.morph == "": # missing in bidix, patch (pääsee)
              phrases[TRANAN][itr].main.pos = sousent.main.pos
            break
        pos = phrases[TRANAN][itr].main.pos
        lemma = phrases[TRANAN][itr].main.lemma
        lemla = phrases[TRANAN][itr].main.lemla
        if "punct" not in phrases[TRANAN][itr].cat and "ignore" not in phrases[TRANAN][itr].cat:  # word, not punctuation or ignored word
          j = jor 
          while j < len(phrases[BILTRS]): # find correspondence in biltrans
            i = 0
            for sousent in phrases[SOURAN]: # find mrf correspondence in source
              if phrases[BILTRS][j].main.lemla == sousent.main.wold:
                if phrases[BILTRS][j].main.morph == "": # missing in bidix, patch (pääsee)
                  phrases[BILTRS][j].main.pos = sousent.main.pos
                  phrases[BILTRS][j].main.lemma = sousent.main.lemma
                  phrases[BILTRS][j].main.lemla = sousent.main.lemla
                  phrases[BILTRS][j].main.word = sousent.main.word
                  phrases[BILTRS][j].main.wold = sousent.main.wold
                  phrases[BILTRS][j].main.morph = sousent.main.morph
              if j+1 < len(phrases[BILTRS]) and sousent.main.lemma.find(phrases[BILTRS][j+1].main.lemma) > 0:
                  phrases[BILTRS][j+1].compound = True
              si = sousent.main.lemma.find(phrases[BILTRS][j].main.lemma)
              if si >= 0: # inclusion!
                phrases[BILTRS][j].tosource = i
                if si > 0:
                  phrases[BILTRS][j].compound = True
                break
              i += 1
            ok = 0
            if phrases[BILTRS][j].totransl < 0:
              if lemma_word_inbiltr(j, lemla, phrases[TRANAN][itr].main.wold) == 'y':
                  phrases[TRANAN][itr].tobiltrs = j
                  phrases[BILTRS][j].totransl = itr
                  ok = 1
                  if itr > 0 and "px3pl" in phrases[BILTRS][j].main.morph and phrases[TRANAN][itr-1].main.lemma == "need":
                    phrases[TRANAN][itr-1].main.cat == "ignore"
                  while jor < len(phrases[BILTRS]) and phrases[BILTRS][jor].totransl >= 0:
                    jor += 1
                  break
              if len(phrases[BILTRS][j].readings) == 1 and phrases[BILTRS][j].readings[0].morph == "":
                if phrases[TRANAN][itr].main.wold == phrases[BILTRS][j].main.wold: 
                  phrases[TRANAN][itr].tobiltrs = j
                  phrases[BILTRS][j].totransl = itr
                  ok = 1
                  if itr > 0 and "px3pl" in phrases[BILTRS][j].main.morph and phrases[TRANAN][itr-1].main.lemma == "need":
                    phrases[TRANAN][itr-1].main.cat == "ignore"
              if ok == 1:
                 break
            j += 1

          j = cor 
          px = []
          while ("notfound" in phrases[TRANAN][itr].cat or "syn&wrongAn" in phrases[TRANAN][itr].cat) and j < len(phrases[TARGAN]): # find correspondence in target 
            if "punct" not in phrases[TARGAN][j].cat: # include ignored: meelest - n part post adv (or adp)
                
              ok = 0
              if phrases[TARGAN][j].totransl < 0 and phrases[TRANAN][itr].guess != "*" or phrases[TARGAN][j].totransl >= 0 and "syn&wrongAn" in phrases[TRANAN][phrases[TARGAN][j].totransl].cat:
                if j > 0 and tail_cmwe(TARGAN, j) and phrases[TRANAN][itr].main.lemla.find(phrases[TARGAN][j-1].main.lemla) == 0 and phrases[TRANAN][itr].main.lemla.find(phrases[TARGAN][j].main.lemla) >= len(phrases[TARGAN][j-1].main.lemla): # jõuluvana, koos+töö+konverents
                  relate(j-1, itr, "wordok1C ")
                  ok = 1
                for rt in phrases[TRANAN][itr].readings:
                  for rd in phrases[TARGAN][j].readings:
                    if rt.lemla == rd.lemla or rt.lemla == rd.lemla.replace('+', '').replace('-', ''): 
                      relate(j, itr, "wordok1 ")
                      ok = 1
                      break
                  if ok == 1:
                      break
                if ok == 1:
                  while cor < len(phrases[TARGAN]) and (phrases[TARGAN][cor].totransl >= 0 or "punct" in phrases[TARGAN][cor].cat): # or "ignore" in phrases[TARGAN][cor].cat): - include ignored
                    cor += 1

              if ok == 0 and phrases[TARGAN][j].totransl < 0 or phrases[TARGAN][j].totransl >= 0 and "syn&wrongAn" in phrases[TRANAN][phrases[TARGAN][j].totransl].cat:
                if phrases[TARGAN][j].main.wold == phrases[TRANAN][itr].main.wold: # compare surface forms (Aru - aru, without morph as the compound aru saama)
                  relate(j, itr, "wordok2 ")
                  ok = 1
                elif j > 0 and len(phrases[TRANAN][itr].main.wold) > 3 and phrases[TARGAN][j].main.wold[0] != phrases[TARGAN][j].main.word[0] and (cmp(phrases[TARGAN][j].main.wold[: len(phrases[TRANAN][itr].main.wold)-3], phrases[TRANAN][itr].main.wold[:-3]) == 0 or cmp(phrases[TRANAN][itr].main.wold[: len(phrases[TARGAN][j].main.wold)-3], phrases[TARGAN][j].main.wold[:-3]) == 0): # np
                  relate(j, itr, "wordok2 ")
                  ok = 1
                elif phrases[TARGAN][j].main.pos in ignorepos and phrases[SOURAN][phrases[BILTRS][phrases[TRANAN][itr].tobiltrs].tosource].main.pos in ignorepos and phrases[TRANAN][itr].main.wold.find(phrases[TARGAN][j].main.wold[0:-1]) == 0: # (aikana-ajal)
                  relate(j, itr, "ignored ")
                  ok = 1
                else:
                  for lemtar in phrases[TARGAN][j].readings: # check lemmas in target
                    repl = lemma_word_inbiltr(phrases[TRANAN][itr].tobiltrs, lemtar.lemla, lemtar.wold)
                    if repl == 'm':
                        relate(j, itr, "mwe ", [], [], 'R')
                        ok = 1
                        break
                    if repl == 'w':
                        relate(j, itr, "lexselw ")
                        phrases[TRANAN][itr].mwe = True
                        ok = 1
                        break
                    if repl == 'y':
                        relate(j, itr, "lexsel ")
                        ok = 1
                        break
                    if ok == 1:
                      break
                if ok == 1:
                  while cor < len(phrases[TARGAN]) and (phrases[TARGAN][cor].totransl >= 0 or "punct" in phrases[TARGAN][cor].cat): # or "ignore" in phrases[TARGAN][cor].cat): - include ignored
                    cor += 1
                    break
              #if ok == 1:
              #  break
              if ok == 0 and j > 0 and "px" in phrases[BILTRS][phrases[TRANAN][itr].tobiltrs].main.morph and phrases[TARGAN][j].totransl < 0 and ("prn><pers" in phrases[TARGAN][j-1].main.morph or phrases[TARGAN][j-1].main.lemma == "oma"):
                  px.append(j)
              # if already added to lrlems
              if ok == 0 and phrases[BILTRS][phrases[TRANAN][itr].tobiltrs].main.lemla in lrlems:
                  wtr = lrules[lrlems.index(phrases[BILTRS][phrases[TRANAN][itr].tobiltrs].main.lemla)]
                  for tr in wtr.translations:
                      if cmp(phrases[TARGAN][j].main.lemla, tr.lemla) == 0:
                          relate(j, itr, "syn&wrongL ")
                          ok = 1
            j += 1
          if ok == 0 and len(px) == 1:
              relate(px[0], itr, "syn&wrongX ")
              ok = 1
        itr += 1  

      # continuation
      gapl, trgapl = continuation([], [])

      gaps = 0
      gapl = []
      conj = []
      trgapl = []
      verb = -1
      comp = -1
      i = 0
      while i < len(phrases[TARGAN]):
        if "punct" not in phrases[TARGAN][i].cat:
          if verb < 0 and "vblex" == phrases[TARGAN][i].main.pos and "ignore" not in phrases[TARGAN][i].cat and "<neg>" not in phrases[TARGAN][i].main.morph: 
            verb = i
          elif comp < 0 and phrases[TARGAN][i].compound == True: 
            comp = i
          if phrases[TARGAN][i].totransl < 0 and "notfound" in phrases[TARGAN][i].cat:

            # compounds starts_cmwe
            if i > 0 and tail_cmwe(TARGAN, i) != 'n': # and phrases[TARGAN][i-1].totransl+1 < len(phrases[TRANAN]):
              if tail_cmwe(TRANAN, phrases[TARGAN][i-1].totransl+1) != 'n' and phrases[TRANAN][phrases[TARGAN][i-1].totransl+1].totarget < 0 and "notfound" in phrases[TRANAN][phrases[TARGAN][i-1].totransl+1].cat:
                phrases[TARGAN][i].totransl = phrases[TARGAN][i-1].totransl + 1
                phrases[TRANAN][phrases[TARGAN][i].totransl].totarget = i
                phrases[TRANAN][phrases[TARGAN][i].totransl].cat = "syn&wrongC"
              else: # tranan one word
                phrases[TARGAN][i].totransl = phrases[TARGAN][i-1].totransl
              i += 1
              continue
            if i+1 < len(phrases[TARGAN]) and starts_cmwe(TARGAN, i) != 'n' and phrases[TARGAN][i+1].totransl-1 >= 0 and phrases[TRANAN][phrases[TARGAN][i+1].totransl-1].totarget < 0 and "notfound" in phrases[TRANAN][phrases[TARGAN][i+1].totransl-1].cat:
              phrases[TARGAN][i].totransl = phrases[TARGAN][i+1].totransl - 1
              phrases[TRANAN][phrases[TARGAN][i].totransl].totarget = i
              phrases[TRANAN][phrases[TARGAN][i].totransl].cat = "syn&wrongC"
              i += 1
              continue
            if phrases[TARGAN][i].compound == True and i > 0 and phrases[TARGAN][i-1].totransl+1 < len(phrases[TRANAN]) and phrases[TRANAN][phrases[TARGAN][i-1].totransl+1].totarget >= 0:
              phrases[TARGAN][i].totransl = phrases[TARGAN][i-1].totransl 
              #phrases[TRANAN][phrases[TARGAN][i].totransl].totarget same
              i += 1
              continue
            if i > 0 and phrases[TARGAN][i-1].totransl+1 >= len(phrases[TRANAN]):
              phrases[TARGAN][i].totransl = phrases[TARGAN][i-1].totransl 
              #phrases[TRANAN][phrases[TARGAN][i].totransl].totarget same
              i += 1
              continue
            if i+1 < len(phrases[TARGAN]) and phrases[TARGAN][i+1].compound == True and phrases[TARGAN][i+1].totransl-1 >= 0 and phrases[TRANAN][phrases[TARGAN][i+1].totransl-1].totarget >= 0:
              phrases[TARGAN][i].totransl = phrases[TARGAN][i+1].totransl
              #phrases[TRANAN][phrases[TARGAN][i].totransl].totarget same
              i += 1
              continue

            lemta = phrases[TARGAN][i].main.lemla
            if lemta != "":
              # try to fill - phrases[TARGAN][i].totransl < 0 
              if i > 0 and phrases[TARGAN][i-1].totransl > 0 and "notfound" in phrases[TRANAN][phrases[TARGAN][i-1].totransl+1].cat: 
                 if phrases[TARGAN][i-1].totransl+1 < len(phrases[TRANAN]) and "notfound" in phrases[TRANAN][phrases[TARGAN][i-1].totransl+1].cat and phrases[TARGAN][i].main.pos == phrases[TRANAN][phrases[TARGAN][i-1].totransl+1].main.pos: # try next
                   phrases[TARGAN][i].totransl = phrases[TARGAN][i-1].totransl + 1
                   phrases[TRANAN][phrases[TARGAN][i].totransl].totarget = i
                   phrases[TRANAN][phrases[TARGAN][i].totransl].cat = "syn&wrong3 " 
                   if phrases[TARGAN][i].main.wold == phrases[TRANAN][phrases[TARGAN][i].totransl].main.wold:
                     phrases[TRANAN][phrases[TARGAN][i].totransl].cat = "wordok4 " # lemmas don't match, but wordforms do ("silmad", "lapsile/lastele")
                 elif phrases[TARGAN][i].totransl < 0 and "notfound" in phrases[TARGAN][i].cat:
                   gaps += 1
                   gapl.append(i)
              elif phrases[TARGAN][i].totransl < 0 and "notfound" in phrases[TARGAN][i].cat:
                 gaps += 1
                 gapl.append(i)
          if i > 0 and "cnjcoo" in phrases[TARGAN][i].main.morph:
              conj.append(len(gapl))
        i += 1
      trgapl = []
      trconj = []
      trcon = []
      i = 1
      while i < len(phrases[TRANAN]): # conj in translation
          if phrases[TRANAN][i].totarget < 0 and "notfound" in phrases[TRANAN][i].cat:
              trgapl.append(i)
          if "cnjcoo" in phrases[TRANAN][i].main.morph:
              trconj.append(len(trgapl))
              trcon.append(i)
          i += 1
      if len(conj) != len(trconj):
          trconj = []
          trcon = []
          conj = []        
      lc = len(conj)

      r = 0
      conto = len(phrases[TRANAN])
      maxr = lc + 1        
      while len(gapl) > 0 and len(trgapl) > 0 and r < maxr: # gaps match
        for ii in range(2):
           confrom = 0
           if r < maxr-1 and lc > 0:
               rgapl = gapl
               rtrgapl = trgapl
               if r == 0 and len(rgapl) > conj[0] and len(rtrgapl) > trconj[0]:
                 if conj[0] == 0 or trconj[0] == 0:
                   r += 1
                   continue
                 gapl = rgapl[:conj[0]]
                 trgapl = rtrgapl[:trconj[0]]
                 conto = trcon[0]
               elif r == lc and len(rgapl) > conj[-1] and len(rtrgapl) > trconj[-1]:
                 gapl = rgapl[conj[-1]:]
                 trgapl = rtrgapl[trconj[-1]:]
                 confrom = trcon[-1]
                 conto = len(phrases[TRANAN])
               elif r > 0 and r < lc and len(rgapl) > conj[r] and len(rtrgapl) > trconj[r]:
                 if conj[r] == conj[r-1] or trconj[r] == trconj[r-1]:
                   r += 1
                   continue
                 gapl = rgapl[conj[r-1]:conj[r]]
                 trgapl = rtrgapl[trconj[r-1]:trconj[r]]
                 confrom = trcon[r-1]
                 conto = trcon[r]
               else:
                 r += 1
                 continue
           trgapln = []
           gaps = len(gapl)
           #cmp_file.write(str(gapl)+" " +str(trgapl)+"\n")
           for trgap in trgapl: trgapln.append(trgap)
           for trgap in trgapln: 
             candy = []
             trpos = phrases[TRANAN][trgap].main.pos
             for targap in gapl: 
               if phrases[TARGAN][targap].main.pos in ps.keys() and trpos in ps[phrases[TARGAN][targap].main.pos]:
                 candy.append(targap)
             scandy = -1
             if len(candy) == 1:
               scandy = candy[0]
             else:
               ms = 0
               for ca in candy:
                 sc = 0
                 for mrs in phrases[TRANAN][trgap].main.morset:
                   if mrs in phrases[TARGAN][ca].main.morset:
                     sc += 2
                   elif mrs in phrases[TARGAN][ca].main.altmor:
                     sc += 1
                 if sc > ms:
                   ms = sc 
                   scandy = ca
                 if sc == ms:
                   #scandy = -1 
                   #break
                   l = len(phrases[TARGAN][ca].main.lemla)
                   if l >= 5: l = l-2 
                   if phrases[TARGAN][ca].main.pos == phrases[TRANAN][trgap].main.pos and phrases[TARGAN][scandy].main.pos != phrases[TRANAN][trgap].main.pos:
                     scandy = ca
                   elif phrases[TRANAN][trgap].main.lemla.find(phrases[TARGAN][ca].main.lemla[:l]) == 0 and phrases[TRANAN][trgap].main.lemla.find(phrases[TARGAN][scandy].main.lemla[:l]) != 0:
                     scandy = ca
                   else:
                     #scandy = -1
                     if abs(ca-trgap) < abs(scandy-trgap):
                       scandy = ca
             if scandy > -1:
               gapl, trgapl = relate(scandy, trgap, "syn&wrongN", gapl, trgapl)
               gaps = len(gapl)

           #trgapl = []
           i = confrom # 0
           while i < conto: # len(phrases[TRANAN]): # gaps in translation
             if phrases[TRANAN][i].totarget < 0 and "notfound" in phrases[TRANAN][i].cat:
       
               if comp > 0 and phrases[TARGAN][comp].totransl < 0 and "punct" not in phrases[TARGAN][comp].cat and (phrases[BILTRS][phrases[TRANAN][i].tobiltrs].compound == True or phrases[TRANAN][i].tobiltrs+1 < len(phrases[BILTRS]) and phrases[BILTRS][phrases[TRANAN][i].tobiltrs+1].compound == True):
                 phrases[TARGAN][comp].totransl = i
                 phrases[TRANAN][i].totarget = comp
                 phrases[TRANAN][i].cat = "syn&wrongC " 
                 if i > 0 and phrases[TRANAN][i-1].totarget < 0 and "notfound" in phrases[TRANAN][i-1].cat:
                   phrases[TARGAN][comp-1].totransl = i-1
                   phrases[TRANAN][i-1].totarget = comp-1
                   phrases[TRANAN][i-1].cat = "syn&wrongC " 
                   if i-1 in trgapl:
                     trgapl.remove(i-1)
                   if comp-1 in gapl:
                     gapl.remove(comp-1)
                     gaps -= 1
                 else: 
                   phrases[TARGAN][comp-1].totransl = i
                 if comp in gapl:
                   gapl.remove(comp)
                   gaps -= 1
               elif verb > 0 and phrases[TARGAN][verb].totransl < 0 and (phrases[TRANAN][i].main.pos == "vblex" or phrases[BILTRS][phrases[TRANAN][i].tobiltrs].main.pos == "vblex"):
                 phrases[TARGAN][verb].totransl = i
                 phrases[TRANAN][i].totarget = verb
                 phrases[TRANAN][i].cat = "syn&wrongV " 
                 if verb in gapl:
                   gapl.remove(verb)
                   gaps -= 1
               #else:
               #  trgapl.append(i)
             i += 1
           if gaps < 1: break
           r += 1
           if gaps == 1 and len(trgapl) == 0:
               if gapl[0]+1 < len(phrases[TARGAN]) and phrases[TARGAN][gapl[0]+1].totransl > -1:
                    phrases[TARGAN][gapl[0]].totransl = phrases[TARGAN][gapl[0]+1].totransl
                    gaps = 0
               elif gapl[0]-1 >= 0 and phrases[TARGAN][gapl[0]-1].totransl > -1:
                    phrases[TARGAN][gapl[0]].totransl = phrases[TARGAN][gapl[0]-1].totransl
                    gaps = 0
           if gaps == 1 and len(trgapl) == 2 and trgapl[0] + 1 == trgapl[1]: 
                    phrases[TRANAN][trgapl[1]].totarget = gapl[0]
                    phrases[TRANAN][trgapl[1]].cat = "syn&wrong43 "
                    phrases[TRANAN][trgapl[0]].totarget = gapl[0]
                    phrases[TRANAN][trgapl[0]].cat = "syn&wrong43 "
                    phrases[TRANAN][trgapl[1]].mwe = True
                    gaps = 0
           if gaps == 1 or (gaps == 2 and gapl[0] + 1 == gapl[1]): # add more variants with sparse parts
             if len(trgapl) == 1:
                    phrases[TRANAN][trgapl[0]].totarget = gapl[0]
                    phrases[TRANAN][trgapl[0]].cat = "syn&wrong41 "
                    phrases[TARGAN][gapl[0]].totransl = trgapl[0]
                    if gaps == 2:
                      phrases[TARGAN][gapl[1]].totransl = trgapl[0]
                      if phrases[TARGAN][gapl[1]].compound != True:
                        phrases[TARGAN][gapl[1]].mwe = True
                    gaps = 0
             elif gaps == 2 and len(trgapl) == 2 and trgapl[0] + 1 == trgapl[1]:
               if phrases[TRANAN][trgapl[0]].main.pos == phrases[TARGAN][gapl[1]].main.pos and phrases[TRANAN][trgapl[1]].main.pos == phrases[TARGAN][gapl[0]].main.pos or phrases[TRANAN][trgapl[0]].main.pos == "vblex" and phrases[TARGAN][gapl[1]].main.pos == "vblex" or phrases[TRANAN][trgapl[1]].main.pos == "vblex" and phrases[TARGAN][gapl[0]].main.pos == "vblex":
                    relate(gapl[1], trgapl[0], "syn&wrong42 ")
                    relate(gapl[0], trgapl[1], "syn&wrong42 ")
               else: 
                    relate(gapl[0], trgapl[0], "syn&wrong42 ")
                    relate(gapl[1], trgapl[1], "syn&wrong42 ")
                    if phrases[TRANAN][trgapl[1]].compound == True:
                      phrases[TARGAN][gapl[1]].compound = True
                    elif phrases[TARGAN][gapl[1]].compound != True:
                      phrases[TARGAN][gapl[1]].mwe = True               
               gaps = 0
           if gaps == 0:
           	 continue      
    
           i = 0
           istr = ""
           while i < len(gapl):  
             if phrases[TARGAN][gapl[i]].totransl == -1 and "notfound" in phrases[TARGAN][gapl[i]].cat:
                 lpos = phrases[TARGAN][i].main.pos 
                 istr += lpos
             i += 1
           i = 0
           while i < len(gapl):  
             lpos = phrases[TARGAN][i].main.pos 
             if phrases[TARGAN][gapl[i]].totransl == -1 and "notfound" in phrases[TARGAN][gapl[i]].cat and lpos not in istr: 
               j = 0
               vb = 0
               while j < len(trgapl): 
                 lpos = phrases[TARGAN][i].main.pos 
                 rpos = phrases[TRANAN][j].main.pos
                 if rpos == "vblex":
                   vb = j
                 if lpos == rpos: 
                   phrases[TRANAN][j].totarget = gapl[i]
                   phrases[TRANAN][j].cat = "syn&wrongs "
                   phrases[TARGAN][gapl[i]].totransl = j
                   gaps -= 1
                   gapl.remove(gapl[i])
                 j += 1
               if phrases[TARGAN][gapl[i]].totransl == -1 and lpos == "adv":
                   phrases[TRANAN][vb].totarget = gapl[i]
                   phrases[TRANAN][vb].cat = "syn&wrongs "
                   phrases[TARGAN][gapl[i]].totransl = vb
                   gaps -= 1
                   gapl.remove(gapl[i])
             i += 1

           itr = confrom # 0
           while itr < conto: # len(phrases[TRANAN]): # word in phrase IIb
             # more general form - 2 adjacent words
             if itr > 0 and "notfound" in phrases[TRANAN][itr].cat and phrases[TRANAN][itr].totarget > 0 and "notfound" in phrases[TRANAN][itr-1].cat and phrases[TARGAN][phrases[TRANAN][itr].totarget - 1].totransl == -1:
                  ind = phrases[TRANAN][itr].totarget - 1
                  phrases[TRANAN][itr-1].totarget = ind
                  phrases[TARGAN][ind].totransl = itr - 1
                  phrases[TRANAN][itr-1].cat = "syn&wrong2 " 
                  if phrases[TARGAN][ind].main.wold == phrases[TRANAN][itr-1].main.wold:
                    phrases[TRANAN][itr-1].cat = "wordok3 " # lemmas don't match, but wordforms do ("Ü/ülikoolis")
    
             if phrases[TRANAN][itr].totarget == -1 and "notfound" in phrases[TRANAN][itr].cat: 
               j = cor 
               while j < len(phrases[TARGAN]) and phrases[TRANAN][itr].totarget == -1: 
                 if phrases[TARGAN][j].totransl == -1 and "notfound" in phrases[TARGAN][j].cat and (phrases[TARGAN][j].main.pos != "?" and phrases[TRANAN][itr].main.pos in ps[phrases[TARGAN][j].main.pos] or phrases[TRANAN][itr].tobiltrs >=0 and phrases[BILTRS][phrases[TRANAN][itr].tobiltrs].guess == "*" and phrases[BILTRS][phrases[TRANAN][itr].tobiltrs].main.pos != "?" and phrases[TARGAN][j].main.pos in ps[phrases[BILTRS][phrases[TRANAN][itr].tobiltrs].main.pos]): 
                   t_lemla = phrases[TARGAN][j].main.lemla
                   if "notfound" in phrases[TARGAN][j].cat:
    
                     if phrases[BILTRS][phrases[TRANAN][itr].tobiltrs].guess == "*":
                       phrases[TRANAN][itr].cat = "spell&new " 
                     else:
                       phrases[TRANAN][itr].cat = "syn&wrong5 " 
                     gapl, trgapl = relate(j, itr, "", gapl, trgapl)
                     gaps = len(gapl)

                     while cor < len(phrases[TARGAN]) and (phrases[TARGAN][cor].totransl >= 0 or "punct" in phrases[TARGAN][cor].cat): # or "ignore" in phrases[TARGAN][cor].cat): - include ignored
                       cor += 1
                     break
                 j += 1
             itr += 1  
           gapl, trgapl = continuation(gapl, trgapl)
           gaps = len(gapl)
           if r < maxr-1 and lc > 0:
               gapl = rgapl
               trgapl = rtrgapl
      # end of gaps match

      itr = 0
      while itr < len(phrases[TRANAN]):
        if "notfound" in phrases[TRANAN][itr].cat and phrases[TRANAN][itr].totarget < 0:
          # ^vaihto<n><sg><nom>/vahetus<n><sg><nom>$ ^opiskelija<n><sg><ess>/üliõpilane<n><sg><ess>$
          if itr > 0 and tail_cmwe(TRANAN, itr) != 'n' or tail_cmwe(SOURAN, phrases[BILTRS][phrases[TRANAN][itr].tobiltrs].tosource) != 'n': 
            if tail_cmwe(TARGAN, phrases[TRANAN][itr-1].totarget+1) != 'n' and phrases[TARGAN][phrases[TRANAN][itr-1].totarget+1].totransl == phrases[TARGAN][phrases[TRANAN][itr-1].totarget].totransl:
                phrases[TARGAN][phrases[TRANAN][itr-1].totarget+1].totransl = itr
                phrases[TRANAN][itr].totarget = phrases[TRANAN][itr-1].totarget+1
                phrases[TRANAN][itr].cat = "syn&wrongC"
          if phrases[TRANAN][itr].main.pos == "prn": # se - ta
                phrases[TRANAN][itr].cat = "pronoun"

          i1 = -2
          i2 = -1
          i3 = -1
          if itr == 0:
            i1 = itr
          if itr == len(phrases[TRANAN])-1:
            i2 = len(phrases[TARGAN])-1
          if i1 < 0 and itr > 0 and phrases[TRANAN][itr-1].totarget > -1 and phrases[TRANAN][itr-1].totarget + 1 < len(phrases[TRANAN]):
            i1 = phrases[TRANAN][itr-1].totarget + 1
          if i2 < 0 and itr+1 < len(phrases[TRANAN]) and phrases[TRANAN][itr+1].totarget > -1 and phrases[TRANAN][itr+1].totarget - 1 >= 0:
            i2 = phrases[TRANAN][itr+1].totarget - 1
          if i1 < 0 and i2 > -1 and (phrases[TARGAN][i2].main.lemma == phrases[TRANAN][itr-1].main.lemma or phrases[TARGAN][i2].main.lemma in sb.keys() and phrases[TRANAN][itr-1].main.lemma in sb[phrases[TARGAN][i2].main.lemma]):
            if i2+1 < len(phrases[TARGAN]):
              i3 = i2+1
            else: i3 = i2
          if i2 < 0 and i1 > -1 and i1 < len(phrases[TARGAN]) and (phrases[TARGAN][i1].main.lemma == phrases[TRANAN][itr+1].main.lemma or phrases[TARGAN][i1].main.lemma in sb.keys() and phrases[TRANAN][itr+1].main.lemma in sb[phrases[TARGAN][i1].main.lemma]):
            if i1-1 > 0:
              i3 = i1-1
            else: i3 = i1
          if i1 == i2 and i3 < 0: # i3 start or end
            i3 = i1
          if i1 == i2+1 and i3 < 0:
            if i1 < len(phrases[TARGAN]): # i3 with next
              i3 = i1
            else: # i3 with previous
              i3 = i2
          if i3 > -1:
            phrases[TRANAN][itr].totarget = i3
            phrases[TRANAN][itr].cat = "syn&wrongJ " 
        itr += 1

      # generate entries
      generate_bidix_entries()  

      # output relations
      i = 0
      itr = 0
      pi2 = -1
      trlen = len(phrases[TRANAN])
      tarlen = len(phrases[TARGAN])
      while i < trlen: # nos
        if phrases[TRANAN][i].totarget < 0:
          if "punct" in phrases[TRANAN][i].cat or "ignore" in phrases[TRANAN][i].cat:
            phrases[TRANAN][i].color = "grey"
          else:
            phrases[TRANAN][i].color = "red"
        else:
          pi1 = pi2 
          pi2 = phrases[TRANAN][i].totarget
          if i > 0 and pi1 >= 0 and pi2 >= 0:
            if pi1 <= pi2:
              phrases[TRANAN][i-1].color = "green"
              if i == trlen - 1:
                phrases[TRANAN][i].color = "green"  
            else:
              phrases[TRANAN][i-1].color = "blue"
              if i == trlen - 1:
                phrases[TRANAN][i].color = "blue"
        i += 1
      i = 0
      pi2 = -1
      while i < tarlen:
        if phrases[TARGAN][i].totransl < 0:
          if "punct" in phrases[TARGAN][i].cat or "ignore" in phrases[TARGAN][i].cat:
            phrases[TARGAN][i].color = "grey"
          else:
            phrases[TARGAN][i].color = "red"
        else:
          pi1 = pi2 
          pi2 = phrases[TARGAN][i].totransl
          if pi2 < 0:
              phrases[TARGAN][i].color = "red"
          if i > 0 and pi1 >= 0 and pi2 >= 0:
            if pi1 <= pi2:
              phrases[TARGAN][i-1].color = "green"
              if i == tarlen - 1:
                phrases[TARGAN][i].color = "green"
            else:
              phrases[TARGAN][i-1].color = "blue"
              if i == tarlen - 1:
                phrases[TARGAN][i].color = "blue"
        i += 1

      while itr < len(phrases[TRANAN]): # word in phrase

        # cat   translation  -  target  -  biltrans
        cmp_file.write("\n" + phrases[TRANAN][itr].cat + "\t" + phrases[TRANAN][itr].main.word + ' ' + phrases[TRANAN][itr].prints() + "\t- ")
        for jj in range(len(phrases[TARGAN])): # can be multiple correspondences in target (gaps!)
          if jj > 0 and phrases[TARGAN][jj].totransl == -1 and phrases[TARGAN][jj-1].totransl == itr and "notfound" in phrases[TARGAN][jj].cat: # gap
            cmp_file.write(phrases[TARGAN][jj].prints() + ' gap ')
          if phrases[TARGAN][jj].totransl == itr: 
            cmp_file.write(phrases[TARGAN][jj].prints() + ' ')
        if "wordokc" not in phrases[TRANAN][itr].cat and phrases[TRANAN][itr].tobiltrs >= 0: 
          cmp_file.write("\t- " + phrases[BILTRS][phrases[TRANAN][itr].tobiltrs].prints())
        else:
          cmp_file.write("\t- not related")

        # count units
        word = phrases[TRANAN][itr]
        if "punct" in  word.cat:
          punct += 1
        else:
          if "wordok" in  word.cat:
            cor_words += 1 # forms are same
            if "1" not in  word.cat: 
              diff_lemma += 1
            if word.main.wold == phrases[TARGAN][ word.totransl].main.wold: 
              diff_form += 1
              word.cat = "wordok0 " # forms are different
            biltrs = phrases[BILTRS][word.tobiltrs].main.lemla
            if biltrs in lrlems and len(lrules[lrlems.index(biltrs)].translations) > 1: # fix
              for tran in lrules[lrlems.index(biltrs)].translations: 
                if word.main.lemla == tran.lemla and tran.old == True: # fix for prev if 
                  selc_words += 1
          elif "lexsel" in word.cat: # after ls.py missing in biltrs!
            sel_words += 1
          elif "syn&wrong" in  word.cat or "spell&new" in word.cat:
            biltrs = phrases[BILTRS][word.tobiltrs].main.lemla
            if biltrs in lrlems and len(lrules[lrlems.index(biltrs)].translations) > 1: # fix
              for tran in lrules[lrlems.index(biltrs)].translations: 
                if word.main.lemla == tran.lemla and tran.old == True: # fix for prev if 
                  word.cat = "lexselr" # presupposes nrl without dups
                  selr_words += 1
            if "lexsel" not in word.cat:
              inc_words += 1
              if "spell&new" in  word.cat:
                spn_words += 1
          elif "ignore" in  word.cat:
            ignore_words += 1
          elif "notfound" in  word.cat:
            nf_words += 1
          else:
            other =  other + ' ' +  word.cat
        itr = itr + 1      
    
      cmp_file.write("\n" + L1 + ":  " + print_phrase(phrases[SOURCE]) + L2 + ":  " + print_phrase(phrases[TARGET]) + "MT:   " + print_phrase(phrases[TRANSL]) + "BIL:\t" + print_phrase(phrases[BILTRS]) + L1 + " A:\t" + print_phrase(phrases[SOURAN]) + L2 + " A:\t" + print_phrase(phrases[TARGAN])+ "MT A:\t" + print_phrase(phrases[TRANAN]) + "\n\n")

      itr = 0
      while itr < len(phrases[BILTRS]):
        word = phrases[BILTRS][itr]
        if "punct" not in word.cat and len(word.main.lemla) > 1 and word.totransl >= 0 and phrases[TRANAN][word.totransl].totarget >= 0:
          # and (len(word.readings) > 1 or word.main.lemla in lrlems): # then don't count before
          # so add all and output with mult trans
          targettr = phrases[TARGAN][phrases[TRANAN][word.totransl].totarget]
          ttr = None
          if phrases[TRANAN][word.totransl].totarget +1 < len(phrases[TARGAN]) and phrases[TARGAN][phrases[TRANAN][word.totransl].totarget].totransl == phrases[TARGAN][phrases[TRANAN][word.totransl].totarget+1].totransl:
            ttr = phrases[TARGAN][phrases[TRANAN][word.totransl].totarget+1]
          near = []
          if len(lemmas) == 0:
            near = plemmas
          if lemmas == []:
            near = lemmas
          prevlemma = ""
          prevmorph = ""
          if itr > 0 and "punct" not in phrases[BILTRS][itr-1].cat:
            prevlemma = phrases[BILTRS][itr-1].main.lemla
            prevmorph = phrases[BILTRS][itr-1].main.morph
          nextlemma = ""
          nextmorph = ""
          if itr+1 < len(phrases[BILTRS]) and "punct" not in phrases[BILTRS][itr+1].cat:
            nextlemma = phrases[BILTRS][itr+1].main.lemla
            nextmorph = phrases[BILTRS][itr+1].main.morph
         
          if word.main.lemla in lrlems: # existing from file or from txt
            lrules[lrlems.index(word.main.lemla)].add_context(word, targettr, ttr, prevlemma, prevmorph, nextlemma, nextmorph, near)
          else: # new
            wtr = Wordtrans(word)
            wtr.add_context(word, targettr, ttr, prevlemma, prevmorph, nextlemma, nextmorph, near)
            lrules.append(wtr)
            lrlems.append(word.main.lemla)
        itr += 1 

      try:
        if len(lemmas) > 0: # =0 for continuation of sentence
          plemmas = lemmas
        phrases, lemmas = phrases_itr.next()
      except StopIteration:
        break

  except IndexError:
    sys.stderr.write("Could not read phrase nr %i, %i: \n%s" % (sentno, len(phrases), print_phrases(phrases)))
    sys.exit(1)

  all_words = cor_words + sel_words + selr_words + inc_words + nf_words + ignore_words
  cmp_file.write("\n\n\nWords all(atomic): "+str(all_words)+"\tincl compound parts:"+"\t"+str(comp_parts)+"\ncorrect:"+"\t"+str(cor_words)+"\t"+"incl lexsel+ (correctly selected by ls): \t"+str(selc_words)+"\nlexsel errors: "+"\t"+str(sel_words)+"\tlexsel- (by ls): "+"\t"+str(selr_words)+"\nincorr: "+"\t"+str(inc_words)+"\tincl spell&new:"+"\t"+str(spn_words)+"\nnotfound:"+"\t"+str(nf_words)+"\tignored:"+"\t"+str(ignore_words)+"\tpunct\t"+str(punct)+"\n")  # how many props? "\tincl diff lemma:"+"\t"+str(diff_lemma)+"\tincl diff forms:"+"\t"+

  cmp_file.close()
  lex_file.close()

  rul_file = open(infilenames[TRANSL]+nrr+".rul", 'w')
  wordtrans_to_txt(lrules, rul_file)
  rul_file.close()

def usage():
    sys.stderr.write("""Finds new bidictionary entries based on previous incomplete translations.  
    Usage: python comp.py [source] [target] [transl] [biltrans] [source_an] [target_an] [transl_an] [lexrules] [symbol] \n""")
    # [source] and [target] facilitate reading
    # all other inputs are used for relating and comparing target with translation and generation of entries

if __name__ == "__main__":

    if len(sys.argv)!=10:
        usage()
        sys.exit(1)
    sys.stderr.write(sys.argv[1] + " " + sys.argv[2] + " " + sys.argv[3] + " " + sys.argv[4] + " " + sys.argv[5] + " " + sys.argv[6] +  " " + sys.argv[7] + "\n")
    compare(sys.argv[1:10])

