/*
 * ac101.c
 * (C) Copyright 2017-2018
 * Seeed Technology Co., Ltd. <www.seeedstudio.com>
 *
 * PeterYang <linsheng.yang@seeed.cc>
 *
 * (C) Copyright 2014-2017
 * Reuuimlla Technology Co., Ltd. <www.reuuimllatech.com>
 *
 * huangxin <huangxin@Reuuimllatech.com>
 * liushaohua <liushaohua@allwinnertech.com>
 *
 * X-Powers AC101 codec driver
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of
 * the License, or (at your option) any later version.
 *
 */
#undef AC101_DEBG
#include <linux/module.h>
#include <sound/pcm.h>
#include <sound/pcm_params.h>
#include <sound/soc.h>
#include <sound/soc-dapm.h>
#include <sound/tlv.h>
#include <linux/i2c.h>
#include <linux/irq.h>
#include <linux/workqueue.h>
#include <linux/clk.h>
#include <linux/gpio/consumer.h>
#include <linux/regmap.h>
#include "ac101_regs.h"
#include "ac10x.h"

/*Default initialize configuration*/
static bool speaker_double_used = 1;
static int double_speaker_val	= 0x1B;
static int single_speaker_val	= 0x19;
static int headset_val		= 0x3B;
static int mainmic_val		= 0x4;
static int headsetmic_val	= 0x4;
static bool dmic_used		= 0;
static int adc_digital_val	= 0xb0b0;
static bool drc_used		= false;

#define AC101_RATES  (SNDRV_PCM_RATE_8000_96000 &		\
		~(SNDRV_PCM_RATE_32000 | SNDRV_PCM_RATE_64000 | \
		SNDRV_PCM_RATE_88200))
#define AC101_FORMATS (/*SNDRV_PCM_FMTBIT_S16_LE | \
			SNDRV_PCM_FMTBIT_S24_LE |*/	\
			SNDRV_PCM_FMTBIT_S32_LE	| \
			0)

static struct ac10x_priv* static_ac10x;


int ac101_read(struct snd_soc_codec *codec, unsigned reg) {
	struct ac10x_priv *ac10x = snd_soc_codec_get_drvdata(codec);
	int r, v = 0;

	if ((r = regmap_read(ac10x->regmap101, reg, &v)) < 0) {
		return r;
	}
	return v;
}

int ac101_write(struct snd_soc_codec *codec, unsigned reg, unsigned val) {
	struct ac10x_priv *ac10x = snd_soc_codec_get_drvdata(codec);

	return regmap_write(ac10x->regmap101, reg, val);
}

int ac101_update_bits(struct snd_soc_codec *codec, unsigned reg,
			unsigned mask, unsigned value
) {
	struct ac10x_priv *ac10x = snd_soc_codec_get_drvdata(codec);

	return regmap_update_bits(ac10x->regmap101, reg, mask, value);
}

void drc_config(struct snd_soc_codec *codec)
{
	int reg_val;
	reg_val = ac101_read(codec, 0xa3);
	reg_val &= ~(0x7ff<<0);
	reg_val |= 1<<0;
	ac101_write(codec, 0xa3, reg_val);
	ac101_write(codec, 0xa4, 0x2baf);

	reg_val = ac101_read(codec, 0xa5);
	reg_val &= ~(0x7ff<<0);
	reg_val |= 1<<0;
	ac101_write(codec, 0xa5, reg_val);
	ac101_write(codec, 0xa6, 0x2baf);

	reg_val = ac101_read(codec, 0xa7);
	reg_val &= ~(0x7ff<<0);
	ac101_write(codec, 0xa7, reg_val);
	ac101_write(codec, 0xa8, 0x44a);

	reg_val = ac101_read(codec, 0xa9);
	reg_val &= ~(0x7ff<<0);
	ac101_write(codec, 0xa9, reg_val);
	ac101_write(codec, 0xaa, 0x1e06);

	reg_val = ac101_read(codec, 0xab);
	reg_val &= ~(0x7ff<<0);
	reg_val |= (0x352<<0);
	ac101_write(codec, 0xab, reg_val);
	ac101_write(codec, 0xac, 0x6910);

	reg_val = ac101_read(codec, 0xad);
	reg_val &= ~(0x7ff<<0);
	reg_val |= (0x77a<<0);
	ac101_write(codec, 0xad, reg_val);
	ac101_write(codec, 0xae, 0xaaaa);

	reg_val = ac101_read(codec, 0xaf);
	reg_val &= ~(0x7ff<<0);
	reg_val |= (0x2de<<0);
	ac101_write(codec, 0xaf, reg_val);
	ac101_write(codec, 0xb0, 0xc982);

	ac101_write(codec, 0x16, 0x9f9f);

}

void drc_enable(struct snd_soc_codec *codec,bool on)
{
	int reg_val;
	if (on) {
		ac101_write(codec, 0xb5, 0xA080);
		reg_val = ac101_read(codec, MOD_CLK_ENA);
		reg_val |= (0x1<<6);
		ac101_write(codec, MOD_CLK_ENA, reg_val);
		reg_val = ac101_read(codec, MOD_RST_CTRL);
		reg_val |= (0x1<<6);
		ac101_write(codec, MOD_RST_CTRL, reg_val);

		reg_val = ac101_read(codec, 0xa0);
		reg_val |= (0x7<<0);
		ac101_write(codec, 0xa0, reg_val);
	} else {
		ac101_write(codec, 0xb5, 0x0);
		reg_val = ac101_read(codec, MOD_CLK_ENA);
		reg_val &= ~(0x1<<6);
		ac101_write(codec, MOD_CLK_ENA, reg_val);
		reg_val = ac101_read(codec, MOD_RST_CTRL);
		reg_val &= ~(0x1<<6);
		ac101_write(codec, MOD_RST_CTRL, reg_val);

		reg_val = ac101_read(codec, 0xa0);
		reg_val &= ~(0x7<<0);
		ac101_write(codec, 0xa0, reg_val);
	}
}

