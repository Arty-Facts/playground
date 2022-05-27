import pygame
from random import randint
import numpy as np
from lib.button import Button
from lib.utils import get_font          


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
        self.bSize = 22 if isFish else 17
        self.orig_image = pygame.transform.rotate(self.image.copy(), -90)
        self.dir = pygame.Vector2(1, 0)  # sets up forward direction
        maxW, maxH = self.drawSurf.get_size()
        self.rect = self.image.get_rect(center=(randint(50, maxW - 50), randint(50, maxH - 50)))
        self.ang = randint(0, 360)  # random start angle, & position ^
        self.pos = pygame.Vector2(self.rect.center)
        
    def update(self, dt, speed, ejWrap=False):
        maxW, maxH = self.drawSurf.get_size()
        turnDir = xvt = yvt = yat = xat = 0
        turnRate = 120 * dt  # about 120 seems ok
        margin = 42
        array_dists = (self.pos.x - self.data.array[:,0])**2 + (self.pos.y - self.data.array[:,1])**2
        closeBoidIs = np.argsort(array_dists)[1:8]
        neiboids = self.data.array[closeBoidIs]
        neiboids[:,3] = np.sqrt(array_dists[closeBoidIs])
        neiboids = neiboids[neiboids[:,3] < self.bSize*12]
        if neiboids.size > 1:  # if has neighborS, do math and sim rules
            yat = np.sum(np.sin(np.deg2rad(neiboids[:,2])))
            xat = np.sum(np.cos(np.deg2rad(neiboids[:,2])))
            # averages the positions and angles of neighbors
            tAvejAng = np.rad2deg(np.arctan2(yat, xat))
            targetV = (np.mean(neiboids[:,0]), np.mean(neiboids[:,1]))
            # if too close, move away from closest neighbor
            if neiboids[0,3] < self.bSize : 
                targetV = (neiboids[0,0], neiboids[0,1])
            # get angle differences for steering
            tDiff = pygame.Vector2(targetV) - self.pos
            tDistance, tAngle = pygame.math.Vector2.as_polar(tDiff)
            # if boid is close enough to neighbors, match their average angle
            if tDistance < self.bSize*6 : 
                tAngle = tAvejAng
            # computes the difference to reach target angle, for smooth steering
            angleDiff = (tAngle - self.ang) + 180
            if abs(tAngle - self.ang) > 1.2: 
                turnDir = (angleDiff / 360 - (angleDiff // 360)) * 360 - 180
            # if boid gets too close to target, steer away
            if tDistance < self.bSize and targetV == (neiboids[0,0], neiboids[0,1]) : 
                turnDir = -turnDir
        # Avoid edges of screen by turning toward the edge normal-angle
        if not ejWrap and min(self.pos.x, self.pos.y, maxW - self.pos.x, maxH - self.pos.y) < margin:
            if self.pos.x < margin : 
                tAngle = 0
            elif self.pos.x > maxW - margin : 
                tAngle = 180
            if self.pos.y < margin : 
                tAngle = 90
            elif self.pos.y > maxH - margin : 
                tAngle = 270
            angleDiff = (tAngle - self.ang) + 180  # if in margin, increase turnRate to ensure stays on screen
            turnDir = (angleDiff / 360 - (angleDiff // 360)) * 360 - 180
            edgeDist = min(self.pos.x, self.pos.y, maxW - self.pos.x, maxH - self.pos.y)
            turnRate = turnRate + (1 - edgeDist / margin) * (20 - turnRate) #minRate+(1-dist/margin)*(maxRate-minRate)
        if turnDir != 0:  # steers based on turnDir, handles left or right
            self.ang += turnRate * abs(turnDir) / turnDir
            self.ang %= 360  # ensures that the angle stays within 0-360
        # Adjusts angle of boid image to match heading
        self.image = pygame.transform.rotate(self.orig_image, -self.ang)
        self.rect = self.image.get_rect(center=self.rect.center)  # recentering fix
        self.dir = pygame.Vector2(1, 0).rotate(self.ang).normalize()
        self.pos += self.dir * dt * (speed + (7 - neiboids.size) * 2)  # movement speed
        # Optional screen wrap
        if ejWrap and not self.drawSurf.get_rect().contains(self.rect):
            if self.rect.bottom < 0 : 
                self.pos.y = maxH
            elif self.rect.top > maxH : 
                self.pos.y = 0
            if self.rect.right < 0 : 
                self.pos.x = maxW
            elif self.rect.left > maxW : 
                self.pos.x = 0
        # Actually update position of boid
        self.rect.center = self.pos
        # Finally, output pos/ang to array
        self.data.array[self.bnum,:3] = [self.pos[0], self.pos[1], self.ang]

class BoidArray():  # Holds array to store positions and angles
    def __init__(self, size):
        self.array = np.zeros((size, 4), dtype=float)

def game(size=(1280, 720), fullscreen=True, FPS=60, showFPS=True, speed = 150,  fish = 150):
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
    dataArray = BoidArray(fish)
    for id in range(fish):
        nBoids.add(Boid(id, dataArray, screen))  # spawns desired # of boidz

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
        nBoids.update(dt, speed, True)
        nBoids.draw(screen)
            
        if showFPS: 
            screen.blit(get_font(30).render(str(int(clock.get_fps())), True, [0,200,0]), (8, 8))

        pygame.display.update()

if __name__ == "__main__":
    pygame.init()
    print(game())
    pygame.quit()