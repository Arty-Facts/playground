#!/usr/bin/env python3
import pygame
from menu import main_menu
from game import game
from options import options

FPS = 60
SHOWFPS = True

def main():
    pygame.init()  # prepare window
    pygame.display.set_caption("Game")
    try: 
        pygame.display.set_icon(pygame.image.load("assets/icon.svg"))
    except: 
        print("FYI: con.svg icon not found, skipping..")
    
    clock = pygame.time.Clock()
    clock.tick(FPS)
    actions = {
        "back": main_menu,
        "menu": main_menu,
        "play": game,
        "options": options, 
        "quit" :quit
        }

    action = "menu"
    # main loop
    while True:
        action = actions[action]()


if __name__ == '__main__':
    main()  