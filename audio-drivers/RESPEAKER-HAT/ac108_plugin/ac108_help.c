#include "ac108_help.h"

void generate_sine(const snd_pcm_channel_area_t *areas, 
			  snd_pcm_uframes_t offset,
			  int count, double *_phase)
{
	 snd_pcm_format_t format = SND_PCM_FORMAT_S32;	/* sample format */
	 unsigned int rate = 16000;			/* stream rate */
	 unsigned int channels = 4;			/* count of channels */
	 unsigned int buffer_time = 500000;		/* ring buffer length in us */
	 unsigned int period_time = 100000;		/* period time in us */
	 double freq = 160;				/* sinusoidal wave frequency in Hz */
	 int verbose = 0;					/* verbose flag */
	 int resample = 1;				/* enable alsa-lib resampling */
	 int period_event = 0;				/* produce poll event after each period */
		
	static double max_phase = 2. * M_PI;
	double phase = *_phase;
	double step = max_phase*freq/(double)rate;
	unsigned char *samples[channels];
	int steps[channels];
	unsigned int chn;
	int format_bits = snd_pcm_format_width(format);
	unsigned int maxval = (1 << (format_bits - 1)) - 1;
	int bps = format_bits / 8;  /* bytes per sample */
	int phys_bps = snd_pcm_format_physical_width(format) / 8;
	int big_endian = snd_pcm_format_big_endian(format) == 1;
	int to_unsigned = snd_pcm_format_unsigned(format) == 1;
	int is_float = (format == SND_PCM_FORMAT_FLOAT_LE ||
			format == SND_PCM_FORMAT_FLOAT_BE);

	/* verify and prepare the contents of areas */
	for (chn = 0; chn < channels; chn++) {
		if ((areas[chn].first % 8) != 0) {
			printf("areas[%i].first == %i, aborting...\n", chn, areas[chn].first);
			exit(EXIT_FAILURE);
		}
		samples[chn] = /*(signed short *)*/(((unsigned char *)areas[chn].addr) + (areas[chn].first / 8));
		if ((areas[chn].step % 16) != 0) {
			printf("areas[%i].step == %i, aborting...\n", chn, areas[chn].step);
			exit(EXIT_FAILURE);
		}
		steps[chn] = areas[chn].step / 8;
		samples[chn] += offset * steps[chn];
	}
	/* fill the channel areas */
	while (count-- > 0) {
		union {
			float f;
			int i;
		} fval;
		int res, i;
		if (is_float) {
			fval.f = sin(phase);
			res = fval.i;
		} else
			res = sin(phase) * maxval;
		if (to_unsigned)
			res ^= 1U << (format_bits - 1);
		for (chn = 0; chn < channels; chn++) {
			/* Generate data in native endian format */
			if (big_endian) {
				for (i = 0; i < bps; i++)
					*(samples[chn] + phys_bps - 1 - i) = (res >> i * 8) & 0xff;
			} else {
				for (i = 0; i < bps; i++)
					*(samples[chn] + i) = (res >>  i * 8) & 0xff;
			}
			samples[chn] += steps[chn];
		}
		phase += step;
		if (phase >= max_phase)
			phase -= max_phase;
	}
	*_phase = phase;
}