void set_configuration(struct snd_soc_codec *codec)
{
	if (speaker_double_used) {
		ac101_update_bits(codec, SPKOUT_CTRL, (0x1f<<SPK_VOL), (double_speaker_val<<SPK_VOL));
	} else {
		ac101_update_bits(codec, SPKOUT_CTRL, (0x1f<<SPK_VOL), (single_speaker_val<<SPK_VOL));
	}
	ac101_update_bits(codec, HPOUT_CTRL, (0x3f<<HP_VOL), (headset_val<<HP_VOL));
	ac101_update_bits(codec, ADC_SRCBST_CTRL, (0x7<<ADC_MIC1G), (mainmic_val<<ADC_MIC1G));
	ac101_update_bits(codec, ADC_SRCBST_CTRL, (0x7<<ADC_MIC2G), (headsetmic_val<<ADC_MIC2G));
	if (dmic_used) {
		ac101_write(codec, ADC_VOL_CTRL, adc_digital_val);
	}
	if (drc_used) {
		drc_config(codec);
	}
	/*headphone calibration clock frequency select*/
	ac101_update_bits(codec, SPKOUT_CTRL, (0x7<<HPCALICKS), (0x7<<HPCALICKS));

	/* I2S1 DAC Timeslot 0 data <- I2S1 DAC channel 0 */
	// "AIF1IN0L Mux" <= "AIF1DACL"
	// "AIF1IN0R Mux" <= "AIF1DACR"
	ac101_update_bits(codec, AIF1_DACDAT_CTRL, 0x3 << AIF1_DA0L_SRC, 0x0 << AIF1_DA0L_SRC);
	ac101_update_bits(codec, AIF1_DACDAT_CTRL, 0x3 << AIF1_DA0R_SRC, 0x0 << AIF1_DA0R_SRC);
	/* Timeslot 0 Left & Right Channel enable */
	ac101_update_bits(codec, AIF1_DACDAT_CTRL, 0x3 << AIF1_DA0R_ENA, 0x3 << AIF1_DA0R_ENA);

	/* DAC Digital Mixer Source Select <- I2S1 DA0 */
	// "DACL Mixer"	+= "AIF1IN0L Mux"
	// "DACR Mixer" += "AIF1IN0R Mux"
	ac101_update_bits(codec, DAC_MXR_SRC, 0xF << DACL_MXR_ADCL, 0x8 << DACL_MXR_ADCL);
	ac101_update_bits(codec, DAC_MXR_SRC, 0xF << DACR_MXR_ADCR, 0x8 << DACR_MXR_ADCR);
	/* Internal DAC Analog Left & Right Channel enable */
	ac101_update_bits(codec, OMIXER_DACA_CTRL, 0x3 << DACALEN, 0x3 << DACALEN);

	/* Output Mixer Source Select */
	// "Left Output Mixer"  += "DACL Mixer"
	// "Right Output Mixer" += "DACR Mixer"
	ac101_update_bits(codec, OMIXER_SR, 0x1 << LMIXMUTEDACL, 0x1 << LMIXMUTEDACL);
	ac101_update_bits(codec, OMIXER_SR, 0x1 << RMIXMUTEDACR, 0x1 << RMIXMUTEDACR);
	/* Left & Right Analog Output Mixer enable */
	ac101_update_bits(codec, OMIXER_DACA_CTRL, 0x3 << LMIXEN, 0x3 << LMIXEN);

	/* Headphone Ouput Control */ 
	// "HP_R Mux" <= "DACR Mixer"
	// "HP_L Mux" <= "DACL Mixer"
	ac101_update_bits(codec, HPOUT_CTRL, 0x1 << LHPS, 0x0 << LHPS);
	ac101_update_bits(codec, HPOUT_CTRL, 0x1 << RHPS, 0x0 << RHPS);

	/* Speaker Output Control */
	// "SPK_L Mux" <= "SPK_LR Adder"
	// "SPK_R Mux" <= "SPK_LR Adder"
	ac101_update_bits(codec, SPKOUT_CTRL, (0x1 << LSPKS) | (0x1 << RSPKS), (0x1 << LSPKS) | (0x1 << RSPKS));
	/* Enable Left & Right Speaker */
	ac101_update_bits(codec, SPKOUT_CTRL, (0x1 << LSPK_EN) | (0x1 << RSPK_EN), (0x1 << LSPK_EN) | (0x1 << RSPK_EN));
	return;
}

