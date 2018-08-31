/*
 * sound\soc\sunxi\virtual_audio\ac100.h
 * (C) Copyright 2010-2016
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
#define _MASTER_MULTI_CODEC	_MASTER_AC108

#ifdef AC101_DEBG
    #define AC101_DBG(format,args...)  printk("[AC101] "format,##args)
#else
    #define AC101_DBG(...)
#endif

#define _I2C_MUTEX_EN		1

struct ac10x_priv {
	struct i2c_client *i2c[4];
	#if _I2C_MUTEX_EN
	struct mutex i2c_mutex;
	#endif
	int codec_index;
	unsigned sysclk;
	unsigned mclk;	/* master clock or aif_clock/aclk */
	int clk_id;
	unsigned char i2s_mode;
	unsigned char data_protocol;
	struct delayed_work dlywork;
	int tdm_chips_cnt;

/* struct for ac101 .begin */
	struct snd_soc_codec *codec;
	struct i2c_client *i2c101;
	struct regmap* regmap101;

	struct mutex dac_mutex;
	struct mutex adc_mutex;
	u8 dac_enable;
	struct mutex aifclk_mutex;
	u8 aif1_clken;
	u8 aif2_clken;

	struct work_struct codec_resume;
	struct delayed_work dlywork101;
	struct gpio_desc* gpiod_spk_amp_gate;
/* struct for ac101 .end */
};

/* register level access */
int ac10x_read(u8 reg, u8 *rt_value, struct i2c_client *client);
int ac10x_write(u8 reg, unsigned char val, struct i2c_client *client);
int ac10x_update_bits(u8 reg, u8 mask, u8 val, struct i2c_client *client);

/* AC101 DAI operations */
int ac101_audio_startup(struct snd_pcm_substream *substream, struct snd_soc_dai *codec_dai);
void ac101_aif_shutdown(struct snd_pcm_substream *substream, struct snd_soc_dai *codec_dai);
int ac101_set_dai_fmt(struct snd_soc_dai *codec_dai, unsigned int fmt);
int ac101_hw_params(struct snd_pcm_substream *substream,
	struct snd_pcm_hw_params *params,
	struct snd_soc_dai *codec_dai);
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

/* simple card export */
int asoc_simple_card_register_set_clock(int (*set_clock)(int));

#endif//__AC10X_H__
