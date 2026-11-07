# game setup
WIDTH = 1280	
HEIGHT = 720
FPS      = 60

# Tile setup
TILESIZE = 50
COLS = WIDTH // TILESIZE # columns of disco floor
ROWS = HEIGHT // TILESIZE # rows of disco floor

#player settings
PLAYER_START_X = WIDTH // 2
PLAYER_START_Y = HEIGHT // 2
PLAYER_SPEED = 8
SCALE_FACTOR = 0.35
GUN_OFFSET_X = 45
GUN_OFFSET_Y = 20

# Bullet settings
SHOOT_COOLDOWN = 10
BULLET_SCALE = 1.4
BULLET_SPEED = 50
BULLET_LIFETIME = 750

# Disco colors
colors = [
    (255, 0, 100),    # Pink
    (0, 200, 255),    # Blue
    (150, 0, 255),    # Purple
    (0, 255, 100),    # Green
    (255, 200, 0),    # Yellow
    (255, 50, 0)      # Orange
]
