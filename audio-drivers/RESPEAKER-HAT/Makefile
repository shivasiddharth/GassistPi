snd-soc-wm8960-objs := wm8960.o
snd-soc-ac108-objs := ac108.o ac101.o
snd-soc-seeed-voicecard-objs := seeed-voicecard.o


obj-m += snd-soc-wm8960.o
obj-m += snd-soc-ac108.o
obj-m += snd-soc-seeed-voicecard.o

ifdef DEBUG
ifneq ($(DEBUG),0)
	ccflags-y += -DDEBUG -DAC101_DEBG
endif
endif


all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

install:
	sudo cp snd-soc-ac108.ko /lib/modules/$(shell uname -r)/kernel/sound/soc/codecs/
	sudo cp snd-soc-wm8960.ko /lib/modules/$(shell uname -r)/kernel/sound/soc/codecs/
	sudo cp snd-soc-seeed-voicecard.ko /lib/modules/$(shell uname -r)/kernel/sound/soc/bcm/
	sudo depmod -a
