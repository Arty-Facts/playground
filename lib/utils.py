import pygame, sys, numba
from numpy.linalg import norm
import numpy as np
from random import random

def get_font(size): # Returns Press-Start-2P in the desired size
    return pygame.font.Font("assets/font.ttf", size)

def quit():
    pygame.quit()
    sys.exit(0)

@numba.njit(cache=True, nogil=True)
def find_neiboids(array, x, y, max_radius):
    array_dists = (x - array[:,0])**2 + (y - array[:,1])**2
    closeBoidIs = np.argsort(array_dists)[1:10]

    neiboids = array[closeBoidIs]
    neiboids[:,3] = np.sqrt(array_dists[closeBoidIs])
    return neiboids[neiboids[:,3] < max_radius]

@numba.njit(cache=True, nogil=True)
def avg_neiboids_stats(neiboids):
    ang = np.mean(neiboids[:,2])
    pos = np.array((np.mean(neiboids[:,0]), np.mean(neiboids[:,1])), dtype=np.float64)
    return ang, pos

@numba.njit(cache=True, nogil=True)
def target_stats(pos, target, ang):
    vec = target - pos
    dist = norm(vec)
    if dist > 0:
        if vec[1] < 0:
            target_ang = 2*np.pi - np.arccos(vec[0]/dist) - np.pi - ang
        else:
            target_ang = np.arccos(vec[0]/dist) + np.pi - ang
        if target_ang < -np.pi:
            target_ang += 2 * np.pi
        elif target_ang > np.pi:
            target_ang -= 2 * np.pi
    else: 
        target_ang = 0
    return target_ang, dist

@numba.njit(cache=True, nogil=True)
def screen_wrap(pos, max_h, max_w):
    if pos[1] < 0 : 
        pos[1] = max_h
    elif pos[1] > max_h : 
        pos[1] = 0
    if pos[0] < 0 : 
        pos[0]= max_w
    elif pos[0] > max_w : 
        pos[0]= 0

@numba.njit(cache=True, nogil=True)
def update_speed(turn_rate, dist, margin, dt):
    return turn_rate + (1 - dist / margin) * (np.pi * dt - turn_rate) #minRate+(1-dist/margin)*(maxRate-minRate)

@numba.njit(cache=True, nogil=True)
def one_update(array, data, max_radius, min_radius, avg_radius, wrap, max_w, max_h, margin, dt, speed, turn_rate):
    target_ang = None
    x, y = data[:2]
    ang = data[2]
    neiboids = find_neiboids(array, x, y, max_radius)

    if neiboids.size > 1:  # if has neighborS, do math and sim rules
        # averages the positions and angles of neighbors
        avg_ang, avg_pos = avg_neiboids_stats(neiboids)

        # if too close, move away from closest neighbor
        if neiboids[0,3] < min_radius : 
            target_ang , target_dist =  target_stats(data[:2], neiboids[0,:2], ang)
            turn_rate = update_speed(turn_rate, target_dist,  min_radius,  dt)
        else:
            target_ang, target_dist = target_stats(avg_pos, data[:2], ang)
            # get angle differences for steering and the distence

            # if boid is close enough to neighbors, match their average angle
            if target_dist < avg_radius : 
                target_ang = avg_ang - ang
    # Avoid edges of screen by turning toward the edge normal-angle
    if wrap and min(x, y, max_w - x, max_h - y) < margin:
        target_ang, _ = target_stats(np.array((max_w/2, max_h/2), dtype=np.float64), data[:2], ang)
        edge_dist = min(x, y, max_w - x, max_h - y, 0)
        turn_rate = update_speed(turn_rate, edge_dist, margin,  dt)

    if target_ang is not None: 
        # turn only if the angle is large enough
        if abs(target_ang) > 0:
            ang = next_ang(ang, turn_rate, target_ang)
    
    # output pos to array
    data[:2] += next_step(ang, speed, neiboids.size + 1, dt)
    # Optional screen wrap
    if not wrap:
        screen_wrap(data, max_h, max_w)

    # Finally, output ang to array
    data[2] = ang

@numba.jit(cache=True, nopython=True, nogil=True)
def next_step(ang, speed, friends, dt):
    # Adjusts angle of boid image to match heading
    dir =  np.array((np.cos(ang), np.sin(ang)), dtype=np.float64)
    # output pos to array
    return dir * dt * (speed + (random() * speed / 5) +  (10/friends))  # movement speed

@numba.jit(cache=True, nopython=True, nogil=True)
def next_ang(ang, turn_rate, target_ang):
    ang += turn_rate * abs(target_ang) / target_ang
    ang %= 2*np.pi  # ensures that the angle stays within 0-2*pi
    return ang

@numba.jit(cache=True, nopython=True, nogil=True)
def get_turn_rate(dt):
    return np.pi * 0.6 * dt 

@numba.jit(cache=True, nopython=True, nogil=True)
def update_boid(array, max_radius, min_radius, avg_radius, wrap, max_w, max_h, margin, dt, speed):
    turn_rate = get_turn_rate(dt)
    for data in array:
        one_update(array, data, max_radius, min_radius, avg_radius, wrap, max_w, max_h, margin, dt, speed, turn_rate)

@numba.jit(cache=True, nopython=True, nogil=True)
def update_interaction(array, dt, point, attract, max_dist=-1):
    turn_rate = get_turn_rate(dt) 
    for data in array:
        target_ang = None
        ang = data[2]

        if attract:
            target_ang, target_dist =  target_stats(point, data[:2], ang)
        else:
            target_ang, target_dist =  target_stats(data[:2], point, ang)
        
        # skip if no update is needed
        if abs(target_ang) == 0 or max_dist >= 0 and target_dist > max_dist:
            continue
        
        # uppdate the angle for next iteration 
        if max_dist > 0 and target_dist > 1:
            turn_rate *= 1 + 1/target_dist *10
        data[2] = next_ang(ang, turn_rate, target_ang)
    
@numba.jit(cache=True, nopython=True, nogil=True)
def update_all(array, max_rad, min_rad, avg_rad, wrap, maxW, maxH, margin, dt, speed, left, rigth, pos):
    update_boid(array, max_rad, min_rad, avg_rad, wrap, maxW, maxH, margin, dt, speed)
    if left:
        update_interaction(array, dt, pos, True, -1)
    elif rigth:
        update_interaction(array, dt, pos, False, max_rad)


