#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <alsa/asoundlib.h>
#include <alsa/pcm_external.h>
#include <alsa/pcm_plugin.h>
#include <math.h>

void generate_sine(const snd_pcm_channel_area_t *areas,        
                          snd_pcm_uframes_t offset,
                          int count, double *_phase);
