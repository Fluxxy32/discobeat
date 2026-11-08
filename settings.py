# game setup
WIDTH = 1920	
HEIGHT = 1080
FPS = 60
WIN_TIME = 60000   # ms the player must survive

#spawning
START_MAX_ENEMIES = 3
MAX_ENEMIES = 10
START_SPAWN_DELAY = 3000   # ms
MIN_SPAWN_DELAY = 1200

# Tile setup
TILESIZE = 50
COLS = WIDTH // TILESIZE # columns of disco floor
ROWS = HEIGHT // TILESIZE # rows of disco floor

#player settings
PLAYER_START_X = WIDTH // 2
PLAYER_START_Y = HEIGHT // 2
PLAYER_SPEED = 6
SCALE_FACTOR = 0.35
GUN_OFFSET_X = 45
GUN_OFFSET_Y = 20
PLAYER_HEALTH = 100
DAMAGE_DELAY = 1000  #1 second 

#Enemy settings
ENEMY_SPEED = 4
MIN_ENEMY_DISTANCE = 10
ENEMY_DAMAGE = 10
ENEMY_HEALTH = 100

#UI settings
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)
YELLOW = (255,255,0)
BLACK = (0,0,0)
WHITE = (255,255,255)
CURSOR_SCALE_FACTOR = 2.5
TITLE_FONT_SIZE = 70
BUTTON_FONT_SIZE = 30

# Bullet settings
SHOOT_COOLDOWN = 15
BULLET_SCALE = 1.4
BULLET_SPEED = 50
BULLET_LIFETIME = 750

# Beat settings
BEAT_INTERVAL = 500

PERFECT_WINDOW = 50
GOOD_WINDOW = 70

NORMAL_DAMAGE = 20
GOOD_DAMAGE = 25
PERFECT_DAMAGE = 1000

# Disco colors
colors = [
    (255, 0, 100),    # Pink
    (0, 200, 255),    # Blue
    (150, 0, 255),    # Purple
    (0, 255, 100),    # Green
    (255, 200, 0),    # Yellow
    (255, 50, 0)      # Orange
]
