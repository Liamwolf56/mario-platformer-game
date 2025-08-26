import pygame
import os
import random
import math
import json

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
ATTACK_COOLDOWN = 30 # Frames for cooldown (e.g., 0.5 seconds at 60 FPS)
SHIELD_DURATION = 60 # Frames for shield duration (e.g., 1 second at 60 FPS)
BLAST_SPEED = 10
ROLL_DURATION = 15 # Frames for roll (e.g., 0.25 seconds)
ROLL_SPEED_MULTIPLIER = 2.5 # How much faster the player moves when rolling
ROLL_COOLDOWN = 60 # Frames (1 second cooldown after a roll)
FIRE_DASH_DURATION = 20 # Frames for fire dash
FIRE_DASH_SPEED_MULTIPLIER = 4 # How much faster the player moves during fire dash
FIRE_DASH_COOLDOWN = 120 # Frames (2 seconds cooldown for fire dash)


# Boss Constants
BOSS_WIDTH = 80
BOSS_HEIGHT = 100
BOSS_HEALTH_MAX = 100
BOSS_SPEED = 1 # Slower movement for boss
BOSS_PATROL_RANGE = 200
BOSS_BLAST_COOLDOWN = 90 # Frames (1.5 seconds at 60 FPS)
BOSS_PROJECTILE_SIZE = 30
BOSS_PROJECTILE_SPEED = 7

# New Enemy Constants
SHOOTER_ENEMY_WIDTH = 48
SHOOTER_ENEMY_HEIGHT = 48
SHOOTER_SPEED = 1.5
SHOOTER_BLAST_COOLDOWN = 120 # Frames (2 seconds)
SHOOTER_PROJECTILE_SIZE = 25
SHOOTER_PROJECTILE_SPEED = 6

GUARD_ENEMY_WIDTH = 40
GUARD_ENEMY_HEIGHT = 50
GUARD_HEALTH_MAX = 3 # Guard enemies take 3 hits
GUARD_SPEED = 1 # Slower than regular enemies

FLYER_ENEMY_WIDTH = 50
FLYER_ENEMY_HEIGHT = 50
FLYER_SPEED = 1.5
FLYER_VERTICAL_OSCILLATION_MAGNITUDE = 30 # How high up/down they oscillate
FLYER_VERTICAL_OSCILLATION_SPEED = 0.05 # How fast they oscillate

# Colors (RGB tuples)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0) # Used for menu text and default background
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0) # For lives text and Game Over
GRAY = (150, 150, 150, 100) # For pause overlay (R,G,B, Alpha)
LIGHT_BLUE = (173, 216, 230) # For testing background visibility if image fails
PURPLE = (128, 0, 128) # For player blast projectile
LIGHT_GRAY = (200, 200, 200) # For shield visual fallback
DARK_GRAY = (50, 50, 50) # For boss health bar background
BOSS_PURPLE = (100, 0, 100) # For boss projectile fallback
BOSS_HEALTH_COLOR = (255, 0, 0) # Red for boss health bar
ORANGE = (255, 165, 0) # For selected player text
GOLD = (255, 215, 0) # For weapon select highlights
ENEMY_GREEN = (0, 150, 0) # Default enemy color if image fails
FIRE_RED = (255, 50, 0, 180) # For fire dash visual (R,G,B, Alpha)
FLYER_TEAL = (0, 128, 128) # Fallback for flyer enemy


# Player physics constants
GRAVITY = 0.5
JUMP_STRENGTH = -10 # Magnitude of jump velocity
PLAYER_SPEED = 5
MAX_JUMPS = 2
MAX_FALL_VELOCITY = 15 # Cap player's fall speed

# Game variables
INITIAL_LIVES = 3
BOSS_APPEAR_INTERVAL = 5 # Boss appears every 5 levels
# Maximum vertical distance player can jump relative to previous platform
MAX_PLATFORM_JUMP_HEIGHT = 180 # Pixels (allows for comfortable double jumping to next platform)

# Power-up specific constants
BLAST_ATTACK_UNLOCK_LEVEL = 1 # Player gets blast attack from level 2 (current_level 1)
POWERUP_SPAWN_INTERVAL = 3 # Power-ups appear every 3 levels
ORBIT_SHIELD_MAX_HITS = 5 # Max hits the orbiting shield can block
ORBIT_SHIELD_RADIUS = 30 # Radius of orbit around the player
ORBIT_SHIELD_SIZE = 20 # Size of the orbiting light sprite
QUAD_JUMP_COUNT = 4 # How many jumps the 4x Jump powerup gives

# Weapon Specific Constants
ATTACK_RANGE_SLASH = 40 # Default slash range
ATTACK_RANGE_BIG_SWORD = 70 # Big sword range
KNOCKBACK_STRENGTH = 20 # Pixels to knock back enemies
FIRE_DASH_DAMAGE_MULTIPLIER = 5 # 5x damage for fire dash

# New Enemy Spawn Levels
NEW_ENEMY_SPAWN_LEVEL = 3 # New enemy types (Shooter, Guard) appear after level 3 (current_level >= 3)


# --- File Paths ---
PLAYER_PROFILES_FILE = "player_profiles.json" # For multiple player profiles

# Declare these as global variables at the module level.
player = None # This will be initialized once, outside setup_game
all_sprites = pygame.sprite.Group()
platforms = pygame.sprite.Group()
moving_platforms = pygame.sprite.Group()
coins = pygame.sprite.Group()
enemies = pygame.sprite.Group() # Holds regular and guard enemies
shooter_enemies = pygame.sprite.Group() # New: for shooter enemies
shooter_projectiles = pygame.sprite.Group() # New: for shooter projectiles
flyer_enemies = pygame.sprite.Group() # New: for flyer enemies
projectiles = pygame.sprite.Group() # Player blast projectiles
shields = pygame.sprite.Group()     # Player shield visual
powerups = pygame.sprite.Group()    # New: Group for power-up items
orbiting_lights_group = pygame.sprite.Group() # Global group for all orbiting lights

# Boss related global variables
boss_active = False
boss_sprite = None
boss_projectiles = pygame.sprite.Group() # Boss dark blast projectiles

score = 0
lives = INITIAL_LIVES
current_level = 0 # Track the current level

# Multi-player profiles
player_profiles = [] # List of dictionaries: [{'name': 'Liam', 'high_score': 0}, ...]
selected_player_index = -1 # Index of the currently active player in player_profiles
selected_player_name = "Guest" # Display name of the currently active player
high_score = 0 # High score for the currently selected player (updated from profile)

initial_coin_count_level = 0 # This helps determine if level is complete even if no coins left

current_game_state = 0 # Initialize here to GAME_STATE_MENU


# --- Game States ---
GAME_STATE_MENU = 0
GAME_STATE_PLAYING = 1
GAME_STATE_PAUSED = 2
GAME_STATE_GAMEOVER = 3
GAME_STATE_LEVEL_COMPLETE = 4
GAME_STATE_BOSS_FIGHT = 5 # New state for boss battle
GAME_STATE_PLAYER_SELECT = 6 # New state for player selection
GAME_STATE_CREATE_PLAYER = 7 # New state for creating a new player
GAME_STATE_WEAPON_SELECT = 8 # New state for weapon selection


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

# Player Combat Assets
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

# Boss Assets
BOSS_IMAGE = None
try:
    BOSS_IMAGE = pygame.image.load('image_a5e99a.png').convert_alpha()
    BOSS_IMAGE = pygame.transform.scale(BOSS_IMAGE, (BOSS_WIDTH, BOSS_HEIGHT))
    print("Asset Load: image_a5e99a.png (Boss) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_a5e99a.png (Boss) not found.")

DARK_BLAST_IMAGE = None
try:
    DARK_BLAST_IMAGE = pygame.image.load('image_a5e960.png').convert_alpha()
    DARK_BLAST_IMAGE = pygame.transform.scale(DARK_BLAST_IMAGE, (BOSS_PROJECTILE_SIZE, BOSS_PROJECTILE_SIZE))
    print("Asset Load: image_a5e960.png (Dark Blast) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_a5e960.png (Dark Blast) not found.")

# Power-up Images
DOUBLE_BLAST_POWERUP_IMAGE = None
try:
    DOUBLE_BLAST_POWERUP_IMAGE = pygame.image.load('image_893031.png').convert_alpha()
    DOUBLE_BLAST_POWERUP_IMAGE = pygame.transform.scale(DOUBLE_BLAST_POWERUP_IMAGE, (COIN_SIZE, COIN_SIZE))
    print("Asset Load: image_893031.png (Double Blast Powerup) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_893031.png (Double Blast Powerup) not found.")

ORBIT_SHIELD_POWERUP_IMAGE = None
try:
    ORBIT_SHIELD_POWERUP_IMAGE = pygame.image.load('image_892ff0.png').convert_alpha()
    ORBIT_SHIELD_POWERUP_IMAGE = pygame.transform.scale(ORBIT_SHIELD_POWERUP_IMAGE, (COIN_SIZE, COIN_SIZE))
    print("Asset Load: image_892ff0.png (Orbit Shield Powerup) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_892ff0.png (Orbit Shield Powerup) not found.")

ORBITING_LIGHT_IMAGE = None # Will use the same image as Orbit Shield Powerup, but scaled smaller
try:
    ORBITING_LIGHT_IMAGE = pygame.image.load('image_892ff0.png').convert_alpha()
    ORBITING_LIGHT_IMAGE = pygame.transform.scale(ORBITING_LIGHT_IMAGE, (ORBIT_SHIELD_SIZE, ORBIT_SHIELD_SIZE))
    print("Asset Load: image_892ff0.png (Orbiting Light) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_892ff0.png (Orbiting Light) not found.")

JUMP_POWERUP_IMAGE = None
try:
    JUMP_POWERUP_IMAGE = pygame.image.load('image_7d564d.png').convert_alpha()
    JUMP_POWERUP_IMAGE = pygame.transform.scale(JUMP_POWERUP_IMAGE, (COIN_SIZE, COIN_SIZE))
    print("Asset Load: image_7d564d.png (Jump Powerup) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_7d564d.png (Jump Powerup) not found.")

LIFE_POWERUP_IMAGE = None # New image for extra life
try:
    LIFE_POWERUP_IMAGE = pygame.image.load('image_33b612.jpg').convert_alpha()
    LIFE_POWERUP_IMAGE = pygame.transform.scale(LIFE_POWERUP_IMAGE, (COIN_SIZE, COIN_SIZE))
    print("Asset Load: image_33b612.jpg (Life Powerup) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_33b612.jpg (Life Powerup) not found.")

# Weapon Images
BIG_SWORD_IMAGE = None
try:
    BIG_SWORD_IMAGE = pygame.image.load('image_335fbb.png').convert_alpha()
    BIG_SWORD_IMAGE = pygame.transform.scale(BIG_SWORD_IMAGE, (PLAYER_WIDTH * 2, PLAYER_HEIGHT * 2))
    print("Asset Load: image_335fbb.png (Big Sword) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_335fbb.png (Big Sword) not found.")

DAGGER_IMAGE = None
try:
    DAGGER_IMAGE = pygame.image.load('image_3358d3.png').convert_alpha()
    DAGGER_IMAGE = pygame.transform.scale(DAGGER_IMAGE, (PLAYER_WIDTH * 2, PLAYER_HEIGHT * 2))
    print("Asset Load: image_3358d3.png (Dagger) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_3358d3.png (Dagger) not found.")

CLUB_IMAGE = None
try:
    CLUB_IMAGE = pygame.image.load('image_33541d.jpg').convert_alpha()
    CLUB_IMAGE = pygame.transform.scale(CLUB_IMAGE, (PLAYER_WIDTH * 2, PLAYER_HEIGHT * 2))
    print("Asset Load: image_33541d.jpg (Club) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_33541d.jpg (Club) not found.")

