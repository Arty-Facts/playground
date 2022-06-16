import pygame
from lib.button import Button
from lib.utils import get_font

def options(size=(1280, 720)):
    pygame.display.set_caption("Options")
    screen = pygame.display.set_mode(size, pygame.RESIZABLE)
    text = get_font(45).render("This is the OPTIONS screen.", True, "Black")
    rect = text.get_rect(center=(640, 260))
    while True:
        mouse_pos = pygame.mouse.get_pos()

        screen.fill("white")

        screen.blit(text, rect)

        back_bt = Button(image=None, pos=(640, 460), 
                            text_input="BACK", font=get_font(75), base_color="Black", hovering_color="Green")

        back_bt.changeColor(mouse_pos)
        back_bt.update(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_bt.checkForInput(mouse_pos):
                    return "back"

        pygame.display.update()

if __name__ == "__main__":
    pygame.init()
    print(options())
    pygame.quit()