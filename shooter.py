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
obstacles_group = pygame.sprite.Group()

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

    #movement of the player
    def update(self, beat_timer):
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
            self.is_shooting(beat_timer)
        else:
            self.shoot = False

        self.pos = pygame.math.Vector2(self.hitbox_rect.center)

        self.player_rotation()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def is_shooting(self, beat_timer): 
        if self.shoot_cooldown == 0 and self.shoot:
            self.shoot_cooldown = SHOOT_COOLDOWN

            if is_perfect_beat(beat_timer):
                damage = PERFECT_DAMAGE
            elif is_good_beat(beat_timer):
                damage = GOOD_DAMAGE
            else:
                damage = NORMAL_DAMAGE
    
            spawn_bullet_pos = self.pos + self.gun_barrel_offset.rotate(self.angle)
            self.bullet = Bullet(spawn_bullet_pos[0], spawn_bullet_pos[1], self.angle, damage)
            bullet_group.add(self.bullet)
            all_sprites_group.add(self.bullet)
        

    def player_rotation(self):
        self.mouse_coords = pygame.mouse.get_pos()
        
        self.x_change_mouse_player = (self.mouse_coords[0] - self.hitbox_rect.centerx)
        self.y_change_mouse_player = (self.mouse_coords[1] - self.hitbox_rect.centery)
        self.angle = math.degrees(math.atan2(self.y_change_mouse_player, self.x_change_mouse_player))
        self.image = pygame.transform.rotate(self.base_player_image, -self.angle)
        self.rect = self.image.get_rect(center = self.hitbox_rect.center)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, damage):
        super().__init__()
        self.image = pygame.image.load("assets/1.png").convert_alpha()
        self.image = pygame.transform.rotozoom(self.image, 0, BULLET_SCALE)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.x = x
        self.y = y
        self.angle = angle
        self.damage = damage
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

    def bullet_collisions(self): 
        hits = pygame.sprite.spritecollide(self, enemy_group, False) # Checks for collisions with enemies

        if hits:
            for enemy in hits:
                enemy.health -= self.damage
                self.kill()  # Destroy the bullet after hitting an enemy

        if pygame.sprite.spritecollide(self, obstacles_group, False): # Check wall collisions
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
        self.health = ENEMY_HEALTH
        
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

    def update(self): #enemy movement
        if self.health <= 0:
            self.kill()
            return
        self.get_his_ass() 

class UI(): 
    def __init__(self, font): 
        self.font = font
        self.current_health = player.health
        self.maximum_health = 100
        self.health_bar_length = 100
        self.health_ratio = self.maximum_health / self.health_bar_length 
        self.current_colour = None

    def display_health_bar(self): 
        pygame.draw.rect(screen, BLACK, (10, 15, self.health_bar_length * 3, 20)) # black

        if self.current_health >= 75:
            pygame.draw.rect(screen, GREEN, (10, 15, self.current_health * 3, 20)) # green
            self.current_colour = GREEN
        elif self.current_health >= 25:
            pygame.draw.rect(screen, YELLOW, (10, 15, self.current_health * 3, 20)) # yellow
            self.current_colour = YELLOW 
        elif self.current_health >= 0:
            pygame.draw.rect(screen, RED, (10, 15, self.current_health * 3, 20)) # red 
            self.current_colour = RED

        pygame.draw.rect(screen, WHITE, (10, 15, self.health_bar_length * 3, 20), 4) # white border

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

def hitbox_collide(sprite1, sprite2):
    return sprite1.base_zombie_rect.colliderect(sprite2.rect)

player = Player()
enemy = Enemy((400, 400))

def is_perfect_beat(beat_timer): #Checks if the player is shooting on the beat
    distance_to_beat = min(
        beat_timer,
        BEAT_INTERVAL - beat_timer
    )

    return distance_to_beat <= PERFECT_WINDOW

def is_good_beat(beat_timer): #Checks if the player is shooting on the beat
    distance_to_beat = min(
        beat_timer,
        BEAT_INTERVAL - beat_timer
    )

    return distance_to_beat <= GOOD_WINDOW

def main():
    pygame.init()
    pygame.mixer.init()
    #Loads music and plays music
    pygame.mixer.music.load(r"assets\Mitch Murder - Hollywood Heights (SPOTISAVER).mp3")
    pygame.mixer.music.play(1, 0.0)

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

        while change_timer >= BEAT_INTERVAL:
            change_timer -= BEAT_INTERVAL

            for row in range(ROWS):
                for col in range(COLS):
                    tiles[row][col] = random.choice(colors)

        #drawing on the screen
        screen.fill((10, 10, 10))
        disco_floor(screen, tiles, ROWS, COLS, TILESIZE)
        screen.blit(player.image, player.rect)

        player.update(change_timer)
        enemy.update()
        ui.update()

        for bullet in bullet_group:
            bullet.bullet_movement()
            bullet.bullet_collisions() #Checks for collisions with enemies and walls

        pygame.draw.rect(screen, "red", player.hitbox_rect, width=2) #hitbox 1
        pygame.draw.rect(screen, "yellow", player.rect, width=2) #hitbox 2
        all_sprites_group.draw(screen)
        pygame.display.flip()

if __name__ == "__main__":
  main()
