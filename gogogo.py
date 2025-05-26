from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.prefabs.button import Button
import random
from enum import Enum
import math

# --- Constants and Configuration ---

class GameState(Enum):
    """Defines the various states the game can be in."""
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    WIN = 3
    LOSE = 4

class GameConfig:
    """Centralized configuration for all game settings."""
    def __init__(self):
        # Window Settings
        self.WINDOW_TITLE = "Cube Maze Adventure PRO"
        self.WINDOW_BORDERLESS = False
        self.WINDOW_FULLSCREEN = False
        self.WINDOW_FPS_COUNTER = True

        # Player Settings
        self.PLAYER_SPEED = 8
        self.JUMP_HEIGHT = 10
        self.GRAVITY = 25
        self.PLAYER_HEIGHT_OFFSET = 0.5 # To place player correctly on ground
        self.PLAYER_MAX_HEALTH = 3
        self.PLAYER_HIT_INVULNERABILITY_TIME = 1.0 # seconds after taking damage

        # Monster Settings
        self.MONSTER_SPEED = 2.5
        self.MONSTER_VISION_RANGE = 10 # How far the monster can "see" the player
        self.MONSTER_PATROL_TYPE = 'sine' # 'linear' or 'sine'
        self.MONSTER_PATROL_AMPLITUDE = 8 # Distance for monster to patrol if no player seen
        self.MONSTER_PATROL_FREQUENCY = 1.0 # How fast the sine wave oscillates
        self.MONSTER_ATTACK_COOLDOWN = 3.0 # seconds between attacks
        self.MONSTER_ATTACK_WINDUP_TIME = 1.0 # time before projectile fires
        self.MONSTER_ATTACK_PROJECTILE_SPEED = 15
        self.MONSTER_ATTACK_PROJECTILE_LIFETIME = 2.0 # how long projectile exists
        self.MONSTER_ATTACK_DAMAGE = 1

        # Maze Settings
        self.MAZE_DIMENSION = 20 # Maze will be MAZE_DIMENSION x MAZE_DIMENSION (must be odd for recursive backtracking)
        self.MAZE_WALL_HEIGHT = 1.0 # Height of the raised maze walls
        self.MAZE_PATH_HEIGHT = 0.0 # Height of the paths
        self.CELL_SIZE = 1.0 # Size of each maze cell (wall or path)

        # Ground Plane Visuals
        self.GROUND_SCALE = self.MAZE_DIMENSION * self.CELL_SIZE * 1.5 # Larger than maze for padding
        self.GROUND_TEXTURE_SCALE = self.GROUND_SCALE / self.CELL_SIZE # Texture tiling

        # Entity Colors
        self.COLOR_PLAYER = color.azure
        self.COLOR_GOAL = color.orange
        self.COLOR_MONSTER = color.red
        self.COLOR_MONSTER_ATTACK_CUE = color.yellow # For attack wind-up
        self.COLOR_PROJECTILE = color.magenta
        self.COLOR_GROUND_PATH = color.light_gray # Color for maze paths
        self.COLOR_GROUND_WALL = color.dark_gray # Color for maze walls
        self.COLOR_OUTSIDE_MAZE = color.green # Color for area outside the maze

        # UI Colors
        self.COLOR_UI_TITLE = color.azure
        self.COLOR_UI_WIN = color.lime
        self.COLOR_UI_LOSE = color.red
        self.COLOR_UI_HEALTH = color.red
        self.COLOR_UI_HEALTH_BG = color.gray

        # Camera Settings (for menu/game over scenes)
        self.MENU_CAMERA_POS = (0, 20, -30)
        self.MENU_CAMERA_ROT = (30, 0, 0)
        self.GAME_OVER_CAMERA_POS = (0, 0, -10)
        self.GAME_OVER_CAMERA_ROT = (0, 0, 0)
        self.PLAYER_CAMERA_FOV = 90 # FOV when camera is attached to player

        # Ensure maze dimension is odd for recursive backtracking
        if self.MAZE_DIMENSION % 2 == 0:
            self.MAZE_DIMENSION += 1 # Make it odd


# --- Game Entities ---

