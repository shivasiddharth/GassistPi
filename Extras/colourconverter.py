#!/usr/bin/env python

#Convert MS-Access colour to RGB

import math

def colourconv(x):
    accesscolour=int(x)
    R=math.floor(accesscolour/65536)
    G=math.floor((accesscolour-(R*65536))/256)
    B=accesscolour-(R*65536)-(G*256)

    return R,G,B
