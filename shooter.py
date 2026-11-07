#imports
import pygame
from sys import exit
import math
from settings import *
import random

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.image = pygame.image.load(
            "/home/daniil/CS1/discobeat/discobeat/assets/0.png"
        ).convert_alpha()

        self.pos = pygame.math.Vector2(PLAYER_START_X, PLAYER_START_Y)
        self.rect = self.image.get_rect(center=self.pos)
        self.speed = PLAYER_SPEED

    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_s]:
            self.rect.y += self.speed
        if keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_d]:
            self.rect.x += self.speed

def disco_floor(screen, tiles, rows, cols, tile_size):
    for row in range(rows):
        for col in range(cols):
            x = col * tile_size
            y = row * tile_size

            pygame.draw.rect(
                screen,
                tiles[row][col],
                (x + 3, y + 3, tile_size - 6, tile_size - 6)
            )

def generate_floor(rows, cols):
    tiles = [
        [random.choice(colors) for _ in range(cols)]
        for _ in range(rows)
    ]
    return tiles

def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DISCOBEAT")
    clock = pygame.time.Clock()

    player = Player()
    tiles = generate_floor(ROWS, COLS)
    change_timer = 0

    while True:
        #quitting the game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        #timer
        dt = clock.tick(FPS)
        change_timer += dt

        if change_timer >= 400:
            change_timer = 0

            for row in range(ROWS):
                for col in range(COLS):
                    tiles[row][col] = random.choice(colors)

        player.update()

        #drawing on the screen
        screen.fill((10, 10, 10))
        disco_floor(screen, tiles, ROWS, COLS, TILESIZE)
        screen.blit(player.image, player.rect)

        pygame.display.flip()

if __name__ == "__main__":
  main()
