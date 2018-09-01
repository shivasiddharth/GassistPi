/*
 * ac10x.h
 *
 * (C) Copyright 2017-2018
 * Seeed Technology Co., Ltd. <www.seeedstudio.com>
 *
 * PeterYang <linsheng.yang@seeed.cc>
 *
 * (C) Copyright 2010-2017
 * Reuuimlla Technology Co., Ltd. <www.reuuimllatech.com>
 * huangxin <huangxin@reuuimllatech.com>
 *
 * some simple description for this code
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of
 * the License, or (at your option) any later version.
 *
 */
#ifndef __AC10X_H__
#define __AC10X_H__

#define AC101_I2C_ID		4
#define _MASTER_AC108		0
#define _MASTER_AC101		1
#define _MASTER_MULTI_CODEC	_MASTER_AC101

/* enable headset detecting & headset button pressing */
#define CONFIG_AC101_SWITCH_DETECT


#ifdef AC101_DEBG
    #define AC101_DBG(format,args...)  printk("[AC101] "format,##args)
#else
    #define AC101_DBG(...)
#endif


#ifdef CONFIG_AC101_SWITCH_DETECT
enum headphone_mode_u {
	HEADPHONE_IDLE,
	FOUR_HEADPHONE_PLUGIN,
	THREE_HEADPHONE_PLUGIN,
};
#endif

struct ac10x_priv {
	struct i2c_client *i2c[4];
	struct regmap* i2cmap[4];
	int codec_cnt;
	unsigned sysclk;
#define _FREQ_24_576K		24576000
#define _FREQ_22_579K		22579200
	unsigned mclk;	/* master clock or aif_clock/aclk */
	int clk_id;
	unsigned char i2s_mode;
	unsigned char data_protocol;
	struct delayed_work dlywork;
	int tdm_chips_cnt;
	int sysclk_en;

	/* member for ac101 .begin */
	struct snd_soc_codec *codec;
	struct i2c_client *i2c101;
	struct regmap* regmap101;

	struct mutex dac_mutex;
	u8 dac_enable;
	spinlock_t lock;
	u8 aif1_clken;

	struct work_struct codec_resume;
	struct gpio_desc* gpiod_spk_amp_gate;

	#ifdef CONFIG_AC101_SWITCH_DETECT
	struct gpio_desc* gpiod_irq;
	int irq;
	volatile int irq_cntr;
	volatile int pullout_cntr;
	volatile int state;

	enum headphone_mode_u mode;
	struct work_struct work_switch;
	struct work_struct work_clear_irq;

	struct input_dev* inpdev;
	#endif
	/* member for ac101 .end */
};


/* AC101 DAI operations */
int ac101_audio_startup(struct snd_pcm_substream *substream, struct snd_soc_dai *codec_dai);
void ac101_aif_shutdown(struct snd_pcm_substream *substream, struct snd_soc_dai *codec_dai);
int ac101_set_dai_fmt(struct snd_soc_dai *codec_dai, unsigned int fmt);
int ac101_hw_params(struct snd_pcm_substream *substream,
	struct snd_pcm_hw_params *params,
	struct snd_soc_dai *codec_dai);
int ac101_trigger(struct snd_pcm_substream *substream, int cmd,
	 	  struct snd_soc_dai *dai);
int ac101_aif_mute(struct snd_soc_dai *codec_dai, int mute);

/* codec driver specific */
int ac101_codec_probe(struct snd_soc_codec *codec);
int ac101_codec_remove(struct snd_soc_codec *codec);
int ac101_codec_suspend(struct snd_soc_codec *codec);
int ac101_codec_resume(struct snd_soc_codec *codec);
int ac101_set_bias_level(struct snd_soc_codec *codec, enum snd_soc_bias_level level);

/* i2c device specific */
int ac101_probe(struct i2c_client *i2c, const struct i2c_device_id *id);
void ac101_shutdown(struct i2c_client *i2c);
int ac101_remove(struct i2c_client *i2c);

/* seeed voice card export */
int seeed_voice_card_register_set_clock(int stream, int (*set_clock)(int));

int ac10x_fill_regcache(struct device* dev, struct regmap* map);

#endif//__AC10X_H__
