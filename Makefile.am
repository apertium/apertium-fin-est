###############################################################################
## Makefile for fin-est
###############################################################################

VERSION=0.1.0
LANG1=fin
LANG2=est
PREFIX1=$(LANG1)-$(LANG2)
PREFIX2=$(LANG2)-$(LANG1)

BASENAME=apertium-$(PREFIX1)

TARGETS_COMMON = $(PREFIX1).autobil.bin $(PREFIX2).autobil.bin \
	$(PREFIX1).automorf.hfst $(PREFIX1).autogen.bin $(PREFIX1).t1x.bin  \
	$(PREFIX2).automorf.bin $(PREFIX2).autogen.hfst $(PREFIX2).t1x.bin  \
        $(PREFIX1).t2x.bin $(PREFIX1).t3x.bin \
        $(PREFIX2).t2x.bin $(PREFIX2).t3x.bin \
        $(PREFIX1).rlx.bin $(PREFIX2).rlx.bin \
        $(PREFIX1).autolex.bin $(PREFIX2).autolex.bin \
	$(PREFIX1).mode $(PREFIX2).mode modes 


# Use this goal for creating .deps, otherwise make -j2 will give problems:
.deps/.d:
	if [ ! -d .deps ]; then mkdir .deps; fi
	touch $@

# Prevent the .d file from being removed automatically:
.PRECIOUS: .deps/.d

###############################################################################
## Finnish→Estonian monolingual transducers
###############################################################################

# fin->est mor
$(PREFIX1).automorf.hfst: $(AP_LIB1)/$(LANG1).automorf.att.gz .deps/.d
	$(ZCAT) $< | hfst-txt2fst -o .deps/$(PREFIX1).automorf.hfst
	hfst-fst2fst -O .deps/$(PREFIX1).automorf.hfst -o $@

# est->fin mor
$(PREFIX2).automorf.bin: $(BASENAME).$(PREFIX2).LR.att.gz 
	$(ZCAT) $< > .deps/$(PREFIX2).automorf.LR.att
	lt-comp lr .deps/$(PREFIX2).automorf.LR.att $@

# fin->est gen
$(PREFIX1).autogen.bin: $(BASENAME).$(PREFIX2).RL.att.gz 
	$(ZCAT) $<  > .deps/$(PREFIX1).autogen.RL.att
	lt-comp lr .deps/$(PREFIX1).autogen.RL.att $@

# est->fin gen
$(PREFIX2).autogen.hfst: $(AP_LIB1)/$(LANG1).autogen.hfst
	cp $< $@



###############################################################################
## Prob files for tagger
###############################################################################

#$(PREFIX1).prob: $(AP_LIB1)/$(LANG1).prob
#	cp $< $@

###############################################################################
## Bilingual dictionaries
###############################################################################

$(PREFIX1).autobil.bin: $(BASENAME).$(PREFIX1).dix
	apertium-validate-dictionary $<
	lt-comp lr $< $@

$(PREFIX2).autobil.bin: $(BASENAME).$(PREFIX1).dix
	apertium-validate-dictionary $< 
	lt-comp rl $< $@

###############################################################################
## Disambiguation rules 
###############################################################################

$(PREFIX1).rlx.bin: $(AP_SRC1)/apertium-$(LANG1).$(LANG1).rlx
	cg-comp $< $@

$(PREFIX2).rlx.bin: $(BASENAME).$(PREFIX2).rlx
	cg-comp $< $@


###############################################################################
## Lexical selection rules
###############################################################################

$(PREFIX1).autolex.bin: $(BASENAME).$(PREFIX1).lrx
	lrx-comp $< $@

$(PREFIX2).autolex.bin: $(BASENAME).$(PREFIX2).lrx
	lrx-comp $< $@

###############################################################################
## Structural transfer rules
###############################################################################

$(PREFIX1).t1x.bin: $(BASENAME).$(PREFIX1).t1x
	apertium-validate-transfer $(BASENAME).$(PREFIX1).t1x
	apertium-preprocess-transfer $(BASENAME).$(PREFIX1).t1x $@

$(PREFIX1).t2x.bin: $(BASENAME).$(PREFIX1).t2x
	apertium-validate-interchunk $(BASENAME).$(PREFIX1).t2x
	apertium-preprocess-transfer $(BASENAME).$(PREFIX1).t2x $@

$(PREFIX1).t3x.bin: $(BASENAME).$(PREFIX1).t3x
	apertium-validate-postchunk $(BASENAME).$(PREFIX1).t3x
	apertium-preprocess-transfer $(BASENAME).$(PREFIX1).t3x $@

