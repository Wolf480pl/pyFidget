import copy

def _frameRect(a, b):
    if b == 1:
        return None
    return (a*64, b*64, 64, 128 if b == 0 and (a < 16 or a > 32) else 64)

_frame = [_frameRect(a, b) for b in range(6) for a in range(40)]

def getFrameRect(n):
    return _frame[n]


class IAnimation():
    def update(self, dt):
        "forward animation given time in miliseconds"
    def state(self, dt):
        "returns what should be drawn, (destPoint, frameNumber)"
    def reset(self):
        "reset state"


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

class Fidget(IAnimation):
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
                shiftedRange(160, 239, 60), 35, (79, 66))

        print(wagTail.length)
        print(bodyShake.length)
        self.animations = [
                LoopAnimation(wagTail),
                leftWing, rightWing,
                LoopAnimation(bodyShake),
                LoopAnimation(SequenceAnimation([lookUpward, doNothing, lookForward, doNothing]))
                ]

    def update(self, dt):
        for a in self.animations:
            a.update(dt)

    def state(self):
        return [frame for a in self.animations for frame in a.state()]

    def reset(self):
        for a in self.animations:
            a.reset()
