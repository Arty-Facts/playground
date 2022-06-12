import pygame, sys, numba
from numpy.linalg import norm
import numpy as np

def get_font(size): # Returns Press-Start-2P in the desired size
    return pygame.font.Font("assets/font.ttf", size)

def quit():
    pygame.quit()
    sys.exit(0)

@numba.jit(cache=True, nopython=True, nogil=True)
def update_boid(array, max_radius, min_radius, avg_radius, wrap, maxW, maxH, margin, dt, speed, point=None, attract=False):
    for data in array:
        turnDir = 0
        turnRate = 120 * dt 
        x, y = data[:2]
        ang = data[2]
        
        array_dists = (x - array[:,0])**2 + (y - array[:,1])**2
        closeBoidIs = np.argsort(array_dists)[1:8]

        neiboids = array[closeBoidIs]
        neiboids[:,3] = np.sqrt(array_dists[closeBoidIs])
        neiboids = neiboids[neiboids[:,3] < max_radius]
        if point is not None and attract:
            neiboids = point
            neiboids[0,2] = ang
            neiboids[0,3] = (x - neiboids[0,0])**2 + (y - neiboids[0,1])**2
        # print(x, y, ang, neiboids)

        if neiboids.size > 1:  # if has neighborS, do math and sim rules
            # averages the positions and angles of neighbors
            tAvejAng = np.mean(neiboids[:,2])
            targetV = np.array((np.mean(neiboids[:,0]), np.mean(neiboids[:,1])), dtype=np.float64)
            # if too close, move away from closest neighbor
            if neiboids[0,3] < min_radius : 
                targetV = neiboids[0,:2]
            # get angle differences for steering
            tDistance = norm(targetV - data[:2])
            tAngle = np.rad2deg(np.cos(targetV[0]/norm(targetV)))

            # if boid is close enough to neighbors, match their average angle
            if tDistance < avg_radius : 
                tAngle = tAvejAng
            # computes the difference to reach target angle, for smooth steering
            angleDiff = (tAngle - ang) + 180
            if abs(tAngle - ang) > 1.2: 
                turnDir = (angleDiff / 360 - (angleDiff // 360)) * 360 - 180
            # if boid gets too close to target, steer away
            if tDistance < min_radius: 
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
        dir =  np.array((np.cos(ang * np.pi / 180.), np.sin(ang * np.pi / 180.)), dtype=np.float64)
        # output pos to array
        data[:2] += dir * dt * (speed + (7 - neiboids.size) * 2)  # movement speed

        # Optional screen wrap
        if not wrap:
            if data[1] < 0 : 
                data[1] = maxH
            elif data[1] > maxH : 
                data[1] = 0
            if data[0] < 0 : 
                data[0]= maxW
            elif data[0] > maxW : 
                data[0]= 0

        # Finally, output ang to array
        data[2] = ang