class Player(FirstPersonController):
    """
    Custom player entity. Extends FirstPersonController for built-in FPS movement,
    with added game-specific logic for health, damage, and state management.
    """
    def __init__(self, position):
        super().__init__(
            position=position,
            speed=game_config.PLAYER_SPEED,
            jump_height=game_config.JUMP_HEIGHT,
            gravity=game_config.GRAVITY,
            collider='box', # Collider against the terrain
            origin_y=-game_config.PLAYER_HEIGHT_OFFSET, # Adjust visual origin
            name='player_entity'
        )
        self.start_position = position # Store initial position for restarts
        self.color = game_config.COLOR_PLAYER

        self.max_health = game_config.PLAYER_MAX_HEALTH
        self.current_health = self.max_health
        self.is_invulnerable = False
        self._invulnerability_timer = 0.0

    def on_enable(self):
        """Called when the entity is enabled."""
        super().on_enable()
        camera.parent = self
        camera.position = (0, 0, 0) # Camera is at player's head
        camera.rotation = (0, 0, 0)
        camera.fov = game_config.PLAYER_CAMERA_FOV
        mouse.locked = True # Lock mouse for FPS control
        self.visible = True # Ensure player is visible

    def on_disable(self):
        """Called when the entity is disabled."""
        super().on_disable()
        mouse.locked = False # Unlock mouse when player is not active
        self.visible = False # Hide player when disabled

    def update(self):
        """Player-specific update logic."""
        super().update() # Call base FirstPersonController update

        if self.is_invulnerable:
            self._invulnerability_timer -= time.dt
            # Simple blinking effect
            self.visible = not self.visible if int(self._invulnerability_timer * 10) % 2 == 0 else True
            if self._invulnerability_timer <= 0:
                self.is_invulnerable = False
                self.visible = True # Ensure visible after invulnerability ends

    def take_damage(self, amount):
        """Applies damage to the player."""
        if not self.is_invulnerable:
            self.current_health -= amount
            print(f"Player took {amount} damage. Health: {self.current_health}/{self.max_health}")
            game.ui_manager.update_health_display(self.current_health)

            if self.current_health <= 0:
                game.set_game_state(GameState.LOSE)
            else:
                self.is_invulnerable = True
                self._invulnerability_timer = game_config.PLAYER_HIT_INVULNERABILITY_TIME
                # Optional: Play a hit sound or animation here

    def reset_state(self):
        """Resets the player to their starting position, full health, and normal state."""
        self.position = self.start_position
        self.rotation = (0, 0, 0) # Reset player orientation
        self.current_health = self.max_health
        self.is_invulnerable = False
        self._invulnerability_timer = 0.0
        self.visible = True
        self.enabled = True # Ensure enabled for next game, handled by GameState
        game.ui_manager.update_health_display(self.current_health) # Update UI


class Goal(Entity):
    """The goal entity the player needs to reach to win."""
    def __init__(self, position):
        super().__init__(
            model='cube',
            color=game_config.COLOR_GOAL,
            scale=(game_config.CELL_SIZE * 0.8, game_config.MAZE_WALL_HEIGHT * 1.5, game_config.CELL_SIZE * 0.8),
            position=position,
            collider='box', # Trigger collider
            name='goal_entity'
        )
        # Goal should be placed slightly above the path height
        self.y += game_config.MAZE_PATH_HEIGHT + self.scale_y / 2
        self.visible = True # Ensure visible initially

    def on_trigger_enter(self, other):
        """
        Called when another collider enters this entity's trigger.
        Used to detect when the player reaches the goal.
        """
        if other == game.player:
            invoke(game.set_game_state, GameState.WIN, delay=0.1)

    def reset_state(self):
        """Resets the goal's state (mainly visibility)."""
        self.enabled = True
        self.visible = True


class MonsterProjectile(Entity):
    """Represents a projectile fired by the monster."""
    def __init__(self, start_pos, target_dir):
        super().__init__(
            model='sphere', # Or 'cube', depending on preference
            color=game_config.COLOR_PROJECTILE,
            scale=0.5,
            position=start_pos,
            collider='sphere', # Smaller collider for projectile
            name='monster_projectile'
        )
        self.speed = game_config.MONSTER_ATTACK_PROJECTILE_SPEED
        self.direction = target_dir.normalized()
        self.lifetime = game_config.MONSTER_ATTACK_PROJECTILE_LIFETIME
        self._timer = self.lifetime
        self.y = game_config.MAZE_PATH_HEIGHT + self.scale_y / 2 # Keep it floating above ground

    def update(self):
        """Projectile movement and collision detection."""
        self.position += self.direction * self.speed * time.dt
        self._timer -= time.dt

        if self._timer <= 0:
            destroy(self) # Destroy projectile after its lifetime

        # Check collision with player
        if game.player and game.player.enabled and self.intersects(game.player).hit:
            game.player.take_damage(game_config.MONSTER_ATTACK_DAMAGE)
            destroy(self) # Destroy on hit


