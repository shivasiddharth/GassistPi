snd-soc-wm8960-objs := wm8960.o
snd-soc-ac108-objs := ac108.o ac101.o
snd-soc-simple-card-objs := simple-card.o


obj-m += snd-soc-wm8960.o
obj-m += snd-soc-ac108.o
obj-m += snd-soc-simple-card.o


all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

install:
	sudo cp snd-soc-ac108.ko /lib/modules/$(shell uname -r)/kernel/sound/soc/codecs/
	sudo cp snd-soc-wm8960.ko /lib/modules/$(shell uname -r)/kernel/sound/soc/codecs/
	sudo cp snd-soc-simple-card.ko /lib/modules/$(shell uname -r)/kernel/sound/soc/generic/
	sudo depmod -a
