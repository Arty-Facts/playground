import pygame

from lib.button import Button
from lib.utils import get_font    
from lib.boid import BoidSim

def game(size=(1280, 720), fullscreen=True, FPS=60, showFPS=True, speed = 170,  fish = 100):
    pygame.display.set_caption("Game")
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else: 
        screen = pygame.display.set_mode(size, pygame.RESIZABLE)
    screen.fill("black")

    size_x, size_y = pygame.display.get_window_size()
    text = get_font(45).render("Loading...", True, "White")

    rect = text.get_rect(center=(size_x/2, size_y/2))
    back_bt = Button(image=None, pos=(size_x-75*3, size_y-75), 
                        text_input="BACK", font=get_font(75), base_color="White", hovering_color="Green")
    
    screen.blit(text, rect)
    pygame.display.update()
    clock = pygame.time.Clock()

    boidSim = BoidSim(fish, screen)

    while True:
        mouse_pos = pygame.mouse.get_pos()

        screen.fill("black")

        back_bt.changeColor(mouse_pos)
        back_bt.update(screen)

        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_bt.checkForInput(mouse_pos):
                    return "back"
        boidSim.update(dt, speed)
            
        if showFPS: 
            screen.blit(get_font(30).render(str(int(clock.get_fps())), True, [0,200,0]), (8, 8))

        pygame.display.update()

if __name__ == "__main__":
    pygame.init()
    print(game())
    pygame.quit()