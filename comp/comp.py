#!/usr/bin/python -w
# -*- coding: utf8 -*-

import sys
from collections import defaultdict

def compare(f1, f2, f3, f4, f5, f6, f7):
  # Usage: python comp.py [source] [target] [transl] [biltrans] [source_an] [target_an] [transl_an] \n""")
  # python com.py soome.txt eesti.txt soome.tolge soome.biltr soome.mrf eesti.mrf soome.pchnk

  sou_file = file(f1)
  tar_file = file(f2)
  trans_file = file(f3)
  biltr_file = file(f4)
  sou_an_file = file(f5)
  tar_an_file = file(f6)
  trans_an_file = file(f7)
  cmp_file = open(f3+".log", 'w')
  lex_file = open(f3+".dix", 'w')
  cmp_file.write("Correspondence class\t  MT translation\t- Correct translation\t- Inner bitranslation\n\n")

  all_words = 0
  ccor_words = 0
  csel_words = 0
  cinc_words = 0
  cspn_words = 0
  nf_words = 0
  pron_words = 0
  comp_parts = 0

  cor_words = 0
  sel_words = 0
  inc_words = 0
  spn_words = 0


  sou = sou_file.readline().strip().replace('.', " .").replace(',', " ,").replace(':', " :").replace(';', " ;").replace('!', " !").replace('?', " ?")
  row = 1

  try:
    while sou:
      cr = "CORR"
      rd = ""

      tar = tar_file.readline().strip().replace('.', " .").replace(',', " ,").replace(':', " :").replace(';', " ;").replace('!', " !").replace('?', " ?")
      trans = trans_file.readline().strip().replace(" *", " ").replace(" #", " ")
      # trans: if row ends with  ( ) / @ + - = " %   -> append next row
      while trans == "" or trans[-1]=='(' or trans[-1]==')' or trans[-1]=='+' or trans[-1]=='-' or trans[-1]=='=' or trans[-1]=='@' or trans[-1]=='/' or trans[-1]=='"' or trans[-1]=='%':
        if trans != "" and (trans[-1]==')' or trans[-1]=='"' or trans[-1]=='=' or trans[-1]=='%'):
          trans = trans + ' '
        trans = trans + trans_file.readline().strip().replace(" *", " ").replace(" #", " ")
      biltr = ""
      biltr = biltr_file.readline().strip().replace("¹", "")
      # biltr-an: if row doesn't end with '$' -> append next row
      while not biltr or biltr[-1]!='$':
        biltr = biltr + ' ' + biltr_file.readline().strip().replace("¹", "")
      sou_an = sou_an_file.readline().strip()
      while not sou_an or sou_an[-1]!='$':
        sou_an = sou_an + ' ' + sou_an_file.readline().strip()
      sou_an = sou_an.replace("<N>", "<n>").replace("<N><Prop>", "<np>").replace("<V>", "<vblex>").replace("<A>", "<adj>").replace("<Adv>", "<adv>").replace("<Pcle>", "<adv>").replace("<Pron>", "<prn>")
      tar_an = tar_an_file.readline().strip()
      while not tar_an or tar_an[-1]!='$':
        tar_an = tar_an + ' ' + tar_an_file.readline().strip()
      tar_an = tar_an.replace("<N>", "<n>").replace("<N><Prop>", "<np>").replace("<V>", "<vblex>").replace("<A>", "<adj>").replace("<Adv>", "<adv>").replace("<Pcle>", "<adv>").replace("<Pron>", "<prn>").replace("<Hom1>", "").replace("<Hom2>", "").replace("<Hom3>", "")
      trans_an = trans_an_file.readline().strip().replace("¹", "")
      while not trans_an or trans_an[-1]!='$':
        trans_an = trans_an + ' ' + trans_an_file.readline().strip().replace("¹", "")
      
      csou = sou.split(" , ")
      ctar = tar.split(" , ")
      ctrans = trans.split(" , ")
      cbiltr = biltr.split(" ^,<cm>/,<cm>$ ")
      csouan = sou_an.split(" ^,/,<Punct>$ ")
      ctaran = tar_an.split(" ^,/,<?>$ ")
      ctransan = trans_an.split(" ^,<cm>$ ")

      x = len(ctransan) - len(ctaran) 
      if x != 0: # x > 0: add comma to tar(_an); x < 0: remove comma from tar(_an)
        xtar = tar.split()
        xtaran = tar_an.split()
        xtransan = trans_an.split()
        tarr = xtar[0]+' '
        tar_ann = xtaran[0]+' '
        for i in xrange(len(xtar)-2):
          if x > 0 and "^,<cm>" in xtransan[i+1] and xtar[i] != "," and xtar[i+1]!= "," and (i+2>=len(xtar) or xtar[i+2]!= ","): 
            tarr += ", "
            tar_ann += "^,/,<?>$ "
            x -= 1
          if x < 0 and xtar[i+1] == ',' and xtransan[i] not in " ^,<cm>$ " and xtransan[i+1] not in " ^,<cm>$ " and (i+2>=len(xtransan) or xtransan[i+2] not in " ^,<cm>$ "): 
            x += 1
          else:
            tarr += xtar[i+1]+' '
            tar_ann += xtaran[i+1]+' '
        tarr += xtar[len(xtar)-1]
        tar_ann += xtaran[len(xtaran)-1]
        ctaran = tar_ann.split(" ^,/,<?>$ ")
        ctar = tarr.split(" , ")
       
      if len(ctar) == 1: 
        csou = [sou]
        ctrans = [trans]
        cbiltr = [biltr]
        csouan = [sou_an]
        ctaran = [tar_an]
        ctransan = [trans_an]
        

      ctr = 0
      while ctr < len(ctransan): # chunk in sent
       itrans = ctrans[ctr].split()
       ibiltr = cbiltr[ctr].split()
       itaran = ctaran[ctr].split()
       itransan = ctransan[ctr].split()
       prefix = ctransan[ctr].split()
       
       ind_tar_tr = [-1 for i in range(len(itaran)+1)]
       ind_tr_tar = [-1 for i in range(len(itransan)+1)]
       ind_tr_btr = [-1 for i in range(len(itransan))]
       ind_btr_tr = [-1 for i in range(len(ibiltr))]

       jor = 0 # first unattached in source (biltrans)
       kor = 0 # first unattached in target (est_mrf)
       itr = 0
       pos = ""
       lemma = ""
       lemmal = ""
       lemmab = ""
       while itr < len(itransan): # word in chunk I
        prefix[itr] = "notfound "

        ppos = pos
        plemma = lemma
        plemmal = lemmal
        plemmab = lemmab
        lemma = ""
        #word  = ""
        if len(itransan[itr]) < 3 or len(itransan[itr]) <= 7 and (itransan[itr][0] != '^' or itransan[itr][1] != '*'):  # punctuation
          prefix[itr] = "punct "
        elif itransan[itr][1] in '...,:;()?..!.."/@\'+=\\#¤%&[]£${}^|<>0123456789' or (itransan[itr][1] in '*-' and itransan[itr][2] in '/<') or "<cm>" in itransan[itr] or "<sent>" in itransan[itr]:  # don't take ...
          prefix[itr] = "punct "
        if "punct" not in prefix[itr]:
          if itransan[itr][1] == '*':
            lemma = '/' + itransan[itr][2:-1] + '<'
            pos = "<np>"
          else:
            pos = '<' + itransan[itr].split('<')[1].split('>')[0] + '>'
            lemma = '/' + itransan[itr].split('<')[0][1:] + '<'
        lemmal = lemma.lower().replace('Ä', 'ä').replace('Ö', 'ö').replace('Ü', 'ü').replace('Õ', 'õ')
        #cmp_file.write("\nlemma"+ lemma+" "+lemmal +" "+ itransan[itr])
        if "punct" not in prefix[itr] and len(lemmal) > 0 and lemmal in "/ma</sa</ta</mina</sina</tema</me</te</meie</teie</nemad</nad<":
          prefix[itr] = "pron " # don't care for personal pronouns so far
        elif "punct" not in prefix[itr]: #if len(itransan[itr]) > 7:  # word, not punctuation or personal pronoun
          j = jor 
          if lemma[-2] == '$':
            lemmab = '*' + lemma[1:-1]
          else:
            lemmab = '*' + lemma[1:-1] + '$'
          while j < len(ibiltr): # find correspondence in biltrans
            if "@compoundX" in lemma and "@compoundX<cc>" in ibiltr[j]:
              ind_tr_btr[itr] = j
              ind_btr_tr[j] = itr
              break
            if itr > 1 and j > 1 and "@compoundX<cc>" in ibiltr[j-1] and "@compoundX" in itransan[itr-1]:
              ind_tr_btr[itr] = ind_tr_btr[itr-1] + 1
              ind_btr_tr[j] = ind_btr_tr[j-1] + 1
              break
            biltr_jl = ibiltr[j].lower().replace('Ä', 'ä').replace('Ö', 'ö').replace('Ü', 'ü').replace('Õ', 'õ')
            if '_'+lemmal[1:-1]+'_' in biltr_jl or '_'+lemmal[1:] in biltr_jl or lemmal[:-1]+'_' in biltr_jl or '+'+lemmal[1:] in biltr_jl:
              if ind_btr_tr[j] < 0: # only if not set yet
                ind_tr_btr[itr] = j
              ind_btr_tr[j] = itr
              break
            if ind_btr_tr[j] < 0 and (lemma in ibiltr[j] or lemmal in biltr_jl or lemmab in ibiltr[j]): # main
              ind_tr_btr[itr] = j
              ind_btr_tr[j] = itr
              while jor < len(ibiltr) and ind_btr_tr[jor] >= 0:
                jor += 1
              break
            j += 1

          j = kor 
          while j < len(itaran): # find correspondence in target
            if "@compoundX" in lemma:
              ind_tr_tar[itr] = ind_tr_tar[itr-1]
              prefix[itr] = "compound "
              cmp_file.write("\compX\t" + lemma+'\t'+str(ind_tr_tar[itr])+'\t'+str(itr))
              break
            if itr > 1 and "@compoundX" in itransan[itr-1]:
              ind_tr_tar[itr] = ind_tr_tar[itr-1]
              prefix[itr] = "compound "
              cmp_file.write("\ngIIa\t" + itransan[itr-1] +'\t'+ str(ind_tr_tar[itr])+'\t'+str(itr))
              break
            if ind_tar_tr[j] < 0:
              if lemma in itaran[j] or lemmal in itaran[j].lower(): # or ' ' + lemma[1:-1] + ' ' in ctar[ctr] and ' ' + lemma[1:-1] + ' ' not in csou[ctr]:
                cor_words += 1
                prefix[itr] = "wordok " # don't care for its form at the moment
                ind_tr_tar[itr] = j
                ind_tar_tr[j] = itr
                while kor < len(itaran) and ind_tar_tr[kor] >= 0:
                  kor += 1
                break
              ok = 0
              lemtar = itaran[j].split('/')
              for i in xrange(len(lemtar)-1): # check lemmas in target
               if '<' in lemtar[i+1]:
                lemtar[i+1] = lemtar[i+1].split('<')[0]
                if lemtar[i+1][-1] != '>' and '/'+lemtar[i+1]+'<' in ibiltr[ind_tr_btr[itr]]:
                  if ' ' + lemma[1:-1] + ' ' in ' '+ctar[ctr]+' ': # was correct form in translation (eg compound)
                    cor_words += 1
                    prefix[itr] = "wordok "  # better to compare here surface forms!
                  else:
                    sel_words += 1
                    prefix[itr] = "lexsel "  # includes also form and compounding differences
                  ind_tr_tar[itr] = j
                  ind_tar_tr[j] = itr
                  while kor < len(itaran) and ind_tar_tr[kor] >= 0:
                    kor +=  1
                  ok = 1
                  break
              if ok == 1:
                break
            j += 1
          if itr > 0 and ind_tr_tar[itr] > 0 and (pos == "<n>" or pos == "<np>") and prefix[itr-1] == "notfound ":
            pbiltr = ibiltr[ind_tr_btr[itr]-1]
            if "<adj>" in pbiltr or "<dem>" in pbiltr: 
              ind_tr_tar[itr-1] = ind_tr_tar[itr] - 1
              ind_tar_tr[ind_tr_tar[itr] - 1] = itr - 1
              prefix[itr-1] = "syn&wrong1 " 
              inc_words += 1
          # more general
          if itr > 0 and ind_tr_tar[itr] > 0 and "notfound" in prefix[itr-1] and ind_tar_tr[ind_tr_tar[itr] - 1] < 0:
              ind = ind_tr_tar[itr] - 1
              ind_tr_tar[itr-1] = ind
              ind_tar_tr[ind] = itr - 1
              prefix[itr-1] = "syn&wrong2 " 
              inc_words += 1
              wf = ' ' + itaran[ind].split('/')[0][1:] + ' '
              wfl = wf.lower().replace('Ä', 'ä').replace('Ö', 'ö').replace('Ü', 'ü').replace('Õ', 'õ')
              if wf in ' ' + ctrans[ctr] + ' ' or wfl in ' ' + ctrans[ctr] + ' ': 
                prefix[itr-1] = "wordok " # lemmas don't match, but wordforms do ("Ü/ülikoolis")
        itr += 1  

       gaps = 0
       gapl = []
       verb = -1
       for i in xrange(len(itaran)):
         if verb == 0 and "<vblex>" in itaran[i]: 
           verb = i
         if len(itaran[i]) <= 3 or itaran[i][1] in '...,:;()?..!.."/@\'+=\\#¤%&[]£${}^|<>0123456789' or (itaran[i][1] in '-*' and itaran[i][2] in '/<'):
           ind_tar_tr[i] = -2
         elif ind_tar_tr[i] == -1 and '/' in itaran[i] and "//" not in itaran[i] and '<' in itaran[i]:
           lemmal = '/' + itaran[i].split('/')[1]
           if len(lemmal[1]) > 0:
             lemmal = lemmal.split('<')[0].lower() + '<'
             if lemmal and lemmal not in "/ma</sa</ta</mina</sina</tema</me</te</meie</teie</nemad</nad<":
               # try to fill - ind_tar_tr[i] < 0 
               if i > 0 and ind_tar_tr[i-1] > 0 and "syn&wrong" not in prefix[ind_tar_tr[i-1]]: 
                 if ind_tar_tr[i-1]+1 < len(itransan) and "notfound" in prefix[ind_tar_tr[i-1]+1]:
                   ind_tar_tr[i] = ind_tar_tr[i-1] + 1
                   ind_tr_tar[ind_tar_tr[i]] = i
                   prefix[ind_tar_tr[i]] = "syn&wrong3 " 
                   inc_words += 1
                   wf = itaran[i].split('/')[0][1:]
                   if ' '+wf+' ' in ' '+ctrans[ctr]+' ' or ' '+wf+'/' in ' '+ctrans[ctr]+' ' or '/'+wf+' ' in ' '+ctrans[ctr]+' ': 
                     prefix[ind_tar_tr[i]] = "wordok " # lemmas don't match, but wordforms do ("silmad", "lapsile/lastele")
                 elif verb >= 0 and "<adv>" in itaran[i]: # ind_tar_tr[i-1]+1 >= len(itransan) ! findverb
                   ind_tar_tr[i] = ind_tar_tr[verb]
                   prefix[ind_tar_tr[i]] = "adverb " 
                   inc_words += 1
                 else:
                   gaps += 1
                   gapl.append(i)
               else:
                 gaps += 1
                 gapl.append(i)
         i += 1

       if gaps == 1: # add more variants with sparse parts
         itr = 0
         while itr < len(itransan): # word in chunk IIa
           if ind_tr_tar[itr] < 0 and "notfound" in prefix[itr]:
              ind_tr_tar[itr] = gapl[0]
              prefix[itr] = "syn&wrong4 "
              inc_words += 1
              cmp_file.write("\ngIIa\t" + itransan[itr])
              if gaps == 1:
                ind_tar_tr[gapl[0]] = itr
                gaps = 0
              if ' ' + itaran[gapl[0]].split('/')[0][1:] + ' ' in ' ' + ctrans[ctr] + ' ': 
                prefix[itr] = "wordok " # lemmas don't match, but wordforms do ("minu meelest")
           itr += 1      

       itr = 0
       while itr < len(itransan): # word in chunk IIb
        if ind_tr_tar[itr] == -1 and "notfound" in prefix[itr]: # ? or prefix[itr] == "syn&wrong "):
          lemma = ""
          if "punct" not in prefix[itr]:
            if itransan[itr][1] == '*':
              lemma = '/' + itransan[itr][2:-1] + '<'
              pos = "<np>" # *Haluaisin not <np>!
            else:
              pos = '<' + itransan[itr].split('<')[1].split('>')[0] + '>'
              lemma = '/' + itransan[itr].split('<')[0][1:] + '<'
          lemmal = lemma.lower().replace('Ä', 'ä').replace('Ö', 'ö').replace('Ü', 'ü').replace('Õ', 'õ')
          j = kor 
          while j < len(itaran) and ind_tr_tar[itr] == -1: # and "/*" not in ibiltr[ind_tr_btr[itr]]: # find correspondence in target, based on pos (or /*)
            if ind_tar_tr[j] == -1 and ("/*" in ibiltr[ind_tr_btr[itr]] or pos in itaran[j]): # can look more precisely 
             lemmat = '/' + itaran[j].split('/')[1].split('<')[0] + '<'
             if lemmat not in "/ma</sa</ta</mina</sina</tema</me</te</meie</teie</nemad</nad<":

              if "/*" in ibiltr[ind_tr_btr[itr]]:
                prefix[itr] = "spell&new " 
                spn_words += 1
              else:
                prefix[itr] = "syn&wrong5 " 
                inc_words += 1
              ind_tr_tar[itr] = j
              ind_tar_tr[j] = itr
              gaps -= 1
              while kor < len(itaran) and ind_tar_tr[kor] >= 0:
                kor += 1
              break
            j += 1
        itr += 1  
       if gaps == 1:
         itr = 0
         while itr < len(itransan): # word in chunk IIIa
           if ind_tr_tar[itr] == -1 and "notfound" in prefix[itr]:
              ind_tr_tar[itr] = gapl[0]
              prefix[itr] = "syn&wrong6 "
              inc_words += 1
              cmp_file.write("\ngIIIa\t" + itransan[itr])
              if gaps == 1:
                ind_tar_tr[gapl[0]] = itr
                gaps = 0
           itr += 1
       # lisa mwe, kus mitmene vastavus

       itr = 0
       while itr < len(itransan): # word in chunk IIIb
           if ("syn&wrong" in prefix[itr] or "spell&new" in prefix[itr]) and ind_tr_btr[itr] >= 0:
              #if prefix[itr] == "syno? ":
              if "/*" in ibiltr[ind_tr_btr[itr]]:
                lembtr = ibiltr[ind_tr_btr[itr]].split('/*')[1][:-1]
              else:
                lembtr = ibiltr[ind_tr_btr[itr]].split('<')[0][1:]
              lemtar = itaran[ind_tr_tar[itr]].split('/')
              if pos != "<np>":
                lembtr = lembtr.lower()
              for i in xrange(len(lemtar)-1):  # new bidix candidate
                lemtar[i+1] = lemtar[i+1].split('<')[0]
                if pos != "<np>":
                  lemtar[i+1] = lemtar[i+1].lower()
                if lemtar[i+1][-1] != '>':
                  lex_file.write('    <e><p><l>'+lembtr+'<s n="n"/></l><r>'+lemtar[i+1]+'<s n="n"/></r></p></e>\n')
                  cmp_file.write("\nbidix"+ lembtr+" "+lemtar[i+1] +" "+ str(itr))
           itr += 1  
       ctr +=  1   


       itr = 0
       while itr < len(itransan): # word in chunk
        #cmp_file.write("\n" + prefix[itr] + "\t\t" + itrans[itr] + "\t-\t" + itar[ind_tr_tar[itr]] + "\t-\t" + isou[ind_tr_btr[itr]] + "\t-\t"+ inf)
        if ind_tr_btr[itr] >= 0: # prefix   translation  -  target  -  biltrans
          cmp_file.write("\n" + prefix[itr] + "\t" + itransan[itr] + "\t- " + itaran[ind_tr_tar[itr]] + "\t- " + ibiltr[ind_tr_btr[itr]])
        else:
          cmp_file.write("\n" + prefix[itr] + "\t" + itransan[itr] + "\t- " + itaran[ind_tr_tar[itr]] + "\t- not related")
        if "punct" not in prefix[itr] and "compound" not in prefix[itr]:
          all_words += 1
        elif "compound" in prefix[itr]:
          comp_parts += 1
        if "wordok" in prefix[itr]:
          ccor_words += 1
        if "lexsel" in prefix[itr]:
          csel_words += 1
        if "syn&wrong" in prefix[itr]:
          cinc_words += 1
        if "spell&new" in prefix[itr]:
          cspn_words += 1
        if "pron" in prefix[itr]:
          pron_words += 1
        if "notfound" in prefix[itr]:
          nf_words += 1
        itr = itr + 1
      
    
      cmp_file.write("\nFIN:  " + sou + "\nEST:  " + tar + "\nMT:   " + trans + "\nBIL:\t" + biltr + "\nFIN A:\t" + sou_an + "\nEST A:\t" + tar_an+ "\nMT A:\t" + trans_an + "\n\n")
      sou = sou_file.readline().strip().replace('.', " .").replace(',', " ,").replace(':', " :").replace(';', " ;").replace('!', " !").replace('?', " ?")
      row = row + 1
  except IndexError:
    sys.stderr.write("Could not read line nr %i: \n%s\n%s\n%s\n%s\n" % (row, trans_an, tar_an, biltr, trans))
    sys.exit(1)

  cmp_file.write("\n\n\nWords all: "+str(all_words)+"\tcorr:"+"\t"+str(ccor_words)+"\tlexsel:"+"\t"+str(csel_words)+"\tincorr&syno:"+"\t"+str(cinc_words)+"\tspell&new:"+"\t"+str(cspn_words)+"\tnotfound:"+"\t"+str(nf_words)+"\tPpronouns:"+"\t"+str(pron_words)+"\tcompound parts (not in all):"+"\t"+str(comp_parts)+"\n")


def usage():
    sys.stderr.write("""
    Usage: python comp.py [source] [target] [transl] [biltrans] [source_an] [target_an] [transl_an] \n""")
    # python com.py soome.txt eesti.txt soome.tolge soome.biltr soome.mrf eesti.mrf soome.pchnk
    # python com.py vsoome.txt veesti.txt vsoome.tolge vsoome.biltr vsoome.mrf veesti.mrf vsoome.pchnk
    # cat vsoome.txt | apertium -d . fin-est > vsoome.tolge
    # cat vsoome.txt | apertium -d . fin-est-biltrans > vsoome.biltr
    # cat vsoome.txt | apertium -d . fin-est-mrf > vsoome.mrf
    # cat veesti.txt | apertium -d . est-fin-mrf > veesti.mrf
    # cat vsoome.txt | apertium -d . fin-est-postchunk  > vsoome.pchnk
if __name__ == "__main__":

    if len(sys.argv)!=8:
        usage()
        sys.exit(1)
    sys.stderr.write(sys.argv[1] + " " + sys.argv[2] + " " + sys.argv[3] + " " + sys.argv[4] + " " + sys.argv[5] + " " + sys.argv[6] +  " " + sys.argv[7] + "\n")
    compare(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])

