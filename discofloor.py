
import pygame
import random

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Disco Floor")

clock = pygame.time.Clock()

# Tile settings
TILE_SIZE = 50
COLS = WIDTH // TILE_SIZE
ROWS = HEIGHT // TILE_SIZE

# Disco colors
colors = [
    (255, 0, 100),    # Pink
    (0, 200, 255),    # Blue
    (150, 0, 255),    # Purple
    (0, 255, 100),    # Green
    (255, 200, 0),    # Yellow
    (255, 50, 0)      # Orange
]

# Initial tile colors
tiles = [
    [random.choice(colors) for _ in range(COLS)]
    for _ in range(ROWS)
]

change_timer = 0

running = True

while running:

    dt = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    change_timer += dt

    if change_timer >= 500:
        change_timer = 0

        for row in range(ROWS):
            for col in range(COLS):
                tiles[row][col] = random.choice(colors)

    # Draw floor
    screen.fill((10, 10, 10))

    for row in range(ROWS):
        for col in range(COLS):

            x = col * TILE_SIZE
            y = row * TILE_SIZE

            # Draw tile
            pygame.draw.rect(
                screen,
                tiles[row][col],
                (x + 3, y + 3, TILE_SIZE - 6, TILE_SIZE - 6)
            )

    pygame.display.flip()

pygame.quit()