class Monster(Entity):
    """The monster entity that patrols, chases, and attacks the player."""
    def __init__(self, position):
        super().__init__(
            model='cube',
            color=game_config.COLOR_MONSTER,
            scale=(game_config.CELL_SIZE * 1.2, game_config.MAZE_WALL_HEIGHT * 1.5, game_config.CELL_SIZE * 1.2),
            position=position,
            collider='box',
            name='monster_entity'
        )
        self.start_position = position
        self.speed = game_config.MONSTER_SPEED
        self.current_patrol_time = 0.0 # For sine wave patrolling
        self.patrol_start_x = position.x # Base for sine wave

        self.y = game_config.MAZE_PATH_HEIGHT + self.scale_y / 2 # Keep it floating above ground

        self._attack_cooldown_timer = 0.0
        self._attack_windup_timer = 0.0
        self._is_winding_up_attack = False
        self.target_for_attack = None # Player's position when attack initiated

        self.visible = True # Ensure visible initially

    def update(self):
        """Monster's AI update logic."""
        if game.current_state != GameState.PLAYING:
            return

        if self._is_winding_up_attack:
            self._attack_windup_timer -= time.dt
            if self._attack_windup_timer <= 0:
                self._execute_attack()
                self._is_winding_up_attack = False
                self._attack_cooldown_timer = game_config.MONSTER_ATTACK_COOLDOWN
                self.color = game_config.COLOR_MONSTER # Reset color
            else:
                # Keep facing player during wind-up
                if game.player and game.player.enabled:
                    self.look_at(game.player.position)
            return # Don't move or start new attack while winding up

        self._attack_cooldown_timer -= time.dt

        # Check if player is within vision range
        player_in_range = game.player and game.player.enabled and \
                          distance(self.position, game.player.position) < game_config.MONSTER_VISION_RANGE

        if player_in_range and self._attack_cooldown_timer <= 0:
            # Player in range and attack off cooldown - initiate attack wind-up
            self._start_attack_windup()
            self.color = game_config.COLOR_MONSTER_ATTACK_CUE # Visual cue
        elif player_in_range:
            # Player in range but attack on cooldown, just chase
            self._chase_player()
        else:
            # No player in range, patrol
            self._patrol()

    def _chase_player(self):
        """Monster chases the player."""
        direction_to_target = (game.player.position - self.position).normalized()
        direction_to_target.y = 0 # Keep movement on XZ plane
        self.position += direction_to_target * self.speed * time.dt
        self.look_at(self.position + direction_to_target)

    def _patrol(self):
        """Monster patrols based on configured type."""
        if game_config.MONSTER_PATROL_TYPE == 'linear':
            target_a = Vec3(self.patrol_start_x, self.y, self.start_position.z)
            target_b = Vec3(self.patrol_start_x + game_config.MONSTER_PATROL_AMPLITUDE, self.y, self.start_position.z)

            if self.target_position is None or distance(self.position, self.target_position) < 0.1:
                if self.target_position == target_a:
                    self.target_position = target_b
                else:
                    self.target_position = target_a

            if self.target_position:
                direction_to_target = (self.target_position - self.position).normalized()
                self.position += direction_to_target * self.speed * time.dt
                self.look_at(self.position + direction_to_target)

        elif game_config.MONSTER_PATROL_TYPE == 'sine':
            self.current_patrol_time += time.dt * game_config.MONSTER_PATROL_FREQUENCY
            new_x = self.patrol_start_x + math.sin(self.current_patrol_time) * game_config.MONSTER_PATROL_AMPLITUDE

            old_x = self.position.x
            self.position = Vec3(new_x, self.y, self.start_position.z)

            if new_x > old_x:
                self.look_at(self.position + Vec3(1,0,0))
            else:
                self.look_at(self.position + Vec3(-1,0,0))

    def _start_attack_windup(self):
        """Initiates the monster's attack wind-up phase."""
        self._is_winding_up_attack = True
        self._attack_windup_timer = game_config.MONSTER_ATTACK_WINDUP_TIME
        # Store player's position at start of wind-up to shoot at it
        if game.player and game.player.enabled:
            self.target_for_attack = game.player.position
        else:
            self.target_for_attack = self.forward * 10 # Shoot forward if no player

        # Optional: Play attack wind-up sound
        # Audio('monster_windup.wav', autoplay=True)

    def _execute_attack(self):
        """Fires the monster's projectile."""
        if self.target_for_attack:
            # Determine projectile direction (from monster to target)
            direction_to_target = (self.target_for_attack - self.position).normalized()
            # Spawn projectile slightly in front of the monster
            projectile_spawn_pos = self.position + self.forward * (self.scale_x / 2 + 0.1)
            MonsterProjectile(projectile_spawn_pos, direction_to_target)
            # Optional: Play attack sound
            # Audio('monster_shoot.wav', autoplay=True)
        self.target_for_attack = None # Clear target for next attack

    def reset_state(self):
        """Resets the monster to its starting position and state."""
        self.position = self.start_position
        self.y = game_config.MAZE_PATH_HEIGHT + self.scale_y / 2
        self.target_position = None # Clear patrol target
        self.current_patrol_time = 0.0 # Reset sine wave patrol
        self._attack_cooldown_timer = 0.0
        self._attack_windup_timer = 0.0
        self._is_winding_up_attack = False
        self.color = game_config.COLOR_MONSTER # Reset to default color
        self.visible = True
        self.enabled = True # Ensure enabled for next game, handled by GameState


# --- Maze and Terrain Generation ---

