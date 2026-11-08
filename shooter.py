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

        self.rhythm_meter = 0
        self.max_rhythm_meter = 100 # Combo bar
        self.idle_timer = 0
        self.idle_delay = 2000  # 2 seconds of inactivity before combo bar decay
        self.idle_decay_rate = 5  # Lose 5% per second when idle

        self.base_damage = NORMAL_DAMAGE
        self.max_damage_multiplier = 3.0

    #movement of the player
    def update(self, beat_timer, dt):
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


        # Idle decay for rhythm meter
        if not self.shoot:
            self.idle_timer += dt
            if self.idle_timer >= self.idle_delay:
                decay_amount = (self.idle_decay_rate * dt) / 1000  # Convert to per second
                self.rhythm_meter -= decay_amount
                self.rhythm_meter = max(0, min(self.rhythm_meter, self.max_rhythm_meter))  # Ensure it doesn't go below 0
        else:
            self.idle_timer = 0  # Reset idle timer when shooting

        self.pos = pygame.math.Vector2(self.hitbox_rect.center)

        self.player_rotation()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def is_shooting(self, beat_timer): 
        if self.shoot_cooldown == 0 and self.shoot:
            self.shoot_cooldown = SHOOT_COOLDOWN

            if is_perfect_beat(beat_timer):
                grade = "Perfect"
            elif is_good_beat(beat_timer):
                grade = "Good"
            else:
                grade = "Bad"
                self.rhythm_meter -= 10  # Lose 10% for shooting off-beat

            damage_multiplier = 1 + (self.rhythm_meter / self.max_rhythm_meter) * (self.max_damage_multiplier - 1) # Calculate damage multiplier based on rhythm meter
            damage = self.base_damage * damage_multiplier
            self.rhythm_meter = max(0, min(self.rhythm_meter, self.max_rhythm_meter))  # Clamp the combo bar between 0 and max
    
            spawn_bullet_pos = self.pos + self.gun_barrel_offset.rotate(self.angle)
            self.bullet = Bullet(spawn_bullet_pos[0], spawn_bullet_pos[1], self.angle, damage, grade)
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
    def __init__(self, x, y, angle, damage, grade):
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
        self.grade = grade  # Store the grade of the bullet (Perfect, Good, Bad)

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
            enemy = hits[0]  # Affect the first enemy hit
            enemy.health -= self.damage

            if self.grade == "Perfect": # Checks bullet grade and updates the player's rhythm meter accordingly
                player.rhythm_meter += 20
            elif self.grade == "Good":
                player.rhythm_meter += 10
            else:
                player.rhythm_meter -= 10  # Lose 10% for shooting off-beat

            player.rhythm_meter = max(0, min(player.rhythm_meter, player.max_rhythm_meter))  # Clamp the combo bar between 0 and max   
                
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

    def display_combo_bar(self):
        bar_width = 200
        bar_height = 20
        bar_x = WIDTH - bar_width - 10
        bar_y = 10

        # Draw the background of the combo bar
        pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height))

        # Calculate the width of the filled portion based on the rhythm meter
        filled_width = (player.rhythm_meter / player.max_rhythm_meter) * bar_width

        # Draw the filled portion of the combo bar
        pygame.draw.rect(screen, BLUE, (bar_x, bar_y, filled_width, bar_height))

        # Draw the border of the combo bar
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

        meter_text = self.font.render(f"Combo: {player.rhythm_meter}%", True, WHITE)

        screen.blit(meter_text, (bar_x, bar_y + 25))

    def update(self): 
        self.display_health_bar()
        self.display_health_text()
        self.display_combo_bar()

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

        player.update(change_timer, dt)
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
