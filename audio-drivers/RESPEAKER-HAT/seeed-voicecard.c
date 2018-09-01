/*
 * SEEED voice card
 *
 * (C) Copyright 2017-2018
 * Seeed Technology Co., Ltd. <www.seeedstudio.com>
 *
 * base on ASoC simple sound card support
 *
 * Copyright (C) 2012 Renesas Solutions Corp.
 * Kuninori Morimoto <kuninori.morimoto.gx@renesas.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 */
/* #undef DEBUG */
#include <linux/version.h>
#include <linux/clk.h>
#include <linux/device.h>
#include <linux/gpio.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/of_gpio.h>
#include <linux/platform_device.h>
#include <linux/string.h>
#include <sound/soc.h>
#include <sound/soc-dai.h>
#include <sound/simple_card_utils.h>

/*
 * single codec:
 *	0 - allow multi codec
 *	1 - yes
 */
#define _SINGLE_CODEC		1

struct seeed_card_data {
	struct snd_soc_card snd_card;
	struct seeed_dai_props {
		struct asoc_simple_dai cpu_dai;
		struct asoc_simple_dai codec_dai;
		unsigned int mclk_fs;
	} *dai_props;
	unsigned int mclk_fs;
	unsigned channels_playback_default;
	unsigned channels_playback_override;
	unsigned channels_capture_default;
	unsigned channels_capture_override;
	struct snd_soc_dai_link *dai_link;
	spinlock_t lock;
};

struct seeed_card_info {
	const char *name;
	const char *card;
	const char *codec;
	const char *platform;

	unsigned int daifmt;
	struct asoc_simple_dai cpu_dai;
	struct asoc_simple_dai codec_dai;
};

#define seeed_priv_to_dev(priv) ((priv)->snd_card.dev)
#define seeed_priv_to_link(priv, i) ((priv)->snd_card.dai_link + (i))
#define seeed_priv_to_props(priv, i) ((priv)->dai_props + (i))

#define DAI	"sound-dai"
#define CELL	"#sound-dai-cells"
#define PREFIX	"seeed-voice-card,"

static int seeed_voice_card_startup(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = substream->private_data;
	struct seeed_card_data *priv =	snd_soc_card_get_drvdata(rtd->card);
	struct seeed_dai_props *dai_props =
		seeed_priv_to_props(priv, rtd->num);
	int ret;

	ret = clk_prepare_enable(dai_props->cpu_dai.clk);
	if (ret)
		return ret;

	ret = clk_prepare_enable(dai_props->codec_dai.clk);
	if (ret)
		clk_disable_unprepare(dai_props->cpu_dai.clk);

	if (rtd->cpu_dai->driver->playback.channels_min) {
		priv->channels_playback_default = rtd->cpu_dai->driver->playback.channels_min;
	}
	if (rtd->cpu_dai->driver->capture.channels_min) {
		priv->channels_capture_default = rtd->cpu_dai->driver->capture.channels_min;
	}
	rtd->cpu_dai->driver->playback.channels_min = priv->channels_playback_override;
	rtd->cpu_dai->driver->playback.channels_max = priv->channels_playback_override;
	rtd->cpu_dai->driver->capture.channels_min = priv->channels_capture_override;
	rtd->cpu_dai->driver->capture.channels_max = priv->channels_capture_override;

	return ret;
}

static void seeed_voice_card_shutdown(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = substream->private_data;
	struct seeed_card_data *priv =	snd_soc_card_get_drvdata(rtd->card);
	struct seeed_dai_props *dai_props =
		seeed_priv_to_props(priv, rtd->num);

	rtd->cpu_dai->driver->playback.channels_min = priv->channels_playback_default;
	rtd->cpu_dai->driver->playback.channels_max = priv->channels_playback_default;
	rtd->cpu_dai->driver->capture.channels_min = priv->channels_capture_default;
	rtd->cpu_dai->driver->capture.channels_max = priv->channels_capture_default;

	clk_disable_unprepare(dai_props->cpu_dai.clk);

	clk_disable_unprepare(dai_props->codec_dai.clk);
}

