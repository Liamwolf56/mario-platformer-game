import pygame
import os
import random

# --- Game Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_WIDTH = 32
PLAYER_HEIGHT = 32
PLATFORM_HEIGHT = 20
COIN_SIZE = 30
ENEMY_WIDTH = 40
ENEMY_HEIGHT = 50
ENEMY_SPEED = 2
PROJECTILE_SIZE = 20
SHIELD_WIDTH = 40
SHIELD_HEIGHT = 40
ATTACK_RANGE_SLASH = 40 # Pixels for close-range attack
ATTACK_RANGE_BLAST = 200 # Pixels for far-range attack
ATTACK_COOLDOWN = 30 # Frames for cooldown (e.g., 0.5 seconds at 60 FPS)
SHIELD_DURATION = 60 # Frames for shield duration (e.g., 1 second at 60 FPS)
BLAST_SPEED = 10

# Colors (RGB tuples)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0) # Used for menu text and default background
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0) # For lives text and Game Over
GRAY = (150, 150, 150, 100) # For pause overlay (R,G,B, Alpha)
LIGHT_BLUE = (173, 216, 230) # For testing background visibility if image fails
PURPLE = (128, 0, 128) # For blast projectile
LIGHT_GRAY = (200, 200, 200) # For shield visual fallback

# Player physics constants
GRAVITY = 0.5
JUMP_STRENGTH = -10
PLAYER_SPEED = 5
MAX_JUMPS = 2

# Game variables
INITIAL_LIVES = 3

# High Score File
HIGHSCORE_FILE = "highscore.txt"

# Declare these as global variables at the module level.
# They will be initialized by setup_game or directly here.
player = None
all_sprites = pygame.sprite.Group()
platforms = pygame.sprite.Group()
moving_platforms = pygame.sprite.Group()
coins = pygame.sprite.Group()
enemies = pygame.sprite.Group()
projectiles = pygame.sprite.Group() # New: for blast attacks
shields = pygame.sprite.Group()     # New: for player shield
score = 0
lives = INITIAL_LIVES
initial_coin_count_level = 0
current_game_state = 0 # Initialize here too, as it's modified globally
high_score = 0 # Initialize high score


# --- Game States ---
GAME_STATE_MENU = 0
GAME_STATE_PLAYING = 1
GAME_STATE_PAUSED = 2
GAME_STATE_GAMEOVER = 3
GAME_STATE_LEVEL_COMPLETE = 4

# Initialize Pygame
pygame.init()

# Set up the display screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Boot.dev Platformer")

# Create a clock object
clock = pygame.time.Clock()

# Set up fonts
font = pygame.font.Font(None, 36)
menu_font_large = pygame.font.Font(None, 74)
menu_font_medium = pygame.font.Font(None, 40) # New font size for subheadings
menu_font_small = pygame.font.Font(None, 30) # Adjusted for controls list
game_over_font = pygame.font.Font(None, 100)


# --- Load Global Assets ---
BACKGROUND_IMAGE = None # Initialize to None
try:
    BACKGROUND_IMAGE = pygame.image.load('background_image.png').convert()
    BACKGROUND_IMAGE = pygame.transform.scale(BACKGROUND_IMAGE, (SCREEN_WIDTH, SCREEN_HEIGHT))
    print("Asset Load: background_image.png loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - background_image.png not found. Using default light blue background.")
    pass # No default image, will use screen.fill(LIGHT_BLUE) later

# New Combat Assets
SLASH_IMAGE = None
try:
    SLASH_IMAGE = pygame.image.load('image_628cc4.png').convert_alpha()
    SLASH_IMAGE = pygame.transform.scale(SLASH_IMAGE, (PLAYER_WIDTH * 2, PLAYER_HEIGHT * 2)) # Larger for effect
    print("Asset Load: image_628cc4.png (Slash) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_628cc4.png (Slash) not found.")

BLAST_IMAGE = None
try:
    BLAST_IMAGE = pygame.image.load('image_629081.png').convert_alpha()
    BLAST_IMAGE = pygame.transform.scale(BLAST_IMAGE, (PROJECTILE_SIZE * 2, PROJECTILE_SIZE * 2)) # Larger than actual collision size
    print("Asset Load: image_629081.png (Blast) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_629081.png (Blast) not found.")

