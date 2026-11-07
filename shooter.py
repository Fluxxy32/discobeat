#imports
import pygame
from sys import exit
import math
from settings import *
import random

def main():
    pygame.init()

    #setting up the window
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    pygame.display.set_caption('DISCOBEAT')
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        #fill the screen with black
        screen.fill((0,0,0))

        #draw the disco floor
        for row in range(HEIGHT // TILESIZE):
            for col in range(WIDTH // TILESIZE):
                color = random.choice(colors)
                pygame.draw.rect(
                    screen,
                    color,
                    (col * TILESIZE, row * TILESIZE, TILESIZE, TILESIZE)
                )

        pygame.display.flip()
        clock.tick(FPS)


main()