static int seeed_voice_card_hw_params(struct snd_pcm_substream *substream,
				      struct snd_pcm_hw_params *params)
{
	struct snd_soc_pcm_runtime *rtd = substream->private_data;
	struct snd_soc_dai *codec_dai = rtd->codec_dai;
	struct snd_soc_dai *cpu_dai = rtd->cpu_dai;
	struct seeed_card_data *priv = snd_soc_card_get_drvdata(rtd->card);
	struct seeed_dai_props *dai_props =
		seeed_priv_to_props(priv, rtd->num);
	unsigned int mclk, mclk_fs = 0;
	int ret = 0;

	if (priv->mclk_fs)
		mclk_fs = priv->mclk_fs;
	else if (dai_props->mclk_fs)
		mclk_fs = dai_props->mclk_fs;

	if (mclk_fs) {
		mclk = params_rate(params) * mclk_fs;
		ret = snd_soc_dai_set_sysclk(codec_dai, 0, mclk,
					     SND_SOC_CLOCK_IN);
		if (ret && ret != -ENOTSUPP)
			goto err;

		ret = snd_soc_dai_set_sysclk(cpu_dai, 0, mclk,
					     SND_SOC_CLOCK_OUT);
		if (ret && ret != -ENOTSUPP)
			goto err;
	}
	return 0;
err:
	return ret;
}

#define _SET_CLOCK_CNT		2
static int (* _set_clock[_SET_CLOCK_CNT])(int y_start_n_stop);

int seeed_voice_card_register_set_clock(int stream, int (*set_clock)(int)) {
	if (! _set_clock[stream]) {
		_set_clock[stream] = set_clock;
	}
	return 0;
}
EXPORT_SYMBOL(seeed_voice_card_register_set_clock);

static int seeed_voice_card_trigger(struct snd_pcm_substream *substream, int cmd)
{
	struct snd_soc_pcm_runtime *rtd = substream->private_data;
	struct snd_soc_dai *dai = rtd->codec_dai;
	struct seeed_card_data *priv = snd_soc_card_get_drvdata(rtd->card);
	unsigned long flags;
	int ret = 0;

	dev_dbg(rtd->card->dev, "%s() stream=%s  cmd=%d play:%d, capt:%d\n",
		__FUNCTION__, snd_pcm_stream_str(substream), cmd,
		dai->playback_active, dai->capture_active);

	/* I know it will degrades performance, but I have no choice */
	spin_lock_irqsave(&priv->lock, flags);

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_RESUME:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
		if (_set_clock[SNDRV_PCM_STREAM_CAPTURE]) _set_clock[SNDRV_PCM_STREAM_CAPTURE](1);
		if (_set_clock[SNDRV_PCM_STREAM_PLAYBACK]) _set_clock[SNDRV_PCM_STREAM_PLAYBACK](1);
		break;

	case SNDRV_PCM_TRIGGER_STOP:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
		/* capture channel resync, if overrun */
		if (dai->capture_active && substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
			break;
		}
		if (_set_clock[SNDRV_PCM_STREAM_CAPTURE]) _set_clock[SNDRV_PCM_STREAM_CAPTURE](0);
		if (_set_clock[SNDRV_PCM_STREAM_PLAYBACK]) _set_clock[SNDRV_PCM_STREAM_PLAYBACK](0);
		break;
	default:
		ret = -EINVAL;
	}

	spin_unlock_irqrestore(&priv->lock, flags);

	return ret;
}

static struct snd_soc_ops seeed_voice_card_ops = {
	.startup = seeed_voice_card_startup,
	.shutdown = seeed_voice_card_shutdown,
	.hw_params = seeed_voice_card_hw_params,
	.trigger = seeed_voice_card_trigger,
};

static int seeed_voice_card_dai_init(struct snd_soc_pcm_runtime *rtd)
{
	struct seeed_card_data *priv =	snd_soc_card_get_drvdata(rtd->card);
	struct snd_soc_dai *codec = rtd->codec_dai;
	struct snd_soc_dai *cpu = rtd->cpu_dai;
	struct seeed_dai_props *dai_props =
		seeed_priv_to_props(priv, rtd->num);
	int ret;

	ret = asoc_simple_card_init_dai(codec, &dai_props->codec_dai);
	if (ret < 0)
		return ret;

	ret = asoc_simple_card_init_dai(cpu, &dai_props->cpu_dai);
	if (ret < 0)
		return ret;

	return 0;
}

