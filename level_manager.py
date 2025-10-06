"""Level management, loading, and collision detection."""
import pygame

class LevelManager:
    def __init__(self):
        self.levels = {}
        self.current_level = 0
        self.platforms = []
        self.enemies = []
        self.goal = None
        self.load_levels()
    
    def load_levels(self):
        """Define the three levels of the game."""
        # Level 1: Basic platforms
        self.levels[1] = {
            'platforms': [
                {'x': 0, 'y': 500, 'width': 300, 'height': 20, 'color': (0, 200, 0)},
                {'x': 400, 'y': 500, 'width': 400, 'height': 20, 'color': (0, 200, 0)},
                {'x': 200, 'y': 400, 'width': 200, 'height': 20, 'color': (0, 200, 0)},
                {'x': 500, 'y': 300, 'width': 200, 'height': 20, 'color': (0, 200, 0)},
                {'x': 100, 'y': 200, 'width': 200, 'height': 20, 'color': (0, 200, 0)}
            ],
            'enemies': [],
            'goal': {'x': 150, 'y': 150, 'width': 50, 'height': 50, 'color': (255, 215, 0)},
            'start_pos': (100, 50),
            'background': (135, 206, 235)  # Sky blue
        }
        
        # Level 2: Water level with floating platforms
        self.levels[2] = {
            'platforms': [
                # Ground
                {'x': 0, 'y': 550, 'width': 800, 'height': 50, 'color': (139, 69, 19)},
                # Floating platforms
                {'x': 100, 'y': 450, 'width': 100, 'height': 20, 'color': (0, 200, 0)},
                {'x': 300, 'y': 400, 'width': 100, 'height': 20, 'color': (0, 200, 0)},
                {'x': 500, 'y': 350, 'width': 100, 'height': 20, 'color': (0, 200, 0)},
                # Water surface
                {'x': 0, 'y': 500, 'width': 800, 'height': 50, 'color': (64, 164, 223), 'type': 'water'},
                # Exit platform
                {'x': 650, 'y': 300, 'width': 100, 'height': 20, 'color': (200, 0, 0)}
            ],
            'enemies': [
                {'x': 200, 'y': 430, 'width': 30, 'height': 20, 'color': (255, 0, 0), 'patrol': [150, 250]}
            ],
            'goal': {'x': 675, 'y': 250, 'width': 50, 'height': 50, 'color': (255, 215, 0)},
            'start_pos': (150, 400),
            'background': (100, 149, 237)  # Cornflower blue
        }
        
        # Level 3: More complex with moving platforms and enemies
        self.levels[3] = {
            'platforms': [
                # Ground with gaps
                {'x': 0, 'y': 550, 'width': 200, 'height': 50, 'color': (139, 69, 19)},
                {'x': 300, 'y': 550, 'width': 200, 'height': 50, 'color': (139, 69, 19)},
                {'x': 600, 'y': 550, 'width': 200, 'height': 50, 'color': (139, 69, 19)},
                # Platforms
                {'x': 100, 'y': 450, 'width': 100, 'height': 20, 'color': (0, 200, 0)},
                {'x': 300, 'y': 400, 'width': 100, 'height': 20, 'color': (0, 200, 0)},
                {'x': 500, 'y': 350, 'width': 100, 'height': 20, 'color': (0, 200, 0)},
                # Moving platform
                {'x': 200, 'y': 300, 'width': 100, 'height': 20, 'color': (0, 200, 0), 'type': 'moving', 'start_x': 200, 'end_x': 400, 'speed': 1},
                # Exit platform
                {'x': 650, 'y': 200, 'width': 100, 'height': 20, 'color': (200, 0, 0)}
            ],
            'enemies': [
                {'x': 400, 'y': 530, 'width': 30, 'height': 20, 'color': (255, 0, 0), 'patrol': [350, 450]},
                {'x': 600, 'y': 400, 'width': 30, 'height': 20, 'color': (255, 0, 0), 'patrol': [550, 650]}
            ],
            'goal': {'x': 675, 'y': 150, 'width': 50, 'height': 50, 'color': (255, 215, 0)},
            'start_pos': (100, 400),
            'background': (47, 79, 79)  # Dark slate gray
        }
    
    def load_level(self, level_num):
        """Load a specific level."""
        if level_num in self.levels:
            self.current_level = level_num
            level_data = self.levels[level_num]
            self.platforms = level_data['platforms']
            self.enemies = level_data['enemies']
            self.goal = level_data['goal']
            return level_data['start_pos']
        return None
    
    def update(self, player):
        """Update level elements like moving platforms and enemies."""
        # Update moving platforms
        for platform in self.platforms:
            if platform.get('type') == 'moving':
                platform['x'] += platform.get('speed', 1)
                if platform['x'] > platform.get('end_x', platform['x'] + 100):
                    platform['x'] = platform['end_x']
                    platform['speed'] *= -1
                elif platform['x'] < platform.get('start_x', platform['x'] - 100):
                    platform['x'] = platform['start_x']
                    platform['speed'] *= -1
        
        # Update enemies
        for enemy in self.enemies:
            if 'patrol' in enemy:
                enemy['x'] += enemy.get('speed', 1)
                if enemy['x'] > enemy['patrol'][1]:
                    enemy['x'] = enemy['patrol'][1]
                    enemy['speed'] = -1
                elif enemy['x'] < enemy['patrol'][0]:
                    enemy['x'] = enemy['patrol'][0]
                    enemy['speed'] = 1
        
        # Check for goal collision
        if self.check_goal_collision(player):
            return 'level_complete'
            
        # Check for enemy collision
        if self.check_enemy_collision(player):
            return 'player_dead'
            
        return None
    
    def check_goal_collision(self, player):
        """Check if player has reached the goal."""
        if not self.goal:
            return False
            
        # Simple circle-rectangle collision
        dx = abs(player.x - (self.goal['x'] + self.goal['width']/2))
        dy = abs(player.y - (self.goal['y'] + self.goal['height']/2))
        
        if (dx > (self.goal['width']/2 + player.customization['size'])):
            return False
        if (dy > (self.goal['height']/2 + player.customization['size'])):
            return False
            
        if (dx <= (self.goal['width']/2)) or (dy <= (self.goal['height']/2)):
            return True
            
        corner_dist = (dx - self.goal['width']/2)**2 + (dy - self.goal['height']/2)**2
        return corner_dist <= (player.customization['size'] ** 2)
    
    def check_enemy_collision(self, player):
        """Check if player has collided with an enemy."""
        for enemy in self.enemies:
            # Simple circle-rectangle collision
            dx = abs(player.x - (enemy['x'] + enemy['width']/2))
            dy = abs(player.y - (enemy['y'] + enemy['height']/2))
            
            if (dx > (enemy['width']/2 + player.customization['size'])):
                continue
            if (dy > (enemy['height']/2 + player.customization['size'])):
                continue
                
            if (dx <= (enemy['width']/2)) or (dy <= (enemy['height']/2)):
                return True
                
            corner_dist = (dx - enemy['width']/2)**2 + (dy - enemy['height']/2)**2
            if corner_dist <= (player.customization['size'] ** 2):
                return True
                
        return False
    
    def get_water_platforms(self):
        """Get all water platforms for water physics."""
        return [p for p in self.platforms if p.get('type') == 'water']
    
    def render(self, screen):
        """Render the current level."""
        if self.current_level in self.levels:
            # Draw background
            screen.fill(self.levels[self.current_level]['background'])
            
            # Draw platforms
            for platform in self.platforms:
                pygame.draw.rect(screen, platform['color'], 
                               (platform['x'], platform['y'], 
                                platform['width'], platform['height']))
            
            # Draw goal
            if self.goal:
                pygame.draw.rect(screen, self.goal['color'],
                               (self.goal['x'], self.goal['y'],
                                self.goal['width'], self.goal['height']))
            
            # Draw enemies
            for enemy in self.enemies:
                pygame.draw.rect(screen, enemy['color'],
                               (enemy['x'], enemy['y'],
                                enemy['width'], enemy['height']))
