##
# This file is part of pyFidget, licensed under the MIT License (MIT).
#
# Copyright (c) 2016 teqwve <teqwve@openmailbox.org>
# Copyright (c) 2016 Wolf480pl <wolf480@interia.pl>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
##

import math
from animation import *

def _frameRect(a, b):
    if b == 1:
        return None
    return (a*64, b*64, 64, 128 if b == 0 and (a < 16 or a > 32) else 64)

_frame = [_frameRect(a, b) for b in range(6) for a in range(40)]

def getFrameRect(n):
    return _frame[n]


class Fidget(ITransformingAnimation,IAttachableAnimation):
    def __init__(self):

        leftWing    = LoopAnimation(FrameAnimation(range(8), 37, (53, 17), (119, 17), (55, 145)))
        rightWing   = LoopAnimation(FrameAnimation(range(8, 16), 37, (110, 17), (174, 17), (110, 145)))

        lookForward = FrameAnimation(
                range(18, 21) + [21 for i in range(10)] + range(20, 17, -1), 70, (75, 25))
        lookUpward  = FrameAnimation(
                range(25, 21, -1) + [16 for i in range(10)] + range(23, 25), 70, (75, 25))

        doNothing = FrameAnimation(
                [31 for i in range(50)], 70, (75, 25))

        wagTail = FrameAnimation(
#                range(80, 159), 35, (79 + 1, 77) , (143 + 1, 77), (71 + 1, 138))
                range(80, 159), 35, (79 + 1, 77) , (143 + 1, 77), (63 + 1, 138))

        bodyShake = FrameAnimation(
#                range(160, 239), 35, (79, 66))
#                range(200, 239) + range(160, 200), 35, (79, 66))
                shiftedRange(160, 239, 50), 35, (79, 66))

        self.animations = [
                LoopAnimation(wagTail),
                leftWing, rightWing,
                LoopAnimation(bodyShake),
                LoopAnimation(SequenceAnimation([lookUpward, doNothing, lookForward, doNothing]))
                ]

        yPeriod = 300 * 25
        def yFloatFun(t):
            t1 = t * math.pi * 2 / yPeriod
            return translation(0, 15 * math.cos(t1))

        yFloat = TimeFunTransformer(yFloatFun, yPeriod)

        xPeriod = 500 * 25
        def xFloatFun(t):
            t1 = t * math.pi * 2 / xPeriod
            return translation(20 * math.cos(t1), 0)

        xFloat = TimeFunTransformer(xFloatFun, xPeriod)

        self.transformers = [yFloat, xFloat]

    def update(self, dt):
        for a in self.animations:
            a.update(dt)

        for t in self.transformers:
            t.update(dt)

    def state(self):
        return [frame for a in self.animations for frame in a.state()]

    def transforms(self):
        return [trans for t in self.transformers for trans in t.transforms()]

    def attachment(self, name):
        return {
            "mouth": (110, 85)
        }.get(name, None)

    def reset(self):
        for a in self.animations:
            a.reset()

        for t in self.transformers:
            t.reset()
