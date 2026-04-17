"""
TESLA Configuration File
Contains all game settings, constants, and color definitions
"""

# Screen Settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900
FPS = 60
TITLE = "TESLA - Autonomous Driving Simulator"

# Colors - Lesogo-inspired palette (warm earthy tones)
COLORS = {
    'background': (240, 235, 225),  # Warm cream
    'road': (90, 85, 80),  # Dark warm grey
    'road_line': (255, 240, 200),  # Warm yellow
    'road_line_yellow': (255, 180, 80),  # Warm orange-yellow
    'lane_marking': (150, 140, 130),  # Warm grey
    'zebra_crossing': (240, 235, 220),  # Cream
    'grass': (120, 150, 90),  # Warm olive green
    'path_to_trees': (200, 180, 160),  # Warm sandy path
    'path_to_road': (160, 150, 140),  # Greyish path
    'building': (180, 140, 100),  # Warm terracotta
    'building_window': (255, 200, 100),  # Warm golden
    'tree_trunk': (100, 70, 40),  # Warm brown
    'tree_leaves': (70, 110, 60),  # Warm forest green
    'tesla_blue': (100, 150, 180),  # Warm slate blue
    'tesla_red': (200, 80, 60),  # Warm terracotta red
    'tesla_white': (245, 240, 235),  # Warm white
    'tesla_dark': (70, 60, 50),  # Warm dark brown
    'neon_blue': (100, 160, 190),  # Warm sky blue
    'neon_cyan': (120, 170, 160),  # Warm teal
    'dashboard_bg': (0, 0, 0),  # Warm dark grey
    'dashboard_text': (230, 220, 210),  # Warm light
    'warning': (220, 100, 60),  # Warm orange
    'success': (120, 180, 100),  # Warm sage green
    'traffic_red': (220, 80, 60),  # Warm red
    'traffic_yellow': (255, 180, 80),  # Warm yellow
    'traffic_green': (120, 180, 100),  # Warm green
    'pedestrian': (255, 200, 150),  # Warm peach
    'obstacle': (160, 90, 70),  # Warm brown
    'shadow': (50, 40, 35),  # Warm shadow
    'pedestrian_crossing_indicator': (120, 160, 190),  # Warm blue
}

# Road Settings
LANE_WIDTH = 80
NUM_LANES = 3
ROAD_Y_START = 250
ROAD_HEIGHT = LANE_WIDTH * NUM_LANES
ROAD_MARGIN = 20

# Tesla Car Settings
CAR_WIDTH = 35
CAR_LENGTH = 70
CAR_MAX_SPEED = 5.5  # Reduced from 8.0 to limit max speed to ~82 MPH
CAR_ACCELERATION = 0.08  # Smoother acceleration (reduced from 0.15)
CAR_DECELERATION = 0.12  # Smoother deceleration (reduced from 0.25)
CAR_BRAKE_POWER = 0.35  # Slightly reduced brake power
CAR_TURN_SPEED = 3.0
SAFE_DISTANCE = 120
CRITICAL_DISTANCE = 60

# Speed Limits
MAX_SPEED_MPH = 85  # Maximum speed limit in MPH
MIN_SPEED_MPH = 0

# AI Settings
AI_UPDATE_INTERVAL = 100  # milliseconds
SENSOR_RANGE = 300
SENSOR_ANGLE_SPREAD = 30  # Reduced spread for focused front detection
NUM_SENSOR_RAYS = 15      # Increased rays to detect thin obstacles (barrier/red-white thing)


# Traffic Settings
MAX_TRAFFIC_CARS = 6
TRAFFIC_SPAWN_INTERVAL = 3000  # milliseconds
TRAFFIC_MIN_SPEED = 2.0
TRAFFIC_MAX_SPEED = 4.5  # Reduced from 5.0 for slower traffic
TRAFFIC_MIN_SPAWN_DISTANCE = 250  # Minimum distance between spawned cars
TRAFFIC_SPAWN_AHEAD_DISTANCE = 400  # Minimum distance ahead of agent to spawn

# Pedestrian Settings
MAX_PEDESTRIANS = 6
PEDESTRIAN_SPAWN_INTERVAL = 3000
PEDESTRIAN_SPEED = 1.8

# Pedestrian Crossing Indicator (replaces traffic lights)
CROSSING_INDICATOR_SIZE = 40
CROSSING_INDICATOR_MARGIN = 20

# Legacy traffic light settings (kept for backwards compatibility)
LIGHT_RED_DURATION = 5000
LIGHT_GREEN_DURATION = 5000
LIGHT_YELLOW_DURATION = 1500
TRAFFIC_LIGHT_POSITIONS = []

# Obstacle Settings
MAX_STATIC_OBSTACLES = 3
OBSTACLE_SPAWN_CHANCE = 0.3

# Learning/Memory Settings
import os
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(_BASE_DIR, 'ai', 'memory.json')
CRASH_PENALTY = -50
SAFE_PASS_REWARD = 10
LANE_CHANGE_REWARD = 5
SMOOTH_DRIVING_REWARD = 1

# UI Settings
DASHBOARD_HEIGHT = 150
DASHBOARD_OPACITY = 220
MINI_MAP_SIZE = 150
FONT_SIZE_LARGE = 24
FONT_SIZE_MEDIUM = 18
FONT_SIZE_SMALL = 14

# Prolog Rules File
PROLOG_RULES_FILE = os.path.join(_BASE_DIR, 'ai', 'prolog_rules.pl')

# Game Modes
MODE_SIMULATION = 'simulation'