$(PREFIX2).t1x.bin: $(BASENAME).$(PREFIX2).t1x
	apertium-validate-transfer $(BASENAME).$(PREFIX2).t1x
	apertium-preprocess-transfer $(BASENAME).$(PREFIX2).t1x $@

$(PREFIX2).t2x.bin: $(BASENAME).$(PREFIX2).t2x
	apertium-validate-interchunk $(BASENAME).$(PREFIX2).t2x
	apertium-preprocess-transfer $(BASENAME).$(PREFIX2).t2x $@

$(PREFIX2).t3x.bin: $(BASENAME).$(PREFIX2).t3x
	apertium-validate-postchunk $(BASENAME).$(PREFIX2).t3x
	apertium-preprocess-transfer $(BASENAME).$(PREFIX2).t3x $@


###############################################################################
## Postgeneration dictionaries
###############################################################################

#$(PREFIX1).autopgen.bin: $(BASENAME).post-$(LANG1).dix
#	apertium-validate-dictionary $<
#	lt-comp lr $< $@
#
#$(PREFIX2).autopgen.bin: $(BASENAME).post-$(LANG2).dix
#	apertium-validate-dictionary $< 
#	lt-comp lr $< $@

###############################################################################
## Translation modes
###############################################################################

modes/$(PREFIX1).mode: modes.xml
	apertium-validate-modes modes.xml
	apertium-gen-modes modes.xml
	cp *.mode modes/

modes/$(PREFIX2).mode: modes.xml
	apertium-validate-modes modes.xml
	apertium-gen-modes modes.xml
	cp *.mode modes/

###############################################################################
## Installation stuff
###############################################################################

EXTRA_DIST=$(PREFIX1).prob $(PREFIX2).prob \
           $(BASENAME).$(PREFIX1).t1x $(BASENAME).$(PREFIX1).t2x $(BASENAME).$(PREFIX1).t3x \
           $(BASENAME).$(PREFIX2).t1x $(BASENAME).$(PREFIX2).t2x $(BASENAME).$(PREFIX2).t3x \
           modes.xml

apertium_fin_estmodesdir=$(prefix)/share/apertium/modes/
apertium_fin_estdir=$(prefix)/share/apertium/$(BASENAME)/

apertium_fin_est_DATA=$(PREFIX1).autobil.bin $(PREFIX2).autobil.bin \
                    $(PREFIX1).prob $(PREFIX2).prob \
		    $(PREFIX1).autogen.bin $(PREFIX2).autogen.hfst \
		    $(PREFIX1).automorf.hfst $(PREFIX2).automorf.bin \
		    $(PREFIX1).t1x.bin $(PREFIX2).t1x.bin \
		    $(PREFIX1).t2x.bin $(PREFIX2).t2x.bin \
		    $(PREFIX1).t3x.bin $(PREFIX2).t3x.bin \
		    $(PREFIX1).rlx.bin $(PREFIX2).rlx.bin \
		    $(PREFIX1).autolex.bin $(PREFIX2).autolex.bin \
		    $(BASENAME).$(PREFIX1).t1x $(BASENAME).$(PREFIX2).t1x \
		    modes.xml

#		    $(PREFIX1).autopgen.bin $(PREFIX2).autopgen.bin 

noinst_DATA=modes/$(PREFIX1).mode modes/$(PREFIX2).mode


install-data-local:
	mv modes modes~
	$(prefix)/bin/apertium-gen-modes modes.xml $(BASENAME)
	rm -rf modes
	mv modes~ modes
	test -d $(DESTDIR)$(apertium_fin_estmodesdir) || mkdir $(DESTDIR)$(apertium_fin_estmodesdir)
	$(INSTALL_DATA) $(PREFIX1).mode $(DESTDIR)$(apertium_fin_estmodesdir)
	rm $(PREFIX1).mode
	rm $(PREFIX2).mode
	$(INSTALL_DATA) $(BASENAME).$(PREFIX1).t1x $(DESTDIR)$(apertium_fin_estdir)
	$(INSTALL_DATA) $(BASENAME).$(PREFIX2).t1x $(DESTDIR)$(apertium_fin_estdir)
	$(INSTALL_DATA) $(BASENAME).$(PREFIX1).t2x $(DESTDIR)$(apertium_fin_estdir)
	$(INSTALL_DATA) $(BASENAME).$(PREFIX2).t2x $(DESTDIR)$(apertium_fin_estdir)
	$(INSTALL_DATA) $(BASENAME).$(PREFIX1).t3x $(DESTDIR)$(apertium_fin_estdir)
	$(INSTALL_DATA) $(BASENAME).$(PREFIX2).t3x $(DESTDIR)$(apertium_fin_estdir)

CLEANFILES = -r $(TARGETS_COMMON) .deps/
