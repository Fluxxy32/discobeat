#imports
import pygame
from sys import exit
import math
from settings import *
import random

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Background image
BACKGROUND_PATH = "assets/arabic set/arabic1.png"

# Dance floor position and dimensions (adjust these)
FLOOR_RECT = pygame.Rect(637, 665, 650, 250)
# --- Wall collisions ---
# Rects are in ORIGINAL image pixels (544x416): (x, y, width, height)
IMG_W, IMG_H = 544, 416
BG_W = int(WIDTH * 1.15)          # same stretch used in main()
BG_LEFT = WIDTH // 2 - BG_W // 2  # same centering used in main()

WALLS_IMG = [
    (0,   0,   544, 160),  # top back wall + cabinets
    (192, 160, 160, 52),   # bed / alcove pillars
    (0,   0,   64,  416),  # left wall
    (480, 0,   64,  416),  # right wall
    (0,   384, 544, 32),   # bottom wall
    (64,  140, 32,  52),   # plant, top-left
    (448, 140, 32,  52),   # plant, top-right
    (96,  300, 32,  52),   # plant, bottom-left
    (416, 300, 32,  52),   # plant, bottom-right
]

def img_to_screen_rect(r):
    x, y, w, h = r
    sx = BG_W / IMG_W
    sy = HEIGHT / IMG_H
    return pygame.Rect(
        round(BG_LEFT + x * sx), round(y * sy),
        round(w * sx), round(h * sy)
    )

WALL_RECTS = [img_to_screen_rect(r) for r in WALLS_IMG]
# --- Sizes and spawn areas ---
PLAYER_SCALE = 0.6      # multiplier on top of SCALE_FACTOR (lower = smaller)
ENEMY_SIZE = 110        # enemy sprite size in pixels (was 196)

# Player spawns in the middle of the dance floor
PLAYER_SPAWN = (FLOOR_RECT.centerx, FLOOR_RECT.centery)

# Open tiled area enemies may spawn in (image coords -> screen coords)
SPAWN_AREA = img_to_screen_rect((64, 192, 416, 192))

# Dance floor grid
FLOOR_ROWS = 8
FLOOR_COLS = 12

MENU = "menu"
PLAYING = "playing"
DEAD = "dead"
WON = "won"

game_state = MENU