# Enemy Images
REGULAR_ENEMY_IMAGE = None # New: For generic enemies
try:
    # Assuming 'enemy_sprite.png' is the generic enemy sprite used previously
    REGULAR_ENEMY_IMAGE = pygame.image.load('enemy_sprite.png').convert_alpha()
    REGULAR_ENEMY_IMAGE = pygame.transform.scale(REGULAR_ENEMY_IMAGE, (ENEMY_WIDTH, ENEMY_HEIGHT))
    print("Asset Load: enemy_sprite.png (Regular Enemy) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - enemy_sprite.png (Regular Enemy) not found. Using default color.")


SHOOTER_ENEMY_IMAGE = None
try:
    SHOOTER_ENEMY_IMAGE = pygame.image.load('image_333e73.png').convert_alpha()
    SHOOTER_ENEMY_IMAGE = pygame.transform.scale(SHOOTER_ENEMY_IMAGE, (SHOOTER_ENEMY_WIDTH, SHOOTER_ENEMY_HEIGHT))
    print("Asset Load: image_333e73.png (Shooter Enemy) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_333e73.png (Shooter Enemy) not found.")

SHOOTER_PROJECTILE_IMAGE = None
try:
    SHOOTER_PROJECTILE_IMAGE = pygame.image.load('image_334931.png').convert_alpha()
    SHOOTER_PROJECTILE_IMAGE = pygame.transform.scale(SHOOTER_PROJECTILE_IMAGE, (SHOOTER_PROJECTILE_SIZE, SHOOTER_PROJECTILE_SIZE))
    print("Asset Load: image_334931.png (Shooter Projectile) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_334931.png (Shooter Projectile) not found.")

GUARD_ENEMY_IMAGE = None
try:
    GUARD_ENEMY_IMAGE = pygame.image.load('image_016ed6.png').convert_alpha()
    GUARD_ENEMY_IMAGE = pygame.transform.scale(GUARD_ENEMY_IMAGE, (GUARD_ENEMY_WIDTH, GUARD_ENEMY_HEIGHT))
    print("Asset Load: image_016ed6.png (Guard Enemy) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_016ed6.png (Guard Enemy) not found.")

FLYER_ENEMY_IMAGE = None # New: For flyer enemies
try:
    FLYER_ENEMY_IMAGE = pygame.image.load('image_f33c19.png').convert_alpha()
    FLYER_ENEMY_IMAGE = pygame.transform.scale(FLYER_ENEMY_IMAGE, (FLYER_ENEMY_WIDTH, FLYER_ENEMY_HEIGHT))
    print("Asset Load: image_f33c19.png (Flyer Enemy) loaded successfully.")
except pygame.error:
    print("Asset Load: ERROR - image_f33c19.png (Flyer Enemy) not found.")


# --- High Score & Player Profile Functions ---
def load_player_profiles():
    """Loads all player profiles from a JSON file."""
    global player_profiles, selected_player_index, selected_player_name, high_score
    if os.path.exists(PLAYER_PROFILES_FILE):
        try:
            with open(PLAYER_PROFILES_FILE, "r") as file:
                player_profiles = json.load(file)
            print(f"Player Profiles: Loaded {len(player_profiles)} profiles.")
            # Default to no player selected, or the first one if profiles exist
            if player_profiles:
                # Ensure selected_player_index is valid, otherwise default to first
                if selected_player_index == -1 or selected_player_index >= len(player_profiles):
                    selected_player_index = 0
                selected_player_name = player_profiles[selected_player_index]['name']
                high_score = player_profiles[selected_player_index]['high_score']
            else:
                selected_player_index = -1
                selected_player_name = "Guest"
                high_score = 0
        except json.JSONDecodeError:
            player_profiles = []
            selected_player_index = -1
            selected_player_name = "Guest"
            high_score = 0
            print("Player Profiles: Invalid JSON in file, resetting profiles.")
        except Exception as e:
            player_profiles = []
            selected_player_index = -1
            selected_player_name = "Guest"
            high_score = 0
            print(f"Player Profiles: Error loading file: {e}, resetting profiles.")
    else:
        player_profiles = []
        selected_player_index = -1
        selected_player_name = "Guest"
        high_score = 0
        print("Player Profiles: File not found, starting with no profiles.")

def save_player_profiles():
    """Saves all current player profiles to a JSON file."""
    try:
        with open(PLAYER_PROFILES_FILE, "w") as file:
            json.dump(player_profiles, file, indent=4)
        print("Player Profiles: Saved successfully.")
    except Exception as e:
        print(f"Player Profiles: Error saving file: {e}")

def update_player_high_score(current_score):
    """Updates the high score for the currently selected player."""
    global high_score
    if selected_player_index != -1 and current_score > player_profiles[selected_player_index]['high_score']:
        player_profiles[selected_player_index]['high_score'] = current_score
        high_score = current_score # Update global high_score for display
        save_player_profiles()
        print(f"Player {selected_player_name}: New high score saved: {high_score}")
    else:
        print(f"Player {selected_player_name}: Current score {current_score} not higher than {high_score}.")