SHIELD_IMAGE = None
try:
    SHIELD_IMAGE = pygame.image.load('image_62e378.jpg').convert_alpha()
    SHIELD_IMAGE = pygame.transform.scale(SHIELD_IMAGE, (SHIELD_WIDTH, SHIELD_HEIGHT))
    print("Asset Load: image_62e378.jpg (Shield) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_62e378.jpg (Shield) not found.")


# --- High Score Functions ---
def load_high_score():
    """Loads the high score from a file."""
    global high_score
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r") as file:
                high_score = int(file.read())
            print(f"High Score: Loaded {high_score}")
        except ValueError:
            high_score = 0 # Reset if file content is invalid
            print("High Score: Invalid content in file, resetting to 0.")
        except Exception as e:
            high_score = 0
            print(f"High Score: Error loading file: {e}, resetting to 0.")
    else:
        high_score = 0
        print("High Score: File not found, starting with 0.")

def save_high_score(current_score):
    """Saves the high score to a file if current_score is higher."""
    global high_score
    if current_score > high_score:
        high_score = current_score
        with open(HIGHSCORE_FILE, "w") as file:
            file.write(str(high_score))
        print(f"High Score: New high score saved: {high_score}")
    else:
        print(f"High Score: Current score {current_score} not higher than {high_score}.")

# Load high score once at the start of the game
load_high_score()

# --- Game Classes ---

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width):
        super().__init__()
        self.image = pygame.Surface([width, PLATFORM_HEIGHT])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(x, y))