static int seeed_voice_card_dai_link_of(struct device_node *node,
					struct seeed_card_data *priv,
					int idx,
					bool is_top_level_node)
{
	struct device *dev = seeed_priv_to_dev(priv);
	struct snd_soc_dai_link *dai_link = seeed_priv_to_link(priv, idx);
	struct seeed_dai_props *dai_props = seeed_priv_to_props(priv, idx);
	struct asoc_simple_dai *cpu_dai = &dai_props->cpu_dai;
	struct asoc_simple_dai *codec_dai = &dai_props->codec_dai;
	struct device_node *cpu = NULL;
	struct device_node *plat = NULL;
	struct device_node *codec = NULL;
	char prop[128];
	char *prefix = "";
	int ret, single_cpu;

	/* For single DAI link & old style of DT node */
	if (is_top_level_node)
		prefix = PREFIX;

	snprintf(prop, sizeof(prop), "%scpu", prefix);
	cpu = of_get_child_by_name(node, prop);

	snprintf(prop, sizeof(prop), "%splat", prefix);
	plat = of_get_child_by_name(node, prop);

	snprintf(prop, sizeof(prop), "%scodec", prefix);
	codec = of_get_child_by_name(node, prop);

	if (!cpu || !codec) {
		ret = -EINVAL;
		dev_err(dev, "%s: Can't find %s DT node\n", __func__, prop);
		goto dai_link_of_err;
	}

	ret = asoc_simple_card_parse_daifmt(dev, node, codec,
					    prefix, &dai_link->dai_fmt);
	if (ret < 0)
		goto dai_link_of_err;

	of_property_read_u32(node, "mclk-fs", &dai_props->mclk_fs);

	ret = asoc_simple_card_parse_cpu(cpu, dai_link,
					 DAI, CELL, &single_cpu);
	if (ret < 0)
		goto dai_link_of_err;

	#if _SINGLE_CODEC
	ret = asoc_simple_card_parse_codec(codec, dai_link, DAI, CELL);
	if (ret < 0)
		goto dai_link_of_err;
	#else
	ret = snd_soc_of_get_dai_link_codecs(dev, codec, dai_link);
	if (ret < 0) {
		dev_err(dev, "parse codec info error %d\n", ret);
		goto dai_link_of_err;
	}
	dev_dbg(dev, "dai_link num_codecs = %d\n", dai_link->num_codecs);
	#endif

	ret = asoc_simple_card_parse_platform(plat, dai_link, DAI, CELL);
	if (ret < 0)
		goto dai_link_of_err;

	ret = snd_soc_of_parse_tdm_slot(cpu,	&cpu_dai->tx_slot_mask,
						&cpu_dai->rx_slot_mask,
						&cpu_dai->slots,
						&cpu_dai->slot_width);
	dev_dbg(dev, "cpu_dai : slot,width,tx,rx = %d,%d,%d,%d\n", 
			cpu_dai->slots, cpu_dai->slot_width,
			cpu_dai->tx_slot_mask, cpu_dai->rx_slot_mask
			);
	if (ret < 0)
		goto dai_link_of_err;

	ret = snd_soc_of_parse_tdm_slot(codec,	&codec_dai->tx_slot_mask,
						&codec_dai->rx_slot_mask,
						&codec_dai->slots,
						&codec_dai->slot_width);
	if (ret < 0)
		goto dai_link_of_err;

	#if LINUX_VERSION_CODE <= KERNEL_VERSION(4,10,0)
	ret = asoc_simple_card_parse_clk_cpu(cpu, dai_link, cpu_dai);
	#else
	ret = asoc_simple_card_parse_clk_cpu(dev, cpu, dai_link, cpu_dai);
	#endif
	if (ret < 0)
		goto dai_link_of_err;

	#if LINUX_VERSION_CODE <= KERNEL_VERSION(4,10,0)
	ret = asoc_simple_card_parse_clk_codec(codec, dai_link, codec_dai);
	#else
	ret = asoc_simple_card_parse_clk_codec(dev, codec, dai_link, codec_dai);
	#endif
	if (ret < 0)
		goto dai_link_of_err;

	#if _SINGLE_CODEC
	ret = asoc_simple_card_canonicalize_dailink(dai_link);
	if (ret < 0)
		goto dai_link_of_err;
	#endif

	ret = asoc_simple_card_set_dailink_name(dev, dai_link,
						"%s-%s",
						dai_link->cpu_dai_name,
						#if _SINGLE_CODEC
						dai_link->codec_dai_name
						#else
						dai_link->codecs[0].dai_name
						#endif
	);
	if (ret < 0)
		goto dai_link_of_err;

	dai_link->ops = &seeed_voice_card_ops;
	dai_link->init = seeed_voice_card_dai_init;

	dev_dbg(dev, "\tname : %s\n", dai_link->stream_name);
	dev_dbg(dev, "\tformat : %04x\n", dai_link->dai_fmt);
	dev_dbg(dev, "\tcpu : %s / %d\n",
		dai_link->cpu_dai_name,
		dai_props->cpu_dai.sysclk);
	dev_dbg(dev, "\tcodec : %s / %d\n",
		#if _SINGLE_CODEC
		dai_link->codec_dai_name,
		#else
		dai_link->codecs[0].dai_name,
		#endif
		dai_props->codec_dai.sysclk);

	asoc_simple_card_canonicalize_cpu(dai_link, single_cpu);

dai_link_of_err:
	of_node_put(cpu);
	of_node_put(codec);

	return ret;
}