# Load player profiles once at the start of the game
load_player_profiles()

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

        # New Power-up related attributes
        self.has_blast = False # Starts false, unlocked at Level 2
        self.can_double_blast = False

        self.orbit_shield_hits = 0 # How many hits the orbiting shield can take
        
        # New 4x Jump Power-up attributes
        self.can_quad_jump = False

        # New Roll Ability attributes
        self.is_rolling = False
        self.roll_timer = 0
        self.roll_cooldown_timer = 0

        # New Fire Dash Combo Attack attributes
        self.is_fire_dashing = False
        self.fire_dash_timer = 0
        self.fire_dash_cooldown_timer = 0
        self.fire_dash_active = False # To control invincibility and speed

        # Weapon attributes
        self.current_weapon = "default_slash" # "default_slash", "big_sword", "dagger", "club"
        self.attack_range_current = ATTACK_RANGE_SLASH # Dynamic attack range
        self.attack_damage_multiplier = 1 # Damage multiplier for weapons
        self.attack_knockback = 0 # Knockback for club


    def update(self, platforms, moving_platforms):
        # Store on_ground state before any changes in this frame
        was_on_ground = self.on_ground

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
                self.is_invincible = False # End invincibility from shield
                self.image = self.image_base # Revert to base image
                # Remove any active shield sprite
                for s in shields:
                    if s.player_ref == self:
                        s.kill()
        
        # Update roll timer and cooldown
        if self.roll_cooldown_timer > 0:
            self.roll_cooldown_timer -= 1

        if self.is_rolling:
            self.roll_timer -= 1
            if self.roll_timer <= 0:
                self.is_rolling = False
                self.is_invincible = False # End invincibility from roll
                self.vel_x = 0 # Stop horizontal roll movement
                # Reset image to normal if it was modified for rolling
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.image_base, True, False)
                else:
                    self.image = self.image_base
            else:
                # During roll, apply high horizontal velocity
                if self.facing_right:
                    self.vel_x = PLAYER_SPEED * ROLL_SPEED_MULTIPLIER
                else:
                    self.vel_x = -PLAYER_SPEED * ROLL_SPEED_MULTIPLIER
                self.is_invincible = True # Maintain invincibility during roll
        
        # Update Fire Dash timer and cooldown
        if self.fire_dash_cooldown_timer > 0:
            self.fire_dash_cooldown_timer -= 1

        if self.is_fire_dashing:
            self.fire_dash_timer -= 1
            if self.fire_dash_timer <= 0:
                self.is_fire_dashing = False
                self.is_invincible = False # End invincibility from fire dash
                self.vel_x = 0 # Stop horizontal fire dash movement
                self.fire_dash_active = False # Deactivate for collision checks
                # Reset image to normal
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.image_base, True, False)
                else:
                    self.image = self.image_base
            else:
                # During fire dash, apply very high horizontal velocity
                if self.facing_right:
                    self.vel_x = PLAYER_SPEED * FIRE_DASH_SPEED_MULTIPLIER
                else:
                    self.vel_x = -PLAYER_SPEED * FIRE_DASH_SPEED_MULTIPLIER
                self.is_invincible = True # Maintain invincibility
                self.fire_dash_active = True # Active for collision checks


        # Apply gravity only if not rolling or fire dashing
        if not self.is_rolling and not self.is_fire_dashing:
            self.vel_y += GRAVITY
            # Cap falling velocity
            if self.vel_y > MAX_FALL_VELOCITY:
                self.vel_y = MAX_FALL_VELOCITY
        else: # During roll/fire dash, no vertical movement for simplicity
             self.vel_y = 0

        self.rect.y += self.vel_y

        self.on_ground = False
        all_ground_surfaces = platforms.sprites() + moving_platforms.sprites()
        for platform in all_ground_surfaces:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0 and self.rect.bottom <= platform.rect.bottom: # Falling and hit top of platform
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    if isinstance(platform, MovingPlatform):
                        self.rect.x += platform.vel_x
                elif self.vel_y < 0 and self.rect.top >= platform.rect.top: # Jumping and hit bottom of platform
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

        if self.on_ground and not was_on_ground:
            if self.can_quad_jump:
                self.jumps_remaining = QUAD_JUMP_COUNT # Set to 4 jumps if power-up active
            else:
                self.jumps_remaining = MAX_JUMPS # Otherwise, default 2 jumps

        self.rect.x += self.vel_x

        for platform in all_ground_surfaces:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0: # Moving right and hit left of platform
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0: # Moving left and hit right of platform
                    self.rect.left = platform.rect.right

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        if self.rect.top > SCREEN_HEIGHT:
            self.take_fall_damage() # Handle falling off the screen

        # Update player image for facing direction if not currently attacking, shielding, rolling, or fire dashing
        if not self.attacking and not self.shielding and not self.is_rolling and not self.is_fire_dashing:
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
        # Visual for rolling (can be a temporary color change or different sprite)
        elif self.is_rolling:
            # Example: temporary color change for roll
            temp_image = self.image_base.copy()
            temp_image.fill((0, 255, 255, 128), special_flags=pygame.BLEND_RGBA_MULT) # Cyan overlay for rolling
            if not self.facing_right:
                self.image = pygame.transform.flip(temp_image, True, False)
            else:
                self.image = temp_image
        # Visual for Fire Dashing (fiery red/orange)
        elif self.is_fire_dashing:
            temp_image = self.image_base.copy()
            temp_image.fill(FIRE_RED, special_flags=pygame.BLEND_RGBA_MULT) # Fiery red/orange overlay
            if not self.facing_right:
                self.image = pygame.transform.flip(temp_image, True, False)
            else:
                self.image = temp_image


        # Update orbiting lights position
        if self.orbit_shield_hits > 0:
            for i, ol_sprite in enumerate(orbiting_lights_group): # Use the global group
                ol_sprite.update(self.rect.centerx, self.rect.centery, i)


    def jump(self):
        # Now checks for can_quad_jump for max jumps
        if self.can_quad_jump and self.jumps_remaining > 0:
            self.vel_y = JUMP_STRENGTH
            self.jumps_remaining -= 1
        elif not self.can_quad_jump and self.jumps_remaining > 0: # Regular jump logic
            self.vel_y = JUMP_STRENGTH
            self.jumps_remaining -= 1


    def move_left(self):
        # Only allow movement if not currently fire dashing
        if not self.is_fire_dashing:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False

    def move_right(self):
        # Only allow movement if not currently fire dashing
        if not self.is_fire_dashing:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True

    def stop_move(self):
        # Only allow stopping movement if not currently rolling or fire dashing
        if not self.is_rolling and not self.is_fire_dashing:
            self.vel_x = 0

    def start_roll(self):
        # Can't roll if already rolling, fire dashing, or roll is on cooldown
        if not self.is_rolling and not self.is_fire_dashing and self.roll_cooldown_timer == 0:
            self.is_rolling = True
            self.roll_timer = ROLL_DURATION
            self.roll_cooldown_timer = ROLL_COOLDOWN # Set cooldown
            self.is_invincible = True # Player is invincible during roll
            # Ensure player moves in current facing direction
            if self.facing_right:
                self.vel_x = PLAYER_SPEED * ROLL_SPEED_MULTIPLIER
            else:
                self.vel_x = -PLAYER_SPEED * ROLL_SPEED_MULTIPLIER

    def start_fire_dash(self):
        # Requires blast unlocked, not already fire dashing, and cooldown is ready
        if self.has_blast and not self.is_fire_dashing and self.fire_dash_cooldown_timer == 0:
            self.is_fire_dashing = True
            self.fire_dash_timer = FIRE_DASH_DURATION
            self.fire_dash_cooldown_timer = FIRE_DASH_COOLDOWN
            self.is_invincible = True # Invincible during fire dash
            self.fire_dash_active = True # Activate for collision checks
            # Set high horizontal velocity
            if self.facing_right:
                self.vel_x = PLAYER_SPEED * FIRE_DASH_SPEED_MULTIPLIER
            else:
                self.vel_x = -PLAYER_SPEED * FIRE_DASH_SPEED_MULTIPLIER
            print("FIRE DASH!")


    def slash_attack(self):
        if self.attack_cooldown_timer == 0:
            self.attacking = True
            self.is_slashing_anim = True # Activate slash visual
            self.attack_cooldown_timer = ATTACK_COOLDOWN # Set cooldown

            # Create a temporary slash hitbox based on current weapon's range
            current_attack_range = self.attack_range_current
            
            slash_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height)
            if self.facing_right:
                slash_rect.left = self.rect.right # Attack to the right
            else:
                slash_rect.right = self.rect.left # Attack to the left
            slash_rect.width = current_attack_range # Extend hitbox for slash
            return slash_rect
        return None

    def blast_attack(self):
        if not self.has_blast: # Player cannot use blast attack if not unlocked
            return None
        # Cannot blast if currently fire dashing (combo ability)
        if self.is_fire_dashing:
            return None

        if self.attack_cooldown_timer == 0:
            self.attacking = True
            self.attack_cooldown_timer = ATTACK_COOLDOWN # Set cooldown

            # Single blast
            if self.facing_right:
                blast_x = self.rect.right
                blast_vel_x = BLAST_SPEED
            else:
                blast_x = self.rect.left - PROJECTILE_SIZE
                blast_vel_x = -BLAST_SPEED
            
            blast = Projectile(blast_x, self.rect.centery, blast_vel_x)
            projectiles.add(blast)
            all_sprites.add(blast)

            # Double blast if power-up is active
            if self.can_double_blast:
                # Fire a second blast slightly offset vertically
                blast2_y_offset = 10 # Adjust for visual separation
                blast2 = Projectile(blast_x, self.rect.centery + blast2_y_offset, blast_vel_x)
                projectiles.add(blast2)
                all_sprites.add(blast2)
        return None

    def activate_shield(self):
        # Only activate if not already shielding and not currently attacking, rolling or fire dashing
        if not self.shielding and not self.attacking and not self.is_rolling and not self.is_fire_dashing:
            self.shielding = True
            self.is_invincible = True
            self.shield_timer = SHIELD_DURATION # Set shield duration
            # Create a shield sprite
            shield_sprite = Shield(self.rect.centerx, self.rect.centery)
            shields.add(shield_sprite)
            all_sprites.add(shield_sprite)

    def take_hit(self):
        """Handle player taking a hit, checking for orbiting shield."""
        if self.is_invincible: # Regular shield, roll, or fire dash invincibility active
            return False # Hit was blocked

        if self.orbit_shield_hits > 0:
            self.orbit_shield_hits -= 1
            print(f"Orbit shield blocked a hit! Hits remaining: {self.orbit_shield_hits}")
            # Remove one orbiting light visual if hits drop
            if orbiting_lights_group: # Check the global group
                # Get a list of active orbiting sprites
                active_orbiting_sprites = [s for s in orbiting_lights_group if s.alive()]
                if active_orbiting_sprites:
                    sprite_to_remove = active_orbiting_sprites[-1] # Remove the 'last' one added (or any arbitrary one)
                    sprite_to_remove.kill() # This removes it from its groups (orbiting_lights_group and all_sprites)
            
            if self.orbit_shield_hits <= 0:
                orbiting_lights_group.empty() # Ensure all are gone if hits are 0 or less
            return False # Hit was blocked by orbit shield
        
        # If neither shield is active, player takes actual damage
        return True # Player took damage

    def take_fall_damage(self):
        """Handles player falling off the bottom of the screen."""
        global lives, current_game_state # Explicitly declare for modification
        lives -= 1
        if lives <= 0:
            current_game_state = GAME_STATE_GAMEOVER
            update_player_high_score(score) # Check and save high score on Game Over
            self.reset_position_and_state(keep_powerups=False) # Clear power-ups on game over
        else:
            self.reset_position_and_state(keep_powerups=True) # Reset player for next life, KEEP powerups

    def reset_position_and_state(self, keep_powerups=True):
        """
        Resets player's position and potentially clears active power-ups/shields.
        Set keep_powerups=False to clear power-ups (e.g., on losing a life).
        """
        self.rect.x = 100
        self.rect.y = 100
        self.vel_y = 0
        self.vel_x = 0
        
        # Reset jumps based on power-up state
        if self.can_quad_jump and keep_powerups:
            self.jumps_remaining = QUAD_JUMP_COUNT
        else:
            self.jumps_remaining = MAX_JUMPS

        self.is_invincible = False
        self.shielding = False
        self.attack_cooldown_timer = 0
        self.is_slashing_anim = False
        self.is_rolling = False # Reset roll state
        self.roll_timer = 0
        self.roll_cooldown_timer = 0
        self.is_fire_dashing = False # Reset fire dash state
        self.fire_dash_timer = 0
        self.fire_dash_cooldown_timer = 0
        self.fire_dash_active = False
        
        # Clear specific temporary shields
        for s in shields:
            if s.player_ref == self:
                s.kill()

        if not keep_powerups:
            # Clear all power-up effects if not keeping them
            self.can_double_blast = False
            self.orbit_shield_hits = 0
            self.can_quad_jump = False
            orbiting_lights_group.empty() # Remove orbiting lights from global group
            self.current_weapon = "default_slash" # Reset weapon to default on death
            self.attack_range_current = ATTACK_RANGE_SLASH
            self.attack_damage_multiplier = 1
            self.attack_knockback = 0
        elif self.orbit_shield_hits > 0:
            # If powerups are kept and orbit shield is active, re-create visuals
            # Ensure only the number of actual hits remaining are visually represented
            orbiting_lights_group.empty() # Clear existing visuals
            for i in range(self.orbit_shield_hits): # Only create lights for remaining hits
                angle = i * (2 * math.pi / ORBIT_SHIELD_MAX_HITS) # Re-distribute angles based on max possible lights
                orbit_light = OrbitingLight(self, angle)
                orbiting_lights_group.add(orbit_light)
                all_sprites.add(orbit_light)

    def set_weapon(self, weapon_type):
        self.current_weapon = weapon_type
        if weapon_type == "big_sword":
            self.attack_range_current = ATTACK_RANGE_BIG_SWORD
            self.attack_damage_multiplier = 1
            self.attack_knockback = 0
            print(f"Weapon selected: Big Sword (Range: {self.attack_range_current})")
        elif weapon_type == "dagger":
            self.attack_range_current = ATTACK_RANGE_SLASH # Same range as slash
            self.attack_damage_multiplier = 1 # Damage multiplier applies only from behind
            self.attack_knockback = 0
            print(f"Weapon selected: Dagger (3x damage from behind)")
        elif weapon_type == "club":
            self.attack_range_current = ATTACK_RANGE_SLASH # Same range as slash
            self.attack_damage_multiplier = 1
            self.attack_knockback = KNOCKBACK_STRENGTH
            print(f"Weapon selected: Club (Knockback: {self.attack_knockback})")
        else: # default_slash
            self.attack_range_current = ATTACK_RANGE_SLASH
            self.attack_damage_multiplier = 1
            self.attack_knockback = 0
            print(f"Weapon selected: Default Slash (Range: {self.attack_range_current})")


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
    def __init__(self, x, y, width, height, image_asset, speed, patrol_range=100, health=1):
        super().__init__()
        # Use provided image_asset, fallback to REGULAR_ENEMY_IMAGE, then to a colored surface
        self.image_base = image_asset if image_asset else REGULAR_ENEMY_IMAGE
        if not self.image_base: # If all image assets fail, create a colored surface
            self.image_base = pygame.Surface([width, height])
            self.image_base.fill(ENEMY_GREEN) # Default green for enemies
        else: # Scale the image asset if it was loaded
            self.image_base = pygame.transform.scale(self.image_base, (width, height))

        self.image = self.image_base # Current image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = speed
        self.vel_y = 0
        self.start_x = x
        self.patrol_range = patrol_range
        self.on_ground = False
        self.facing_right = True # For directing enemy visual
        self.health = health # For enemies that take multiple hits

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
            self.vel_x = -self.vel_x # Reverse direction
        elif self.vel_x < 0 and self.rect.left <= self.start_x - self.patrol_range:
            self.vel_x = -self.vel_x # Reverse direction

        # Enemy edge detection (so they don't walk off platforms)
        if self.on_ground: # Only perform edge detection if on ground
            check_offset = 5 # How far ahead to check for platform edge
            if self.vel_x > 0: # Moving right
                check_point_x = self.rect.right + check_offset
            else: # Moving left
                check_point_x = self.rect.left - check_offset

            # Create a small rect to check for ground beneath slightly ahead
            check_rect = pygame.Rect(check_point_x, self.rect.bottom + 1, 5, 5)
            
            # Assume no ground initially
            has_ground_ahead = False
            for platform in all_ground_surfaces:
                if check_rect.colliderect(platform.rect):
                    has_ground_ahead = True
                    break
            
            if not has_ground_ahead:
                self.vel_x *= -1 # Turn around if no ground detected ahead

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill() # Remove enemy if health is zero

class GuardEnemy(Enemy):
    def __init__(self, x, y, patrol_range=100):
        super().__init__(x, y, GUARD_ENEMY_WIDTH, GUARD_ENEMY_HEIGHT, GUARD_ENEMY_IMAGE, GUARD_SPEED, patrol_range, GUARD_HEALTH_MAX)
        if not GUARD_ENEMY_IMAGE:
            self.image_base.fill(BLUE) # Different fallback color for guard
            pygame.draw.rect(self.image_base, BLACK, self.image_base.get_rect(), 2) # Border