class MovingPlatform(Platform):
    def __init__(self, x, y, width, start_x, end_x, speed):
        super().__init__(x, y, width)
        self.start_x = start_x
        self.end_x = end_x
        self.vel_x = speed
        self.image.fill(BLUE) # Different color for moving platform

    def update(self):
        self.rect.x += self.vel_x
        if self.vel_x > 0 and self.rect.right > self.end_x:
            self.rect.right = self.end_x
            self.vel_x *= -1
        elif self.vel_x < 0 and self.rect.left < self.start_x:
            self.rect.left = self.start_x
            self.vel_x *= -1

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.image = pygame.image.load('coin_sprite.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (COIN_SIZE, COIN_SIZE))
        except pygame.error:
            self.image = pygame.Surface([COIN_SIZE, COIN_SIZE], pygame.SRCALPHA)
            pygame.draw.circle(self.image, YELLOW, (COIN_SIZE // 2, COIN_SIZE // 2), COIN_SIZE // 2)
        self.rect = self.image.get_rect(topleft=(x, y))

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.image_base = pygame.image.load('player_sprite.png').convert_alpha()
            self.image_base = pygame.transform.scale(self.image_base, (PLAYER_WIDTH, PLAYER_HEIGHT))
        except pygame.error:
            self.image_base = pygame.Surface([PLAYER_WIDTH, PLAYER_HEIGHT])
            self.image_base.fill(BLUE)

        self.image = self.image_base # Current image to display
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.jumps_remaining = MAX_JUMPS

        self.attacking = False # General flag for cooldown
        self.attack_cooldown_timer = 0
        self.facing_right = True # For directing attacks
        self.is_slashing_anim = False # New: for slash visual only

        self.shielding = False
        self.shield_timer = 0
        self.is_invincible = False # Player is invincible when shielding

    def update(self, platforms, moving_platforms):
        # Update cooldown timers
        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= 1
            if self.attack_cooldown_timer == 0:
                self.attacking = False # Reset general attack state
                self.is_slashing_anim = False # Reset slash visual

        # Update shield timer
        if self.shielding:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shielding = False
                self.is_invincible = False
                self.image = self.image_base # Revert to base image

        was_on_ground = self.on_ground
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        self.on_ground = False
        all_ground_surfaces = platforms.sprites() + moving_platforms.sprites()
        for platform in all_ground_surfaces:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0 and self.rect.bottom <= platform.rect.bottom:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    if isinstance(platform, MovingPlatform):
                        self.rect.x += platform.vel_x
                elif self.vel_y < 0 and self.rect.top >= platform.rect.top:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

        if self.on_ground and not was_on_ground:
            self.jumps_remaining = MAX_JUMPS

        self.rect.x += self.vel_x

        for platform in all_ground_surfaces:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0:
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:
                    self.rect.left = platform.rect.right

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        if self.rect.top > SCREEN_HEIGHT:
            global lives, current_game_state # Explicitly declare for modification
            lives -= 1
            if lives <= 0:
                current_game_state = GAME_STATE_GAMEOVER
                save_high_score(score) # Check and save high score on Game Over
            else:
                self.rect.x = 100
                self.rect.y = 100
                self.vel_y = 0
                self.vel_x = 0
                self.jumps_remaining = MAX_JUMPS
                self.is_invincible = False # Ensure invincibility is off after reset
                self.shielding = False # Ensure shielding is off after reset
                self.attack_cooldown_timer = 0 # Reset cooldown
                self.is_slashing_anim = False # Reset slash visual
                # Remove any active shield sprite
                for s in shields:
                    if s.player_ref == self: # Use self instead of player global
                        s.kill()


        # Update player image for facing direction if not currently attacking or shielding
        if not self.attacking and not self.shielding:
            if self.vel_x < 0 and self.facing_right:
                self.image = pygame.transform.flip(self.image_base, True, False)
                self.facing_right = False
            elif self.vel_x > 0 and not self.facing_right:
                self.image = self.image_base
                self.facing_right = True
            elif self.vel_x == 0 and not self.facing_right:
                 # If standing still and facing left, keep flipped image
                self.image = pygame.transform.flip(self.image_base, True, False)
            elif self.vel_x == 0 and self.facing_right:
                # If standing still and facing right, keep original image
                self.image = self.image_base


    def jump(self):
        if self.jumps_remaining > 0:
            self.vel_y = JUMP_STRENGTH
            self.jumps_remaining -= 1

    def move_left(self):
        self.vel_x = -PLAYER_SPEED
        self.facing_right = False

    def move_right(self):
        self.vel_x = PLAYER_SPEED
        self.facing_right = True

    def stop_move(self):
        self.vel_x = 0

    def slash_attack(self):
        if self.attack_cooldown_timer == 0:
            self.attacking = True
            self.is_slashing_anim = True # Activate slash visual
            self.attack_cooldown_timer = ATTACK_COOLDOWN # Set cooldown
            # Create a temporary slash hitbox (visual feedback will be in draw)
            slash_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height)
            if self.facing_right:
                slash_rect.left = self.rect.right # Attack to the right
            else:
                slash_rect.right = self.rect.left # Attack to the left
            slash_rect.width = ATTACK_RANGE_SLASH # Extend hitbox for slash
            return slash_rect
        return None

    def blast_attack(self):
        if self.attack_cooldown_timer == 0:
            self.attacking = True
            self.attack_cooldown_timer = ATTACK_COOLDOWN # Set cooldown
            # Create a projectile
            if self.facing_right:
                blast_x = self.rect.right
                blast_vel_x = BLAST_SPEED
            else:
                blast_x = self.rect.left - PROJECTILE_SIZE
                blast_vel_x = -BLAST_SPEED
            
            blast = Projectile(blast_x, self.rect.centery, blast_vel_x)
            projectiles.add(blast)
            all_sprites.add(blast)
        return None

    def activate_shield(self):
        # Only activate if not already shielding and not currently attacking
        if not self.shielding and not self.attacking:
            self.shielding = True
            self.is_invincible = True
            self.shield_timer = SHIELD_DURATION # Set shield duration
            # Create a shield sprite
            shield_sprite = Shield(self.rect.centerx, self.rect.centery)
            shields.add(shield_sprite)
            all_sprites.add(shield_sprite)


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, vel_x):
        super().__init__()
        self.image_orig = BLAST_IMAGE if BLAST_IMAGE else pygame.Surface([PROJECTILE_SIZE * 2, PROJECTILE_SIZE * 2], pygame.SRCALPHA)
        if not BLAST_IMAGE:
            pygame.draw.circle(self.image_orig, PURPLE, (PROJECTILE_SIZE, PROJECTILE_SIZE), PROJECTILE_SIZE // 2)

        self.image = self.image_orig
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_x = vel_x
        # Projectile disappears after crossing screen width or a set lifetime
        self.lifetime = SCREEN_WIDTH // abs(BLAST_SPEED) + 10 # Added a small buffer
        self.creation_time = pygame.time.get_ticks() # Store creation time for debugging/long-range tracking

    def update(self):
        self.rect.x += self.vel_x
        
        # Check lifetime based on frames, or position for off-screen
        self.lifetime -= 1
        if self.lifetime <= 0 or self.rect.left > SCREEN_WIDTH or self.rect.right < 0:
            self.kill() # Remove projectile if it goes off screen or lifetime expires

class Shield(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = SHIELD_IMAGE if SHIELD_IMAGE else pygame.Surface([SHIELD_WIDTH, SHIELD_HEIGHT], pygame.SRCALPHA)
        if not SHIELD_IMAGE:
            self.image.fill(LIGHT_GRAY) # Default gray if image not loaded
            pygame.draw.rect(self.image, BLUE, self.image.get_rect(), 2) # Add a blue border

        self.rect = self.image.get_rect(center=(x, y))
        self.player_ref = player # Reference to the player it's attached to

    def update(self):
        # Shield should follow the player's position if player is shielding
        if self.player_ref and self.player_ref.shielding:
            self.rect.center = self.player_ref.rect.center
            # Optionally, adjust position slightly based on facing direction
            # This makes the shield appear slightly in front of the player
            if self.player_ref.facing_right:
                self.rect.left = self.player_ref.rect.right - (SHIELD_WIDTH // 4)
            else:
                self.rect.right = self.player_ref.rect.left + (SHIELD_WIDTH // 4)
        else:
            self.kill() # Remove shield if player is no longer shielding


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_range=100):
        super().__init__()
        try:
            self.image_base = pygame.image.load('enemy_sprite.png').convert_alpha()
            self.image_base = pygame.transform.scale(self.image_base, (ENEMY_WIDTH, ENEMY_HEIGHT))
        except pygame.error:
            self.image_base = pygame.Surface([ENEMY_WIDTH, ENEMY_HEIGHT])
            self.image_base.fill(RED)
        
        self.image = self.image_base # Current image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = ENEMY_SPEED
        self.vel_y = 0
        self.start_x = x
        self.patrol_range = patrol_range
        self.on_ground = False
        self.facing_right = True # For directing enemy visual

    def update(self, platforms, moving_platforms):
        all_ground_surfaces = platforms.sprites() + moving_platforms.sprites()
        
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        self.on_ground = False
        for platform in all_ground_surfaces:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0 and self.rect.bottom <= platform.rect.bottom:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0 and self.rect.top >= platform.rect.top:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

        # Update facing direction for visual flip
        if self.vel_x > 0 and not self.facing_right:
            self.image = self.image_base
            self.facing_right = True
        elif self.vel_x < 0 and self.facing_right:
            self.image = pygame.transform.flip(self.image_base, True, False)
            self.facing_right = False


        self.rect.x += self.vel_x
        
        if self.vel_x > 0 and self.rect.right >= self.start_x + self.patrol_range:
            self.vel_x = -ENEMY_SPEED
        elif self.vel_x < 0 and self.rect.left <= self.start_x - self.patrol_range:
            self.vel_x = ENEMY_SPEED

        # Enemy edge detection (so they don't walk off platforms)
        hit_edge = True
        for platform in all_ground_surfaces:
            if self.vel_x > 0:
                # Check directly in front and slightly below the enemy's bottom-right corner
                check_point_x = self.rect.right
            else:
                # Check directly in front and slightly below the enemy's bottom-left corner
                check_point_x = self.rect.left

            # Create a small rect to check for ground beneath
            check_rect = pygame.Rect(check_point_x, self.rect.bottom + 1, 5, 5) # Check 1 pixel below

            if check_rect.colliderect(platform.rect):
                hit_edge = False
                break
        
        if hit_edge and self.on_ground:
            self.vel_x *= -1 # Turn around if about to walk off an edge


# --- Game Setup Function ---
def setup_game():
    global player, all_sprites, platforms, moving_platforms, coins, enemies, projectiles, shields, score, lives, initial_coin_count_level

    # These are assignments to the globally declared variables
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    moving_platforms = pygame.sprite.Group()
    coins = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    projectiles = pygame.sprite.Group() # Reset projectiles
    shields = pygame.sprite.Group()     # Reset shields

    score = 0
    lives = INITIAL_LIVES

    player = Player(100, SCREEN_HEIGHT - 100)
    all_sprites.add(player)

    ground = Platform(0, SCREEN_HEIGHT - PLATFORM_HEIGHT, SCREEN_WIDTH)
    platforms.add(ground)
    all_sprites.add(ground)

    num_static_platforms = random.randint(3, 7)
    for _ in range(num_static_platforms):
        x = random.randint(50, SCREEN_WIDTH - 150)
        y = random.randint(SCREEN_HEIGHT // 3, SCREEN_HEIGHT - 150)
        width = random.randint(80, 200)
        new_platform = Platform(x, y, width)
        platforms.add(new_platform)
        all_sprites.add(new_platform)
    
    num_moving_platforms = random.randint(1, 3)
    for _ in range(num_moving_platforms):
        width = random.randint(60, 120)
        start_x = random.randint(50, SCREEN_WIDTH - 200)
        end_x = random.randint(start_x + 50, SCREEN_WIDTH - width - 20)
        y = random.randint(SCREEN_HEIGHT // 3, SCREEN_HEIGHT - 150)
        speed = random.choice([-ENEMY_SPEED, ENEMY_SPEED])

        new_moving_platform = MovingPlatform(start_x, y, width, start_x, end_x, speed)
        moving_platforms.add(new_moving_platform)
        all_sprites.add(new_moving_platform)


    all_available_platforms = list(platforms.sprites()) + list(moving_platforms.sprites())
    
    initial_coin_count_level = random.randint(5, 15)

    for _ in range(initial_coin_count_level):
        if not all_available_platforms:
            break
        target_platform = random.choice(all_available_platforms)
        
        coin_x = random.randint(target_platform.rect.left + COIN_SIZE, target_platform.rect.right - COIN_SIZE)
        coin_y = target_platform.rect.top - COIN_SIZE - random.randint(10, 30)

        new_coin = Coin(coin_x, coin_y)
        coins.add(new_coin)
        all_sprites.add(new_coin)

    num_enemies = random.randint(1, 3)
    for _ in range(num_enemies):
        if not all_available_platforms:
            break
        target_platform = random.choice(all_available_platforms)
        enemy_x = random.randint(target_platform.rect.left, target_platform.rect.right - ENEMY_WIDTH)
        enemy_y = target_platform.rect.top - ENEMY_HEIGHT

        new_enemy = Enemy(enemy_x, enemy_y)
        enemies.add(new_enemy)
        all_sprites.add(new_enemy)


# --- Initial Game State ---
# current_game_state is already initialized globally at the top
setup_game() # Initialize game objects for the first time


# --- Game Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if current_game_state == GAME_STATE_MENU:
            if event.type == pygame.KEYDOWN:
                current_game_state = GAME_STATE_PLAYING
                setup_game() # Start a new game, resetting score and lives
                load_high_score() # Reload high score just in case it was changed elsewhere
        elif current_game_state == GAME_STATE_PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    player.move_left()
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    player.move_right()
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    player.jump()
                if event.key == pygame.K_j: # New: Slash attack (close range)
                    slash_rect = player.slash_attack()
                    if slash_rect:
                        # Create a temporary sprite for collision detection with the Rect
                        temp_slash_sprite = pygame.sprite.Sprite()
                        temp_slash_sprite.rect = slash_rect
                        hit_enemies = pygame.sprite.spritecollide(temp_slash_sprite, enemies, True) # True to kill enemy
                        for enemy in hit_enemies:
                            score += 10 # More points for defeating enemies
                if event.key == pygame.K_k: # New: Blast attack (far range)
                    player.blast_attack()
                if event.key == pygame.K_l: # New: Shield activation
                    player.activate_shield()
                if event.key == pygame.K_ESCAPE: # Press ESC to go back to menu
                    current_game_state = GAME_STATE_MENU
                    setup_game() # Reset level when returning to menu
                    save_high_score(score) # Check and save high score if returning to menu
                    load_high_score() # Reload high score for menu display
                if event.key == pygame.K_p: # New: Press 'P' to pause
                    current_game_state = GAME_STATE_PAUSED
            if event.type == pygame.KEYUP:
                if (event.key == pygame.K_LEFT or event.key == pygame.K_a) and player.vel_x < 0:
                    player.stop_move()
                if (event.key == pygame.K_RIGHT or event.key == pygame.K_d) and player.vel_x > 0:
                    player.stop_move()
        elif current_game_state == GAME_STATE_PAUSED:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p: # Press 'P' to unpause
                    current_game_state = GAME_STATE_PLAYING
                if event.key == pygame.K_ESCAPE: # Press ESC to return to menu from pause
                    current_game_state = GAME_STATE_MENU
                    setup_game() # Reset level
                    save_high_score(score) # Check and save high score if returning to menu
                    load_high_score() # Reload high score for menu display
        elif current_game_state == GAME_STATE_GAMEOVER:
            if event.type == pygame.KEYDOWN: # Listen for any key press to return to menu
                current_game_state = GAME_STATE_MENU
                setup_game() # Reset level and prepare for new game from menu
                load_high_score() # Reload high score for menu display

        elif current_game_state == GAME_STATE_LEVEL_COMPLETE:
            if event.type == pygame.KEYDOWN: # Listen for any key press to go to next level
                current_game_state = GAME_STATE_PLAYING # Transition to playing state
                setup_game() # Setup a new random level
                load_high_score() # Reload high score just in case


    # --- Drawing and Game Logic (moved here for continuous updates) ---
    if BACKGROUND_IMAGE:
        screen.blit(BACKGROUND_IMAGE, (0, 0))
    else:
        screen.fill(LIGHT_BLUE) # Fill with light blue if background image is missing

    if current_game_state == GAME_STATE_PLAYING:
        # Update sprites
        player.update(platforms, moving_platforms)
        enemies.update(platforms, moving_platforms)
        moving_platforms.update()
        projectiles.update() # Update projectiles
        shields.update()     # Update shields

        # Player-Enemy Collision (Player takes damage unless shielding)
        colliding_enemies = pygame.sprite.spritecollide(player, enemies, False)
        for enemy in colliding_enemies:
            if not player.is_invincible: # Player only takes damage if not shielding
                lives -= 1
                # Reset player position
                player.rect.x = 100
                player.rect.y = 100
                player.vel_y = 0
                player.vel_x = 0
                player.jumps_remaining = MAX_JUMPS
                player.is_invincible = False # Ensure invincibility is off after reset
                player.shielding = False # Ensure shielding is off after reset
                player.attack_cooldown_timer = 0 # Reset cooldown
                player.is_slashing_anim = False # Reset slash visual
                # Remove any active shield sprite
                for s in shields:
                    if s.player_ref == player:
                        s.kill()

                if lives <= 0:
                    current_game_state = GAME_STATE_GAMEOVER
                    save_high_score(score) # Check and save high score on Game Over
            else:
                # If player is invincible (shielding), enemies are temporarily pushed back or ignore collision
                # For now, let's just make the enemy turn around
                enemy.vel_x *= -1


        # Projectile-Enemy Collision
        for projectile in projectiles:
            hit_enemies = pygame.sprite.spritecollide(projectile, enemies, True) # True to kill enemy
            for enemy in hit_enemies:
                projectile.kill() # Destroy projectile on hit
                score += 10 # More points for defeating enemies


        # Player-Coin Collision
        collected_coins = pygame.sprite.spritecollide(player, coins, True) # True means remove coin on collision
        for coin in collected_coins:
            score += 1


        # Check for Level Complete
        if len(coins) == 0 and initial_coin_count_level > 0:
            current_game_state = GAME_STATE_LEVEL_COMPLETE
            save_high_score(score) # Check and save high score on Level Complete
        
        # Draw all sprites
        all_sprites.draw(screen)

        # Draw slash attack visual ONLY if is_slashing_anim is true
        if player.is_slashing_anim and SLASH_IMAGE:
            if player.facing_right:
                slash_draw_x = player.rect.right - (PLAYER_WIDTH // 2)
            else:
                slash_draw_x = player.rect.left - SLASH_IMAGE.get_width() + (PLAYER_WIDTH // 2)
            screen.blit(SLASH_IMAGE, (slash_draw_x, player.rect.centery - SLASH_IMAGE.get_height() // 2))

        # Draw score and lives in PLAYING state
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        lives_text = font.render(f"Lives: {lives}", True, RED)
        screen.blit(lives_text, (SCREEN_WIDTH - lives_text.get_width() - 10, 10))

    elif current_game_state == GAME_STATE_MENU:
        # Display Title
        title_text = menu_font_large.render("Boot.dev Platformer", True, BLACK)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 200))
        screen.blit(title_text, title_rect)

        # Display High Score on Menu
        high_score_text = menu_font_medium.render(f"High Score: {high_score}", True, BLACK)
        high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
        screen.blit(high_score_text, high_score_rect)


        # Display Controls
        controls_title = menu_font_medium.render("Controls:", True, BLACK)
        controls_title_rect = controls_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        screen.blit(controls_title, controls_title_rect)

        control_lines = [
            "Arrow Keys / WASD: Move Left/Right & Jump",
            "J: Slash Attack (close range)", # New control
            "K: Blast Attack (far range)",   # New control
            "L: Activate Shield",            # New control
            "P: Pause / Resume Game",
            "ESC: Return to Menu (from Game or Pause)",
            "Collect all Coins to complete the level!"
        ]
        
        y_offset = SCREEN_HEIGHT // 2 + 0 # Starting Y for controls list
        for line in control_lines:
            line_text = menu_font_small.render(line, True, BLACK)
            line_rect = line_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            screen.blit(line_text, line_rect)
            y_offset += 35 # Spacing between lines

        # "Press any key to start"
        start_text = menu_font_medium.render("Press any key to START!", True, BLACK)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200))
        screen.blit(start_text, start_rect)


    elif current_game_state == GAME_STATE_PAUSED:
        all_sprites.draw(screen) # Draw game elements first
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(GRAY) # This is 100 alpha, so translucent
        screen.blit(overlay, (0, 0))

        pause_text = menu_font_large.render("PAUSED", True, WHITE)
        resume_text = menu_font_small.render("Press 'P' to resume", True, WHITE)
        menu_return_text = font.render("Press 'ESC' to return to menu", True, WHITE)

        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        menu_return_rect = menu_return_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))

        screen.blit(pause_text, pause_rect)
        screen.blit(resume_text, resume_rect)
        screen.blit(menu_return_text, menu_return_rect)

        # Draw score and lives in PAUSED state
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        lives_text = font.render(f"Lives: {lives}", True, RED)
        screen.blit(lives_text, (SCREEN_WIDTH - lives_text.get_width() - 10, 10))

    # --- Drawing for Game Over state (moved outside event loop for continuous refresh) ---
    elif current_game_state == GAME_STATE_GAMEOVER:
        game_over_text = game_over_font.render("GAME OVER!", True, RED)
        final_score_text = menu_font_medium.render(f"Final Score: {score}", True, WHITE)
        high_score_display_text = menu_font_small.render(f"High Score: {high_score}", True, WHITE)
        restart_text = font.render("Press any key to return to menu", True, WHITE)

        go_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        hs_display_rect = high_score_display_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))

        screen.blit(game_over_text, go_rect)
        screen.blit(final_score_text, score_rect)
        screen.blit(high_score_display_text, hs_display_rect)
        screen.blit(restart_text, restart_rect)

    # --- Drawing for Level Complete state (moved outside event loop for continuous refresh) ---
    elif current_game_state == GAME_STATE_LEVEL_COMPLETE:
        level_complete_text = game_over_font.render("LEVEL COMPLETE!", True, GREEN)
        current_score_text = menu_font_medium.render(f"Score: {score}", True, WHITE)
        high_score_display_text = menu_font_small.render(f"High Score: {high_score}", True, WHITE)
        next_level_text = font.render("Press any key for next level", True, WHITE)

        lc_rect = level_complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        score_rect = current_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        hs_display_rect = high_score_display_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        next_rect = next_level_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))

        screen.blit(level_complete_text, lc_rect)
        screen.blit(current_score_text, score_rect)
        screen.blit(high_score_display_text, hs_display_rect)
        screen.blit(next_level_text, next_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
