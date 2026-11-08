#imports
import pygame
from sys import exit
import math
from settings import *
import random
screen = pygame.display.set_mode((WIDTH, HEIGHT))

all_sprites_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites_group)

        self.image = pygame.transform.scale_by(pygame.image.load("assets/0.png").convert_alpha(), SCALE_FACTOR)
        self.base_player_image = self.image

        self.pos = pygame.math.Vector2(PLAYER_START_X, PLAYER_START_Y)
        self.rect = self.image.get_rect(center=self.pos)
        self.speed = PLAYER_SPEED
        self.hitbox_rect = self.base_player_image.get_rect(center = self.pos)
        self.rect = self.hitbox_rect.copy()

        self.shoot = False
        self.shoot_cooldown = 0
        self.gun_barrel_offset = pygame.math.Vector2(GUN_OFFSET_X, GUN_OFFSET_Y)
        self.health = PLAYER_HEALTH
        self.damage_cooldown = 0
        self.damage_delay = DAMAGE_DELAY  # 1 second

    #movement of the player
    def update(self, dt):
        self.player_rotation()
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.hitbox_rect.y -= self.speed
        if keys[pygame.K_s]:
            self.hitbox_rect.y += self.speed
        if keys[pygame.K_a]:
            self.hitbox_rect.x -= self.speed
        if keys[pygame.K_d]:
            self.hitbox_rect.x += self.speed

        #keeps the player within the vertical screen boundaries
        if self.hitbox_rect.top < 0:
            self.hitbox_rect.top = 0

        if self.hitbox_rect.bottom > HEIGHT:
            self.hitbox_rect.bottom = HEIGHT

        #keeps the player within the horizontal screen boundaries
        if self.hitbox_rect.left < 0:
            self.hitbox_rect.left = 0

        if self.hitbox_rect.right > WIDTH:
            self.hitbox_rect.right = WIDTH

        if pygame.mouse.get_pressed() == (1, 0, 0) or keys[pygame.K_SPACE]:
            self.shoot = True
            self.is_shooting()
        else:
            self.shoot = False

        self.pos = pygame.math.Vector2(self.hitbox_rect.center)

        self.player_rotation()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.damage_cooldown > 0:
            self.damage_cooldown -= dt

    def is_shooting(self): 
        if self.shoot_cooldown == 0 and self.shoot:
            self.shoot_cooldown = SHOOT_COOLDOWN
            spawn_bullet_pos = self.pos + self.gun_barrel_offset.rotate(self.angle)
            self.bullet = Bullet(spawn_bullet_pos[0], spawn_bullet_pos[1], self.angle)
            bullet_group.add(self.bullet)
            all_sprites_group.add(self.bullet)
        

    def player_rotation(self):
        self.mouse_coords = pygame.mouse.get_pos()
        
        self.x_change_mouse_player = (self.mouse_coords[0] - WIDTH // 2)
        self.y_change_mouse_player = (self.mouse_coords[1] - HEIGHT // 2)
        self.angle = math.degrees(math.atan2(self.y_change_mouse_player, self.x_change_mouse_player))
        self.image = pygame.transform.rotate(self.base_player_image, -self.angle)
        self.rect = self.image.get_rect(center = self.hitbox_rect.center)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.image = pygame.image.load("assets/1.png").convert_alpha()
        self.image = pygame.transform.rotozoom(self.image, 0, BULLET_SCALE)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = BULLET_SPEED
        self.x_vel = math.cos(self.angle * (2*math.pi/360)) * self.speed
        self.y_vel = math.sin(self.angle * (2*math.pi/360)) * self.speed
        self.bullet_lifetime = BULLET_LIFETIME
        self.spawn_time = pygame.time.get_ticks() # gets the specific time that the bullet was created

    def bullet_movement(self):  
        self.x += self.x_vel
        self.y += self.y_vel

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        if pygame.time.get_ticks() - self.spawn_time > self.bullet_lifetime:
            self.kill() 

class Particle:
    def __init__(self, x, y, vx, vy, radius):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius

    def update(self):
        # Move the particle based on velocity
        self.x += self.vx
        self.y += self.vy
        
        # Shrink over time (matching the 0.1 decay from the video)
        self.radius -= 0.1

    def draw(self, screen):
        # Pygame requires integer coordinates and radii for drawing circles
        pygame.draw.circle(
            screen, 
            (255, 255, 255), 
            (int(self.x), int(self.y)), 
            int(self.radius)
        )

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__(enemy_group, all_sprites_group)
        self.image = pygame.transform.scale_by(pygame.image.load("assets/00.png").convert_alpha(), 2)
        self.position = pygame.math.Vector2(position)
        self.rect = self.image.get_rect(center=position)
        self.rect.center = position
        
        #extremely advanced enemy AI
        self.direction = pygame.math.Vector2()
        self.velocity = pygame.math.Vector2()
        self.speed = ENEMY_SPEED

    def get_his_ass(self): #hunt the player
        player_pos = pygame.math.Vector2(player.rect.center)
        enemy_pos = pygame.math.Vector2(self.rect.center)
        distance = self.get_distance(player_pos, enemy_pos)

        if distance > 0:
            self.direction = (player_pos - enemy_pos).normalize()
        else:
            self.direction = pygame.math.Vector2(0, 0)

        self.velocity = self.direction * self.speed
        self.position += self.velocity
        self.rect.centerx = self.position.x
        self.rect.centery = self.position.y
            
    def get_distance(self, vector1, vector2):
        return abs(vector1.distance_to(vector2))

    def player_collision(self):
        if self.rect.colliderect(player.hitbox_rect):
            if player.damage_cooldown <= 0:
                player.health = max(0, player.health - ENEMY_DAMAGE)
                player.damage_cooldown = player.damage_delay
                self.kill()

    def update(self, dt):
        self.get_his_ass()
        direction = pygame.Vector2(player.rect.center) - self.position
        if direction.length() > 20:
            self.position += direction.normalize() * self.speed
        self.rect.center = self.position
        self.player_collision()
            
class UI(): 
    def __init__(self, font): 
        self.font = font
        self.maximum_health = PLAYER_HEALTH
        self.health_bar_length = 100
        self.current_colour = None

    def display_health_bar(self):
        current_health = player.health
        pygame.draw.rect(screen, BLACK, (10, 15, self.health_bar_length * 3, 20))

        if current_health >= 75:
            self.current_colour = GREEN
        elif current_health >= 25:
            self.current_colour = YELLOW
        else:
            self.current_colour = RED

        pygame.draw.rect(
            screen,
            self.current_colour,
            (10, 15, current_health * 3, 20)
        )
        pygame.draw.rect(screen, WHITE, (10, 15, self.health_bar_length * 3, 20), 4)

    def display_health_text(self):
        health_surface = self.font.render(f"{player.health} / {self.maximum_health}", False, self.current_colour) 
        health_rect = health_surface.get_rect(center = (410, 25))
        screen.blit(health_surface, health_rect)

    def display_countdown(self, time):
        text_1 = self.font.render(f"Enemies spawning in {int(time/1000)} seconds!",True, RED)
        screen.blit(text_1, (400, 100))

    def update(self): 
        self.display_health_bar()
        self.display_health_text()

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
def separate_enemies(enemies):
    for i, enemy1 in enumerate(enemies):
        for enemy2 in enemies[i + 1:]:

            direction = enemy1.position - enemy2.position
            distance = direction.length()

            min_distance = MIN_ENEMY_DISTANCE  # Adjust to your enemy size

            if distance < min_distance:
                if distance == 0:
                    direction = pygame.Vector2(1, 0)
                else:
                    direction = direction.normalize()

                overlap = min_distance - distance

                enemy1.position += direction * (overlap / 2)
                enemy2.position -= direction * (overlap / 2)

                enemy1.rect.center = enemy1.position
                enemy2.rect.center = enemy2.position

player = Player()
enemy = Enemy((0, 720))
enemy2= Enemy((720, 0))

def main():
    pygame.init()

    font = pygame.font.Font("assets/PublicPixel.ttf", 20) 
    small_font = pygame.font.Font("assets/PublicPixel.ttf", 15)
    title_font = pygame.font.Font("assets/PublicPixel.ttf", 60)
    score_font = pygame.font.Font("assets/PublicPixel.ttf", 50)
    ui = UI(font) 

    pygame.display.set_caption("DISCOBEAT")
    clock = pygame.time.Clock()

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

        #drawing on the screen
        screen.fill((10, 10, 10))
        disco_floor(screen, tiles, ROWS, COLS, TILESIZE)
        screen.blit(player.image, player.rect)

        player.update(dt)
        enemy_group.update(dt)
        separate_enemies(enemy_group.sprites())
        ui.update()

        for bullet in bullet_group:
            bullet.bullet_movement()
            screen.blit(bullet.image, bullet.rect)

        pygame.draw.rect(screen, "red", player.hitbox_rect, width=2) #hitbox 1
        pygame.draw.rect(screen, "yellow", player.rect, width=2) #hitbox 2
        all_sprites_group.draw(screen)
        pygame.display.flip()

if __name__ == "__main__":
  main()