all_sprites_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
obstacles_group = pygame.sprite.Group()
particles = []

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites_group)

        self.image = pygame.transform.scale_by(
            pygame.image.load("assets/0.png").convert_alpha(),
            SCALE_FACTOR * PLAYER_SCALE
        )
        self.base_player_image = self.image
        self.pos = pygame.math.Vector2(PLAYER_SPAWN)
        self.rect = self.image.get_rect(center=self.pos)
        self.speed = PLAYER_SPEED
        self.hitbox_rect = self.base_player_image.get_rect(center = self.pos)
        self.rect = self.hitbox_rect.copy()

        self.shoot = False
        self.shoot_cooldown = 0
        self.gun_barrel_offset = pygame.math.Vector2(GUN_OFFSET_X, GUN_OFFSET_Y) * PLAYER_SCALE
        self.health = PLAYER_HEALTH

        self.rhythm_meter = 0
        self.max_rhythm_meter = 100 # Combo bar
        self.idle_timer = 0
        self.idle_delay = 2000  # 2 seconds of inactivity before combo bar decay
        self.idle_decay_rate = 5  # Lose 5% per second when idle

        self.base_damage = NORMAL_DAMAGE
        self.max_damage_multiplier = 3.0
        self.damage_cooldown = 0
        self.damage_delay = DAMAGE_DELAY

    #movement of the player
    def update(self, beat_timer, dt):
        self.player_rotation()
        keys = pygame.key.get_pressed()

        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * self.speed
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * self.speed

        # Move on X, then fix any overlap
        self.hitbox_rect.x += dx
        for wall in WALL_RECTS:
            if self.hitbox_rect.colliderect(wall):
                if dx > 0:
                    self.hitbox_rect.right = wall.left
                elif dx < 0:
                    self.hitbox_rect.left = wall.right

        # Move on Y, then fix any overlap
        self.hitbox_rect.y += dy
        for wall in WALL_RECTS:
            if self.hitbox_rect.colliderect(wall):
                if dy > 0:
                    self.hitbox_rect.bottom = wall.top
                elif dy < 0:
                    self.hitbox_rect.top = wall.bottom

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
        if self.damage_cooldown > 0:
            self.damage_cooldown -= dt

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

        self.rect.center = (int(self.x), int(self.y))

        if pygame.time.get_ticks() - self.spawn_time > self.bullet_lifetime:
            self.kill() 

    def bullet_collisions(self): 
        hits = pygame.sprite.spritecollide(self, enemy_group, False) # Checks for collisions with enemies

        if hits:
            enemy = hits[0]  # Affect the first enemy hit
            enemy.health -= self.damage

                # Choose particle color based on rhythm grade
            if self.grade == "Perfect":
                  particle_color = (255, 215, 0)  # Gold
            elif self.grade == "Good":
                  particle_color = (50, 200, 255)  # Cyan
            else:
                  particle_color = (255, 60, 60)  # Red

            # Spawn 20 particles at the enemy's position
            for i in range(20):
                particles.append(
                Particle(
                enemy.rect.centerx,
                enemy.rect.centery,
                particle_color
              )
              )

            if self.grade == "Perfect": # Checks bullet grade and updates the player's rhythm meter accordingly
                player.rhythm_meter += 20
            elif self.grade == "Good":
                player.rhythm_meter += 10
            else:
                player.rhythm_meter -= 10  # Lose 10% for shooting off-beat

            player.rhythm_meter = max(0, min(player.rhythm_meter, player.max_rhythm_meter))  # Clamp the combo bar between 0 and max

            self.kill()  # Destroy the bullet after hitting an enemy

        if any(self.rect.colliderect(w) for w in WALL_RECTS):
            self.kill()

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        # Random direction and speed
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(100, 300)

        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.radius = random.randint(4, 8)
        self.life = 600  # Milliseconds
        self.color = color

    def update(self, dt):
        # Move the particle based on velocity
        seconds = dt / 1000
        self.x += self.vx * seconds
        self.y += self.vy * seconds
        
        # Gradually slow down
        self.vx *= 0.97
        self.vy *= 0.97

        # Shrink and disappear
        self.life -= dt
        self.radius -= 0.08 * (dt / 16.67)

    def draw(self, screen):
        if self.life > 0 and self.radius > 0:
         pygame.draw.circle(
            screen, 
            self.color, 
            (int(self.x), int(self.y)), 
            max(1, int(self.radius))
         )