class TerrainMazeGenerator:
    """
    Generates a maze integrated into the ground, dynamically creating a Mesh.
    Uses recursive backtracking for maze generation.
    """
    def __init__(self, dimension, cell_size, wall_height, path_height):
        self.dimension = dimension
        self.cell_size = cell_size
        self.wall_height = wall_height
        self.path_height = path_height
        self.maze_grid = [] # Stores the generated maze layout (0=path, 1=wall)
        self.mesh_entity = None # The Ursina entity holding the mesh

    def generate_random_maze(self):
        """
        Generates a random maze using recursive backtracking and
        creates an Ursina Mesh for the terrain based on it.
        """
        self.clear_maze() # Clear any existing mesh/entities

        # Initialize grid with all walls (1) and borders
        self.maze_grid = [[1 for _ in range(self.dimension)] for _ in range(self.dimension)]

        # Start carving path from a random point (must be odd coordinates for algorithm)
        start_x, start_y = (random.randrange(self.dimension // 2) * 2 + 1,
                            random.randrange(self.dimension // 2) * 2 + 1)
        self._carve_path(start_x, start_y)

        # Create the mesh for the ground terrain
        self._create_mesh_from_grid()

    def _carve_path(self, cx, cy):
        """
        Recursive function to carve paths in the maze grid.
        cx, cy are current coordinates.
        """
        self.maze_grid[cy][cx] = 0 # Mark current cell as path

        # Randomly shuffle directions (dx, dy)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx, ny = cx + dx * 2, cy + dy * 2 # Next cell (2 steps away)
            if 0 < nx < self.dimension - 1 and 0 < ny < self.dimension - 1 and self.maze_grid[ny][nx] == 1:
                # If next cell is within bounds and is a wall, carve path to it
                self.maze_grid[cy + dy][cx + dx] = 0 # Carve path between current and next cell
                self._carve_path(nx, ny) # Recurse

    def _create_mesh_from_grid(self):
        """
        Generates a custom mesh for the ground based on the maze grid.
        Walls are raised, paths are flat.
        """
        vertices = []
        triangles = []
        colors = []
        uvs = [] # Not using textures, but good practice to include

        # Iterate over each cell in the maze grid
        for z_idx in range(self.dimension):
            for x_idx in range(self.dimension):
                is_wall = (self.maze_grid[z_idx][x_idx] == 1)
                height = self.wall_height if is_wall else self.path_height
                cell_color = game_config.COLOR_GROUND_WALL if is_wall else game_config.COLOR_GROUND_PATH

                # Calculate base position for the current cell
                # We offset by half the dimension to center the maze around (0,0)
                base_x = (x_idx - self.dimension / 2) * self.cell_size
                base_z = (z_idx - self.dimension / 2) * self.cell_size

                # Define vertices for the top face of the cell
                # Ensure order is consistent for normals
                v_bl = Vec3(base_x, height, base_z)
                v_br = Vec3(base_x + self.cell_size, height, base_z)
                v_tr = Vec3(base_x + self.cell_size, height, base_z + self.cell_size)
                v_tl = Vec3(base_x, height, base_z + self.cell_size)

                current_vert_start_idx = len(vertices)
                vertices.extend([v_bl, v_br, v_tr, v_tl])
                colors.extend([cell_color] * 4)
                uvs.extend([(0,0), (1,0), (1,1), (0,1)])

                # Triangles for top face (clockwise for front-facing normal)
                triangles.extend([current_vert_start_idx + 0, current_vert_start_idx + 1, current_vert_start_idx + 2, # BL, BR, TR
                                  current_vert_start_idx + 0, current_vert_start_idx + 2, current_vert_start_idx + 3]) # BL, TR, TL

                # Add side faces if this cell is a wall and adjacent to a path or edge of maze
                # These faces go from `height` down to `path_height`

                # North Face (towards positive Z)
                # Check if it's the top edge of the maze or if the cell above is a path
                if z_idx == self.dimension - 1 or (z_idx + 1 < self.dimension and self.maze_grid[z_idx+1][x_idx] == 0):
                    if is_wall: # Only draw wall sides if current cell is a wall
                        v_n_bl = Vec3(base_x, self.path_height, base_z + self.cell_size)
                        v_n_br = Vec3(base_x + self.cell_size, self.path_height, base_z + self.cell_size)
                        v_n_tr = v_tr
                        v_n_tl = v_tl
                        current_vert_start_idx = len(vertices)
                        vertices.extend([v_n_bl, v_n_br, v_n_tr, v_n_tl])
                        colors.extend([cell_color] * 4)
                        uvs.extend([(0,0), (1,0), (1,1), (0,1)])
                        triangles.extend([current_vert_start_idx + 0, current_vert_start_idx + 1, current_vert_start_idx + 2,
                                          current_vert_start_idx + 0, current_vert_start_idx + 2, current_vert_start_idx + 3])

                # South Face (towards negative Z)
                # Check if it's the bottom edge of the maze or if the cell below is a path
                if z_idx == 0 or (z_idx - 1 >= 0 and self.maze_grid[z_idx-1][x_idx] == 0):
                    if is_wall:
                        v_s_bl = Vec3(base_x, self.path_height, base_z)
                        v_s_br = Vec3(base_x + self.cell_size, self.path_height, base_z)
                        v_s_tr = v_br
                        v_s_tl = v_bl
                        current_vert_start_idx = len(vertices)
                        vertices.extend([v_s_br, v_s_bl, v_s_tl, v_s_tr]) # Order for correct normal
                        colors.extend([cell_color] * 4)
                        uvs.extend([(0,0), (1,0), (1,1), (0,1)])
                        triangles.extend([current_vert_start_idx + 0, current_vert_start_idx + 1, current_vert_start_idx + 2,
                                          current_vert_start_idx + 0, current_vert_start_idx + 2, current_vert_start_idx + 3])

                # East Face (towards positive X)
                # Check if it's the right edge of the maze or if the cell to the right is a path
                if x_idx == self.dimension - 1 or (x_idx + 1 < self.dimension and self.maze_grid[z_idx][x_idx+1] == 0):
                    if is_wall:
                        v_e_bl = Vec3(base_x + self.cell_size, self.path_height, base_z)
                        v_e_br = Vec3(base_x + self.cell_size, self.path_height, base_z + self.cell_size)
                        v_e_tr = v_tr
                        v_e_tl = v_br
                        current_vert_start_idx = len(vertices)
                        vertices.extend([v_e_bl, v_e_br, v_e_tr, v_e_tl])
                        colors.extend([cell_color] * 4)
                        uvs.extend([(0,0), (1,0), (1,1), (0,1)])
                        triangles.extend([current_vert_start_idx + 0, current_vert_start_idx + 1, current_vert_start_idx + 2,
                                          current_vert_start_idx + 0, current_vert_start_idx + 2, current_vert_start_idx + 3])

                # West Face (towards negative X)
                # Check if it's the left edge of the maze or if the cell to the left is a path
                if x_idx == 0 or (x_idx - 1 >= 0 and self.maze_grid[z_idx][x_idx-1] == 0):
                    if is_wall:
                        v_w_bl = Vec3(base_x, self.path_height, base_z)
                        v_w_br = Vec3(base_x, self.path_height, base_z + self.cell_size)
                        v_w_tr = v_tl
                        v_w_tl = v_bl
                        current_vert_start_idx = len(vertices)
                        vertices.extend([v_w_br, v_w_bl, v_w_tl, v_w_tr]) # Order for correct normal
                        colors.extend([cell_color] * 4)
                        uvs.extend([(0,0), (1,0), (1,1), (0,1)])
                        triangles.extend([current_vert_start_idx + 0, current_vert_start_idx + 1, current_vert_start_idx + 2,
                                          current_vert_start_idx + 0, current_vert_start_idx + 2, current_vert_start_idx + 3])

        # Create the Ursina mesh entity
        self.mesh_entity = Entity(
            model=Mesh(vertices=vertices, triangles=triangles, colors=colors, uvs=uvs, mode='triangle'),
            collider='mesh', # Use a mesh collider for accurate collision
            texture='white_cube', # A generic texture to see the shape
            position=(0,0,0), # Mesh is built with world positions already
            scale=1,
            name='maze_ground_mesh',
            # Add a basic light to see the mesh better (optional)
            # You might need a light entity in your scene for this to have effect
            # e.g., PointLight(position=(0,10,0), color=color.white)
        )
        self.mesh_entity.set_shader_input('light_color', color.white) # Example for a basic shader


    def clear_maze(self):
        """Destroys the existing maze mesh entity."""
        if self.mesh_entity:
            destroy(self.mesh_entity)
            self.mesh_entity = None
        self.maze_grid = [] # Clear grid data

    def get_world_position(self, grid_x, grid_z):
        """Converts grid coordinates to world coordinates, considering cell size and centering."""
        # Calculate X and Z based on maze dimension and cell size, centering around (0,0)
        world_x = (grid_x - self.dimension / 2 + 0.5) * self.cell_size
        world_z = (grid_z - self.dimension / 2 + 0.5) * self.cell_size
        # Y position is path height + player offset
        return Vec3(world_x, game_config.MAZE_PATH_HEIGHT + game_config.PLAYER_HEIGHT_OFFSET, world_z)

    def _is_valid_grid_pos(self, x, y):
        """Checks if grid coordinates are within maze bounds and are a path."""
        return 0 <= x < self.dimension and \
               0 <= y < self.dimension and \
               self.maze_grid[y][x] == 0

    def find_spawn_point(self):
        """Finds a valid spawn point (path) near the beginning of the maze."""
        for z_idx in range(1, self.dimension - 1):
            for x_idx in range(1, self.dimension - 1):
                if self._is_valid_grid_pos(x_idx, z_idx):
                    return (x_idx, z_idx)
        return (1, 1) # Fallback if no valid path found (shouldn't happen with proper generation)

    def find_goal_point(self):
        """Finds a valid goal point (path) near the end of the maze."""
        for z_idx in range(self.dimension - 2, 0, -1):
            for x_idx in range(self.dimension - 2, 0, -1):
                if self._is_valid_grid_pos(x_idx, z_idx):
                    return (x_idx, z_idx)
        return (self.dimension - 2, self.dimension - 2) # Fallback

    def find_monster_spawn_point(self):
        """Finds a valid spawn point for the monster, typically not near player/goal."""
        attempts = 0
        while attempts < 100:
            x = random.randint(1, self.dimension - 2)
            y = random.randint(1, self.dimension - 2)
            if self._is_valid_grid_pos(x, y):
                # Basic check to prevent spawning monster too close to player/goal initially
                player_pos_grid = self.find_spawn_point() # Assuming these are consistent
                goal_pos_grid = self.find_goal_point()

                dist_to_player = abs(x - player_pos_grid[0]) + abs(y - player_pos_grid[1])
                dist_to_goal = abs(x - goal_pos_grid[0]) + abs(y - goal_pos_grid[1])

                if dist_to_player > self.dimension / 4 and dist_to_goal > self.dimension / 4:
                    return (x, y)
            attempts += 1
        return (self.dimension // 2, self.dimension // 2) # Fallback to center


# --- UI Management ---
class UIManager:
    """Manages the visibility and text of all UI elements."""
    def __init__(self):
        self.ui_elements = [] # Store all UI elements for easy management

        # Menu UI
        # Scale background to cover the whole screen based on camera's aspect ratio
        self.menu_bg = Entity(model='quad', scale_x=camera.aspect_ratio * 2, scale_y=2,
                              color=color.black, z=1, parent=camera.ui)
        self.title_text = Text("CUBE MAZE ADVENTURE PRO", origin=(0,0), scale=0.1, y=0.3,
                               color=game_config.COLOR_UI_TITLE, parent=camera.ui)
        self.start_button = Button(text='Start Game', scale=(0.2,0.1), y=0.1, parent=camera.ui)
        self.exit_button = Button(text='Exit', scale=(0.2,0.1), y=-0.05, parent=camera.ui)
        self.ui_elements.extend([self.menu_bg, self.title_text, self.start_button, self.exit_button])

        # Game Over UI
        self.win_text = Text('', origin=(0,0), scale=0.1, color=game_config.COLOR_UI_WIN, y=0.15, enabled=False, parent=camera.ui)
        self.lose_text = Text('', origin=(0,0), scale=0.1, color=game_config.COLOR_UI_LOSE, y=0.15, enabled=False, parent=camera.ui)
        self.restart_button = Button(text='Restart', scale=(0.2,0.1), y=-0.05, enabled=False, parent=camera.ui)
        self.back_to_menu_button = Button(text='Main Menu', scale=(0.2,0.1), y=-0.2, enabled=False, parent=camera.ui)
        self.ui_elements.extend([self.win_text, self.lose_text, self.restart_button, self.back_to_menu_button])

        # Pause Menu UI
        self.pause_bg = Entity(model='quad', scale_x=camera.aspect_ratio * 2, scale_y=2,
                               color=color.black50, z=1, parent=camera.ui, enabled=False)
        self.pause_text = Text("PAUSED", origin=(0,0), scale=0.1, y=0.2,
                               color=color.white, parent=camera.ui, enabled=False)
        self.resume_button = Button(text='Resume Game', scale=(0.2,0.1), y=0.05, parent=camera.ui, enabled=False)
        self.pause_to_menu_button = Button(text='Main Menu', scale=(0.2,0.1), y=-0.1, parent=camera.ui, enabled=False)
        self.ui_elements.extend([self.pause_bg, self.pause_text, self.resume_button, self.pause_to_menu_button])

        # In-game UI (Health Bar)
        self.health_bar_bg = Entity(model='quad', parent=camera.ui, x=-0.5, y=0.4, scale_x=0.4, scale_y=0.05,
                                    color=game_config.COLOR_UI_HEALTH_BG, enabled=False, origin_x=-0.5)
        self.health_bar_fill = Entity(model='quad', parent=self.health_bar_bg, x=0, y=0, scale_x=1, scale_y=1,
                                      color=game_config.COLOR_UI_HEALTH, origin_x=-0.5)
        self.health_text = Text('HP: 3/3', parent=self.health_bar_bg, x=0.05, y=0, scale=0.07, color=color.white, origin_x=-0.5)
        self.ui_elements.extend([self.health_bar_bg, self.health_bar_fill, self.health_text])


    def _set_ui_group_enabled(self, group_elements, state):
        """Helper to enable/disable a list of UI elements."""
        for element in group_elements:
            element.enabled = state

    def show_menu(self):
        """Displays the main menu UI."""
        self._set_ui_group_enabled(self.ui_elements, False) # Hide all first
        self._set_ui_group_enabled([self.menu_bg, self.title_text, self.start_button, self.exit_button], True)

    def show_game_over_screen(self, is_win):
        """Displays the win or lose screen UI."""
        self._set_ui_group_enabled(self.ui_elements, False) # Hide all first
        if is_win:
            self.win_text.text = '🎉 You Win!'
            self.win_text.enabled = True
        else:
            self.lose_text.text = '💀 You were caught by the monster!'
            self.lose_text.enabled = True
        self._set_ui_group_enabled([self.restart_button, self.back_to_menu_button], True)

    def show_pause_menu(self):
        """Displays the pause menu UI."""
        self._set_ui_group_enabled(self.ui_elements, False) # Hide all first
        self._set_ui_group_enabled([self.pause_bg, self.pause_text, self.resume_button, self.pause_to_menu_button], True)

    def show_game_hud(self):
        """Displays the in-game HUD."""
        self.health_bar_bg.enabled = True
        self.health_bar_fill.enabled = True
        self.health_text.enabled = True

    def hide_all_ui(self):
        """Hides all UI elements."""
        self._set_ui_group_enabled(self.ui_elements, False)

    def update_health_display(self, current_health):
        """Updates the player's health bar and text."""
        self.health_bar_fill.scale_x = current_health / game_config.PLAYER_MAX_HEALTH
        self.health_text.text = f'HP: {current_health}/{game_config.PLAYER_MAX_HEALTH}'


# --- Main Game Class ---

class Game:
    """The main game orchestrator, managing states, entities, and UI."""
    def __init__(self):
        self.current_state = GameState.MENU
        self.player = None
        self.goal = None
        self.monster = None
        self.maze_generator = TerrainMazeGenerator(
            game_config.MAZE_DIMENSION,
            game_config.CELL_SIZE,
            game_config.MAZE_WALL_HEIGHT,
            game_config.MAZE_PATH_HEIGHT
        )
        self.ui_manager = UIManager()
        self.game_entities = [] # List to manage all game-specific entities (player, goal, monster)

        self._setup_global_input()
        self._setup_ui_callbacks()
        self._initialize_environment_elements() # Setup ground/skybox etc.

        self.set_game_state(GameState.MENU) # Start in menu state

    def _setup_global_input(self):
        """Sets up the global input handler for the Ursina application."""
        # Ursina automatically calls an 'input' function if defined in the main script.
        # We wrap it to add our custom game state logic.
        self._original_app_input = app.input # Store original input function
        app.input = self._handle_global_input # Override with our custom handler

    def _handle_global_input(self, key):
        """Processes global input (like Escape for pause/quit)."""
        # First, allow Ursina's default input system to process for entities
        # (e.g., FirstPersonController's movement)
        if self._original_app_input:
            self._original_app_input(key)

        if key == 'escape':
            if self.current_state == GameState.PLAYING:
                self.set_game_state(GameState.PAUSED)
            elif self.current_state == GameState.PAUSED:
                self.set_game_state(GameState.PLAYING)
            elif self.current_state in [GameState.WIN, GameState.LOSE]:
                # If on win/lose screen, escape goes back to main menu
                self.set_game_state(GameState.MENU)
            elif self.current_state == GameState.MENU:
                application.quit() # Exit application from main menu

    def _setup_ui_callbacks(self):
        """Assigns game functions to UI button click events."""
        self.ui_manager.start_button.on_click = self.start_game
        self.ui_manager.exit_button.on_click = application.quit
        self.ui_manager.restart_button.on_click = self.restart_game
        self.ui_manager.back_to_menu_button.on_click = self.go_to_main_menu
        self.ui_manager.resume_button.on_click = lambda: self.set_game_state(GameState.PLAYING)
        self.ui_manager.pause_to_menu_button.on_click = self.go_to_main_menu

    def _initialize_environment_elements(self):
        """Sets up persistent elements of the scene that are not part of the maze."""
        # This ground plane will act as the 'outside' of the maze.
        self.outside_ground = Entity(
            model='plane',
            scale=game_config.GROUND_SCALE,
            color=game_config.COLOR_OUTSIDE_MAZE,
            texture='white_cube',
            texture_scale=(game_config.GROUND_SCALE, game_config.GROUND_SCALE),
            collider='box',
            name='outside_ground_plane',
            y=game_config.MAZE_PATH_HEIGHT - 0.01 # Slightly below maze paths
        )
        # Adding a simple light source
        DirectionalLight(direction=(1, -1, 1), color=color.white)
        AmbientLight(color=color.rgba(100, 100, 100, 10)) # Soft ambient light
        Sky() # Adds a simple skybox


    def set_game_state(self, new_state):
        """Transitions the game to a new state and updates UI and entity visibility."""
        if self.current_state == new_state:
            return # No state change

        print(f"Game State Transition: {self.current_state} -> {new_state}")
        self.current_state = new_state

        # Handle UI visibility based on new state
        self.ui_manager.hide_all_ui() # Hide all UI first
        if new_state == GameState.MENU:
            self.ui_manager.show_menu()
            self._deactivate_gameplay_entities()
            self._set_menu_camera()
            self._unload_game_entities() # Clean up previous game's entities and maze
        elif new_state == GameState.PLAYING:
            self.ui_manager.hide_all_ui()
            self.ui_manager.show_game_hud()
            self._activate_gameplay_entities()
            # Player class handles camera parenting on enable
        elif new_state == GameState.PAUSED:
            self.ui_manager.show_pause_menu()
            # Deactivate monster, but keep player (and camera) active for pause screen
            self._deactivate_gameplay_entities(exclude_player=True)
            self._set_menu_camera(maintain_player_pos=True) # Keep camera at player's location
        elif new_state in [GameState.WIN, GameState.LOSE]:
            self.ui_manager.show_game_over_screen(new_state == GameState.WIN)
            self._deactivate_gameplay_entities() # Freeze game
            self._set_game_over_camera()


    def start_game(self):
        """Initializes/resets game entities and sets state to PLAYING."""
        # Generate a new maze each time the game starts
        self.maze_generator.generate_random_maze()

        # Determine spawn points based on the new maze
        player_grid_pos = self.maze_generator.find_spawn_point()
        goal_grid_pos = self.maze_generator.find_goal_point()
        monster_grid_pos = self.maze_generator.find_monster_spawn_point()

        # Convert grid positions to world positions
        player_world_pos = self.maze_generator.get_world_position(*player_grid_pos)
        goal_world_pos = self.maze_generator.get_world_position(*goal_grid_pos)
        monster_world_pos = self.maze_generator.get_world_position(*monster_grid_pos)

        # Create or reset entities
        if self.player is None:
            self.player = Player(position=player_world_pos)
            self.game_entities.append(self.player)
        else:
            self.player.start_position = player_world_pos # Update start position for new maze
            self.player.reset_state() # Resets position, health, and enables

        if self.goal is None:
            self.goal = Goal(position=goal_world_pos)
            self.game_entities.append(self.goal)
        else:
            self.goal.position = goal_world_pos # Update position for new maze
            self.goal.reset_state() # Resets state (e.g., visibility)

        if self.monster is None:
            self.monster = Monster(position=monster_world_pos)
            self.game_entities.append(self.monster)
        else:
            self.monster.start_position = monster_world_pos # Update start position for new maze
            self.monster.reset_state() # Resets position and enables

        self.set_game_state(GameState.PLAYING)

    def restart_game(self):
        """Restarts the current game by regenerating maze and resetting entities."""
        self.start_game() # Calling start_game handles all setup for a new game

    def go_to_main_menu(self):
        """Transitions from game over/pause to the main menu."""
        self.set_game_state(GameState.MENU)

    def _unload_game_entities(self):
        """Destroys all dynamic game entities (player, monster, goal) and the maze mesh."""
        for entity in self.game_entities:
            if entity: # Check if entity exists before destroying
                destroy(entity)
        self.game_entities.clear() # Clear the list after destroying
        self.player = None # Clear references to destroyed entities
        self.goal = None
        self.monster = None
        self.maze_generator.clear_maze() # Clear the maze mesh

        # Also destroy any active projectiles if they exist
        for p in [e for e in scene.entities if isinstance(e, MonsterProjectile)]:
            destroy(p)


    def _activate_gameplay_entities(self):
        """Enables visibility and updates for game entities relevant during PLAYING state."""
        # Player.on_enable handles camera parenting and mouse lock
        for entity in self.game_entities:
            if entity:
                entity.enabled = True
        if self.maze_generator.mesh_entity:
            self.maze_generator.mesh_entity.enabled = True

    def _deactivate_gameplay_entities(self, exclude_player=False):
        """
        Disables visibility and updates for game entities.
        If exclude_player is True, player remains active (e.g., for pause menu).
        """
        for entity in self.game_entities:
            if entity == self.player and exclude_player:
                continue # Skip player if excluded
            if entity:
                entity.enabled = False # This disables their update method and visibility

        if self.maze_generator.mesh_entity:
            # Maze mesh might not need to be disabled if it's part of the background,
            # but if it has physics/interactions, disabling it might be desired.
            # For this context, keeping it enabled is fine as it's static.
            pass

        # Destroy any active projectiles immediately when game stops
        for p in [e for e in scene.entities if isinstance(e, MonsterProjectile)]:
            destroy(p)

    def _set_menu_camera(self, maintain_player_pos=False):
        """
        Sets the camera position and rotation for the main menu or pause screen.
        If maintain_player_pos is True, camera stays near player but detaches.
        """
        camera.parent = None
        if maintain_player_pos and self.player:
            # Position camera slightly above and behind player for pause view
            camera.position = self.player.position + Vec3(0, 5, -10)
            camera.look_at(self.player.position) # Look at player
            # Adjust rotation if needed for a better static view
            camera.rotation_x += 10 # Tilt down slightly
        else:
            camera.position = game_config.MENU_CAMERA_POS
            camera.rotation = game_config.MENU_CAMERA_ROT
        mouse.locked = False # Ensure mouse is free in menus

    def _set_game_over_camera(self):
        """Sets the camera position and rotation for the game over screen."""
        camera.parent = None
        camera.position = game_config.GAME_OVER_CAMERA_POS
        camera.rotation = game_config.GAME_OVER_CAMERA_ROT
        mouse.locked = False # Ensure mouse is free

    def update(self):
        """Main game loop update function."""
        # Global game logic that doesn't belong to a specific entity
        pass


# --- Application Setup ---
if __name__ == '__main__':
    app = Ursina()

    # Global game configuration instance
    game_config = GameConfig()

    # Create the main game instance
    game = Game()

    # Apply window settings from config
    window.title = game_config.WINDOW_TITLE
    window.borderless = game_config.WINDOW_BORDERLESS
    window.fullscreen = game_config.WINDOW_FULLSCREEN
    window.exit_button.visible = False # Managed by our input handler
    window.fps_counter.enabled = game_config.WINDOW_FPS_COUNTER

    # Run the Ursina application
    app.run()