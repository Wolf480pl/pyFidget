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

class IAnimation():
    def update(self, dt):
        """forwards the animation given time in miliseconds"""
    def state(self):
        """
        returns what should be drawn, (destPoint, frameNumber, p1, p2)
        p1, p2 are optional points that, together with destPoint, make a parallelogram,
        to which the frame will be stretched (scaled and/or tilted)
        """
    def reset(self):
        "resets the animation"

class ISingleAnimation(IAnimation):
    def timeLeft(self):
        "time left to finish, <= 0 when finished"


class FrameAnimation(ISingleAnimation):
    def __init__(self, framesRange, frameTime, destPoint, p1=None, p2=None):
        self.frames = framesRange
        self.length = len(self.frames)
        self.fTime  = frameTime
        self.point  = destPoint
        self.count  = 0
        self.time   = 0.0
        self.p1     = p1
        self.p2     = p2

    def update(self, dt):
        k = min(self.length - self.count - 1, int ((self.time + dt) / self.fTime))
        self.time   = (self.time + dt) - k * self.fTime
        self.count  = self.count + k

    def state(self):
        return [(self.point, self.frames[self.count], self.p1, self.p2)]

    def reset(self):
        self.time, self.count = 0.0, 0

    def timeLeft(self):
        return (self.length - self.count) * self.fTime - self.time


class SequenceAnimation(ISingleAnimation):
    def __init__(self, animations):
        for a in animations:
            assert(isinstance(a, ISingleAnimation))

        self.animations = animations
        self.count      = 0
        self.length     = len(animations)

    def update(self, dt):
        t = max(0, dt - self.animations[self.count].timeLeft())
        self.animations[self.count].update(dt)
        if self.animations[self.count].timeLeft() <= 0:
            if self.count < self.length - 1:
                self.animations[self.count].reset()
                self.count += 1
                self.animations[self.count].update(t)

    def state(self):
        return self.animations[self.count].state()

    def reset(self):
        for a in self.animations:
            a.reset()
        self.count = 0

    def timeLeft(self):
        return sum(map(lambda i: self.animations[i].timeLeft(), range(self.count, self.length)))


class LoopAnimation(IAnimation):
    def __init__(self, animation):
        assert(isinstance(animation, ISingleAnimation))
        self.animation = animation

    def update(self, dt):
        t = max(0, dt - self.animation.timeLeft())
        self.animation.update(dt)
        if self.animation.timeLeft() <= 0:
            self.animation.reset()
            self.animation.update(t)

    def state(self):
        return self.animation.state()

    def reset(self):
        self.animation.reset()


class ReverseAnimation(ISingleAnimation):
    pass


def shiftedRange(start, end, shift):
    return range(start + shift, end) + range(start, start + shift)
