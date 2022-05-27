import pygame, sys

def get_font(size): # Returns Press-Start-2P in the desired size
    return pygame.font.Font("assets/font.ttf", size)

def quit():
    pygame.quit()
    sys.exit(0)