static int seeed_voice_card_parse_aux_devs(struct device_node *node,
					   struct seeed_card_data *priv)
{
	struct device *dev = seeed_priv_to_dev(priv);
	struct device_node *aux_node;
	int i, n, len;

	if (!of_find_property(node, PREFIX "aux-devs", &len))
		return 0;		/* Ok to have no aux-devs */

	n = len / sizeof(__be32);
	if (n <= 0)
		return -EINVAL;

	priv->snd_card.aux_dev = devm_kzalloc(dev,
			n * sizeof(*priv->snd_card.aux_dev), GFP_KERNEL);
	if (!priv->snd_card.aux_dev)
		return -ENOMEM;

	for (i = 0; i < n; i++) {
		aux_node = of_parse_phandle(node, PREFIX "aux-devs", i);
		if (!aux_node)
			return -EINVAL;
		priv->snd_card.aux_dev[i].codec_of_node = aux_node;
	}

	priv->snd_card.num_aux_devs = n;
	return 0;
}

static int seeed_voice_card_parse_of(struct device_node *node,
				     struct seeed_card_data *priv)
{
	struct device *dev = seeed_priv_to_dev(priv);
	struct device_node *dai_link;
	int ret;

	if (!node)
		return -EINVAL;

	dai_link = of_get_child_by_name(node, PREFIX "dai-link");

	/* The off-codec widgets */
	if (of_property_read_bool(node, PREFIX "widgets")) {
		ret = snd_soc_of_parse_audio_simple_widgets(&priv->snd_card,
					PREFIX "widgets");
		if (ret)
			goto card_parse_end;
	}

	/* DAPM routes */
	if (of_property_read_bool(node, PREFIX "routing")) {
		ret = snd_soc_of_parse_audio_routing(&priv->snd_card,
					PREFIX "routing");
		if (ret)
			goto card_parse_end;
	}

	/* Factor to mclk, used in hw_params() */
	of_property_read_u32(node, PREFIX "mclk-fs", &priv->mclk_fs);

	/* Single/Muti DAI link(s) & New style of DT node */
	if (dai_link) {
		struct device_node *np = NULL;
		int i = 0;

		for_each_child_of_node(node, np) {
			dev_dbg(dev, "\tlink %d:\n", i);
			ret = seeed_voice_card_dai_link_of(np, priv,
							   i, false);
			if (ret < 0) {
				of_node_put(np);
				goto card_parse_end;
			}
			i++;
		}
	} else {
		/* For single DAI link & old style of DT node */
		ret = seeed_voice_card_dai_link_of(node, priv, 0, true);
		if (ret < 0)
			goto card_parse_end;
	}

	ret = asoc_simple_card_parse_card_name(&priv->snd_card, PREFIX);
	if (ret < 0)
		goto card_parse_end;

	ret = seeed_voice_card_parse_aux_devs(node, priv);

	priv->channels_playback_default  = 0;
	priv->channels_playback_override = 2;
	priv->channels_capture_default   = 0;
	priv->channels_capture_override  = 2;
	of_property_read_u32(node, PREFIX "channels-playback-default",
				    &priv->channels_playback_default);
	of_property_read_u32(node, PREFIX "channels-playback-override",
				    &priv->channels_playback_override);
	of_property_read_u32(node, PREFIX "channels-capture-default",
				    &priv->channels_capture_default);
	of_property_read_u32(node, PREFIX "channels-capture-override",
				    &priv->channels_capture_override);

card_parse_end:
	of_node_put(dai_link);

