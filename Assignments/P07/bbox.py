import math
import pygame as pg
import quadTree as qt
import random as rd
import sys

WIDTH = 640
HEIGHT = 480


class quadDriver(object):
    def __init__(self, **kwargs):
        self.width = WIDTH
        self.height = HEIGHT
        self.ptcolor = (251, 178, 145)  # a nice peachy color
        self.hilite = (172, 80, 225)
        self.reccolor = (87, 208, 111)
        self.ptrad = 3
        self.prime = kwargs.get("prime", 0)

        self.bbox = pg.Rect((0, 0), (self.width, self.height))
        self.qbbox = qt.Rect(WIDTH/2, HEIGHT/2, WIDTH, HEIGHT)
        self.tree = qt.QuadTree(self.qbbox, 1, 0)

        self.pid = 0
        self.pts = []
        self.recs = []

        if self.prime > 0:
            self.initPts(self.prime)

    def initPts(self, pts):
        while self.pid < pts:
            x = rd.randint(0, self.width)
            y = rd.randint(0, self.height)
            pt = qt.Point(x, y, id=self.pid, color=self.ptcolor,
                          radius=self.ptrad, hili=False)
            self.tree.insert(pt)
            self.pts.append(pt)
            self.pid += 1

    def getPts(self):
        return self.pts

    def getRecs(self):
        return self.recs


class GDrive(object):

    def __init__(self, **kwargs):
        self.prime = kwargs.get("prime", 0)
        self.screen = kwargs.get("screen", [660, 500])

        self.events = {
            "data": {},
            "keysPressed": {}
        }
        self.pressed = {}

        self.quad = quadDriver(prime=self.prime)

    def captureEvents(self):
        for event in pg.event.get():

            if event.type == pg.QUIT:
                self.events["quit"] = True

            if event.type == pg.KEYDOWN:
                mods = pg.key.get_mods()
                press = pg.key.get_pressed()

                for i in range(len(press)):
                    if press[i]:
                        self.events["keysPressed"][i] = True

                if mods:
                    self.events["keysPressed"][i] = True

                self.events["keydown"] = event.key

            if event.type == pg.KEYUP:
                self.events["keyup"] = event.key
                self.events["keysPressed"] = {}

            if event.type == pg.MOUSEBUTTONDOWN:
                self.events["mousedown"] = True
                if event.button == 1:
                    if 511 in self.events["keysPressed"]:
                        self.events["data"]["startPos"] = pg.mouse.get_pos()

            if event.type == pg.MOUSEBUTTONUP:
                self.events["mouseup"] = True
                if event.button == 1:
                    self.events["data"]["clickPos"] = pg.mouse.get_pos()
                    if 511 in self.events["keysPressed"]:
                        self.events["data"]["endPos"] = pg.mouse.get_pos()

            if event.type == pg.MOUSEMOTION:
                self.events["data"]["clickMove"] = pg.mouse.get_pos()
        return self.events

    def updateLogic(self, events):
        if "data" in events:
            if "startPos" in self.events["data"] \
                    and "endPos" in self.events["data"]:
                x1, y1 = self.events["data"]["startPos"]
                x2, y2 = self.events["data"]["endPos"]
                lf = max(min(x1, x2), 0)
                tp = max(min(y1, y2), 0)
                w = abs(x1-x2)
                h = abs(y1-y2)
                self.quad.recs.append(pg.Rect(lf, tp, w, h))
                del self.events["data"]["startPos"]
                del self.events["data"]["endPos"]
            if 32 in self.events["keysPressed"]:
                self.scanrec = pg.Rect(0, 0, 64, 64)
                self.qscan = qt.Rect(32, 32, 64, 64)
        pts = self.quad.getPts()
        for pt in pts:
            pt.hili = False
        try:
            self.scanrec
        except AttributeError:
            pass
        else:
            self.scanrec.move_ip(1, 0)
            if self.scanrec.bottom > HEIGHT:
                del self.scanrec
                del self.qscan
            elif self.scanrec.right > WIDTH:
                self.scanrec.left = 0
                self.scanrec.top += 64
            self.qscan = qt.Rect(self.scanrec.centerx,
                                 self.scanrec.centery,
                                 64, 64)
            for pt in pts:
                # if self.scanrec.collidepoint(pt.x,pt.y):
                if self.qscan.contains(pt):
                    pt.hili = True
        recs = self.quad.getRecs()
        for rec in recs:
            qrec = qt.Rect((rec.left+rec.right)/2, (rec.top+rec.bottom)/2,
                           rec.width, rec.height)
            for pt in pts:
                # if rec.collidepoint(pt.x,pt.y):
                if qrec.contains(pt):
                    pt.hili = True
        for pt in pts:
            if pt.hili:
                pt.color = self.quad.hilite
            else:
                pt.color = self.quad.ptcolor

    def displayFrame(self):
        self.screen.fill((0, 0, 0))
        self.drawPt()
        self.drawRec()
        self.drawScanner()
        pg.display.flip()

    def drawPt(self):
        pts = self.quad.getPts()
        for pt in pts:
            pg.draw.circle(self.screen, pt.color, [pt.x, pt.y], pt.radius)

    def drawRec(self):
        recs = self.quad.getRecs()
        for rec in recs:
            rL = pg.Rect(rec.left, rec.top, 1, abs(rec.bottom-rec.top))
            rR = pg.Rect(rec.right, rec.top, 1, abs(rec.bottom-rec.top))
            rT = pg.Rect(rec.left, rec.top, abs(rec.right-rec.left), 1)
            rB = pg.Rect(rec.left, rec.bottom, abs(rec.right-rec.left), 1)
            pg.draw.rect(self.screen, self.quad.reccolor, rL)
            pg.draw.rect(self.screen, self.quad.reccolor, rR)
            pg.draw.rect(self.screen, self.quad.reccolor, rT)
            pg.draw.rect(self.screen, self.quad.reccolor, rB)

    def drawScanner(self):
        try:
            rec = self.scanrec
        except AttributeError:
            pass
        else:
            rL = pg.Rect(rec.left, rec.top, 1, abs(rec.bottom-rec.top))
            rR = pg.Rect(rec.right, rec.top, 1, abs(rec.bottom-rec.top))
            rT = pg.Rect(rec.left, rec.top, abs(rec.right-rec.left), 1)
            rB = pg.Rect(rec.left, rec.bottom, abs(rec.right-rec.left), 1)
            pg.draw.rect(self.screen, (156, 158, 240), rL)
            pg.draw.rect(self.screen, (156, 158, 240), rR)
            pg.draw.rect(self.screen, (156, 158, 240), rT)
            pg.draw.rect(self.screen, (156, 158, 240), rB)


def main():
    pg.init()
    size = [WIDTH, HEIGHT]
    prime = math.floor((WIDTH/100)*(HEIGHT/100)*2.5)
    screen = pg.display.set_mode(size)

    pg.display.set_caption("QuadTree Query")
    pg.mouse.set_visible(True)
    keepLooping = True
    clock = pg.time.Clock()

    driver = GDrive(screen=screen, prime=prime)

    while keepLooping:
        events = driver.captureEvents()

        if "quit" in events:
            break
        driver.updateLogic(events)
        driver.displayFrame()
        clock.tick(60)

    pg.quit()


if __name__ == "__main__":
    main()
