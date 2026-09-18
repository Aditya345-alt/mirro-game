import json
import pygame
from constants import TILE_SIZE, COLOR_TILE, COLOR_SPIKE, WORLD_THEMES

# Tile type constants for the level grid
TILE_EMPTY = 0
TILE_FLOOR = 1
TILE_SPIKE = 2
TILE_FALLING = 3
TILE_DISAPPEARING = 4

class Level:
    def __init__(self, layout, name="Meadow Run", entities=None, theme="meadow"):
        self.layout = layout
        self.name = name
        self.theme = theme
        self.entities = entities or {}
        self.colliders = []
        self.hazards = []
        self.dynamic_tiles = []
        self.dynamic_timers = {}
        self.inactive_tiles = set()
        self._build_level()

    @classmethod
    def load_from_json(cls, path):
        # Load a level definition from a JSON file containing a 2D tile array.
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return cls(data["layout"], data.get("name", "Meadow Run"), data.get("entities"), data.get("theme", "meadow"))

    @classmethod
    def world_one(cls, index):
        width = 105 + index * 14
        layout = [[0 for _ in range(width)] for _ in range(21)]
        for x in range(width):
            layout[19][x] = 1
            layout[20][x] = 1
        platforms = [(8, 15, 6), (19, 12, 5), (29, 16, 7), (41, 11, 6), (54, 14, 7), (68, 10, 6), (80, 15, 8)]
        if index == 1:
            platforms += [(92, 12, 5), (103, 8, 6)]
        if index == 2:
            platforms += [(92, 11, 5), (104, 7, 5), (116, 13, 6)]
        for start, row, length in platforms:
            for x in range(start, min(width, start + length)):
                layout[row][x] = 1
        for x in range(24 + index * 10, width - 9, 23):
            layout[18][x] = 2
        entities = {
            "enemies": [{"x": x * TILE_SIZE, "y": row * TILE_SIZE - 24, "kind": kind}
                        for x, row, kind in [(14, 18, "walker"), (34, 18, "walker"), (58, 18, "flyer"), (75, 18, "charger")]
                        if x < width - 5],
            "coins": [(x * TILE_SIZE + 8, (18 if x % 3 else 13) * TILE_SIZE) for x in range(6, width - 5, 7)],
            "gems": [(22 * TILE_SIZE, 10 * TILE_SIZE), ((width - 18) * TILE_SIZE, 9 * TILE_SIZE), ((width - 7) * TILE_SIZE, 17 * TILE_SIZE)],
            "checkpoints": [(width // 2 * TILE_SIZE, 18 * TILE_SIZE)],
            "goal": (width * TILE_SIZE - 80, 17 * TILE_SIZE),
        }
        return cls(layout, f"Meadow Run {index + 1}", entities, "meadow")

    @classmethod
    def campaign(cls, world, index):
        """Build one compact, replayable stage for each world and level number."""
        theme = WORLD_THEMES[world]
        width = 112 + index * 12 + world * 3
        height = 21
        layout = [[TILE_EMPTY for _ in range(width)] for _ in range(height)]
        for x in range(width):
            layout[19][x] = TILE_FLOOR
            layout[20][x] = TILE_FLOOR
        platforms = [(7, 15, 6), (18, 12, 6), (31, 16, 7), (45, 11, 7), (60, 14, 7), (75, 10, 7), (91, 14, 8)]
        # Add more platforms in later levels for more challenging platforming
        if index > 0:
            platforms += [(40, 9, 5), (70, 13, 6)]
        if index > 1:
            platforms += [(50, 14, 4), (85, 11, 5)]
        if world > 2 and index > 1:
            platforms += [(25, 17, 3), (65, 8, 4)]
        for start, row, length in platforms:
            for x in range(start, min(width, start + length)):
                layout[row][x] = TILE_FLOOR
        hazard_kind = TILE_SPIKE if world != 2 else TILE_DISAPPEARING
        for x in range(24 + index * 5, width - 10, 19):
            layout[18][x] = hazard_kind
        entities = {
            "enemies": [], "coins": [], "gems": [], "specials": [], "powerups": [],
            "checkpoints": [(width // 2 * TILE_SIZE, 18 * TILE_SIZE)],
            "goal": (width * TILE_SIZE - 80, 17 * TILE_SIZE),
            "boss": world == 4 and index == 2,
        }
        kinds = ["walker", "flyer", "charger", "thrower", "ambusher", "armored", "phantom"]
        difficulty = world + index  # Scale difficulty with world and stage
        # Add more enemies in later levels
        enemy_count = 4 + world + index
        for number in range(enemy_count):
            x = 14 + number * 19 + number * 4
            if x < width - 15:
                kind = kinds[(world + index + number) % len(kinds)]
                entities["enemies"].append({"x": x * TILE_SIZE, "y": 18 * TILE_SIZE - 26, "kind": kind, "difficulty": difficulty})
        for number, x in enumerate(range(6, width - 6, 7)):
            entities["coins"].append((x * TILE_SIZE + 8, (17 if number % 3 else 13) * TILE_SIZE))
        entities["gems"] = [(22 * TILE_SIZE, 10 * TILE_SIZE), ((width // 2 + 5) * TILE_SIZE, 9 * TILE_SIZE), ((width - 12) * TILE_SIZE, 12 * TILE_SIZE)]
        entities["specials"] = [(28 * TILE_SIZE, 14 * TILE_SIZE, "relic"), (width // 2 * TILE_SIZE, 8 * TILE_SIZE, "relic"), ((width - 18) * TILE_SIZE, 13 * TILE_SIZE, "relic")]
        power_types = ["shield", "speed", "double_jump", "projectile", "invincibility"]
        entities["powerups"] = [(38 * TILE_SIZE, 10 * TILE_SIZE, power_types[world % 5]), ((width - 28) * TILE_SIZE, 13 * TILE_SIZE, power_types[(world + index + 1) % 5])]
        if entities["boss"]:
            entities["boss_data"] = {"x": (width - 15) * TILE_SIZE, "y": 12 * TILE_SIZE, "kind": "armored"}
        return cls(layout, f"{theme['name']} {index + 1}", entities, theme["short"].lower())

    def _build_level(self):
        # Create collider and hazard rectangles from the layout grid.
        self.colliders.clear()
        self.hazards.clear()
        self.dynamic_tiles.clear()
        self.dynamic_timers.clear()
        self.inactive_tiles.clear()

        for row_index, row in enumerate(self.layout):
            for col_index, tile_value in enumerate(row):
                tile_rect = pygame.Rect(
                    col_index * TILE_SIZE,
                    row_index * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                if tile_value == TILE_FLOOR:
                    self.colliders.append(tile_rect)
                elif tile_value == TILE_SPIKE:
                    self.hazards.append(tile_rect)
                elif tile_value in (TILE_FALLING, TILE_DISAPPEARING):
                    self.dynamic_tiles.append(tile_rect)
                    self.colliders.append(tile_rect)
                    self.dynamic_timers[(tile_rect.x, tile_rect.y)] = 0

    def update_dynamic(self, player):
        for tile in self.dynamic_tiles:
            key = (tile.x, tile.y)
            if key in self.inactive_tiles:
                continue
            if player.bottom <= tile.top + 12 and player.colliderect(tile):
                self.dynamic_timers[key] += 1
                limit = 28 if self.layout[tile.y // TILE_SIZE][tile.x // TILE_SIZE] == TILE_FALLING else 42
                if self.dynamic_timers[key] >= limit:
                    self.inactive_tiles.add(key)
                    self.colliders = [item for item in self.colliders if item is not tile]

    @property
    def pixel_width(self):
        return len(self.layout[0]) * TILE_SIZE

    @property
    def pixel_height(self):
        return len(self.layout) * TILE_SIZE

    def draw(self, surface, camera_x=0):
        # Draw each tile with a camera offset for side-scrolling.
        for tile in self.colliders:
            draw_rect = tile.copy()
            draw_rect.x -= camera_x
            tile_color = (113, 70, 39) if self.theme == "forest" else COLOR_TILE
            if self.theme == "forest":
                pygame.draw.rect(surface, (38, 71, 48), (draw_rect.x + 4, draw_rect.y + 7, draw_rect.width, draw_rect.height), border_radius=3)
                pygame.draw.rect(surface, tile_color, draw_rect, border_radius=3)
                pygame.draw.polygon(surface, (146, 82, 43), ((draw_rect.left, draw_rect.top + 7), (draw_rect.right, draw_rect.top + 7), (draw_rect.right - 5, draw_rect.bottom), (draw_rect.left + 5, draw_rect.bottom)))
                pygame.draw.rect(surface, (126, 218, 72), (draw_rect.x, draw_rect.y, draw_rect.width, 8), border_radius=4)
                pygame.draw.line(surface, (202, 239, 105), (draw_rect.left + 4, draw_rect.top + 2), (draw_rect.right - 5, draw_rect.top + 2), 2)
                pygame.draw.line(surface, (74, 127, 46), (draw_rect.left + 4, draw_rect.bottom - 5), (draw_rect.right - 4, draw_rect.bottom - 5), 2)
            else:
                pygame.draw.rect(surface, tile_color, draw_rect)

        for hazard in self.hazards:
            draw_rect = hazard.copy()
            draw_rect.x -= camera_x
            pygame.draw.rect(surface, COLOR_SPIKE, draw_rect)
        for tile in self.dynamic_tiles:
            if (tile.x, tile.y) in self.inactive_tiles:
                continue
            draw_rect = tile.copy()
            draw_rect.x -= camera_x
            pygame.draw.rect(surface, (126, 179, 193), draw_rect)