def load_sprite_sheet(path, frame_count):
    sheet = pygame.image.load(path).convert_alpha()
    frames = []

    for i in range(frame_count):
        frame = sheet.subsurface(
            pygame.Rect(i * 128, 0, 128, 128)
        ).copy()
        frame = pygame.transform.scale(frame, (ENEMY_SIZE, ENEMY_SIZE))
        frames.append(frame)
    return frames

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__(enemy_group, all_sprites_group)

        # Load running animation
        self.run_frames = load_sprite_sheet("assets/Gangsters_2/Run.png", 6)

        # Load attack animations
        self.attack_1 = load_sprite_sheet("assets/Gangsters_2/Attack_1.png", 6)
        self.attack_2 = load_sprite_sheet("assets/Gangsters_2/Attack_2.png", 4)
        self.attack_3 = load_sprite_sheet("assets/Gangsters_2/Attack_3.png", 6)

        self.attack_frames = self.attack_1 + self.attack_2 + self.attack_3

        # Start with running animation
        self.frames = self.run_frames

        # Animation variables
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 100

        # Direction the enemy is facing
        self.facing_right = True

        # Animation variables
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 100

        # Set initial sprite
        self.image = self.frames[self.frame_index]

        # Initialize position
        self.position = pygame.math.Vector2(position)

        self.rect = self.image.get_rect(center=self.position)
        self.collision_rect = pygame.Rect(0, 0, int(ENEMY_SIZE * 0.4), int(ENEMY_SIZE * 0.4))
        self.collision_rect.center = self.position

        self.health = ENEMY_HEALTH

        # Attack settings
        self.attack_range = 90 * ENEMY_SIZE / 196
        self.attack_cooldown = 0
        self.attack_delay = 1000

        # Enemy state
        self.state = "run"

        # Enemy movement variables
        self.direction = pygame.math.Vector2()
        self.velocity = pygame.math.Vector2()
        self.speed = ENEMY_SPEED * 60

    def _step(self, axis, amount):
        """Move along one axis, push back out of any wall. Returns the wall hit, if any."""
        hit = None
        if axis == "x":
            self.position.x += amount
        else:
            self.position.y += amount
        self.collision_rect.center = (round(self.position.x), round(self.position.y))

        for wall in WALL_RECTS:
            if self.collision_rect.colliderect(wall):
                if axis == "x":
                    if amount > 0:
                        self.collision_rect.right = wall.left
                    elif amount < 0:
                        self.collision_rect.left = wall.right
                    self.position.x = self.collision_rect.centerx
                else:
                    if amount > 0:
                        self.collision_rect.bottom = wall.top
                    elif amount < 0:
                        self.collision_rect.top = wall.bottom
                    self.position.y = self.collision_rect.centery
                hit = wall
        return hit

    def move_with_walls(self, movement):
        hit_x = self._step("x", movement.x)
        hit_y = self._step("y", movement.y)

        # If the enemy runs straight into a wall, slide sideways around it
        # (otherwise it would freeze behind a plant when lined up with you)
        if hit_x and abs(movement.y) < abs(movement.x) * 0.5:
            self._step("y", math.copysign(abs(movement.x), self.position.y - hit_x.centery))
        elif hit_y and abs(movement.x) < abs(movement.y) * 0.5:
            self._step("x", math.copysign(abs(movement.y), self.position.x - hit_y.centerx))

    def get_his_ass(self, dt):

        # Get player and enemy positions
        player_pos = pygame.math.Vector2(player.hitbox_rect.center)
        enemy_pos = self.position

        # Calculate direction towards player
        direction_vector = player_pos - enemy_pos
        distance = direction_vector.length()

        # Determine which direction the enemy faces
        if direction_vector.x > 1:
            self.facing_right = True
        elif direction_vector.x < -1:
            self.facing_right = False

        # Check whether the enemy is within attack range
        if distance <= self.attack_range:
            self.state = "attack"
            self.velocity = pygame.math.Vector2()

        else:
            self.state = "run"

            # Calculate direction towards player
            self.direction = direction_vector.normalize()

            # Calculate velocity
            self.velocity = self.direction * self.speed

            # Move using delta time
            movement = self.velocity * (dt / 1000)

            # Prevent the enemy from overshooting its stopping distance
            max_movement = distance - self.attack_range

            if movement.length() > max_movement:
                movement.scale_to_length(max_movement)

            self.move_with_walls(movement)


        # Update rectangle
        self.rect.center = self.position

    def get_distance(self, vector1, vector2):
        return vector1.distance_to(vector2)

    def player_collision(self, dt):

        # Reduce attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        # Only attack when within range
        if self.state == "attack":

            if self.attack_cooldown <= 0:

                player.health = max(0, player.health - ENEMY_DAMAGE)

                self.attack_cooldown = self.attack_delay

    def draw_health_bar(self):
        bar_width = 50
        bar_height = 6

        health_ratio = max(0, self.health / ENEMY_HEALTH)

        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - 12

        pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height))

        pygame.draw.rect(
            screen, GREEN,
            (bar_x, bar_y, bar_width * health_ratio, bar_height)
        )

        pygame.draw.rect(
            screen, WHITE,
            (bar_x, bar_y, bar_width, bar_height), 1
        )

    def update(self, dt):

        # Remove dead enemies
        if self.health <= 0:
            self.kill()
            return

        # Update enemy movement and state
        self.get_his_ass(dt)

        # Choose animation based on state
        if self.state == "run":
            new_frames = self.run_frames
        else:
            new_frames = self.attack_1

        # Reset animation when switching states
        if self.frames is not new_frames:
            self.frames = new_frames
            self.frame_index = 0
            self.animation_timer = 0

        # Update animation timer
        self.animation_timer += dt

        if self.animation_timer >= self.animation_speed:
            self.animation_timer -= self.animation_speed
            self.frame_index = (self.frame_index + 1) % len(self.frames)

        # Get current animation frame
        current_frame = self.frames[self.frame_index]

        # Flip according to direction
        if not self.facing_right:
            self.image = pygame.transform.flip(current_frame, True, False)
        else:
            self.image = current_frame

        # Update sprite rectangle
        self.rect = self.image.get_rect(center=self.position)

        # Attack player if within range
        self.player_collision(dt)
            