	return ret;
}

static int seeed_voice_card_probe(struct platform_device *pdev)
{
	struct seeed_card_data *priv;
	struct snd_soc_dai_link *dai_link;
	struct seeed_dai_props *dai_props;
	struct device_node *np = pdev->dev.of_node;
	struct device *dev = &pdev->dev;
	int num, ret;

	/* Get the number of DAI links */
	if (np && of_get_child_by_name(np, PREFIX "dai-link"))
		num = of_get_child_count(np);
	else
		num = 1;

	/* Allocate the private data and the DAI link array */
	priv = devm_kzalloc(dev, sizeof(*priv), GFP_KERNEL);
	if (!priv)
		return -ENOMEM;

	dai_props = devm_kzalloc(dev, sizeof(*dai_props) * num, GFP_KERNEL);
	dai_link  = devm_kzalloc(dev, sizeof(*dai_link)  * num, GFP_KERNEL);
	if (!dai_props || !dai_link)
		return -ENOMEM;

	priv->dai_props			= dai_props;
	priv->dai_link			= dai_link;

	/* Init snd_soc_card */
	priv->snd_card.owner		= THIS_MODULE;
	priv->snd_card.dev		= dev;
	priv->snd_card.dai_link		= priv->dai_link;
	priv->snd_card.num_links	= num;

	if (np && of_device_is_available(np)) {
		ret = seeed_voice_card_parse_of(np, priv);
		if (ret < 0) {
			if (ret != -EPROBE_DEFER)
				dev_err(dev, "parse error %d\n", ret);
			goto err;
		}
	} else {
		struct seeed_card_info *cinfo;

		cinfo = dev->platform_data;
		if (!cinfo) {
			dev_err(dev, "no info for seeed-voice-card\n");
			return -EINVAL;
		}

		if (!cinfo->name ||
		    !cinfo->codec_dai.name ||
		    !cinfo->codec ||
		    !cinfo->platform ||
		    !cinfo->cpu_dai.name) {
			dev_err(dev, "insufficient seeed_voice_card_info settings\n");
			return -EINVAL;
		}

		priv->snd_card.name	= (cinfo->card) ? cinfo->card : cinfo->name;
		dai_link->name		= cinfo->name;
		dai_link->stream_name	= cinfo->name;
		dai_link->platform_name	= cinfo->platform;
		dai_link->codec_name	= cinfo->codec;
		dai_link->cpu_dai_name	= cinfo->cpu_dai.name;
		dai_link->codec_dai_name = cinfo->codec_dai.name;
		dai_link->dai_fmt	= cinfo->daifmt;
		dai_link->init		= seeed_voice_card_dai_init;
		memcpy(&priv->dai_props->cpu_dai, &cinfo->cpu_dai,
					sizeof(priv->dai_props->cpu_dai));
		memcpy(&priv->dai_props->codec_dai, &cinfo->codec_dai,
					sizeof(priv->dai_props->codec_dai));
	}

	snd_soc_card_set_drvdata(&priv->snd_card, priv);

	spin_lock_init(&priv->lock);

	ret = devm_snd_soc_register_card(&pdev->dev, &priv->snd_card);
	if (ret >= 0)
		return ret;

err:
	asoc_simple_card_clean_reference(&priv->snd_card);

	return ret;
}

static int seeed_voice_card_remove(struct platform_device *pdev)
{
	struct snd_soc_card *card = platform_get_drvdata(pdev);

	return asoc_simple_card_clean_reference(card);
}

static const struct of_device_id seeed_voice_of_match[] = {
	{ .compatible = "seeed-voicecard", },
	{},
};
MODULE_DEVICE_TABLE(of, seeed_voice_of_match);

static struct platform_driver seeed_voice_card = {
	.driver = {
		.name = "seeed-voicecard",
		.pm = &snd_soc_pm_ops,
		.of_match_table = seeed_voice_of_match,
	},
	.probe = seeed_voice_card_probe,
	.remove = seeed_voice_card_remove,
};

module_platform_driver(seeed_voice_card);

MODULE_ALIAS("platform:seeed-voice-card");
MODULE_LICENSE("GPL v2");
MODULE_DESCRIPTION("ASoC SEEED Voice Card");
MODULE_AUTHOR("PeterYang<linsheng.yang@seeed.cc>");
