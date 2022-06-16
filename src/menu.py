#!/usr/bin/python3
import pygame
from lib.button import Button
from lib.utils import get_font
 
 
def main_menu(size=(1280, 720)):
    pygame.display.set_caption("Menu")
    screen = pygame.display.set_mode(size)
    background = pygame.image.load("assets/Background.png")


    text = get_font(100).render("MAIN MENU", True, "#b68f40")
    rect = text.get_rect(center=(640, 100))

    play_bt = Button(image=pygame.image.load("assets/Play Rect.png"), pos=(640, 250), 
                        text_input="PLAY", font=get_font(75), base_color="#d7fcd4", hovering_color="White")
    options_bt = Button(image=pygame.image.load("assets/Options Rect.png"), pos=(640, 400), 
                        text_input="OPTIONS", font=get_font(75), base_color="#d7fcd4", hovering_color="White")
    quit_bt = Button(image=pygame.image.load("assets/Quit Rect.png"), pos=(640, 550), 
                        text_input="QUIT", font=get_font(75), base_color="#d7fcd4", hovering_color="White")
    while True:
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(background, (0, 0))
        screen.blit(text, rect)

        for button in [play_bt, options_bt, quit_bt]:
            button.changeColor(mouse_pos)
            button.update(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_bt.checkForInput(mouse_pos):
                    return "play"
                if options_bt.checkForInput(mouse_pos):
                    return "options"
                if quit_bt.checkForInput(mouse_pos):
                    return "quit"
        pygame.display.update()
 
if __name__ == "__main__":
    pygame.init()
    print(main_menu())
    pygame.quit()