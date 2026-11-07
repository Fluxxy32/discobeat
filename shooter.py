#imports
import pygame
from sys import exit
import math
from settings import *
import random

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Disco Floor")

clock = pygame.time.Clock()

def disco_floor(seconds_per_beat, rows, cols, tile_size):
    # Initial tile colors
 tiles = [
    [random.choice(colors) for _ in range(cols)]
    for _ in range(rows)
 ]

 change_timer = 0

 running = True

 while running:

    dt = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    change_timer += dt

    if change_timer >= seconds_per_beat:
        change_timer = 0

        for row in range(rows):
            for col in range(cols):
                tiles[row][col] = random.choice(colors)

    # Draw floor
    screen.fill((10, 10, 10))

    for row in range(rows):
        for col in range(cols):

            x = col * tile_size
            y = row * tile_size

            # Draw tile
            pygame.draw.rect(
                screen,
                tiles[row][col],
                (x + 3, y + 3, tile_size - 6, tile_size - 6)
            )

    pygame.display.flip()

def main():
    pygame.init()
    #setting up the window
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    pygame.display.set_caption('DISCOBEAT')
    clock = pygame.time.Clock()
    disco_floor(400, ROWS, COLS, TILESIZE)
        
    clock.tick(FPS)

if __name__ == "__main__":
  main()