static int late_enable_dac(struct snd_soc_codec* codec, int event) {
	struct ac10x_priv *ac10x = snd_soc_codec_get_drvdata(codec);
	mutex_lock(&ac10x->dac_mutex);
	switch (event) {
	case SND_SOC_DAPM_PRE_PMU:
		AC101_DBG("%s,line:%d\n",__func__,__LINE__);
		if (ac10x->dac_enable == 0){
			/*enable dac module clk*/
			ac101_update_bits(codec, MOD_CLK_ENA, (0x1<<MOD_CLK_DAC_DIG), (0x1<<MOD_CLK_DAC_DIG));
			ac101_update_bits(codec, MOD_RST_CTRL, (0x1<<MOD_RESET_DAC_DIG), (0x1<<MOD_RESET_DAC_DIG));
			ac101_update_bits(codec, DAC_DIG_CTRL, (0x1<<ENDA), (0x1<<ENDA));
			ac101_update_bits(codec, DAC_DIG_CTRL, (0x1<<ENHPF),(0x1<<ENHPF));
		}
		ac10x->dac_enable++;
		break;
	case SND_SOC_DAPM_POST_PMD:
		#if 0
		if (ac10x->dac_enable > 0){
			ac10x->dac_enable--;
		#else
		{
		#endif
			if (ac10x->dac_enable != 0){
				ac10x->dac_enable = 0;

				ac101_update_bits(codec, DAC_DIG_CTRL, (0x1<<ENHPF),(0x0<<ENHPF));
				ac101_update_bits(codec, DAC_DIG_CTRL, (0x1<<ENDA), (0x0<<ENDA));
				/*disable dac module clk*/
				ac101_update_bits(codec, MOD_CLK_ENA, (0x1<<MOD_CLK_DAC_DIG), (0x0<<MOD_CLK_DAC_DIG));
				ac101_update_bits(codec, MOD_RST_CTRL, (0x1<<MOD_RESET_DAC_DIG), (0x0<<MOD_RESET_DAC_DIG));
			}
		}
		break;
	}
	mutex_unlock(&ac10x->dac_mutex);
	return 0;
}

static int ac101_headphone_event(struct snd_soc_codec* codec, int event) {
	switch (event) {
	case SND_SOC_DAPM_POST_PMU:
		/*open*/
		AC101_DBG("post:open:%s,line:%d\n", __func__, __LINE__);
		ac101_update_bits(codec, OMIXER_DACA_CTRL, (0xf<<HPOUTPUTENABLE), (0xf<<HPOUTPUTENABLE));
		ac101_update_bits(codec, HPOUT_CTRL, (0x1<<HPPA_EN), (0x1<<HPPA_EN));
		msleep(10);
		ac101_update_bits(codec, HPOUT_CTRL, (0x3<<LHPPA_MUTE), (0x3<<LHPPA_MUTE));
		break;
	case SND_SOC_DAPM_PRE_PMD:
		/*close*/
		AC101_DBG("pre:close:%s,line:%d\n", __func__, __LINE__);
		ac101_update_bits(codec, HPOUT_CTRL, (0x1<<HPPA_EN), (0x0<<HPPA_EN));
		ac101_update_bits(codec, OMIXER_DACA_CTRL, (0xf<<HPOUTPUTENABLE), (0x0<<HPOUTPUTENABLE));
		ac101_update_bits(codec, HPOUT_CTRL, (0x3<<LHPPA_MUTE), (0x0<<LHPPA_MUTE));
		break;
	}
	return 0;
}
static int ac101_aif1clk(struct snd_soc_codec* codec, int event) {
	struct ac10x_priv *ac10x = snd_soc_codec_get_drvdata(codec);

	AC101_DBG("%s() L%d event=%d pre_up/%d post_down/%d\n", __func__, __LINE__,
		event, SND_SOC_DAPM_PRE_PMU, SND_SOC_DAPM_POST_PMD);

	mutex_lock(&ac10x->aifclk_mutex);
	switch (event) {
	case SND_SOC_DAPM_PRE_PMU:
		if (ac10x->aif1_clken == 0){
			/*enable AIF1CLK*/
			ac101_update_bits(codec, SYSCLK_CTRL, (0x1<<AIF1CLK_ENA), (0x1<<AIF1CLK_ENA));
			ac101_update_bits(codec, MOD_CLK_ENA, (0x1<<MOD_CLK_AIF1), (0x1<<MOD_CLK_AIF1));
			ac101_update_bits(codec, MOD_RST_CTRL, (0x1<<MOD_RESET_AIF1), (0x1<<MOD_RESET_AIF1));
			/*enable systemclk*/
			if (ac10x->aif2_clken == 0)
				ac101_update_bits(codec, SYSCLK_CTRL, (0x1<<SYSCLK_ENA), (0x1<<SYSCLK_ENA));
		}
		ac10x->aif1_clken++;

		break;
	case SND_SOC_DAPM_POST_PMD:
		#if 0
		if (ac10x->aif1_clken > 0){
			ac10x->aif1_clken--;
			if (ac10x->aif1_clken == 0){
		#else
		{
			if (ac10x->aif1_clken != 0) {
				ac10x->aif1_clken = 0;
		#endif
				/*disable AIF1CLK*/
				ac101_update_bits(codec, SYSCLK_CTRL, (0x1<<AIF1CLK_ENA), (0x0<<AIF1CLK_ENA));
				ac101_update_bits(codec, MOD_CLK_ENA, (0x1<<MOD_CLK_AIF1), (0x0<<MOD_CLK_AIF1));
				ac101_update_bits(codec, MOD_RST_CTRL, (0x1<<MOD_RESET_AIF1), (0x0<<MOD_RESET_AIF1));
				/*DISABLE systemclk*/
				if (ac10x->aif2_clken == 0)
					ac101_update_bits(codec, SYSCLK_CTRL, (0x1<<SYSCLK_ENA), (0x0<<SYSCLK_ENA));
			}
		}
		break;
	}
	mutex_unlock(&ac10x->aifclk_mutex);
	return 0;
}

/**
 * snd_ac101_get_volsw - single mixer get callback
 * @kcontrol: mixer control
 * @ucontrol: control element information
 *
 * Callback to get the value of a single mixer control, or a double mixer
 * control that spans 2 registers.
 *
 * Returns 0 for success.
 */
static int snd_ac101_get_volsw(struct snd_kcontrol *kcontrol,
	struct snd_ctl_elem_value *ucontrol
){
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	unsigned int val, mask = (1 << fls(mc->max)) - 1;
	unsigned int invert = mc->invert;
	int ret;

	if ((ret = ac101_read(static_ac10x->codec, mc->reg)) < 0)
		return ret;

	val = (ret >> mc->shift) & mask;
	ucontrol->value.integer.value[0] = val - mc->min;
	if (invert) {
		ucontrol->value.integer.value[0] =
			mc->max - ucontrol->value.integer.value[0];
	}
	return 0;
}

/**
 * snd_ac101_put_volsw - single mixer put callback
 * @kcontrol: mixer control
 * @ucontrol: control element information
 *
 * Callback to set the value of a single mixer control, or a double mixer
 * control that spans 2 registers.
 *
 * Returns 0 for success.
 */
static int snd_ac101_put_volsw(struct snd_kcontrol *kcontrol,
	struct snd_ctl_elem_value *ucontrol
){
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	unsigned int sign_bit = mc->sign_bit;
	unsigned int val, mask = (1 << fls(mc->max)) - 1;
	unsigned int invert = mc->invert;
	int ret;

	if (sign_bit)
		mask = BIT(sign_bit + 1) - 1;

	val = ((ucontrol->value.integer.value[0] + mc->min) & mask);
	if (invert) {
		val = mc->max - val;
	}

	mask = mask << mc->shift;
	val = val << mc->shift;

	ret = ac101_update_bits(static_ac10x->codec, mc->reg, mask, val);
	return ret;
}


static const DECLARE_TLV_DB_SCALE(dac_vol_tlv, -11925, 75, 0);
static const DECLARE_TLV_DB_SCALE(dac_mix_vol_tlv, -600, 600, 0);
static const DECLARE_TLV_DB_SCALE(dig_vol_tlv, -7308, 116, 0);
static const DECLARE_TLV_DB_SCALE(speaker_vol_tlv, -4800, 150, 0);
static const DECLARE_TLV_DB_SCALE(headphone_vol_tlv, -6300, 100, 0);

static struct snd_kcontrol_new ac101_controls[] = {
	/*DAC*/
	SOC_DOUBLE_TLV("DAC volume", DAC_VOL_CTRL, DAC_VOL_L, DAC_VOL_R, 0xff, 0, dac_vol_tlv),
	SOC_DOUBLE_TLV("DAC mixer gain", DAC_MXR_GAIN, DACL_MXR_GAIN, DACR_MXR_GAIN, 0xf, 0, dac_mix_vol_tlv),
	SOC_SINGLE_TLV("digital volume", DAC_DBG_CTRL, DVC, 0x3f, 1, dig_vol_tlv),
	SOC_SINGLE_TLV("speaker volume", SPKOUT_CTRL, SPK_VOL, 0x1f, 0, speaker_vol_tlv),
	SOC_SINGLE_TLV("headphone volume", HPOUT_CTRL, HP_VOL, 0x3f, 0, headphone_vol_tlv),
};

/* PLL divisors */
struct pll_div {
	unsigned int pll_in;
	unsigned int pll_out;
	int m;
	int n_i;
	int n_f;
};

struct aif1_fs {
	unsigned samp_rate;
	int bclk_div;
	int srbit;
	#define _SERIES_24_576K		0
	#define _SERIES_22_579K		1
	int series;
};

struct kv_map {
	int val;
	int bit;
};

/*
 *	Note : pll code from original tdm/i2s driver.
 * 	freq_out = freq_in * N/(m*(2k+1)) , k=1,N=N_i+N_f,N_f=factor*0.2;
 */
static const struct pll_div codec_pll_div[] = {
	{128000, 22579200, 1, 529, 1},
	{192000, 22579200, 1, 352, 4},
	{256000, 22579200, 1, 264, 3},
	{384000, 22579200, 1, 176, 2},/*((176+2*0.2)*6000000)/(38*(2*1+1))*/
	{6000000, 22579200, 38, 429, 0},/*((429+0*0.2)*6000000)/(38*(2*1+1))*/
	{13000000, 22579200, 19, 99, 0},
	{19200000, 22579200, 25, 88, 1},
	{24000000, 22579200, 63, 177, 4},/*((177 + 4 * 0.2) * 24000000) / (63 * (2 * 1 + 1)) */
	{128000, 24576000, 1, 576, 0},
	{192000, 24576000, 1, 384, 0},
	{256000, 24576000, 1, 288, 0},
	{384000, 24576000, 1, 192, 0},
	{1411200, 22579200, 1, 48, 0},
	{2048000, 24576000, 1, 36, 0},
	{6000000, 24576000, 25, 307, 1},
	{13000000, 24576000, 42, 238, 1},
	{19200000, 24576000, 25, 96, 0},
	{24000000, 24576000, 39, 119, 4},/*((119 + 4 * 0.2) * 24000000) / (39 * (2 * 1 + 1)) */
	{11289600, 22579200, 1, 6, 0},
	{12288000, 24576000, 1, 6, 0},
};

static const struct aif1_fs codec_aif1_fs[] = {
	{8000, 12, 0},
	{11025, 8, 1, _SERIES_22_579K},
	{12000, 8, 2},
	{16000, 6, 3},
	{22050, 4, 4, _SERIES_22_579K},
	{24000, 4, 5},
	/* {32000, 3, 6}, dividing by 3 is not support */
	{44100, 2, 7, _SERIES_22_579K},
	{48000, 2, 8},
	{96000, 1, 9},
};

static const struct kv_map codec_aif1_lrck[] = {
	{16, 0},
	{32, 1},
	{64, 2},
	{128, 3},
	{256, 4},
};

static const struct kv_map codec_aif1_wsize[] = {
	{8, 0},
	{16, 1},
	{20, 2},
	{24, 3},
	{32, 3},
};

static const unsigned ac101_bclkdivs[] = {
	  1,   2,   4,   6,
	  8,  12,  16,  24,
	 32,  48,  64,  96,
	128, 192,   0,   0,
};

int ac101_aif_mute(struct snd_soc_dai *codec_dai, int mute)
{
	struct snd_soc_codec *codec = codec_dai->codec;
	struct ac10x_priv *ac10x = snd_soc_codec_get_drvdata(codec);

	AC101_DBG("%s() L%d mute=%d\n", __func__, __LINE__, mute);

	ac101_write(codec, DAC_VOL_CTRL, mute? 0: 0xA0A0);

	if (!mute) {
		late_enable_dac(codec, SND_SOC_DAPM_PRE_PMU);
		ac101_headphone_event(codec, SND_SOC_DAPM_POST_PMU);
		if (drc_used) {
			drc_enable(codec, 1);
		}
		if (ac10x->gpiod_spk_amp_gate) {
			gpiod_set_value(ac10x->gpiod_spk_amp_gate, 1);
		}
		#if _MASTER_MULTI_CODEC != _MASTER_AC101
		/* enable global clock */
		ac101_aif1clk(static_ac10x->codec, SND_SOC_DAPM_PRE_PMU);
		#endif
	} else {
		if (ac10x->gpiod_spk_amp_gate) {
			gpiod_set_value(ac10x->gpiod_spk_amp_gate, 0);
		}
		if (drc_used) {
			drc_enable(codec, 0);
		}
		ac101_headphone_event(codec, SND_SOC_DAPM_PRE_PMD);
		late_enable_dac(codec, SND_SOC_DAPM_POST_PMD);

		ac10x->aif1_clken = 1;
		ac101_aif1clk(codec, SND_SOC_DAPM_POST_PMD);
	}
	return 0;
}

void ac101_aif_shutdown(struct snd_pcm_substream *substream, struct snd_soc_dai *codec_dai)
{
	struct snd_soc_codec *codec = codec_dai->codec;
	int reg_val;

	AC101_DBG("%s,line:%d stream = %d, play-active = %d\n", __func__, __LINE__,
		substream->stream, codec_dai->playback_active);

	if (substream->stream == SNDRV_PCM_STREAM_CAPTURE) {
		reg_val = (ac101_read(codec, AIF_SR_CTRL) >> 12) & 0xF;
		if (codec_dai->playback_active && dmic_used && reg_val == 0x4) {
			ac101_update_bits(codec, AIF_SR_CTRL, (0xf<<AIF1_FS), (0x7<<AIF1_FS));
		}
	}
}

static int ac101_set_pll(struct snd_soc_dai *codec_dai, int pll_id, int source,
			unsigned int freq_in, unsigned int freq_out)
{
	int i = 0;
	int m 	= 0;
	int n_i = 0;
	int n_f = 0;
	struct snd_soc_codec *codec = codec_dai->codec;

	AC101_DBG("%s, line:%d, pll_id:%d\n", __func__, __LINE__, pll_id);

	if (!freq_out)
		return 0;
	if ((freq_in < 128000) || (freq_in > 24576000)) {
		return -EINVAL;
	} else if ((freq_in == 24576000) || (freq_in == 22579200)) {
		if (pll_id == AC101_MCLK1) {
			/*select aif1 clk source from mclk1*/
			ac101_update_bits(codec, SYSCLK_CTRL, (0x3<<AIF1CLK_SRC), (0x0<<AIF1CLK_SRC));
			return 0;
		}
		return -EINVAL;
	}

	switch (pll_id) {
	case AC101_MCLK1:
		/*pll source from MCLK1*/
		ac101_update_bits(codec, SYSCLK_CTRL, (0x3<<PLLCLK_SRC), (0x0<<PLLCLK_SRC));
		break;
	case AC101_BCLK1:
		/*pll source from BCLK1*/
		ac101_update_bits(codec, SYSCLK_CTRL, (0x3<<PLLCLK_SRC), (0x2<<PLLCLK_SRC));
		break;
	default:
		return -EINVAL;
	}
	/* freq_out = freq_in * n/(m*(2k+1)) , k=1,N=N_i+N_f */
	for (i = 0; i < ARRAY_SIZE(codec_pll_div); i++) {
		if ((codec_pll_div[i].pll_in == freq_in) && (codec_pll_div[i].pll_out == freq_out)) {
			m   = codec_pll_div[i].m;
			n_i = codec_pll_div[i].n_i;
			n_f = codec_pll_div[i].n_f;
			break;
		}
	}
	/*config pll m*/
	ac101_update_bits(codec, PLL_CTRL1, (0x3f<<PLL_POSTDIV_M), (m<<PLL_POSTDIV_M));
	/*config pll n*/
	ac101_update_bits(codec, PLL_CTRL2, (0x3ff<<PLL_PREDIV_NI), (n_i<<PLL_PREDIV_NI));
	ac101_update_bits(codec, PLL_CTRL2, (0x7<<PLL_POSTDIV_NF), (n_f<<PLL_POSTDIV_NF));
	ac101_update_bits(codec, PLL_CTRL2, (0x1<<PLL_EN), (1<<PLL_EN));
	/*enable pll_enable*/
	ac101_update_bits(codec, SYSCLK_CTRL, (0x1<<PLLCLK_ENA),  (0x1<<PLLCLK_ENA));
	ac101_update_bits(codec, SYSCLK_CTRL, (0x3<<AIF1CLK_SRC), (0x3<<AIF1CLK_SRC));

	return 0;
}

int ac101_hw_params(struct snd_pcm_substream *substream,
	struct snd_pcm_hw_params *params,
	struct snd_soc_dai *codec_dai)
{
	int i = 0;
	int AIF_CLK_CTRL = AIF1_CLK_CTRL;
	int aif1_word_size = 24;
	int aif1_slot_size = 32;
	int aif1_lrck_div;
	struct snd_soc_codec *codec = codec_dai->codec;
	struct ac10x_priv *ac10x = snd_soc_codec_get_drvdata(codec);
	int reg_val, freq_out;
	unsigned channels;

	AC101_DBG("%s() L%d +++\n", __func__, __LINE__);

	/* Master mode, to clear cpu_dai fifos, disable output bclk & lrck */
	#if 0
	ac10x->aif1_clken = 1;
	ac101_aif1clk(codec, SND_SOC_DAPM_POST_PMD);
	#endif

	/* get channels count & slot size */
	channels = params_channels(params);

	switch (params_format(params)) {
	case SNDRV_PCM_FORMAT_S24_LE:
	case SNDRV_PCM_FORMAT_S32_LE:
		aif1_slot_size = 32;
		break;
	case SNDRV_PCM_FORMAT_S16_LE:
	default:
		aif1_slot_size = 16;
		break;
	}

	/* set LRCK/BCLK ratio */
	aif1_lrck_div = aif1_slot_size * channels;
	for (i = 0; i < ARRAY_SIZE(codec_aif1_lrck); i++) {
		if (codec_aif1_lrck[i].val == aif1_lrck_div) {
			break;
		}
	}
	ac101_update_bits(codec, AIF_CLK_CTRL, (0x7<<AIF1_LRCK_DIV), codec_aif1_lrck[i].bit<<AIF1_LRCK_DIV);

	/* set PLL output freq */
	freq_out = 24576000;
	for (i = 0; i < ARRAY_SIZE(codec_aif1_fs); i++) {
		if (codec_aif1_fs[i].samp_rate == params_rate(params)) {
			if (codec_dai->capture_active && dmic_used && codec_aif1_fs[i].samp_rate == 44100) {
				ac101_update_bits(codec, AIF_SR_CTRL, (0xf<<AIF1_FS), (0x4<<AIF1_FS));
			} else {
				ac101_update_bits(codec, AIF_SR_CTRL, (0xf<<AIF1_FS), ((codec_aif1_fs[i].srbit)<<AIF1_FS));
			}
			if (codec_aif1_fs[i].series == _SERIES_22_579K)
				freq_out = 22579200;
			break;
		}
	}

	/* set I2S word size */
	for (i = 0; i < ARRAY_SIZE(codec_aif1_wsize); i++) {
		if (codec_aif1_wsize[i].val == aif1_word_size) {
			break;
		}
	}
	ac101_update_bits(codec, AIF_CLK_CTRL, (0x3<<AIF1_WORK_SIZ), ((codec_aif1_wsize[i].bit)<<AIF1_WORK_SIZ));

	/* set TDM slot size */
	if ((reg_val = codec_aif1_wsize[i].bit) > 2) reg_val = 2;
	ac101_update_bits(codec, AIF1_ADCDAT_CTRL, 0x3 << AIF1_SLOT_SIZ, reg_val << AIF1_SLOT_SIZ);

	/* setting pll if it's master mode */
	reg_val = ac101_read(codec, AIF_CLK_CTRL);
	if ((reg_val & (0x1 << AIF1_MSTR_MOD)) == 0) {
		unsigned bclkdiv;

		ac101_set_pll(codec_dai, AC101_MCLK1, 0, ac10x->sysclk, freq_out);

		bclkdiv = freq_out / (aif1_lrck_div * params_rate(params));
		for (i = 0; i < ARRAY_SIZE(ac101_bclkdivs) - 1; i++) {
			if (ac101_bclkdivs[i] >= bclkdiv) {
				break;
			}
		}
		ac101_update_bits(codec, AIF_CLK_CTRL, (0xf<<AIF1_BCLK_DIV), i<<AIF1_BCLK_DIV);
	}

	AC101_DBG("rate: %d , channels: %d , samp_res: %d",
		params_rate(params), channels, aif1_slot_size);

	AC101_DBG("%s() L%d ---\n", __func__, __LINE__);
	return 0;
}

#if 0
static int ac101_set_dai_sysclk(struct snd_soc_dai *codec_dai,
				  int clk_id, unsigned int freq, int dir)
{
	struct snd_soc_codec *codec = codec_dai->codec;
	struct ac10x_priv *ac10x = snd_soc_codec_get_drvdata(codec);

	AC101_DBG("%s,line:%d, id=%d freq=%d, dir=%d\n", __func__, __LINE__,
		clk_id, freq, dir);

	ac10x->sysclk = freq;

	return 0;
}
#endif

int ac101_set_dai_fmt(struct snd_soc_dai *codec_dai, unsigned int fmt)
{
	int reg_val;
	int AIF_CLK_CTRL = AIF1_CLK_CTRL;
	struct snd_soc_codec *codec = codec_dai->codec;

	AC101_DBG("%s() L%d\n", __func__, __LINE__);

	/*
	 * 	master or slave selection
	 *	0 = Master mode
	 *	1 = Slave mode
	 */
	reg_val = ac101_read(codec, AIF_CLK_CTRL);
	reg_val &= ~(0x1<<AIF1_MSTR_MOD);
	switch(fmt & SND_SOC_DAIFMT_MASTER_MASK) {
	case SND_SOC_DAIFMT_CBM_CFM:   /* codec clk & frm master, ap is slave*/
		#if _MASTER_MULTI_CODEC == _MASTER_AC101
		pr_warn("AC101 as Master\n");
		reg_val |= (0x0<<AIF1_MSTR_MOD);
		break;
		#else
		pr_warn("AC108 as Master\n");
		#endif
	case SND_SOC_DAIFMT_CBS_CFS:   /* codec clk & frm slave, ap is master*/
		pr_warn("AC101 as Slave\n");
		reg_val |= (0x1<<AIF1_MSTR_MOD);
		break;
	default:
		pr_err("unknwon master/slave format\n");
		return -EINVAL;
	}

	/*
	 * Enable TDM mode
	 */
	reg_val |=  (0x1 << AIF1_TDMM_ENA);
	ac101_write(codec, AIF_CLK_CTRL, reg_val);

	/* i2s mode selection */
	reg_val = ac101_read(codec, AIF_CLK_CTRL);
	reg_val&=~(3<<AIF1_DATA_FMT);
	switch(fmt & SND_SOC_DAIFMT_FORMAT_MASK){
	case SND_SOC_DAIFMT_I2S:        /* I2S1 mode */
		reg_val |= (0x0<<AIF1_DATA_FMT);
		break;
	case SND_SOC_DAIFMT_RIGHT_J:    /* Right Justified mode */
		reg_val |= (0x2<<AIF1_DATA_FMT);
		break;
	case SND_SOC_DAIFMT_LEFT_J:     /* Left Justified mode */
		reg_val |= (0x1<<AIF1_DATA_FMT);
		break;
	case SND_SOC_DAIFMT_DSP_A:      /* L reg_val msb after FRM LRC */
		reg_val |= (0x3<<AIF1_DATA_FMT);
		break;
	default:
		pr_err("%s, line:%d\n", __func__, __LINE__);
		return -EINVAL;
	}
	ac101_write(codec, AIF_CLK_CTRL, reg_val);

	/* DAI signal inversions */
	reg_val = ac101_read(codec, AIF_CLK_CTRL);
	switch(fmt & SND_SOC_DAIFMT_INV_MASK){
	case SND_SOC_DAIFMT_NB_NF:     /* normal bit clock + nor frame */
		reg_val &= ~(0x1<<AIF1_LRCK_INV);
		reg_val &= ~(0x1<<AIF1_BCLK_INV);
		break;
	case SND_SOC_DAIFMT_NB_IF:     /* normal bclk + inv frm */
		reg_val |= (0x1<<AIF1_LRCK_INV);
		reg_val &= ~(0x1<<AIF1_BCLK_INV);
		break;
	case SND_SOC_DAIFMT_IB_NF:     /* invert bclk + nor frm */
		reg_val &= ~(0x1<<AIF1_LRCK_INV);
		reg_val |= (0x1<<AIF1_BCLK_INV);
		break;
	case SND_SOC_DAIFMT_IB_IF:     /* invert bclk + inv frm */
		reg_val |= (0x1<<AIF1_LRCK_INV);
		reg_val |= (0x1<<AIF1_BCLK_INV);
		break;
	}
	ac101_write(codec, AIF_CLK_CTRL, reg_val);

	return 0;
}

int ac101_audio_startup(struct snd_pcm_substream *substream,
	struct snd_soc_dai *codec_dai)
{
	// struct snd_soc_codec *codec = codec_dai->codec;

	AC101_DBG("\n\n%s,line:%d\n", __func__, __LINE__);

	if (substream->stream == SNDRV_PCM_STREAM_CAPTURE) {
	}
	return 0;
}

#if _MASTER_MULTI_CODEC == _MASTER_AC101
static int ac101_set_clock(int y_start_n_stop) {
	if (y_start_n_stop) {
		/* enable global clock */
		ac101_aif1clk(static_ac10x->codec, SND_SOC_DAPM_PRE_PMU);
	}
	return 0;
}
#endif

#if 0
static int ac101_trigger(struct snd_pcm_substream *substream, int cmd,
			     struct snd_soc_dai *dai)
{
	int ret = 0;

	AC101_DBG("%s() stream=%d  cmd=%d\n",
		__FUNCTION__, substream->stream, cmd);

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_RESUME:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:

	case SNDRV_PCM_TRIGGER_STOP:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
		break;
	default:
		ret = -EINVAL;
	}
	return ret;
}

static const struct snd_soc_dai_ops ac101_aif1_dai_ops = {
	//.startup	= ac101_audio_startup,
	//.shutdown	= ac101_aif_shutdown,
	//.set_sysclk	= ac101_set_dai_sysclk,
	//.set_pll	= ac101_set_pll,
	//.set_fmt	= ac101_set_dai_fmt,
	//.hw_params	= ac101_hw_params,
	//.trigger	= ac101_trigger,
	//.digital_mute	= ac101_aif_mute,
};

static struct snd_soc_dai_driver ac101_dai[] = {
	{
		.name = "ac10x-aif1",
		.id = AIF1_CLK,
		.playback = {
			.stream_name = "Playback",
			.channels_min = 1,
			.channels_max = 8,
			.rates = AC101_RATES,
			.formats = AC101_FORMATS,
		},
		#if 0
		.capture = {
			.stream_name = "Capture",
			.channels_min = 1,
			.channels_max = 8,
			.rates = AC101_RATES,
			.formats = AC101_FORMATS,
		},
		#endif
		.ops = &ac101_aif1_dai_ops,
	}
};
#endif

static void codec_resume_work(struct work_struct *work)
{
	struct ac10x_priv *ac10x = container_of(work, struct ac10x_priv, codec_resume);
	struct snd_soc_codec *codec = ac10x->codec;

	AC101_DBG("%s() L%d +++\n", __func__, __LINE__);

	set_configuration(codec);
	if (drc_used) {
		drc_config(codec);
	}
	/*enable this bit to prevent leakage from ldoin*/
	ac101_update_bits(codec, ADDA_TUNE3, (0x1<<OSCEN), (0x1<<OSCEN));

	AC101_DBG("%s() L%d +++\n", __func__, __LINE__);
	return;
}

int ac101_set_bias_level(struct snd_soc_codec *codec, enum snd_soc_bias_level level)
{
	switch (level) {
	case SND_SOC_BIAS_ON:
		AC101_DBG("%s,line:%d, SND_SOC_BIAS_ON\n", __func__, __LINE__);
		break;
	case SND_SOC_BIAS_PREPARE:
		AC101_DBG("%s,line:%d, SND_SOC_BIAS_PREPARE\n", __func__, __LINE__);
		break;
	case SND_SOC_BIAS_STANDBY:
		AC101_DBG("%s,line:%d, SND_SOC_BIAS_STANDBY\n", __func__, __LINE__);
		break;
	case SND_SOC_BIAS_OFF:
		ac101_update_bits(codec, OMIXER_DACA_CTRL, (0xf<<HPOUTPUTENABLE), (0<<HPOUTPUTENABLE));
		ac101_update_bits(codec, ADDA_TUNE3, (0x1<<OSCEN), (0<<OSCEN));
		AC101_DBG("%s,line:%d, SND_SOC_BIAS_OFF\n", __func__, __LINE__);
		break;
	}
	snd_soc_codec_get_dapm(codec)->bias_level = level;
	return 0;
}

int ac101_codec_probe(struct snd_soc_codec *codec)
{
	int ret = 0;
	struct ac10x_priv *ac10x;

	ac10x = dev_get_drvdata(codec->dev);
	if (ac10x == NULL) {
		AC101_DBG("not set client data %s() L%d\n", __func__, __LINE__);
		return -ENOMEM;
	}
	ac10x->codec = codec;

	INIT_WORK(&ac10x->codec_resume, codec_resume_work);
	ac10x->dac_enable = 0;
	ac10x->aif1_clken = 0;
	ac10x->aif2_clken = 0;
	mutex_init(&ac10x->dac_mutex);
	mutex_init(&ac10x->adc_mutex);
	mutex_init(&ac10x->aifclk_mutex);

	#if _MASTER_MULTI_CODEC == _MASTER_AC101
	asoc_simple_card_register_set_clock(ac101_set_clock);
	#endif

	set_configuration(ac10x->codec);

	/*enable this bit to prevent leakage from ldoin*/
	ac101_update_bits(codec, ADDA_TUNE3, (0x1<<OSCEN), (0x1<<OSCEN));
	ac101_write(codec, DAC_VOL_CTRL, 0);

	/* customized get/put inteface */
	for (ret = 0; ret < ARRAY_SIZE(ac101_controls); ret++) {
		struct snd_kcontrol_new* skn = &ac101_controls[ret];

		skn->get = snd_ac101_get_volsw;
		skn->put = snd_ac101_put_volsw;
	}
	ret = snd_soc_add_codec_controls(codec, ac101_controls,	ARRAY_SIZE(ac101_controls));
	if (ret) {
		pr_err("[ac10x] Failed to register audio mode control, "
				"will continue without it.\n");
	}
	return 0;
}

/* power down chip */
int ac101_codec_remove(struct snd_soc_codec *codec)
{
	// struct ac10x_priv *ac10x = snd_soc_codec_get_drvdata(codec);
	return 0;
}

int ac101_codec_suspend(struct snd_soc_codec *codec)
{
	struct ac10x_priv *ac10x = snd_soc_codec_get_drvdata(codec);

	AC101_DBG("[codec]:suspend\n");
	regcache_cache_only(ac10x->regmap101, true);
	return 0;
}

int ac101_codec_resume(struct snd_soc_codec *codec)
{
	struct ac10x_priv *ac10x = snd_soc_codec_get_drvdata(codec);
	int ret;

	AC101_DBG("[codec]:resume");

	/* Sync reg_cache with the hardware */
	regcache_cache_only(ac10x->regmap101, false);
	ret = regcache_sync(ac10x->regmap101);
	if (ret != 0) {
		dev_err(codec->dev, "Failed to sync register cache: %d\n", ret);
		regcache_cache_only(ac10x->regmap101, true);
		return ret;
	}

	ac101_set_bias_level(codec, SND_SOC_BIAS_STANDBY);
	schedule_work(&ac10x->codec_resume);
	return 0;
}

/***************************************************************************/
static ssize_t ac101_debug_store(struct device *dev,
	struct device_attribute *attr, const char *buf, size_t count)
{
	static int val = 0, flag = 0;
	u8 reg,num,i=0;
	u16 value_w,value_r[128];
	struct ac10x_priv *ac10x = dev_get_drvdata(dev);
	val = simple_strtol(buf, NULL, 16);
	flag = (val >> 24) & 0xF;
	if(flag) {
		reg = (val >> 16) & 0xFF;
		value_w =  val & 0xFFFF;
		ac101_write(ac10x->codec, reg, value_w);
		printk("write 0x%x to reg:0x%x\n",value_w,reg);
	} else {
		reg =(val>>8)& 0xFF;
		num=val&0xff;
		printk("\n");
		printk("read:start add:0x%x,count:0x%x\n",reg,num);
		do {
			value_r[i] = ac101_read(ac10x->codec, reg);
			printk("0x%x: 0x%04x ",reg,value_r[i]);
			reg+=1;
			i++;
			if(i == num)
				printk("\n");
			if(i%4==0)
				printk("\n");
		} while(i<num);
	}
	return count;
}
static ssize_t ac101_debug_show(struct device *dev,
	struct device_attribute *attr, char *buf)
{
	printk("echo flag|reg|val > ac10x\n");
	printk("eg read star addres=0x06,count 0x10:echo 0610 >ac10x\n");
	printk("eg write value:0x13fe to address:0x06 :echo 10613fe > ac10x\n");
	return 0;
}
static DEVICE_ATTR(ac10x, 0644, ac101_debug_show, ac101_debug_store);

static struct attribute *audio_debug_attrs[] = {
	&dev_attr_ac10x.attr,
	NULL,
};

static struct attribute_group audio_debug_attr_group = {
	.name   = "ac101_debug",
	.attrs  = audio_debug_attrs,
};
/***************************************************************************/

/************************************************************/
static const struct regmap_config ac101_regmap = {
	.reg_bits = 8,
	.val_bits = 16,
	.reg_stride = 1,
	.max_register = 0xB5,
	.cache_type = REGCACHE_RBTREE,
};

int ac101_probe(struct i2c_client *i2c, const struct i2c_device_id *id)
{
	struct ac10x_priv *ac10x = i2c_get_clientdata(i2c);
	int ret = 0;
	unsigned v = 0;

	AC101_DBG("%s,line:%d\n", __func__, __LINE__);

	static_ac10x = ac10x;

	ac10x->regmap101 = devm_regmap_init_i2c(i2c, &ac101_regmap);
	if (IS_ERR(ac10x->regmap101)) {
		ret = PTR_ERR(ac10x->regmap101);
		dev_err(&i2c->dev, "Fail to initialize I/O: %d\n", ret);
		return ret;
	}

	ret = regmap_read(ac10x->regmap101, CHIP_AUDIO_RST, &v);
	if (ret < 0) {
		dev_err(&i2c->dev, "failed to read vendor ID: %d\n", ret);
		return ret;
	}

	if (v != AC101_CHIP_ID) {
		dev_err(&i2c->dev, "chip is not AC101\n");
		dev_err(&i2c->dev, "Expected %X\n", AC101_CHIP_ID);
		return -ENODEV;
	}

	ret = sysfs_create_group(&i2c->dev.kobj, &audio_debug_attr_group);
	if (ret) {
		pr_err("failed to create attr group\n");
	}

	ac10x->gpiod_spk_amp_gate = devm_gpiod_get_optional(&i2c->dev, "spk-amp-switch", GPIOD_OUT_LOW);
	if (IS_ERR(ac10x->gpiod_spk_amp_gate)) {
		ac10x->gpiod_spk_amp_gate = NULL;
		dev_err(&i2c->dev, "failed get spk-amp-switch in device tree\n");
	}
	return 0;
}

void ac101_shutdown(struct i2c_client *i2c)
{
	struct ac10x_priv *ac10x = i2c_get_clientdata(i2c);
	struct snd_soc_codec *codec = ac10x->codec;
	int reg_val;

	if (codec == NULL) {
		pr_err("%s() L%d: no sound card.\n", __func__, __LINE__);
		return;
	}

	/*set headphone volume to 0*/
	reg_val = ac101_read(codec, HPOUT_CTRL);
	reg_val &= ~(0x3f<<HP_VOL);
	ac101_write(codec, HPOUT_CTRL, reg_val);

	/*disable pa*/
	reg_val = ac101_read(codec, HPOUT_CTRL);
	reg_val &= ~(0x1<<HPPA_EN);
	ac101_write(codec, HPOUT_CTRL, reg_val);

	/*hardware xzh support*/
	reg_val = ac101_read(codec, OMIXER_DACA_CTRL);
	reg_val &= ~(0xf<<HPOUTPUTENABLE);
	ac101_write(codec, OMIXER_DACA_CTRL, reg_val);

	/*unmute l/r headphone pa*/
	reg_val = ac101_read(codec, HPOUT_CTRL);
	reg_val &= ~((0x1<<RHPPA_MUTE)|(0x1<<LHPPA_MUTE));
	ac101_write(codec, HPOUT_CTRL, reg_val);
	return;
}

int ac101_remove(struct i2c_client *i2c)
{
	sysfs_remove_group(&i2c->dev.kobj, &audio_debug_attr_group);
	return 0;
}

MODULE_DESCRIPTION("ASoC ac10x driver");
MODULE_AUTHOR("huangxin,liushaohua");
MODULE_AUTHOR("PeterYang<linsheng.yang@seeed.cc>");
