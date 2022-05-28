import pygame
from random import randint
import numpy as np
from numpy.linalg import norm
import numba
from lib.button import Button
from lib.utils import get_font    

@numba.jit(cache=True, nopython=True, parallel=False, nogil=True)
def get_next_ang(array, pos, bSize, turnRate, turnDir, ang, maxW, maxH, margin, ejWrap):
    x, y = pos
    array_dists = (x - array[:,0])**2 + (y - array[:,1])**2
    closeBoidIs = np.argsort(array_dists)[1:8]
    neiboids = array[closeBoidIs]
    neiboids[:,3] = np.sqrt(array_dists[closeBoidIs])
    neiboids = neiboids[neiboids[:,3] < bSize*12]
    if neiboids.size > 1:  # if has neighborS, do math and sim rules
        yat = np.sum(np.sin(np.deg2rad(neiboids[:,2])))
        xat = np.sum(np.cos(np.deg2rad(neiboids[:,2])))
        # averages the positions and angles of neighbors
        tAvejAng = np.rad2deg(np.arctan2(yat, xat))
        targetV = np.array((np.mean(neiboids[:,0]), np.mean(neiboids[:,1])), dtype=np.float64)
        # if too close, move away from closest neighbor
        if neiboids[0,3] < bSize : 
            targetV = neiboids[0,0:2]
        # get angle differences for steering
        df = targetV - pos
        tAngle = np.arctan2(df[1], df[0])
        tDistance = np.hypot(df[0], df[1])
        # if boid is close enough to neighbors, match their average angle
        if tDistance < bSize*6 : 
            tAngle = tAvejAng
        # computes the difference to reach target angle, for smooth steering
        angleDiff = (tAngle - ang) + 180
        if abs(tAngle - ang) > 1.2: 
            turnDir = (angleDiff / 360 - (angleDiff // 360)) * 360 - 180
        # if boid gets too close to target, steer away
        if tDistance < bSize and norm(targetV - neiboids[0,0:2]) < bSize: 
            turnDir = -turnDir

    # Avoid edges of screen by turning toward the edge normal-angle
    if not ejWrap and min(x, y, maxW - x, maxH - y) < margin:
        if x < margin : 
            tAngle = 0
        elif x > maxW - margin : 
            tAngle = 180
        if y < margin : 
            tAngle = 90
        elif y > maxH - margin : 
            tAngle = 270
        angleDiff = (tAngle - ang) + 180  # if in margin, increase turnRate to ensure stays on screen
        turnDir = (angleDiff / 360 - (angleDiff // 360)) * 360 - 180
        edgeDist = min(x, y, maxW - x, maxH - y)
        turnRate = turnRate + (1 - edgeDist / margin) * (20 - turnRate) #minRate+(1-dist/margin)*(maxRate-minRate)

    if turnDir != 0:  # steers based on turnDir, handles left or right
        ang += turnRate * abs(turnDir) / turnDir
        ang %= 360  # ensures that the angle stays within 0-360
    return ang, neiboids.size

class Boid(pygame.sprite.Sprite):
    """
    This code is taken from Boids simulation - github.com/Nikorasu/PyNBoids
    """
    def __init__(self, boidNum, data, drawSurf, isFish=True, cHSV=None):
        super().__init__()
        self.data = data
        self.bnum = boidNum
        self.drawSurf = drawSurf
        self.image = pygame.Surface((15, 15)).convert()
        self.image.set_colorkey(0)
        self.color = pygame.Color(0)  # preps color so we can use hsva
        self.color.hsva = (randint(0,360), 90, 90) if cHSV is None else cHSV # randint(5,55) #4goldfish
        if isFish:  # (randint(120,300) + 180) % 360  #4noblues
            pygame.draw.polygon(self.image, self.color, ((7,0),(12,5),(3,14),(11,14),(2,5),(7,0)), width=3)
            self.image = pygame.transform.scale(self.image, (16, 24))
        else: 
            pygame.draw.polygon(self.image, self.color, ((7,0), (13,14), (7,11), (1,14), (7,0)))
        self.bSize = 22 
        self.orig_image = pygame.transform.rotate(self.image.copy(), -90)
        self.dir = np.array((1, 0), dtype=np.float64)  # sets up forward direction
        maxW, maxH = self.drawSurf.get_size()
        self.rect = self.image.get_rect(center=(randint(50, maxW - 50), randint(50, maxH - 50)))
        self.ang = randint(0, 360)  # random start angle, & position ^
        self.pos = np.array((self.rect.center), dtype=np.float64)
    
    def update(self, dt, speed, ejWrap=False):
        maxW, maxH = self.drawSurf.get_size()
        x, y = self.pos
        turnDir = xvt = yvt = yat = xat = 0
        turnRate = 120 * dt  # about 120 seems ok
        margin = 42
        self.ang, size = get_next_ang(self.data.array, self.pos, self.bSize, turnRate,turnDir, self.ang, maxW, maxH, margin, ejWrap)

        self.image = pygame.transform.rotate(self.orig_image, -self.ang)
        self.rect = self.image.get_rect(center=self.rect.center)  # recentering fix
        self.dir = pygame.Vector2(1, 0).rotate(self.ang).normalize()
        self.pos += self.dir * dt * (speed + (7 - size) * 2)  # movement speed
        # Optional screen wrap
        if ejWrap and not self.drawSurf.get_rect().contains(self.rect):
            if self.rect.bottom < 0 : 
                self.pos[1] = maxH
            elif self.rect.top > maxH : 
                self.pos[1] = 0
            if self.rect.right < 0 : 
                self.pos[0]= maxW
            elif self.rect.left > maxW : 
                self.pos[0]= 0
        # Actually update position of boid
        self.rect.center = self.pos
        # Finally, output pos/ang to array
        self.data.array[self.bnum,:3] = [self.pos[0], self.pos[1], self.ang]



@numba.jit(cache=True, nopython=True, parallel=False, nogil=True)
def update_boid(array, max_radius, min_radius, avg_radius, wrap, maxW, maxH, margin, dt, speed):
    for id, data in enumerate(array):
        turnDir = yat = xat = 0
        turnRate = 120 * dt 
        x, y = data[id, :2]
        ang = data[id, 2]
        array_dists = (x - array[:,0])**2 + (y - array[:,1])**2
        closeBoidIs = np.argsort(array_dists)[1:8]
        neiboids = array[closeBoidIs]
        neiboids[:,3] = np.sqrt(array_dists[closeBoidIs])
        neiboids = neiboids[neiboids[:,3] < max_radius]
        if neiboids.size > 1:  # if has neighborS, do math and sim rules
            yat = np.sum(np.sin(np.deg2rad(neiboids[:,2])))
            xat = np.sum(np.cos(np.deg2rad(neiboids[:,2])))
            # averages the positions and angles of neighbors
            tAvejAng = np.rad2deg(np.arctan2(yat, xat))
            targetV = np.array((np.mean(neiboids[:,0]), np.mean(neiboids[:,1])), dtype=np.float64)
            # if too close, move away from closest neighbor
            if neiboids[0,3] < min_radius : 
                targetV = neiboids[0,:2]
            # get angle differences for steering
            df = targetV - data[id, :2]
            tAngle = np.arctan2(df[1], df[0])
            tDistance = np.hypot(df[0], df[1])
            # if boid is close enough to neighbors, match their average angle
            if tDistance < avg_radius : 
                tAngle = tAvejAng
            # computes the difference to reach target angle, for smooth steering
            angleDiff = (tAngle - ang) + 180
            if abs(tAngle - ang) > 1.2: 
                turnDir = (angleDiff / 360 - (angleDiff // 360)) * 360 - 180
            # if boid gets too close to target, steer away
            if tDistance < min_radius and norm(targetV - neiboids[0,0:2]) < min_radius: 
                turnDir = -turnDir

        # Avoid edges of screen by turning toward the edge normal-angle
        if wrap and min(x, y, maxW - x, maxH - y) < margin:
            if x < margin : 
                tAngle = 0
            elif x > maxW - margin : 
                tAngle = 180
            if y < margin : 
                tAngle = 90
            elif y > maxH - margin : 
                tAngle = 270
            angleDiff = (tAngle - ang) + 180  # if in margin, increase turnRate to ensure stays on screen
            turnDir = (angleDiff / 360 - (angleDiff // 360)) * 360 - 180
            edgeDist = min(x, y, maxW - x, maxH - y)
            turnRate = turnRate + (1 - edgeDist / margin) * (20 - turnRate) #minRate+(1-dist/margin)*(maxRate-minRate)

        if turnDir != 0:  # steers based on turnDir, handles left or right
            ang += turnRate * abs(turnDir) / turnDir
            ang %= 360  # ensures that the angle stays within 0-360
        
        # Adjusts angle of boid image to match heading
        dir = np.array(np.cos(ang), np.sin(ang), dtype=np.float64)
        data[id, :2] += dir * dt * (speed + (7 - neiboids.size) * 2)  # movement speed

        # Optional screen wrap
        if not wrap:
            if data[id, 1] < 0 : 
                data[id, 1] = maxH
            elif data[id, 1] > maxH : 
                data[id, 1] = 0
            if data[id, 0] < 0 : 
                data[id, 0]= maxW
            elif data[id, 0] > maxW : 
                data[id, 0]= 0

        # Finally, output pos/ang to array
        array[id,3] = ang


class BoidArray():  # Holds array to store positions and angles
    def __init__(self, size, bSize, wrap, maxW, maxH, margin):
        self.array = np.zeros((size, 4), dtype=np.float64)
        self.bSize = bSize
        self.wrap = wrap
        self.maxW = maxW
        self.maxH = maxH
        self.margin = margin

    def update(self, dt, speed):
        update_boid(self.array, self.bSize*12, self.bSize, self.bSize*6, self.wrap, self.maxW, self.maxH, self.margin, dt, speed)
        

BOID = Boid

def game(size=(1280, 720), fullscreen=True, FPS=60, showFPS=True, speed = 150,  fish = 500):
    pygame.display.set_caption("Game")
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else: 
        screen = pygame.display.set_mode(size, pygame.RESIZABLE)

    size_x, size_y = pygame.display.get_window_size()
    text = get_font(45).render("This is the PLAY screen.", True, "White")

    rect = text.get_rect(center=(640, 260))
    back_bt = Button(image=None, pos=(size_x-75*3, size_y-75), 
                        text_input="BACK", font=get_font(75), base_color="White", hovering_color="Green")
    
    clock = pygame.time.Clock()
    nBoids = pygame.sprite.Group()
    dataArray = BoidArray(fish, 22, False,  size_x, size_y, 42)
    for id in range(fish):
        nBoids.add(BOID(id, dataArray, screen))  # spawns desired # of boidz

    while True:
        mouse_pos = pygame.mouse.get_pos()

        screen.fill("black")

        screen.blit(text, rect)

        back_bt.changeColor(mouse_pos)
        back_bt.update(screen)

        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_bt.checkForInput(mouse_pos):
                    return "back"
        # dataArray.update(dt, speed)
        nBoids.update(dt, speed, False)
        nBoids.draw(screen)
            
        if showFPS: 
            screen.blit(get_font(30).render(str(int(clock.get_fps())), True, [0,200,0]), (8, 8))

        pygame.display.update()

if __name__ == "__main__":
    pygame.init()
    print(game())
    pygame.quit()