class UI:
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

        pygame.draw.rect(
            screen, WHITE,
            (10, 15, self.health_bar_length * 3, 20), 4
        )

    def display_health_text(self):
        health_surface = self.font.render(
            f"{player.health} / {self.maximum_health}",
            False,
            self.current_colour
        )
        health_rect = health_surface.get_rect(center=(410, 25))
        screen.blit(health_surface, health_rect)

    def display_countdown(self, time):
        text_1 = self.font.render(
            f"Enemies spawning in {int(time / 1000)} seconds!",
            True,
            RED
        )
        screen.blit(text_1, (400, 100))

    def display_combo_bar(self):
        bar_width = 200
        bar_height = 20
        bar_x = WIDTH - bar_width - 10
        bar_y = 10

        pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height))

        filled_width = (player.rhythm_meter / player.max_rhythm_meter) * bar_width

        pygame.draw.rect(
            screen, BLUE,
            (bar_x, bar_y, filled_width, bar_height)
        )

        pygame.draw.rect(
            screen, WHITE,
            (bar_x, bar_y, bar_width, bar_height), 2
        )

        meter_text = self.font.render(
            f"Combo: {player.rhythm_meter}%",
            True,
            WHITE
        )
        screen.blit(meter_text, (bar_x, bar_y + 25))

    def display_rank(self):
        rank = get_rank(player.rhythm_meter)
        rank_color = get_rank_color(rank)

        rank_text = self.font.render(
            f"RANK: {rank}",
            True,
            rank_color
        )

        rank_rect = rank_text.get_rect(center=(WIDTH - 110, 85))
        screen.blit(rank_text, rank_rect)

    def display_timer(self, survival_time):
        remaining = max(0, WIN_TIME - survival_time)
        seconds = math.ceil(remaining / 1000)
        color = RED if seconds <= 10 else WHITE

        timer_text = self.font.render(f"{seconds // 60}:{seconds % 60:02d}", True, color)
        screen.blit(timer_text, timer_text.get_rect(center=(WIDTH // 2, 25)))

    def update(self, survival_time):
        self.display_health_bar()
        self.display_health_text()
        self.display_combo_bar()
        self.display_rank()
        self.display_timer(survival_time)

class Button:
    def __init__(self, image, pos, text_input, font, base_color, hovering_color):
        self.image = image
        self.x_pos = pos[0]
        self.y_pos = pos[1]
        self.font = font
        self.base_color = base_color
        self.hovering_color = hovering_color
        self.text_input = text_input

        self.text = self.font.render(self.text_input, True, self.base_color)

        if self.image is None:
            self.image = self.text

        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

    def update(self, screen):
        if self.image is not None:
            screen.blit(self.image, self.rect)
        screen.blit(self.text, self.text_rect)

    def checkForInput(self, position):
        return self.rect.collidepoint(position)

    def changeColor(self, position):
        if self.rect.collidepoint(position):
            self.text = self.font.render(self.text_input, True, self.hovering_color)
        else:
            self.text = self.font.render(self.text_input, True, self.base_color)

def get_rank_color(rank):
    rank_colors = {
    "SSS": (255, 215, 0),    # Gold
    "S":   (255, 50, 50),    # Red
    "A":   (180, 80, 255),   # Purple
    "B":   (50, 150, 255),   # Blue
    "C":   (50, 220, 100),   # Green
    "D":   (180, 180, 180)   # Gray
    }
    return rank_colors[rank]

def draw_beat_ring(screen, beat_timer):
    center = pygame.mouse.get_pos()
    t = beat_timer / BEAT_INTERVAL             # 0 right after the beat, ->1 just before the next
    target_r, max_r = 28, 100
    ring_r = target_r + (max_r - target_r) * (1 - t)   # shrinks toward the target

    dist = min(beat_timer, BEAT_INTERVAL - beat_timer) # ms away from the nearest beat
    if dist <= PERFECT_WINDOW:
        color, width = (255, 215, 0), 6
    elif dist <= GOOD_WINDOW:
        color, width = (50, 200, 255), 4
    else:
        color, width = (255, 255, 255), 2

    pygame.draw.circle(screen, color, center, target_r, width)         # fixed target
    pygame.draw.circle(screen, (255, 255, 255), center, int(ring_r), 2)  # shrinking ring

def disco_floor(screen, tiles, floor_rect):

    # Black background behind the tiles
    pygame.draw.rect(screen, (0, 0, 0), floor_rect)

    rows = len(tiles)
    cols = len(tiles[0])

    tile_width = floor_rect.width / cols
    tile_height = floor_rect.height / rows

    for row in range(rows):
        for col in range(cols):

            x = floor_rect.x + col * tile_width
            y = floor_rect.y + row * tile_height

            tile_rect = pygame.Rect(
                round(x) + 3,
                round(y) + 3,
                round(tile_width) - 6,
                round(tile_height) - 6
            )

            pygame.draw.rect(
                screen,
                tiles[row][col],
                tile_rect
            )

def generate_floor(rows, cols):
    tiles = [
        [random.choice(colors) for _ in range(cols)]
        for _ in range(rows)
    ]
    return tiles

def get_floor_interval(combo):
    if combo >= 100:
        return BEAT_INTERVAL
    elif combo >= 80:
        return 800
    elif combo >= 60:
        return 1200
    elif combo >= 40:
        return 1600
    elif combo >= 20:
        return 2000
    else:
        return 2400

def get_rank(combo):
    if combo >= 100:
        return "SSS"
    elif combo >= 80:
        return "S"
    elif combo >= 60:
        return "A"
    elif combo >= 40:
        return "B"
    elif combo >= 20:
        return "C"
    else:
        return "D"

def hitbox_collide(sprite1, sprite2):
    return sprite1.base_zombie_rect.colliderect(sprite2.rect)

def is_perfect_beat(beat_timer): #Checks if the player is shooting on the beat
    distance_to_beat = min(
        beat_timer,
        BEAT_INTERVAL - beat_timer
    )

    return distance_to_beat <= PERFECT_WINDOW

def is_good_beat(beat_timer):
    distance_to_beat = min(beat_timer, BEAT_INTERVAL - beat_timer)
    return distance_to_beat <= GOOD_WINDOW

BEAT_OFFSET = 0 

def get_beat_timer():
    pos = pygame.mixer.music.get_pos()   # ms the song has been playing
    if pos < 0:
        return 0
    return (pos - BEAT_OFFSET) % BEAT_INTERVAL

def update_music_volume(combo):
    min_volume = 0.2 # Minimum volume when combo is 0
    max_volume = 1.0 # Maximum volume when combo is 100

    volume = min_volume + (combo / 100) * (max_volume - min_volume)

    pygame.mixer.music.set_volume(volume)

class ScreenPulse:
    def __init__(self):
        self.phase = 0
        self.alpha = 0

        # Transparent overlay
        self.overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

    def update(self, combo, dt):
        # Keep combo between 0 and 100
        combo = max(0, min(combo, 100))

        # Increase pulse frequency as combo increases
        min_frequency = 0.5
        max_frequency = 2.0

        frequency = min_frequency + (combo / 100) * (
            max_frequency - min_frequency
        )

        # Update animation phase
        self.phase += (2 * math.pi * frequency * dt) / 1000

        # Calculate pulse intensity
        intensity = (math.sin(self.phase) + 1) / 2

        # Stronger pulse at higher combo
        self.alpha = int(intensity * 100 * (combo / 100))

    def draw(self, screen):
        self.overlay.fill((140, 40, 200, self.alpha))
        screen.blit(self.overlay, (0, 0))

class BorderPulse:
    def __init__(self):
        self.phase = 0
        self.surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    def update(self, combo, dt):
        combo = max(0, min(combo, 100))

        # Pulse speed increases with combo
        min_frequency = 0.5
        max_frequency = 3.0

        frequency = min_frequency + (combo / 100) * (
            max_frequency - min_frequency
        )

        self.phase += (2 * math.pi * frequency * dt) / 1000

        # Calculate brightness
        intensity = (math.sin(self.phase) + 1) / 2

        self.alpha = int(intensity * 200 * (combo / 100))

    def draw(self, screen):
        self.surface.fill((0, 0, 0, 0))

        # Neon purple border
        border_color = (180, 40, 255, self.alpha)

        border_thickness = 25

        # Top
        pygame.draw.rect(
            self.surface, border_color,
            (0, 0, WIDTH, border_thickness)
        )

        # Bottom
        pygame.draw.rect(
            self.surface, border_color,
            (0, HEIGHT - border_thickness, WIDTH, border_thickness)
        )

        # Left
        pygame.draw.rect(
            self.surface, border_color,
            (0, 0, border_thickness, HEIGHT)
        )

        # Right
        pygame.draw.rect(
            self.surface, border_color,
            (WIDTH - border_thickness, 0, border_thickness, HEIGHT)
        )

        screen.blit(self.surface, (0, 0))

class EnemySpawner:
    def __init__(self):
        self.elapsed = 0
        self.spawn_timer = 0
        self.max_enemies = START_MAX_ENEMIES
        self.spawn_delay = START_SPAWN_DELAY

    def spawn_enemy(self):
        half = ENEMY_SIZE // 2
        for _ in range(50):  # try up to 50 random spots
            x = random.randint(SPAWN_AREA.left + half, SPAWN_AREA.right - half)
            y = random.randint(SPAWN_AREA.top + half, SPAWN_AREA.bottom - half)
            test_rect = pygame.Rect(0, 0, ENEMY_SIZE, ENEMY_SIZE)
            test_rect.center = (x, y)

            too_close = pygame.math.Vector2(x, y).distance_to(player.hitbox_rect.center) < 400
            in_wall = any(test_rect.colliderect(w) for w in WALL_RECTS)

            if not too_close and not in_wall:
                Enemy((x, y))
                return

    def update(self, dt):
        self.elapsed += dt
        seconds = self.elapsed / 1000

        # +1 enemy every 12 s, spawn delay shrinks 25 ms per second
        self.max_enemies = min(MAX_ENEMIES, START_MAX_ENEMIES + int(seconds // 12))
        self.spawn_delay = max(MIN_SPAWN_DELAY, START_SPAWN_DELAY - seconds * 25)

        if len(enemy_group) < self.max_enemies:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_delay:
                self.spawn_enemy()
                self.spawn_timer = 0
        else:
            self.spawn_timer = 0

def main_menu():
    pygame.mouse.set_visible(False)
    menu = True
    title_font = pygame.font.Font("assets/PublicPixel.ttf", TITLE_FONT_SIZE)
    button_font = pygame.font.Font("assets/PublicPixel.ttf", BUTTON_FONT_SIZE)
    title = title_font.render("DISCOBEAT", True, WHITE)
    play_button = Button(None, (WIDTH // 2, HEIGHT // 2 + 50), "PLAY", button_font, WHITE, YELLOW)
    quit_button = Button(None, (WIDTH - 40, 40), "X", button_font, WHITE, RED)

    while menu:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.checkForInput(mouse_pos):
                    menu = False
                if quit_button.checkForInput(mouse_pos):
                    pygame.quit()
                    exit()
        screen.fill((65, 10, 30))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 3)))

        play_button.changeColor(mouse_pos)
        play_button.update(screen)
        quit_button.changeColor(mouse_pos)
        quit_button.update(screen)

        mouse_cursor = pygame.transform.rotozoom(
            pygame.image.load("assets/menu_assets/x1/icons/cursor.png"), 0, CURSOR_SCALE_FACTOR
        ).convert_alpha()
        screen.blit(mouse_cursor, mouse_cursor.get_rect(topleft=mouse_pos))
        pygame.display.flip()
    pygame.mouse.set_visible(True)

def main():
    global player

    pygame.mixer.init()

    # Create the player and game objects
    player = Player()
    spawner = EnemySpawner()

    font = pygame.font.Font("assets/PublicPixel.ttf", 20)
    ui = UI(font)

    pulse = ScreenPulse()
    border_pulse = BorderPulse()

    pygame.display.set_caption("DISCOBEAT")
    clock = pygame.time.Clock()

    # Load background
    background = pygame.image.load(BACKGROUND_PATH).convert()

# Stretch horizontally
    background = pygame.transform.scale(
        background,
        (int(WIDTH * 1.15), HEIGHT)
    )

    # Center the stretched image
    background_rect = background.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    # Load and start music
    pygame.mixer.music.load(
        "assets/Miami Disco.mp3"
    )
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play()

    # Initialize floor and timers
    tiles = generate_floor(FLOOR_ROWS, FLOOR_COLS)
    change_timer = 0
    floor_timer = 0
    survival_time = 0

    game_state = PLAYING

    while True:

        dt = clock.tick(FPS)

        # --------------------------------
        # 1. EVENT HANDLING
        # --------------------------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:

                # Restart after death
                if game_state == DEAD and event.key == pygame.K_r:

                    # Remove all existing sprites
                    for sprite in list(all_sprites_group):
                        sprite.kill()

                    # Clear remaining groups
                    bullet_group.empty()
                    enemy_group.empty()
                    obstacles_group.empty()

                    # Create a fresh player
                    player = Player()

                    # Reset the spawner
                    spawner.spawn_timer = 0
                    spawner.elapsed = 0

                    # Reset timers
                    change_timer = 0
                    floor_timer = 0
                    survival_time = 0

                    # Generate a fresh floor
                    tiles = generate_floor(FLOOR_ROWS, FLOOR_COLS)

                    # Restart the music
                    pygame.mixer.music.play()

                    game_state = PLAYING

                # Quit after winning
                elif game_state == WON and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()

        # --------------------------------
        # 2. GAMEPLAY
        # --------------------------------

        if game_state == PLAYING:
            survival_time += dt
            if player.health <= 0:
                game_state = DEAD
            elif survival_time >= WIN_TIME:
                game_state = WON

            # Update beat timer
            change_timer = get_beat_timer()

            # Update floor animation
            floor_interval = get_floor_interval(player.rhythm_meter)

            floor_timer += dt

            while floor_timer >= floor_interval:
                floor_timer -= floor_interval
                    
                for row in range(FLOOR_ROWS):
                    for col in range(FLOOR_COLS):
                        tiles[row][col] = random.choice(colors)

            # Update music volume
            update_music_volume(player.rhythm_meter)

            # Update player and enemies
            player.update(change_timer, dt)
            spawner.update(dt)
            enemy_group.update(dt)

            # Update bullets
            for bullet in list(bullet_group):
                bullet.bullet_movement()
                bullet.bullet_collisions()

            for particle in particles[:]:  # Iterate over a copy of the list to avoid issues when removing particles
              particle.update(dt)
              if particle.life <= 0 or particle.radius <= 0:
                 particles.remove(particle)

            # Update visual effects
            pulse.update(player.rhythm_meter, dt)
            border_pulse.update(player.rhythm_meter, dt)

            # 1. Draw background
            screen.blit(background, background_rect)

            # 2. Draw animated dance floor over the carpet
            disco_floor(screen, tiles, FLOOR_RECT)

            # 3. Draw player, enemies and bullets
            all_sprites_group.draw(screen)

        #pygame.draw.rect(screen, "red", player.hitbox_rect, width=2) #hitbox 1
        #pygame.draw.rect(screen, "yellow", player.rect, width=2) #hitbox 2
        #for w in WALL_RECTS: #debug for wall hitboxes
            #pygame.draw.rect(screen, "cyan", w, width=2)/
        all_sprites_group.draw(screen)


        for enemy in enemy_group:
            enemy.draw_health_bar()
        # Draw screen pulse over the game world
        pulse.draw(screen)
        # Draw border pulse over the game world
        border_pulse.draw(screen)

        # Draw UI last so it stays visible
        ui.update(survival_time)
        draw_beat_ring(screen, change_timer)

        # Draw particles LAST so they appear above everything
        for particle in particles:
            particle.draw(screen)

        if game_state == DEAD:
             draw_death_screen()

        elif game_state == WON:
             draw_win_screen()

        pygame.display.flip()

def draw_death_screen():
    screen.fill((12, 3, 5))

    title_font = pygame.font.Font("assets/PublicPixel.ttf", 110)
    prompt_font = pygame.font.Font("assets/PublicPixel.ttf", 40)

    title = title_font.render("WASTED", True, (200, 25, 35))
    prompt = prompt_font.render("PRESS R TO RESTART", True, (190, 170, 170))

    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
    screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 45)))


def draw_win_screen():
    screen.fill((5, 4, 15))

    title_font = pygame.font.Font("assets/PublicPixel.ttf", 110)
    prompt_font = pygame.font.Font("assets/PublicPixel.ttf", 40)

    title = title_font.render("YOU WIN", True, (180, 100, 255))
    prompt = prompt_font.render("PRESS ESC TO QUIT", True, (190, 180, 210))

    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
    screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 45)))

if __name__ == "__main__":
    pygame.init()

    main_menu()
    main()