class ShooterEnemy(Enemy):
    def __init__(self, x, y, patrol_range=100):
        super().__init__(x, y, SHOOTER_ENEMY_WIDTH, SHOOTER_ENEMY_HEIGHT, SHOOTER_ENEMY_IMAGE, SHOOTER_SPEED, patrol_range, health=1)
        self.attack_cooldown_timer = SHOOTER_BLAST_COOLDOWN
        self.is_shooting = False # State to indicate if currently shooting (can affect movement)
        if not SHOOTER_ENEMY_IMAGE:
            self.image_base.fill(RED) # Different fallback color for shooter
            pygame.draw.circle(self.image_base, BLACK, (SHOOTER_ENEMY_WIDTH // 2, SHOOTER_ENEMY_HEIGHT // 2), SHOOTER_ENEMY_WIDTH // 2, 2)

    def update(self, platforms, moving_platforms):
        super().update(platforms, moving_platforms) # Call base Enemy update for movement and gravity

        self.attack_cooldown_timer -= 1
        if self.attack_cooldown_timer <= 0:
            self.shoot_blast()
            self.attack_cooldown_timer = SHOOTER_BLAST_COOLDOWN

    def shoot_blast(self):
        # Determine direction to shoot based on player position (simple tracking)
        # For simplicity, just shoot straight in facing direction for now
        blast_vel_x = SHOOTER_PROJECTILE_SPEED if self.facing_right else -SHOOTER_PROJECTILE_SPEED
        
        # Position the projectile to originate from the shooter's "weapon" if possible
        blast_x = self.rect.centerx + (self.rect.width // 2 * (1 if self.facing_right else -1))
        blast_y = self.rect.centery # Roughly from the center of the enemy

        new_projectile = ShooterProjectile(blast_x, blast_y, blast_vel_x, 0) # No vertical vel for now
        shooter_projectiles.add(new_projectile)
        all_sprites.add(new_projectile)

class ShooterProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, vel_x, vel_y):
        super().__init__()
        self.image_orig = SHOOTER_PROJECTILE_IMAGE if SHOOTER_PROJECTILE_IMAGE else pygame.Surface([SHOOTER_PROJECTILE_SIZE, SHOOTER_PROJECTILE_SIZE], pygame.SRCALPHA)
        if not SHOOTER_PROJECTILE_IMAGE:
            self.image_orig.fill(BLACK) # Default black for shooter projectile
            pygame.draw.circle(self.image_orig, WHITE, (SHOOTER_PROJECTILE_SIZE // 2, SHOOTER_PROJECTILE_SIZE // 2), SHOOTER_PROJECTILE_SIZE // 2 - 2, 1)

        self.image = self.image_orig
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.lifetime = 180 # Projectile disappears after 3 seconds (60 FPS * 3)

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.lifetime -= 1
        
        # Kill if off-screen or lifetime expires
        if self.lifetime <= 0 or \
           self.rect.left > SCREEN_WIDTH or self.rect.right < 0 or \
           self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0:
            self.kill()

class FlyerEnemy(Enemy):
    def __init__(self, x, y, patrol_range=150):
        super().__init__(x, y, FLYER_ENEMY_WIDTH, FLYER_ENEMY_HEIGHT, FLYER_ENEMY_IMAGE, FLYER_SPEED, patrol_range, health=1)
        self.initial_y = y # Store initial Y for oscillation
        self.oscillation_timer = random.uniform(0, 2 * math.pi) # Start at a random point in sine wave
        if not FLYER_ENEMY_IMAGE:
            self.image_base.fill(FLYER_TEAL) # Fallback color for flyer

    def update(self, platforms, moving_platforms):
        # Horizontal movement (from base Enemy class)
        self.rect.x += self.vel_x
        if self.vel_x > 0 and self.rect.right >= self.start_x + self.patrol_range:
            self.vel_x = -self.vel_x
        elif self.vel_x < 0 and self.rect.left <= self.start_x - self.patrol_range:
            self.vel_x = -self.vel_x
        
        # Vertical oscillation
        self.oscillation_timer += FLYER_VERTICAL_OSCILLATION_SPEED
        self.rect.y = self.initial_y + FLYER_VERTICAL_OSCILLATION_MAGNITUDE * math.sin(self.oscillation_timer)

        # Update facing direction for visual flip
        if self.vel_x > 0 and not self.facing_right:
            self.image = self.image_base
            self.facing_right = True
        elif self.vel_x < 0 and self.facing_right:
            self.image = pygame.transform.flip(self.image_base, True, False)
            self.facing_right = False
        
        # Keep within screen bounds (vertical too for flying enemies)
        if self.rect.top < 0:
            self.rect.top = 0
            self.initial_y = self.rect.y # Reset initial_y if it hits top edge
            self.oscillation_timer = math.pi/2 # Start going down
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.initial_y = self.rect.y # Reset initial_y if it hits bottom edge
            self.oscillation_timer = 3*math.pi/2 # Start going up


class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_range=BOSS_PATROL_RANGE):
        super().__init__()
        self.image_base = BOSS_IMAGE if BOSS_IMAGE else pygame.Surface([BOSS_WIDTH, BOSS_HEIGHT], pygame.SRCALPHA)
        if not BOSS_IMAGE:
            pygame.draw.circle(self.image_base, BOSS_PURPLE, (BOSS_WIDTH // 2, BOSS_HEIGHT // 2), BOSS_WIDTH // 2, 2)
        
        self.image = self.image_base
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = BOSS_SPEED
        self.vel_y = 0
        self.start_x = x
        self.patrol_range = patrol_range
        self.on_ground = False
        self.facing_right = True
        self.health = BOSS_HEALTH_MAX
        self.attack_cooldown_timer = BOSS_BLAST_COOLDown # Initial cooldown for blast

    def update(self, platforms, moving_platforms, player_rect):
        all_ground_surfaces = platforms.sprites() + moving_platforms.sprites()

        # Boss "floating" movement - less affected by gravity
        self.vel_y += GRAVITY * 0.2 # Reduced gravity for floating effect
        if self.vel_y > MAX_FALL_VELOCITY / 2: # Cap boss fall speed
            self.vel_y = MAX_FALL_VELOCITY / 2
        self.rect.y += self.vel_y

        # Collision with platforms (simplified for boss)
        for platform in all_ground_surfaces:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0: # Falling
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                elif self.vel_y < 0: # Hitting head on platform
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
        
        # Horizontal patrol
        self.rect.x += self.vel_x
        if self.vel_x > 0 and self.rect.right >= self.start_x + self.patrol_range:
            self.vel_x = -BOSS_SPEED
        elif self.vel_x < 0 and self.rect.left <= self.start_x - self.patrol_range:
            self.vel_x = BOSS_SPEED

        # Keep boss within screen bounds horizontally
        if self.rect.left < 0:
            self.rect.left = 0
            self.vel_x *= -1
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.vel_x *= -1

        # Boss vertical "hover" behavior (simple up and down)
        if self.rect.top < SCREEN_HEIGHT // 4: # If too high, move down
            self.vel_y = 0.5
        elif self.rect.bottom > SCREEN_HEIGHT * 0.6: # If too low, move up
            self.vel_y = -0.5

        # Update facing direction for visual flip (if you have different boss images)
        if self.vel_x > 0 and not self.facing_right:
            self.image = self.image_base
            self.facing_right = True
        elif self.vel_x < 0 and self.facing_right:
            self.image = pygame.transform.flip(self.image_base, True, False)
            self.facing_right = False

        # Boss attack logic
        self.attack_cooldown_timer -= 1
        if self.attack_cooldown_timer <= 0:
            self.dark_blast_attack(player_rect)
            self.attack_cooldown_timer = BOSS_BLAST_COOLDOWN

    def dark_blast_attack(self, player_rect):
        # Calculate direction vector towards the player
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)

        if distance > 0:
            # Normalize vector and scale by projectile speed
            vel_x = (dx / distance) * BOSS_PROJECTILE_SPEED
            vel_y = (dy / distance) * BOSS_PROJECTILE_SPEED
            
            blast = BossProjectile(self.rect.centerx, self.rect.centery, int(vel_x), int(vel_y)) # Cast to int
            boss_projectiles.add(blast)
            all_sprites.add(blast)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill() # Remove boss if health is zero


class BossProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, vel_x, vel_y):
        super().__init__()
        self.image_orig = DARK_BLAST_IMAGE if DARK_BLAST_IMAGE else pygame.Surface([BOSS_PROJECTILE_SIZE, BOSS_PROJECTILE_SIZE], pygame.SRCALPHA)
        if not DARK_BLAST_IMAGE:
            pygame.draw.circle(self.image_orig, BOSS_PURPLE, (BOSS_PROJECTILE_SIZE // 2, BOSS_PROJECTILE_SIZE // 2), BOSS_PROJECTILE_SIZE // 2)

        self.image = self.image_orig
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.lifetime = 180 # Projectile disappears after 3 seconds (60 FPS * 3)

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.lifetime -= 1
        
        # Kill if off-screen or lifetime expires
        if self.lifetime <= 0 or \
           self.rect.left > SCREEN_WIDTH or self.rect.right < 0 or \
           self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    """Base class for all power-up items."""
    def __init__(self, x, y, image, pu_type):
        super().__init__()
        self.image = image if image else pygame.Surface([COIN_SIZE, COIN_SIZE], pygame.SRCALPHA)
        if not image: # Default if image not loaded
            if pu_type == 'double_blast':
                pygame.draw.rect(self.image, WHITE, self.image.get_rect(), 0, 3) # White square
                pygame.draw.line(self.image, PURPLE, (5,15), (25,15), 3) # Double line
                pygame.draw.line(self.image, PURPLE, (5,10), (25,10), 3)
            elif pu_type == 'orbit_shield':
                pygame.draw.circle(self.image, WHITE, (COIN_SIZE // 2, COIN_SIZE // 2), COIN_SIZE // 2 - 2, 2) # White circle outline
                pygame.draw.circle(self.image, RED, (COIN_SIZE // 2, COIN_SIZE // 2), COIN_SIZE // 4) # Red inner
            elif pu_type == 'quad_jump':
                pygame.draw.polygon(self.image, WHITE, [(COIN_SIZE//2, 0), (COIN_SIZE, COIN_SIZE//2), (COIN_SIZE//2, COIN_SIZE), (0, COIN_SIZE//2)])
                pygame.draw.line(self.image, BLUE, (COIN_SIZE//4, COIN_SIZE//2), (COIN_SIZE*3//4, COIN_SIZE//2), 2)
                pygame.draw.line(self.image, BLUE, (COIN_SIZE//2, COIN_SIZE//4), (COIN_SIZE//2, COIN_SIZE*3//4), 2)
            elif pu_type == 'extra_life': # New extra life power-up visual
                pygame.draw.circle(self.image, WHITE, (COIN_SIZE // 2, COIN_SIZE // 2), COIN_SIZE // 2 - 2, 2)
                pygame.draw.line(self.image, RED, (COIN_SIZE // 2, COIN_SIZE // 4), (COIN_SIZE // 2, COIN_SIZE * 3 // 4), 3)
                pygame.draw.line(self.image, RED, (COIN_SIZE // 4, COIN_SIZE // 2), (COIN_SIZE * 3 // 4, COIN_SIZE // 2), 3)

        self.rect = self.image.get_rect(topleft=(x, y))
        self.type = pu_type # 'double_blast', 'orbit_shield', 'quad_jump', or 'extra_life'

    def apply_effect(self, player_ref):
        """Applies the power-up's effect to the player."""
        global lives # Need to modify global lives for extra life
        if self.type == 'double_blast':
            player_ref.can_double_blast = True
            print("Double Blast Power-up collected!")
        elif self.type == 'orbit_shield':
            player_ref.orbit_shield_hits = ORBIT_SHIELD_MAX_HITS
            print(f"Orbit Shield Power-up collected! {ORBIT_SHIELD_MAX_HITS} hits available.")
            
            # Clear existing global orbiting lights and spawn new ones to match MAX_HITS
            orbiting_lights_group.empty() # Clear existing visuals
            for i in range(ORBIT_SHIELD_MAX_HITS):
                # Distribute angles evenly around the player
                angle = i * (2 * math.pi / ORBIT_SHIELD_MAX_HITS)
                orbit_light = OrbitingLight(player_ref, angle)
                orbiting_lights_group.add(orbit_light) # Add to global group
                all_sprites.add(orbit_light)
        elif self.type == 'quad_jump':
            player_ref.can_quad_jump = True
            player_ref.jumps_remaining = QUAD_JUMP_COUNT # Give max jumps immediately
            print("4x Jump Power-up collected!")
        elif self.type == 'extra_life': # New extra life effect
            lives += 1
            print("Extra Life Power-up collected! Lives: ", lives)
                
        self.kill() # Power-up item disappears after collection


class OrbitingLight(pygame.sprite.Sprite):
    """A small light that orbits the player and blocks hits."""
    def __init__(self, player_ref, initial_angle_offset):
        super().__init__()
        self.image = ORBITING_LIGHT_IMAGE if ORBITING_LIGHT_IMAGE else pygame.Surface([ORBIT_SHIELD_SIZE, ORBIT_SHIELD_SIZE], pygame.SRCALPHA)
        if not ORBITING_LIGHT_IMAGE:
            pygame.draw.circle(self.image, RED, (ORBIT_SHIELD_SIZE // 2, ORBIT_SHIELD_SIZE // 2), ORBIT_SHIELD_SIZE // 2)

        self.rect = self.image.get_rect()
        self.player_ref = player_ref
        self.current_angle = initial_angle_offset # Dynamic angle for rotation
        self.rotation_speed = 0.05 # Radians per frame

        self.update(self.player_ref.rect.centerx, self.player_ref.rect.centery, 0) # Initial position

    def update(self, player_center_x, player_center_y, index):
        # The light should only update its position, its removal is handled by player.take_hit
        self.current_angle += self.rotation_speed
        
        # Adjust angle based on player facing direction for a more natural look
        if not self.player_ref.facing_right:
            angle_modifier = math.pi # Flip orbit direction to be consistent
        else:
            angle_modifier = 0

        # Position relative to player's center
        self.rect.centerx = player_center_x + ORBIT_SHIELD_RADIUS * math.cos(self.current_angle + angle_modifier)
        self.rect.centery = player_center_y + ORBIT_SHIELD_RADIUS * math.sin(self.current_angle + angle_modifier)


# --- Game Setup Function ---
def setup_game():
    global player, all_sprites, platforms, moving_platforms, coins, enemies, projectiles, shields
    global boss_active, boss_sprite, boss_projectiles, score, lives, initial_coin_count_level, current_level, current_game_state
    global powerups, orbiting_lights_group, shooter_enemies, shooter_projectiles, flyer_enemies # Include new groups

    # Clear all LEVEL-SPECIFIC sprite groups
    platforms.empty()
    moving_platforms.empty()
    coins.empty()
    enemies.empty()
    shooter_enemies.empty() # Clear shooter enemies
    shooter_projectiles.empty() # Clear shooter projectiles
    flyer_enemies.empty() # Clear flyer enemies
    projectiles.empty()
    shields.empty() # Player temporary shields clear
    boss_projectiles.empty()
    powerups.empty()      # Clear power-up items

    # Remove all sprites from all_sprites that are not the player or orbiting lights
    # This prevents old level elements from persisting.
    for sprite in all_sprites.copy():
        if sprite != player and sprite not in orbiting_lights_group:
            sprite.kill()

    # Reset boss state when setting up a new level
    boss_active = False
    boss_sprite = None
    
    # Reset player's position and temporary states, but keep powerups
    # Only reset power-ups if current_game_state implies a fresh start (e.g., GAME OVER)
    # Otherwise, power-ups should be kept on level transition.
    player.reset_position_and_state(keep_powerups=True) 
    
    # Set initial player power-up states based on level (for blast unlock)
    player.has_blast = (current_level >= BLAST_ATTACK_UNLOCK_LEVEL)
    
    # Do not generate level immediately if in MENU, PLAYER_SELECT, CREATE_PLAYER, or WEAPON_SELECT state
    if current_game_state == GAME_STATE_MENU or \
       current_game_state == GAME_STATE_PLAYER_SELECT or \
       current_game_state == GAME_STATE_CREATE_PLAYER or \
       current_game_state == GAME_STATE_WEAPON_SELECT:
        return # Exit setup_game early, no level generation needed yet

    # --- Weapon Selection Trigger ---
    # After completing Level 1 (meaning current_level becomes 1), trigger weapon selection
    # Only trigger if the player still has the default weapon
    if current_level == 1 and player.current_weapon == "default_slash":
        current_game_state = GAME_STATE_WEAPON_SELECT
        return # Stop setting up game if we are going to weapon select

    # If we reached here, it means we are transitioning to a PLAYING or BOSS_FIGHT state
    # Check if it's a boss level
    if current_level > 0 and current_level % BOSS_APPEAR_INTERVAL == 0:
        boss_active = True
        print(f"Starting Boss Level {current_level} (Boss Fight)!")
        current_game_state = GAME_STATE_BOSS_FIGHT # Set state to boss fight
        
        # For boss level, create a minimal platform for the player to stand on
        ground = Platform(0, SCREEN_HEIGHT - PLATFORM_HEIGHT, SCREEN_WIDTH)
        platforms.add(ground)
        all_sprites.add(ground)

        # Spawn the boss
        boss_sprite = Boss(SCREEN_WIDTH // 2 - BOSS_WIDTH // 2, SCREEN_HEIGHT // 4)
        all_sprites.add(boss_sprite)
        # Some simple platforms for strategy in boss fight
        num_static_platforms = random.randint(1, 3)
        for _ in range(num_static_platforms):
            x = random.randint(50, SCREEN_WIDTH - 150)
            y = random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT - 100)
            width = random.randint(80, 200)
            new_platform = Platform(x, y, width)
            platforms.add(new_platform)
            all_sprites.add(new_platform)

    else: # Regular level generation
        current_game_state = GAME_STATE_PLAYING # Set state to playing
        print(f"Starting Regular Level {current_level}!")
        
        # Always add a ground platform first for consistency
        ground = Platform(0, SCREEN_HEIGHT - PLATFORM_HEIGHT, SCREEN_WIDTH)
        platforms.add(ground)
        all_sprites.add(ground)

        # Track the top of the most recently placed *reachable* platform
        # Start from the ground for the first platforms
        last_reachable_platform_top = SCREEN_HEIGHT - PLATFORM_HEIGHT
        
        # Generate static platforms
        num_static_platforms = random.randint(3, 7)
        for _ in range(num_static_platforms):
            # Calculate a reachable y-position for the new platform
            min_new_platform_y = int(max(
                PLAYER_HEIGHT, # Don't place platforms too high off screen (top edge)
                last_reachable_platform_top - MAX_PLATFORM_JUMP_HEIGHT
            ))
            # Ensure platforms are not too low either (above the ground + player height)
            max_new_platform_y = int(SCREEN_HEIGHT - (2 * PLATFORM_HEIGHT) - PLAYER_HEIGHT)

            # Ensure min_new_platform_y is not greater than max_new_platform_y
            if min_new_platform_y >= max_new_platform_y:
                # If range collapses, give a default valid range
                y = random.randint(max(0, max_new_platform_y - 50), max_new_platform_y)
            else:
                y = random.randint(min_new_platform_y, max_new_platform_y)
            
            x = random.randint(50, SCREEN_WIDTH - 150)
            width = random.randint(80, 200)
            new_platform = Platform(x, y, width)
            
            # Simple check to avoid overlapping with existing platforms too much
            overlap = False
            for p in platforms:
                if pygame.Rect.colliderect(new_platform.rect, p.rect.inflate(10, 10)): # Inflate slightly for buffer
                    overlap = True
                    break
            
            if not overlap:
                platforms.add(new_platform)
                all_sprites.add(new_platform)
                last_reachable_platform_top = new_platform.rect.top # Update for next platform


        # Generate moving platforms
        num_moving_platforms = random.randint(1, 3)
        for _ in range(num_moving_platforms):
            width = random.randint(60, 120)
            start_x = random.randint(50, SCREEN_WIDTH - 200)
            end_x = random.randint(start_x + 50, SCREEN_WIDTH - width - 20)
            
            # Use similar reachable height logic for moving platforms
            min_new_platform_y = int(max(
                PLAYER_HEIGHT,
                last_reachable_platform_top - MAX_PLATFORM_JUMP_HEIGHT
            ))
            max_new_platform_y = int(SCREEN_HEIGHT - (2 * PLATFORM_HEIGHT) - PLAYER_HEIGHT)

            if min_new_platform_y >= max_new_platform_y:
                y = random.randint(max(0, max_new_platform_y - 50), max_new_platform_y)
            else:
                y = random.randint(min_new_platform_y, max_new_platform_y)
            
            new_moving_platform = MovingPlatform(start_x, y, width, start_x, end_x, speed=random.choice([-ENEMY_SPEED, ENEMY_SPEED]))
            
            overlap = False
            for p in platforms: # Check against static platforms
                if pygame.Rect.colliderect(new_moving_platform.rect, p.rect.inflate(10, 10)):
                    overlap = True
                    break
            for p in moving_platforms: # Check against other moving platforms
                if pygame.Rect.colliderect(new_moving_platform.rect, p.rect.inflate(10, 10)):
                    overlap = True
                    break

            if not overlap:
                moving_platforms.add(new_moving_platform)
                all_sprites.add(new_moving_platform)
                # For moving platforms, we won't strictly update last_reachable_platform_top,
                # as their 'base' Y doesn't always reflect a new jump point.
                # The static platforms primarily define the upward path.
                
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

        # Spawn new enemy types or regular enemies
        if current_level >= NEW_ENEMY_SPAWN_LEVEL: # After level 3
            # Spawn one special enemy per level
            special_enemy_type = random.choice(['shooter', 'guard'])
            if all_available_platforms:
                target_platform = random.choice(all_available_platforms)
                enemy_x = random.randint(target_platform.rect.left, target_platform.rect.right - ENEMY_WIDTH)
                enemy_y = target_platform.rect.top - ENEMY_HEIGHT
                
                if special_enemy_type == 'shooter':
                    new_enemy = ShooterEnemy(enemy_x, enemy_y)
                    shooter_enemies.add(new_enemy)
                    all_sprites.add(new_enemy)
                    print(f"Spawned Shooter Enemy on Level {current_level+1}!")
                else: # guard
                    new_enemy = GuardEnemy(enemy_x, enemy_y)
                    enemies.add(new_enemy) # Guard enemies are added to general enemies group
                    all_sprites.add(new_enemy)
                    print(f"Spawned Guard Enemy on Level {current_level+1}!")
            
            # Also spawn some regular enemies (fewer to balance with special enemy)
            num_enemies = random.randint(1, 2)
            for _ in range(num_enemies):
                target_platform = random.choice(all_available_platforms)
                enemy_x = random.randint(target_platform.rect.left, target_platform.rect.right - ENEMY_WIDTH)
                enemy_y = target_platform.rect.top - ENEMY_HEIGHT
                new_enemy = Enemy(enemy_x, enemy_y, ENEMY_WIDTH, ENEMY_HEIGHT, REGULAR_ENEMY_IMAGE, ENEMY_SPEED) # Pass regular enemy image
                enemies.add(new_enemy)
                all_sprites.add(new_enemy)

        else: # Before new enemy spawn level, only spawn regular enemies
            num_enemies = random.randint(1, 3)
            for _ in range(num_enemies):
                if not all_available_platforms:
                    break
                target_platform = random.choice(all_available_platforms)
                enemy_x = random.randint(target_platform.rect.left, target_platform.rect.right - ENEMY_WIDTH)
                enemy_y = target_platform.rect.top - ENEMY_HEIGHT

                new_enemy = Enemy(enemy_x, enemy_y, ENEMY_WIDTH, ENEMY_HEIGHT, REGULAR_ENEMY_IMAGE, ENEMY_SPEED) # Pass regular enemy image
                enemies.add(new_enemy)
                all_sprites.add(new_enemy)
        
        # Spawn Flyer enemies (can appear in any level)
        num_flyer_enemies = random.randint(1, 2)
        for _ in range(num_flyer_enemies):
            flyer_x = random.randint(50, SCREEN_WIDTH - FLYER_ENEMY_WIDTH - 50)
            flyer_y = random.randint(SCREEN_HEIGHT // 4, SCREEN_HEIGHT // 2) # Fly higher up
            new_flyer = FlyerEnemy(flyer_x, flyer_y)
            flyer_enemies.add(new_flyer)
            all_sprites.add(new_flyer)
            print(f"Spawned Flyer Enemy on Level {current_level+1}!")

        # Power-up spawning logic
        if (current_level + 1) % POWERUP_SPAWN_INTERVAL == 0 and current_level > 0: # Ensures not on level 0 and aligned
            if all_available_platforms:
                target_platform = random.choice(all_available_platforms)
                pu_x = random.randint(target_platform.rect.left + COIN_SIZE, target_platform.rect.right - COIN_SIZE)
                pu_y = target_platform.rect.top - COIN_SIZE - random.randint(10, 30)
                
                # Randomly choose power-up type
                powerup_types = ['double_blast', 'orbit_shield', 'quad_jump', 'extra_life'] # Added extra_life
                powerup_type = random.choice(powerup_types)

                powerup_image = None
                if powerup_type == 'double_blast':
                    powerup_image = DOUBLE_BLAST_POWERUP_IMAGE
                elif powerup_type == 'orbit_shield':
                    powerup_image = ORBIT_SHIELD_POWERUP_IMAGE
                elif powerup_type == 'quad_jump':
                    powerup_image = JUMP_POWERUP_IMAGE
                elif powerup_type == 'extra_life': # New power-up image assignment
                    powerup_image = LIFE_POWERUP_IMAGE
                
                new_powerup = PowerUp(pu_x, pu_y, powerup_image, powerup_type)
                powerups.add(new_powerup)
                all_sprites.add(new_powerup)
                print(f"Spawned {powerup_type} power-up on Level {current_level+1}!")


# --- Input Box for Player Creation ---
class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = BLACK
        self.text = text
        self.font = font
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False
        self.blink_timer = 0
        self.blink_interval = 30 # frames

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = ORANGE if self.active else BLACK
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    # Player finished typing name, return it for creation
                    return self.text
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.unicode.isprintable(): # Only add printable characters
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = self.font.render(self.text, True, self.color)
        return None # No name entered yet

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)
        # Blinking cursor
        if self.active:
            self.blink_timer = (self.blink_timer + 1) % (2 * self.blink_interval)
            if self.blink_timer < self.blink_interval:
                cursor_x = self.rect.x + 5 + self.txt_surface.get_width()
                cursor_y = self.rect.y + 5
                pygame.draw.line(screen, self.color, (cursor_x, cursor_y), (cursor_x, cursor_y + self.font.get_height()), 2)


# --- Initial Game State setup ---
current_game_state = GAME_STATE_MENU # Ensure starting in menu

# Initialize player once at the very start of the script
player = Player(100, SCREEN_HEIGHT - 100)
all_sprites.add(player) # Add player to all_sprites immediately

# --- Game Loop ---
running = True
new_player_input_box = None # For player creation state
weapon_select_index = 0 # For weapon selection screen

# Track key states for combo attacks
key_k_pressed = False
key_lshift_pressed = False
key_rshift_pressed = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            save_player_profiles() # Save profiles before quitting
        
        # Check key down events for combo and individual actions
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_k:
                key_k_pressed = True
            elif event.key == pygame.K_LSHIFT:
                key_lshift_pressed = True
            elif event.key == pygame.K_RSHIFT:
                key_rshift_pressed = True
        
        # Check key up events for combo and individual actions
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_k:
                key_k_pressed = False
            elif event.key == pygame.K_LSHIFT:
                key_lshift_pressed = False
            elif event.key == pygame.K_RSHIFT:
                key_rshift_pressed = False

        # Fire Dash combo check (Blast + Roll)
        # This needs to be checked *before* individual K or SHIFT presses are processed
        if (key_k_pressed and (key_lshift_pressed or key_rshift_pressed)) and \
           (current_game_state == GAME_STATE_PLAYING or current_game_state == GAME_STATE_BOSS_FIGHT):
            if player.has_blast and not player.is_fire_dashing and player.fire_dash_cooldown_timer == 0:
                player.start_fire_dash()
                # Consume key presses so they don't trigger individual actions
                key_k_pressed = False
                key_lshift_pressed = False
                key_rshift_pressed = False


        if current_game_state == GAME_STATE_MENU:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    current_game_state = GAME_STATE_PLAYER_SELECT # Go to player select
                elif event.key == pygame.K_ESCAPE:
                    running = False # Quit game
        
        elif current_game_state == GAME_STATE_PLAYER_SELECT:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: # Go back to main menu
                    current_game_state = GAME_STATE_MENU
                elif event.key == pygame.K_n: # 'N' to create new player
                    current_game_state = GAME_STATE_CREATE_PLAYER
                    new_player_input_box = InputBox(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 40)
                    new_player_input_box.active = True # Automatically activate input box
                elif event.key == pygame.K_r: # 'R' to reset high score for selected player
                    if selected_player_index != -1:
                        player_profiles[selected_player_index]['high_score'] = 0
                        high_score = 0 # Update global for display
                        save_player_profiles()
                        print(f"High score for {selected_player_name} reset to 0.")
                elif event.key == pygame.K_d: # 'D' to delete selected player
                    if selected_player_index != -1:
                        deleted_player_name = player_profiles[selected_player_index]['name']
                        del player_profiles[selected_player_index]
                        save_player_profiles()
                        print(f"Player {deleted_player_name} deleted.")
                        if player_profiles: # If there are still players, select the first one
                            selected_player_index = 0
                            selected_player_name = player_profiles[selected_player_index]['name']
                            high_score = player_profiles[selected_player_index]['high_score']
                        else: # No players left
                            selected_player_index = -1
                            selected_player_name = "Guest"
                            high_score = 0
                elif event.key == pygame.K_UP:
                    if len(player_profiles) > 0:
                        selected_player_index = (selected_player_index - 1) % len(player_profiles)
                        selected_player_name = player_profiles[selected_player_index]['name']
                        high_score = player_profiles[selected_player_index]['high_score']
                elif event.key == pygame.K_DOWN:
                    if len(player_profiles) > 0:
                        selected_player_index = (selected_player_index + 1) % len(player_profiles)
                        selected_player_name = player_profiles[selected_player_index]['name']
                        high_score = player_profiles[selected_player_index]['high_score']
                elif event.key == pygame.K_RETURN: # Select current player and start game
                    if selected_player_index != -1:
                        # Reset level and game state for selected player
                        current_game_state = GAME_STATE_PLAYING # Prepare to play
                        current_level = 0
                        lives = INITIAL_LIVES
                        score = 0
                        player.set_weapon("default_slash") # Ensure default weapon
                        setup_game() # NOW call setup_game to build the first level (or go to weapon select)
            
        elif current_game_state == GAME_STATE_CREATE_PLAYER:
            player_name = new_player_input_box.handle_event(event)
            if player_name is not None: # Means ENTER was pressed in input box
                if player_name.strip() and all(p['name'].lower() != player_name.strip().lower() for p in player_profiles):
                    # Add new player profile
                    player_profiles.append({'name': player_name.strip(), 'high_score': 0})
                    save_player_profiles()
                    selected_player_index = len(player_profiles) - 1 # Select the newly created player
                    selected_player_name = player_profiles[selected_player_index]['name']
                    high_score = player_profiles[selected_player_index]['high_score']
                    current_game_state = GAME_STATE_PLAYER_SELECT # Go back to player select
                else:
                    # Handle invalid or duplicate name
                    print(f"Invalid name '{player_name}' or player already exists!")
                    # You could draw an error message on screen here
                    new_player_input_box.text = "" # Clear input
                    new_player_input_box.txt_surface = new_player_input_box.font.render(new_player_input_box.text, True, new_player_input_box.color)
                    new_player_input_box.active = True # Keep input box active for retry

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: # Cancel creation
                current_game_state = GAME_STATE_PLAYER_SELECT
                new_player_input_box = None
        
        elif current_game_state == GAME_STATE_WEAPON_SELECT:
            weapons = ["big_sword", "dagger", "club"]
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    weapon_select_index = (weapon_select_index - 1) % len(weapons)
                elif event.key == pygame.K_DOWN:
                    weapon_select_index = (weapon_select_index + 1) % len(weapons)
                elif event.key == pygame.K_RETURN:
                    chosen_weapon = weapons[weapon_select_index]
                    player.set_weapon(chosen_weapon)
                    current_game_state = GAME_STATE_PLAYING # Return to playing after selection
                    setup_game() # Continue setting up the level
                elif event.key == pygame.K_ESCAPE: # Go back to menu if ESC is pressed
                    current_game_state = GAME_STATE_PLAYER_SELECT


        elif current_game_state == GAME_STATE_PLAYING or current_game_state == GAME_STATE_BOSS_FIGHT: # Listen for input in both playing and boss fight
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
                        
                        # Apply damage to enemies based on weapon
                        # Define a function to handle damage application to various enemy types
                        def apply_player_damage(target_enemy, player_ref, score_increment=10):
                            global score # Refer to global score
                            damage_dealt = player_ref.attack_damage_multiplier
                            # Dagger specific damage from behind
                            if player_ref.current_weapon == "dagger":
                                # Check if player is behind the enemy
                                if (player_ref.facing_right and target_enemy.rect.left > player_ref.rect.right) or \
                                   (not player_ref.facing_right and target_enemy.rect.right < player_ref.rect.left):
                                    damage_dealt *= 3 # 3x damage from behind
                            
                            target_enemy.take_damage(damage_dealt)
                            if not target_enemy.alive():
                                score += score_increment # Points for defeating enemies
                            
                            # Club specific knockback
                            if player_ref.current_weapon == "club" and player_ref.attack_knockback > 0:
                                knockback_direction = 1 if player_ref.facing_right else -1
                                target_enemy.rect.x += player_ref.attack_knockback * knockback_direction
                                # Clamp enemy position within screen bounds after knockback
                                target_enemy.rect.left = max(0, target_enemy.rect.left)
                                target_enemy.rect.right = min(SCREEN_WIDTH, target_enemy.rect.right)

                        # Check for regular/guard enemy collisions
                        hit_enemies = pygame.sprite.spritecollide(temp_slash_sprite, enemies, False)
                        for enemy in hit_enemies:
                            apply_player_damage(enemy, player, 10) # 10 points for regular/guard

                        # Check for shooter enemy collisions
                        hit_shooter_enemies = pygame.sprite.spritecollide(temp_slash_sprite, shooter_enemies, False)
                        for enemy in hit_shooter_enemies:
                            apply_player_damage(enemy, player, 10) # 10 points for shooter

                        # Check for flyer enemy collisions
                        hit_flyer_enemies = pygame.sprite.spritecollide(temp_slash_sprite, flyer_enemies, False)
                        for enemy in hit_flyer_enemies:
                            apply_player_damage(enemy, player, 10) # 10 points for flyer

                        # Check for boss collision with the slash hitbox
                        if boss_active and boss_sprite and pygame.sprite.collide_rect(temp_slash_sprite, boss_sprite):
                            boss_sprite.take_damage(10 * player.attack_damage_multiplier) # Slash does 10 damage to boss
                            score += 5 # Small score for hitting boss
                            # Apply knockback to boss if club is used (less effective on boss)
                            if player.current_weapon == "club" and player.attack_knockback > 0:
                                knockback_direction = 1 if player.facing_right else -1
                                boss_sprite.rect.x += (player.attack_knockback / 2) * knockback_direction # Half knockback for boss
                                boss_sprite.rect.left = max(0, boss_sprite.rect.left)
                                boss_sprite.rect.right = min(SCREEN_WIDTH, boss_sprite.rect.right)


                if event.key == pygame.K_k and not (key_lshift_pressed or key_rshift_pressed): # Only blast if SHIFT is NOT pressed
                    player.blast_attack()
                if event.key == pygame.K_l: # New: Shield activation
                    player.activate_shield()
                if (event.key == pygame.K_RSHIFT or event.key == pygame.K_LSHIFT) and not key_k_pressed: # Only roll if K is NOT pressed
                    player.start_roll()
                if event.key == pygame.K_ESCAPE: # Press ESC to go back to menu
                    current_game_state = GAME_STATE_MENU # Go to main menu
                    update_player_high_score(score) # Check and save high score if returning to menu
                    load_player_profiles() # Reload profiles for menu display
                if event.key == pygame.K_p: # New: Press 'P' to pause
                    current_game_state = GAME_STATE_PAUSED
            if event.type == pygame.KEYUP:
                if (event.key == pygame.K_LEFT or event.key == pygame.K_a) and player.vel_x < 0 and not player.is_rolling and not player.is_fire_dashing:
                    player.stop_move()
                if (event.key == pygame.K_RIGHT or event.key == pygame.K_d) and player.vel_x > 0 and not player.is_rolling and not player.is_fire_dashing:
                    player.stop_move()
        elif current_game_state == GAME_STATE_PAUSED:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p: # Press 'P' to unpause
                    # Resume to correct state (PLAYING or BOSS_FIGHT)
                    if current_level > 0 and current_level % BOSS_APPEAR_INTERVAL == 0:
                        current_game_state = GAME_STATE_BOSS_FIGHT
                    else:
                        current_game_state = GAME_STATE_PLAYING
                if event.key == pygame.K_ESCAPE: # Press ESC to return to menu from pause
                    current_game_state = GAME_STATE_MENU # Go to main menu
                    update_player_high_score(score) # Check and save high score if returning to menu
                    load_player_profiles() # Reload profiles for menu display
        elif current_game_state == GAME_STATE_GAMEOVER:
            if event.type == pygame.KEYDOWN: # Listen for any key press to return to menu
                current_game_state = GAME_STATE_PLAYER_SELECT # Go to player select after game over
                load_player_profiles() # Reload profiles for menu display (to show new high score)

        elif current_game_state == GAME_STATE_LEVEL_COMPLETE:
            if event.type == pygame.KEYDOWN: # Listen for any key press to go to next level
                current_level += 1 # Advance to the next level
                setup_game() # Setup a new random level (or boss level, or weapon select)
                load_player_profiles() # Reload profiles just in case


    # --- Drawing Logic ---
    if BACKGROUND_IMAGE:
        screen.blit(BACKGROUND_IMAGE, (0, 0))
    else:
        screen.fill(LIGHT_BLUE) # Fill with light blue if background image is missing

    if current_game_state == GAME_STATE_PLAYING or current_game_state == GAME_STATE_BOSS_FIGHT:
        # Update sprites
        player.update(platforms, moving_platforms)
        # Orbiting lights update is now called within player.update, using the global group

        moving_platforms.update()
        projectiles.update() # Player projectiles
        shields.update()     # Player shields
        powerups.update()    # Update power-up items (not strictly necessary but good practice)

        if boss_active and boss_sprite:
            boss_sprite.update(platforms, moving_platforms, player.rect)
            boss_projectiles.update()
        else:
            enemies.update(platforms, moving_platforms) # Only update regular and guard enemies if no boss

        shooter_enemies.update(platforms, moving_platforms) # Update shooter enemies regardless of boss
        shooter_projectiles.update() # Update shooter projectiles
        flyer_enemies.update(platforms, moving_platforms) # Update flyer enemies


        # --- Collision Detection ---

        # Player-PowerUp Collision
        hit_powerups = pygame.sprite.spritecollide(player, powerups, False) # Don't kill immediately
        for pu in hit_powerups:
            pu.apply_effect(player) # Apply effect, which also calls pu.kill()
            # powerups.remove(pu) # This is handled by pu.kill() which removes from all groups


        # Player-Enemy Collision (Player takes damage unless shielding, rolling, or fire dashing)
        # Define a function to handle player-to-enemy collision damage to reduce redundancy
        def handle_player_enemy_collision(enemy_sprite, player_ref):
            global lives, current_game_state, score # Access global variables
            if player_ref.take_hit(): # Player takes damage (checks shields internally)
                lives -= 1
                if lives <= 0:
                    current_game_state = GAME_STATE_GAMEOVER
                    update_player_high_score(score)
                    player_ref.reset_position_and_state(keep_powerups=False) # Clear power-ups on game over
                else:
                    player_ref.reset_position_and_state(keep_powerups=True) # Reset player for next life, KEEP powerups
            else: # Hit was blocked by a shield or invincibility
                # Push enemy back slightly if blocked (optional)
                if hasattr(enemy_sprite, 'vel_x'): # Check if enemy has vel_x
                    enemy_sprite.vel_x *= -1

        # Fire Dash collision (priority)
        if player.is_fire_dashing and player.fire_dash_active:
            fire_dash_enemies = pygame.sprite.spritecollide(player, enemies, False) + \
                                pygame.sprite.spritecollide(player, shooter_enemies, False) + \
                                pygame.sprite.spritecollide(player, flyer_enemies, False)
            
            for enemy_target in fire_dash_enemies:
                damage_dealt = FIRE_DASH_DAMAGE_MULTIPLIER * player.attack_damage_multiplier
                enemy_target.take_damage(damage_dealt)
                if not enemy_target.alive():
                    score += 10 # Points for defeating enemies with fire dash

            if boss_active and boss_sprite and pygame.sprite.collide_rect(player, boss_sprite):
                boss_sprite.take_damage(FIRE_DASH_DAMAGE_MULTIPLIER * player.attack_damage_multiplier * 5) # Fire dash stronger on boss
                score += 25 # More score for fire dashing boss


        # Regular and Guard enemies
        colliding_enemies_general = pygame.sprite.spritecollide(player, enemies, False)
        for enemy in colliding_enemies_general:
            # Only take damage if not fire dashing
            if not player.is_fire_dashing:
                handle_player_enemy_collision(enemy, player)

        # Shooter enemies
        colliding_shooter_enemies = pygame.sprite.spritecollide(player, shooter_enemies, False)
        for enemy in colliding_shooter_enemies:
            if not player.is_fire_dashing:
                handle_player_enemy_collision(enemy, player)
        
        # Flyer enemies
        colliding_flyer_enemies = pygame.sprite.spritecollide(player, flyer_enemies, False)
        for enemy in colliding_flyer_enemies:
            if not player.is_fire_dashing:
                handle_player_enemy_collision(enemy, player)


        # Player-Boss Direct Collision
        if boss_active and boss_sprite and pygame.sprite.collide_rect(player, boss_sprite):
            if not player.is_fire_dashing: # Only take damage if not fire dashing
                handle_player_enemy_collision(boss_sprite, player)


        # Projectile-Enemy Collision (Player's blast hits regular enemies)
        for projectile in projectiles:
            hit_enemies_general = pygame.sprite.spritecollide(projectile, enemies, False) # Check for regular/guard
            for enemy in hit_enemies_general:
                projectile.kill()
                enemy.take_damage(1 * player.attack_damage_multiplier) # Player blast damage
                if not enemy.alive():
                    score += 10
            
            hit_shooter_enemies = pygame.sprite.spritecollide(projectile, shooter_enemies, False) # Check for shooter
            for enemy in hit_shooter_enemies:
                projectile.kill()
                enemy.take_damage(1 * player.attack_damage_multiplier) # Player blast damage
                if not enemy.alive():
                    score += 10
            
            hit_flyer_enemies = pygame.sprite.spritecollide(projectile, flyer_enemies, False) # Check for flyer
            for enemy in hit_flyer_enemies:
                projectile.kill()
                enemy.take_damage(1 * player.attack_damage_multiplier) # Player blast damage
                if not enemy.alive():
                    score += 10


        # Projectile-Boss Collision (Player's blast hits boss)
        if boss_active and boss_sprite:
            for projectile in projectiles:
                if pygame.sprite.collide_rect(projectile, boss_sprite):
                    boss_sprite.take_damage(20 * player.attack_damage_multiplier) # Blast does 20 damage to boss
                    projectile.kill() # Destroy projectile on hit
                    score += 5 # Small score for hitting boss

        # Boss Projectile-Player/Orbiting Light Collision
        if boss_active and boss_sprite and player:
            potential_targets = pygame.sprite.Group()
            potential_targets.add(player)
            if player.orbit_shield_hits > 0:
                potential_targets.add(orbiting_lights_group.sprites())

            collided_projectiles_map = pygame.sprite.groupcollide(boss_projectiles, potential_targets, True, False)

            for projectile, targets_hit in collided_projectiles_map.items():
                for target in targets_hit:
                    if target == player:
                        if not player.is_fire_dashing: # Only take damage if not fire dashing
                            handle_player_enemy_collision(target, player)
                        break # Only process one hit for this projectile
                    elif isinstance(target, OrbitingLight):
                        player.take_hit() # Consume shield charge
                        break # Only process one hit for this projectile

        # Shooter Projectile-Player/Orbiting Light Collision (New logic for shooter projectiles)
        if player and shooter_enemies: # Only check if player and shooter enemies exist
            potential_targets_for_shooter = pygame.sprite.Group()
            potential_targets_for_shooter.add(player)
            if player.orbit_shield_hits > 0:
                potential_targets_for_shooter.add(orbiting_lights_group.sprites())

            collided_shooter_projectiles_map = pygame.sprite.groupcollide(shooter_projectiles, potential_targets_for_shooter, True, False)

            for projectile, targets_hit in collided_shooter_projectiles_map.items():
                for target in targets_hit:
                    if target == player:
                        if not player.is_fire_dashing: # Only take damage if not fire dashing
                            handle_player_enemy_collision(target, player)
                        break
                    elif isinstance(target, OrbitingLight):
                        player.take_hit() # Consume shield charge
                        break


        # Player-Coin Collision
        collected_coins = pygame.sprite.spritecollide(player, coins, True) # True means remove coin on collision
        for coin in collected_coins:
            score += 1


        # --- Level Completion Logic ---
        # Check for boss defeat
        if boss_active and boss_sprite and not boss_sprite.alive():
            print("BOSS DEFEATED!")
            current_game_state = GAME_STATE_LEVEL_COMPLETE
            update_player_high_score(score)
            boss_sprite = None
            boss_projectiles.empty()
        # Check for regular level completion (all coins collected and no enemies left)
        elif not boss_active and len(coins) == 0 and initial_coin_count_level > 0 and \
             len(enemies) == 0 and len(shooter_enemies) == 0 and len(flyer_enemies) == 0: # Include flyer enemies
            current_game_state = GAME_STATE_LEVEL_COMPLETE
            update_player_high_score(score)
        
        # Draw all sprites
        all_sprites.draw(screen)
        # Draw power-ups (separately so they appear on top of platforms)
        powerups.draw(screen)
        # Draw orbiting lights (separately so they appear on top of player)
        orbiting_lights_group.draw(screen) # Use global group for drawing

        # Draw slash attack visual ONLY if is_slashing_anim is true and player exists
        if player and player.is_slashing_anim and SLASH_IMAGE:
            # Determine which weapon image to draw for slash animation
            weapon_draw_image = None
            if player.current_weapon == "big_sword" and BIG_SWORD_IMAGE:
                weapon_draw_image = BIG_SWORD_IMAGE
            elif player.current_weapon == "dagger" and DAGGER_IMAGE:
                weapon_draw_image = DAGGER_IMAGE
            elif player.current_weapon == "club" and CLUB_IMAGE:
                weapon_draw_image = CLUB_IMAGE
            else: # Default slash image if no specific weapon or image missing
                weapon_draw_image = SLASH_IMAGE

            if weapon_draw_image:
                # Adjust position to be near the player and facing correct direction
                if player.facing_right:
                    slash_draw_x = player.rect.right - (PLAYER_WIDTH // 4) # Slightly overlap player
                    draw_image = weapon_draw_image
                else:
                    slash_draw_x = player.rect.left - weapon_draw_image.get_width() + (PLAYER_WIDTH // 4) # Slightly overlap
                    draw_image = pygame.transform.flip(weapon_draw_image, True, False) # Flip for left
                screen.blit(draw_image, (slash_draw_x, player.rect.centery - draw_image.get_height() // 2))


        # Draw Boss Health Bar
        if boss_active and boss_sprite and boss_sprite.alive():
            bar_width = BOSS_WIDTH * 2 # Make health bar wider than boss
            bar_height = 10
            bar_x = boss_sprite.rect.centerx - bar_width // 2
            bar_y = boss_sprite.rect.top - bar_height - 5 # Above the boss

            # Background bar
            pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height), 0, 3) # Rounded corners

            # Health portion
            health_width = (boss_sprite.health / BOSS_HEALTH_MAX) * bar_width
            pygame.draw.rect(screen, BOSS_HEALTH_COLOR, (bar_x, bar_y, health_width, bar_height), 0, 3) # Rounded corners

        # Draw score and lives in PLAYING/BOSS_FIGHT state
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        lives_text = font.render(f"Lives: {lives}", True, RED)
        screen.blit(lives_text, (SCREEN_WIDTH - lives_text.get_width() - 10, 10))

        level_text = font.render(f"Level: {current_level + 1}", True, WHITE) # Display actual level number (1-indexed)
        screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 10))

        player_name_text = font.render(f"Player: {selected_player_name}", True, ORANGE)
        screen.blit(player_name_text, (10, 50))

        # Display active power-up status (without timers)
        hud_y_offset = 90
        if player.can_double_blast:
            double_blast_status = font.render(f"Double Blast!", True, WHITE)
            screen.blit(double_blast_status, (10, hud_y_offset))
            hud_y_offset += 40
        if player.orbit_shield_hits > 0:
            orbit_shield_status = font.render(f"Orbit Shield: {player.orbit_shield_hits} hits", True, WHITE)
            screen.blit(orbit_shield_status, (10, hud_y_offset))
            hud_y_offset += 40
        if player.can_quad_jump:
            quad_jump_status = font.render(f"4x Jump!", True, WHITE)
            screen.blit(quad_jump_status, (10, hud_y_offset))
            hud_y_offset += 40
        if player.is_rolling: # Display rolling status
            roll_status = font.render(f"Rolling!", True, (0, 255, 255)) # Cyan text
            screen.blit(roll_status, (10, hud_y_offset))
            hud_y_offset += 40
        if player.is_fire_dashing: # Display fire dash status
            fire_dash_status = font.render(f"Fire Dashing!", True, FIRE_RED[:3]) # Fiery red text
            screen.blit(fire_dash_status, (10, hud_y_offset))
            hud_y_offset += 40
        
        # Display current weapon
        weapon_display_name = player.current_weapon.replace('_', ' ').title()
        weapon_text = font.render(f"Weapon: {weapon_display_name}", True, GOLD)
        screen.blit(weapon_text, (10, hud_y_offset))


    elif current_game_state == GAME_STATE_MENU:
        # Display Title
        title_text = menu_font_large.render("Boot.dev Platformer", True, BLACK)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 200))
        screen.blit(title_text, title_rect)

        # Display High Score for selected player on Menu
        high_score_text = menu_font_medium.render(f"High Score ({selected_player_name}): {high_score}", True, BLACK)
        high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
        screen.blit(high_score_text, high_score_rect)

        # "Press ENTER to Select Player"
        select_player_prompt = menu_font_medium.render("Press ENTER to Select Player", True, BLACK)
        select_player_rect = select_player_prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(select_player_prompt, select_player_rect)

        # "Press ESC to Quit"
        quit_prompt = menu_font_medium.render("Press ESC to Quit", True, BLACK)
        quit_rect = quit_prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        screen.blit(quit_prompt, quit_rect)


    elif current_game_state == GAME_STATE_PLAYER_SELECT:
        screen.fill(LIGHT_BLUE) # Clear screen for player select
        
        select_title = menu_font_large.render("Select Player", True, BLACK)
        select_title_rect = select_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 200))
        screen.blit(select_title, select_title_rect)

        y_offset = SCREEN_HEIGHT // 2 - 100
        if not player_profiles:
            no_players_text = menu_font_medium.render("No players found. Press 'N' to create one!", True, RED)
            no_players_rect = no_players_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset + 50))
            screen.blit(no_players_text, no_players_rect)
        else:
            for i, profile in enumerate(player_profiles):
                color = ORANGE if i == selected_player_index else BLACK
                player_display_text = font.render(f"{profile['name']} (High Score: {profile['high_score']})", True, color)
                player_display_rect = player_display_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset + i * 40))
                screen.blit(player_display_text, player_display_rect)

            select_prompt = menu_font_small.render("Use UP/DOWN to select, ENTER to play", True, BLACK)
            select_prompt_rect = select_prompt.get_rect(center=(SCREEN_WIDTH // 2, y_offset + len(player_profiles) * 40 + 50))
            screen.blit(select_prompt, select_prompt_rect)
        
        create_player_prompt = menu_font_small.render("Press 'N' to Create New Player", True, BLACK)
        create_player_rect = create_player_prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 130))
        screen.blit(create_player_prompt, create_player_rect)

        reset_hs_prompt = menu_font_small.render("Press 'R' to Reset High Score", True, BLACK)
        reset_hs_rect = reset_hs_prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 90))
        screen.blit(reset_hs_prompt, reset_hs_rect)

        delete_player_prompt = menu_font_small.render("Press 'D' to Delete Player", True, BLACK)
        delete_player_rect = delete_player_prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        screen.blit(delete_player_prompt, delete_player_rect)


    elif current_game_state == GAME_STATE_CREATE_PLAYER:
        screen.fill(LIGHT_BLUE)
        create_title = menu_font_large.render("Create New Player", True, BLACK)
        create_title_rect = create_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(create_title, create_title_rect)

        enter_name_prompt = font.render("Enter Name:", True, BLACK)
        enter_name_rect = enter_name_prompt.get_rect(topright=(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2 + 10))
        screen.blit(enter_name_prompt, enter_name_rect)

        new_player_input_box.draw(screen)

        confirm_prompt = font.render("Press ENTER to Confirm, ESC to Cancel", True, BLACK)
        confirm_rect = confirm_prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        screen.blit(confirm_prompt, confirm_rect)

    elif current_game_state == GAME_STATE_WEAPON_SELECT:
        screen.fill(LIGHT_BLUE)
        weapon_title = menu_font_large.render("Choose Your Weapon!", True, BLACK)
        weapon_title_rect = weapon_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 200))
        screen.blit(weapon_title, weapon_title_rect)

        weapons_options = [
            ("Big Sword", BIG_SWORD_IMAGE, "Longer range, standard damage."),
            ("Dagger", DAGGER_IMAGE, "3x damage when attacking from behind."),
            ("Club", CLUB_IMAGE, "Knocks enemies away on hit.")
        ]
        
        y_offset = SCREEN_HEIGHT // 2 - 50
        for i, (name, image, description) in enumerate(weapons_options):
            color = GOLD if i == weapon_select_index else BLACK
            
            # Display weapon image
            if image:
                # Scale for display in menu, maybe slightly larger
                display_image = pygame.transform.scale(image, (PLAYER_WIDTH * 3, PLAYER_HEIGHT * 3))
                image_rect = display_image.get_rect(midright=(SCREEN_WIDTH // 2 - 20, y_offset + i * 100 + display_image.get_height() // 2))
                screen.blit(display_image, image_rect)
            
            # Display weapon name
            weapon_name_text = menu_font_medium.render(name, True, color)
            weapon_name_rect = weapon_name_text.get_rect(midleft=(SCREEN_WIDTH // 2 + 20, y_offset + i * 100 + 10))
            screen.blit(weapon_name_text, weapon_name_rect)

            # Display weapon description
            weapon_desc_text = menu_font_small.render(description, True, BLACK)
            weapon_desc_rect = weapon_desc_text.get_rect(topleft=(SCREEN_WIDTH // 2 + 20, y_offset + i * 100 + 40))
            screen.blit(weapon_desc_text, weapon_desc_rect)
            

        select_prompt = menu_font_small.render("Use UP/DOWN to select, ENTER to confirm", True, BLACK)
        select_prompt_rect = select_prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        screen.blit(select_prompt, select_prompt_rect)


    elif current_game_state == GAME_STATE_PAUSED:
        all_sprites.draw(screen) # Draw game elements first
        boss_projectiles.draw(screen) # Ensure boss projectiles are also drawn underneath overlay
        shooter_projectiles.draw(screen) # Draw shooter projectiles underneath overlay
        # Draw power-ups and orbiting lights underneath overlay too
        powerups.draw(screen)
        orbiting_lights_group.draw(screen) # Use global group for drawing

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
        level_text = font.render(f"Level: {current_level + 1}", True, WHITE)
        screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 10))
        player_name_text = font.render(f"Player: {selected_player_name}", True, ORANGE)
        screen.blit(player_name_text, (10, 50))
        
        # Display active power-up status (without timers)
        hud_y_offset = 90
        if player.can_double_blast:
            double_blast_status = font.render(f"Double Blast!", True, WHITE)
            screen.blit(double_blast_status, (10, hud_y_offset))
            hud_y_offset += 40
        if player.orbit_shield_hits > 0:
            orbit_shield_status = font.render(f"Orbit Shield: {player.orbit_shield_hits} hits", True, WHITE)
            screen.blit(orbit_shield_status, (10, hud_y_offset))
            hud_y_offset += 40
        if player.can_quad_jump:
            quad_jump_status = font.render(f"4x Jump!", True, WHITE)
            screen.blit(quad_jump_status, (10, hud_y_offset))
            hud_y_offset += 40
        if player.is_rolling: # Display rolling status
            roll_status = font.render(f"Rolling!", True, (0, 255, 255)) # Cyan text
            screen.blit(roll_status, (10, hud_y_offset))
            hud_y_offset += 40
        if player.is_fire_dashing: # Display fire dash status
            fire_dash_status = font.render(f"Fire Dashing!", True, FIRE_RED[:3]) # Fiery red text
            screen.blit(fire_dash_status, (10, hud_y_offset))
            hud_y_offset += 40
        
        # Display current weapon
        weapon_display_name = player.current_weapon.replace('_', ' ').title()
        weapon_text = font.render(f"Weapon: {weapon_display_name}", True, GOLD)
        screen.blit(weapon_text, (10, hud_y_offset))


    elif current_game_state == GAME_STATE_GAMEOVER:
        game_over_text = game_over_font.render("GAME OVER!", True, RED)
        final_score_text = menu_font_medium.render(f"Final Score ({selected_player_name}): {score}", True, WHITE)
        high_score_display_text = menu_font_small.render(f"High Score: {high_score}", True, WHITE)
        restart_text = font.render("Press any key to return to player select", True, WHITE)

        go_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        hs_display_rect = high_score_display_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))

        screen.blit(game_over_text, go_rect)
        screen.blit(final_score_text, score_rect)
        screen.blit(high_score_display_text, hs_display_rect)
        screen.blit(restart_text, restart_rect)

    elif current_game_state == GAME_STATE_LEVEL_COMPLETE:
        level_complete_text = game_over_font.render("LEVEL COMPLETE!", True, GREEN)
        current_score_text = menu_font_medium.render(f"Score ({selected_player_name}): {score}", True, WHITE)
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
