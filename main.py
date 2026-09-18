import math
import random
import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE, WORLD_THEMES
from enemy import Enemy
from level import Level
from player import Player
from progression import Progress
from audio import Audio

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Lumenwild: The Five Frontiers")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 27)
big_font = pygame.font.Font(None, 72)

def label(surface, value, position, color=(244, 244, 228), large=False):
    surface.blit((big_font if large else font).render(value, True, color), position)


def draw_button(surface, rect, text, color=(255, 189, 89), selected=False):
    border = (255, 214, 120) if selected else (116, 140, 167)
    pygame.draw.rect(surface, (29, 42, 58), rect, border_radius=16)
    pygame.draw.rect(surface, color, rect.inflate(-8, -8), border_radius=12)
    pygame.draw.rect(surface, border, rect, 3, border_radius=16)
    label(surface, text, (rect.centerx - font.size(text)[0] // 2, rect.centery - 12), (20, 27, 39), False)


class HazardProjectile(pygame.Rect):
    def __init__(self, x, y, velocity):
        super().__init__(x, y, 12, 8)
        self.velocity = velocity


def stage_data(world, stage, abilities):
    level = Level.campaign(world, stage)
    player = Player(96, 19 * TILE_SIZE - 48, abilities | ({"dash"} if world else set()))
    difficulty = world + stage  # Calculate difficulty for enemy scaling
    enemies = [Enemy(item["x"], item["y"], kind=item["kind"], difficulty=item.get("difficulty", difficulty)) for item in level.entities["enemies"]]
    boss = None
    if level.entities.get("boss"):
        data = level.entities["boss_data"]
        boss_difficulty = world + 1  # Boss gets harder with world progression
        boss = Enemy(data["x"], data["y"], 1, 0, "armored", difficulty=boss_difficulty)
        boss.width, boss.height = 70, 70
        boss.health = 12 + world * 3  # More health in harder worlds
    return level, player, enemies, boss

def draw_collectible(surface, item, camera, color, gem=False):
    x, y = item[:2]
    point = (int(x - camera), int(y + math.sin(pygame.time.get_ticks() / 180 + x) * 4))
    if gem:
        pygame.draw.polygon(surface, color, ((point[0], point[1] - 12), (point[0] + 10, point[1]), (point[0], point[1] + 12), (point[0] - 10, point[1])))
    else:
        pygame.draw.circle(surface, color, point, 8)
        pygame.draw.circle(surface, (255, 244, 154), point, 4)


def draw_cloud_sprite(surface, x, y, size, style, color):
    """Draw a pixelated cloud sprite with layered details."""
    dark_color = (tuple(max(0, c - 30) for c in color))
    
    if style == 0:  # Small compact cloud
        pygame.draw.circle(surface, color, (x - 2, y - 2), int(size * 0.4))
        pygame.draw.circle(surface, color, (x + 4, y), int(size * 0.35))
        pygame.draw.circle(surface, dark_color, (x - 3, y + 3), int(size * 0.2))
    
    elif style == 1:  # Large fluffy cloud
        pygame.draw.circle(surface, color, (x - 8, y), int(size * 0.5))
        pygame.draw.circle(surface, color, (x, y - 4), int(size * 0.55))
        pygame.draw.circle(surface, color, (x + 8, y), int(size * 0.5))
        pygame.draw.circle(surface, color, (x - 4, y + 4), int(size * 0.3))
        pygame.draw.circle(surface, color, (x + 4, y + 4), int(size * 0.3))
        pygame.draw.circle(surface, dark_color, (x - 6, y + 6), int(size * 0.2))
        pygame.draw.circle(surface, dark_color, (x + 6, y + 6), int(size * 0.2))
    
    elif style == 2:  # Wide cloud
        pygame.draw.circle(surface, color, (x - 10, y - 2), int(size * 0.45))
        pygame.draw.circle(surface, color, (x, y - 5), int(size * 0.5))
        pygame.draw.circle(surface, color, (x + 10, y - 2), int(size * 0.45))
        pygame.draw.circle(surface, color, (x + 5, y + 3), int(size * 0.3))
        pygame.draw.circle(surface, dark_color, (x - 8, y + 5), int(size * 0.2))
        pygame.draw.circle(surface, dark_color, (x + 8, y + 5), int(size * 0.2))
    
    elif style == 3:  # Tall cloud
        pygame.draw.circle(surface, color, (x, y - 8), int(size * 0.4))
        pygame.draw.circle(surface, color, (x - 6, y - 2), int(size * 0.5))
        pygame.draw.circle(surface, color, (x + 6, y - 2), int(size * 0.5))
        pygame.draw.circle(surface, color, (x, y + 4), int(size * 0.35))
        pygame.draw.circle(surface, dark_color, (x - 5, y + 6), int(size * 0.2))
        pygame.draw.circle(surface, dark_color, (x + 5, y + 6), int(size * 0.2))
    
    elif style == 4:  # Dense cloud cluster
        pygame.draw.circle(surface, color, (x - 6, y - 6), int(size * 0.4))
        pygame.draw.circle(surface, color, (x, y - 8), int(size * 0.45))
        pygame.draw.circle(surface, color, (x + 6, y - 6), int(size * 0.4))
        pygame.draw.circle(surface, color, (x - 8, y + 2), int(size * 0.45))
        pygame.draw.circle(surface, color, (x + 8, y + 2), int(size * 0.45))
        pygame.draw.circle(surface, color, (x, y + 6), int(size * 0.35))
        pygame.draw.circle(surface, dark_color, (x - 7, y + 8), int(size * 0.2))
        pygame.draw.circle(surface, dark_color, (x + 7, y + 8), int(size * 0.2))


def draw_tree_sprite(surface, x, y, size, style, foliage_color, trunk_color):
    """Draw a pixelated tree sprite with layered foliage."""
    trunk_width = max(10, int(size * 0.3))
    trunk_height = int(size * 2)
    
    # Draw trunk
    pygame.draw.rect(surface, trunk_color, (x - trunk_width // 2, y, trunk_width, trunk_height))
    
    # Darker trunk shading
    dark_trunk = (tuple(max(0, c - 40) for c in trunk_color))
    pygame.draw.rect(surface, dark_trunk, (x + 2, y + 10, trunk_width // 3, trunk_height - 10))
    
    if style == 0:  # Rounded tree
        pygame.draw.circle(surface, foliage_color, (x, y - size * 0.8), int(size * 0.5))
        pygame.draw.circle(surface, foliage_color, (x - size * 0.35, y - size * 0.35), int(size * 0.4))
        pygame.draw.circle(surface, foliage_color, (x + size * 0.35, y - size * 0.35), int(size * 0.4))
    
    elif style == 1:  # Conical/pointed tree
        pygame.draw.circle(surface, foliage_color, (x, y - size * 1.0), int(size * 0.4))
        pygame.draw.circle(surface, foliage_color, (x - size * 0.4, y - size * 0.45), int(size * 0.45))
        pygame.draw.circle(surface, foliage_color, (x + size * 0.4, y - size * 0.45), int(size * 0.45))
        pygame.draw.circle(surface, foliage_color, (x - size * 0.25, y + size * 0.05), int(size * 0.35))
        pygame.draw.circle(surface, foliage_color, (x + size * 0.25, y + size * 0.05), int(size * 0.35))
    
    elif style == 2:  # Wide bushy tree
        pygame.draw.circle(surface, foliage_color, (x, y - size * 0.5), int(size * 0.65))
        pygame.draw.circle(surface, foliage_color, (x - size * 0.5, y - size * 0.15), int(size * 0.6))
        pygame.draw.circle(surface, foliage_color, (x + size * 0.5, y - size * 0.15), int(size * 0.6))
        pygame.draw.circle(surface, foliage_color, (x, y + size * 0.25), int(size * 0.5))
    
    elif style == 3:  # Compact tree
        pygame.draw.circle(surface, foliage_color, (x, y - size * 0.65), int(size * 0.5))
        pygame.draw.circle(surface, foliage_color, (x - size * 0.3, y - size * 0.2), int(size * 0.45))
        pygame.draw.circle(surface, foliage_color, (x + size * 0.3, y - size * 0.2), int(size * 0.45))
    
    elif style == 4:  # Sparse thin tree
        pygame.draw.circle(surface, foliage_color, (x, y - size * 0.9), int(size * 0.35))
        pygame.draw.circle(surface, foliage_color, (x - size * 0.25, y - size * 0.35), int(size * 0.3))
        pygame.draw.circle(surface, foliage_color, (x + size * 0.25, y - size * 0.35), int(size * 0.3))


def draw_forest_background(surface, camera, style="classic"):
    """Parallax forest background with selectable aesthetic presets for different platformer looks."""
    if style == "indie":
        sky_color = (154, 221, 255)
        cloud_color = (250, 251, 255)
        hill_a, hill_b = (162, 209, 146), (122, 180, 120)
        tree_dark, tree_light = (137, 172, 120), (112, 188, 122)
        grass_top, grass_mid = (115, 189, 111), (95, 164, 94)
        soil_color = (102, 78, 52)
        sun_alpha = 35
        cloud_scale = 1.0
        detail_scale = 0.8
    elif style == "forest":
        sky_color = (127, 204, 255)
        cloud_color = (240, 246, 255)
        hill_a, hill_b = (137, 178, 110), (96, 152, 86)
        tree_dark, tree_light = (78, 142, 85), (108, 185, 102)
        grass_top, grass_mid = (116, 203, 92), (88, 168, 70)
        soil_color = (92, 71, 43)
        sun_alpha = 42
        cloud_scale = 1.15
        detail_scale = 1.2
    else:  # classic
        sky_color = (125, 211, 255)
        cloud_color = (245, 250, 255)
        hill_a, hill_b = (142, 197, 116), (109, 174, 95)
        tree_dark, tree_light = (94, 156, 96), (72, 163, 90)
        grass_top, grass_mid = (130, 206, 100), (96, 176, 78)
        soil_color = (101, 75, 43)
        sun_alpha = 52
        cloud_scale = 1.2
        detail_scale = 1.0

    surface.fill(sky_color)

    # Layer 1: sky and clouds, repeated seamlessly
    for i in range(-2, 12):
        cx = (i * 260) - ((camera * 0.12) % 260)
        cy = 75 + (i % 5) * 22
        draw_cloud_sprite(surface, int(cx), int(cy), int((28 + (i % 3) * 8) * cloud_scale), i % 5, cloud_color)

    glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (255, 245, 180, sun_alpha), (430, 35, 220, 160))
    surface.blit(glow, (0, 0))

    # Layer 2: distant rolling hills and trees
    for i in range(-2, 18):
        hill_x = i * 190 - ((camera * 0.22) % 190)
        hill_y = 420
        pygame.draw.ellipse(surface, hill_a, (hill_x, hill_y, 170, 130))
        pygame.draw.ellipse(surface, hill_b, (hill_x + 25, hill_y - 12, 120, 110))
        draw_tree_sprite(surface, int(hill_x + 32), int(hill_y - 16), int(24 * detail_scale), i % 5, tree_dark, (104, 72, 46))
        draw_tree_sprite(surface, int(hill_x + 122), int(hill_y - 4), int(28 * detail_scale), (i + 2) % 5, tree_light, (112, 79, 47))

    # Layer 3: midground forest and bushes
    mid_repeat = 120
    offset_3 = (camera * 0.42) % mid_repeat
    for i in range(-2, SCREEN_WIDTH // mid_repeat + 10):
        x = i * mid_repeat - offset_3
        y = 455
        draw_tree_sprite(surface, int(x), int(y), int(46 * detail_scale), i % 5, tree_light, (100, 72, 44))
        pygame.draw.ellipse(surface, (55, 170, 88), (int(x) - 42, 510, 84, 24))
        pygame.draw.ellipse(surface, (77, 194, 108), (int(x) - 24, 500, 60, 20))

    # Layer 4: foreground grass and terrain with strong edge shape
    terrain_repeat = 72
    offset_4 = (camera * 0.82) % terrain_repeat
    for i in range(-2, SCREEN_WIDTH // terrain_repeat + 12):
        gx = i * terrain_repeat - offset_4
        grass_top = 560
        soil_top = 602
        pygame.draw.rect(surface, grass_top, (gx, grass_top, terrain_repeat, 58))
        pygame.draw.rect(surface, soil_color, (gx, soil_top, terrain_repeat, 78))
        pygame.draw.line(surface, (76, 164, 70), (gx, grass_top), (gx + terrain_repeat, grass_top), 5)
        pygame.draw.line(surface, (94, 180, 78), (gx + 10, grass_top + 3), (gx + 32, grass_top - 12), 4)
        pygame.draw.line(surface, (94, 180, 78), (gx + 40, grass_top + 3), (gx + 62, grass_top - 12), 4)
        if i % 2 == 0:
            pygame.draw.circle(surface, (242, 190, 89), (gx + 18, grass_top - 8), 5)
            pygame.draw.circle(surface, (245, 118, 181), (gx + 55, grass_top - 6), 4)

    # Edge framing bushes
    for bx in (-80, SCREEN_WIDTH - 40):
        pygame.draw.ellipse(surface, (48, 172, 85), (bx, 518, 92, 74))
        pygame.draw.ellipse(surface, (75, 194, 108), (bx + 18, 502, 72, 60))
        pygame.draw.ellipse(surface, (63, 146, 80), (bx + 42, 520, 62, 52))

    # Decorations
    for i in range(14):
        mx = ((i * 170) - (camera * 0.75)) % (SCREEN_WIDTH + 140) - 70
        my = 536 + (i % 3) * 12
        pygame.draw.circle(surface, (226, 93, 74), (mx, my), 6)
        pygame.draw.circle(surface, (230, 101, 90), (mx + 10, my + 2), 6)
        pygame.draw.rect(surface, (188, 122, 70), (mx + 3, my + 6, 5, 18))

    haze = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for layer in range(3):
        pygame.draw.ellipse(haze, (255, 255, 255, 17 - layer * 4), (0, 245 + layer * 75, SCREEN_WIDTH, 220))
    surface.blit(haze, (0, 0))

def draw_title_screen(surface):
    surface.fill((18, 29, 42))
    label(surface, "LUMENWILD", (SCREEN_WIDTH // 2 - big_font.size("LUMENWILD")[0] // 2, 155), (255, 220, 116), True)
    label(surface, "THE FIVE FRONTIERS", (SCREEN_WIDTH // 2 - font.size("THE FIVE FRONTIERS")[0] // 2, 245), (192, 220, 228))
    draw_button(surface, pygame.Rect(335, 430, 430, 90), "START ADVENTURE", (255, 200, 94), True)
    label(surface, "CLICK OR PRESS ENTER", (SCREEN_WIDTH // 2 - font.size("CLICK OR PRESS ENTER")[0] // 2, 540), (188, 212, 216))


def draw_map(surface, progress, selected, stage):
    surface.fill((18, 29, 42))
    label(surface, "CHOOSE WORLD", (420, 60), (255, 220, 116), True)
    for number, theme in enumerate(WORLD_THEMES):
        x = 120 + number * 205
        unlocked = progress.unlocked(number, 0)
        color = theme["accent"] if number == selected else ((90, 104, 121) if unlocked else (53, 59, 70))
        pygame.draw.circle(surface, color, (x, 150), 42 if number == selected else 32)
        label(surface, str(number + 1), (x - 8, 140), (20, 30, 35), True)
        label(surface, theme["short"], (x - 36, 215), theme["accent"] if unlocked else (110, 112, 120))
    label(surface, "LEVEL SELECT", (440, 260), (255, 220, 116), True)
    for index in range(4):
        rect = pygame.Rect(80 + index * 220, 330, 170, 100)
        active = index == stage
        color = WORLD_THEMES[selected]["accent"] if active else (102, 125, 148)
        draw_button(surface, rect, f"LEVEL {index + 1}", color, active)
    label(surface, f"WORLD {selected + 1}   SELECTED LEVEL {stage + 1}", (300, 470), WORLD_THEMES[selected]["accent"])
    draw_button(surface, pygame.Rect(360, 565, 380, 60), "START LEVEL", WORLD_THEMES[selected]["accent"], True)

def main():
    progress = Progress()
    audio = Audio()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0) if pygame.joystick.get_count() else None
    world = stage = selected = 0
    background_style = "classic"
    abilities, state, score, shake = set(), "title", 0, 0
    level_timer = 0  # Track time spent on current level
    level, player, enemies, boss = stage_data(world, stage, abilities)
    coins, gems = set(level.entities["coins"]), set(level.entities["gems"])
    specials, powerups, checkpoint = set(level.entities["specials"]), set(level.entities["powerups"]), None
    enemy_projectiles = []
    touch_left = touch_right = touch_jump = False

    def restart():
        nonlocal level, player, enemies, boss, coins, gems, specials, powerups, checkpoint, enemy_projectiles, level_timer
        level_timer = 0  # Reset timer on level restart
        level, player, enemies, boss = stage_data(world, stage, abilities)
        coins, gems = set(level.entities["coins"]), set(level.entities["gems"])
        specials, powerups, checkpoint = set(level.entities["specials"]), set(level.entities["powerups"]), None
        enemy_projectiles = []

    running = True
    while running:
        jump_pressed = attack_pressed = False
        touch_left = touch_right = touch_jump = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.FINGERDOWN:
                touch_left = event.x < 0.22
                touch_right = event.x > 0.78
                touch_jump = event.y < 0.75 and not (touch_left or touch_right)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if state == "title":
                    start_button = pygame.Rect(335, 430, 430, 90)
                    if start_button.collidepoint(mouse_pos): state = "map"
                elif state == "map":
                    for index, theme in enumerate(WORLD_THEMES):
                        world_rect = pygame.Rect(120 + index * 205 - 42, 108, 84, 84)
                        if world_rect.collidepoint(mouse_pos):
                            selected = index
                            break
                    for index in range(4):
                        level_rect = pygame.Rect(80 + index * 220, 330, 170, 100)
                        if level_rect.collidepoint(mouse_pos):
                            stage = index
                            break
                    start_button = pygame.Rect(360, 565, 380, 60)
                    if start_button.collidepoint(mouse_pos) and progress.unlocked(selected, stage):
                        world, state = selected, "play"
                        restart()
            elif event.type == pygame.JOYBUTTONDOWN:
                jump_pressed |= event.button == 0
                attack_pressed |= event.button == 1
            elif event.type == pygame.KEYDOWN:
                jump_pressed |= event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP)
                attack_pressed |= event.key in (pygame.K_z, pygame.K_x)
                if event.key == pygame.K_ESCAPE and state in ("play", "pause"): state = "pause" if state == "play" else "play"
                elif event.key == pygame.K_r and state in ("play", "pause", "dead"): restart(); state = "play"
                elif event.key == pygame.K_1: background_style = "classic"
                elif event.key == pygame.K_2: background_style = "indie"
                elif event.key == pygame.K_3: background_style = "forest"
                elif state == "title" and event.key in (pygame.K_RETURN, pygame.K_SPACE): state = "map"
                elif state == "map":
                    if event.key in (pygame.K_LEFT, pygame.K_a): selected = max(0, selected - 1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d): selected = min(4, selected + 1)
                    elif event.key in (pygame.K_UP, pygame.K_w): stage = max(0, stage - 1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s): stage = min(3, stage + 1)
                    elif event.key == pygame.K_RETURN and progress.unlocked(selected, stage): world, state = selected, "play"; restart()
                elif event.key == pygame.K_m and state == "play": state = "map"
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and state in ("dead", "clear", "win"):
                    if state == "clear":
                        progress.complete(world, stage, len(level.entities["coins"]) - len(coins)); stage += 1
                        if stage >= 3: state = "win" if world == 4 else "map"; selected = min(4, world + 1)
                        else: restart(); state = "play"
                    else: world = stage = score = 0; abilities.clear(); restart(); state = "play"
        if state == "play":
            level_timer += 1  # Increment timer each frame
            keys = pygame.key.get_pressed(); dash = getattr(pygame, "K_LSHIFT", 304)
            axis = joystick.get_axis(0) if joystick and joystick.get_numaxes() else 0
            left = keys[pygame.K_a] or keys[pygame.K_LEFT] or axis < -0.35 or touch_left
            right = keys[pygame.K_d] or keys[pygame.K_RIGHT] or axis > 0.35 or touch_right
            jump = keys[pygame.K_SPACE] or jump_pressed or touch_jump
            player.update({pygame.K_a: left, pygame.K_d: right, pygame.K_SPACE: jump, dash: keys[dash] if dash < len(keys) else False}, level.colliders)
            level.update_dynamic(player)
            if jump_pressed: audio.play("jump")
            if attack_pressed: player.attack(); player.fire_projectile(); audio.play("hit")
            for projectile in player.projectiles[:]:
                projectile.x += 11 if player.facing_right else -11
                if projectile.right < 0 or projectile.left > level.pixel_width: player.projectiles.remove(projectile)
            for enemy in enemies:
                enemy.update(player)
                if enemy.kind == "thrower" and enemy.telegraph == 1:
                    direction = 1 if player.centerx > enemy.centerx else -1
                    enemy_projectiles.append(HazardProjectile(enemy.centerx, enemy.centery, direction * 8))
            for item in list(coins):
                if player.colliderect(pygame.Rect(item[0] - 3, item[1] - 10, 22, 22)): coins.remove(item); score += 100; audio.play("coin")
            for item in list(gems):
                if player.colliderect(pygame.Rect(item[0] - 10, item[1] - 12, 20, 24)): gems.remove(item); score += 500
            for item in list(specials):
                if player.colliderect(pygame.Rect(item[0] - 12, item[1] - 12, 24, 24)): specials.remove(item); score += 1000
            for item in list(powerups):
                if player.colliderect(pygame.Rect(item[0] - 12, item[1] - 12, 24, 24)):
                    powerups.remove(item); abilities.add(item[2]); player.powerups.add(item[2]); audio.play("powerup")
                    if item[2] == "shield": player.shield = 1
                    if item[2] == "invincibility": player.invincible_timer = 360
            for marker in level.entities["checkpoints"]:
                if player.centerx > marker[0] and checkpoint != marker:
                    checkpoint = marker; audio.play("checkpoint")
            for projectile in enemy_projectiles[:]:
                projectile.x += projectile.velocity
                if projectile.right < 0 or projectile.left > level.pixel_width:
                    enemy_projectiles.remove(projectile)
                elif player.colliderect(projectile):
                    enemy_projectiles.remove(projectile)
                    if player.take_damage(): shake = 8
            hitbox = player.get_attack_hitbox()
            for enemy in enemies[:]:
                for projectile in player.projectiles[:]:
                    if projectile.colliderect(enemy):
                        enemy.health -= 1; player.projectiles.remove(projectile)
                if hitbox and hitbox.colliderect(enemy): enemy.health -= 1
                elif player.colliderect(enemy) and player.vel_y > 0 and player.bottom - enemy.top < 20: enemies.remove(enemy); player.vel_y = -10; score += 250
                elif player.colliderect(enemy) and player.take_damage(): player.topleft = checkpoint or (96, 19 * TILE_SIZE - 48); shake = 8
                if enemy.health <= 0 and enemy in enemies: enemies.remove(enemy); score += 250
            if boss:
                boss.update(player)
                # Boss becomes more aggressive as it takes damage (phase transitions)
                phase_modifier = (12 - boss.health) // 4  # Increase aggression every 4 health
                if boss.telegraph == 1:
                    direction = 1 if player.centerx > boss.centerx else -1
                    # Fire multiple projectiles in later phases
                    for offset in range(1 + phase_modifier):
                        enemy_projectiles.append(HazardProjectile(boss.centerx, boss.centery - offset * 8, direction * 10))
                if hitbox and hitbox.colliderect(boss) and not boss.telegraph: boss.health -= 1; boss.phase = boss.health < 8; shake = 6
                if player.colliderect(boss) and player.take_damage(): shake = 10
                if boss.health <= 0: state = "clear"
            if any(player.colliderect(hazard) for hazard in level.hazards) or player.top > level.pixel_height:
                if player.take_damage(): player.topleft = checkpoint or (96, 19 * TILE_SIZE - 48)
            if player.health <= 0: state = "dead"
            elif player.colliderect(pygame.Rect(*level.entities["goal"], 46, 80)) and not boss: state = "clear"
        camera = max(0, min(player.centerx - SCREEN_WIDTH // 2, level.pixel_width - SCREEN_WIDTH))
        camera += random.randint(-shake, shake) if shake else 0
        shake = max(0, shake - 1)
        theme = WORLD_THEMES[world]
        if world == 0:
            draw_forest_background(screen, camera, background_style)
        else:
            screen.fill(theme["sky"])
            pygame.draw.rect(screen, theme["ground"], (0, 610, SCREEN_WIDTH, 70))
        label(screen, f"WORLD {world + 1} / LEVEL {stage + 1}  {theme['short']}", (28, 22))
        level.draw(screen, camera)
        for item in coins: draw_collectible(screen, item, camera, theme["accent"])
        for item in gems: draw_collectible(screen, item, camera, (87, 238, 218), True)
        for item in specials: draw_collectible(screen, item, camera, (255, 111, 206), True)
        for item in powerups: draw_collectible(screen, item, camera, (232, 245, 255), True)
        for enemy in enemies: enemy.draw(screen, camera)
        for projectile in enemy_projectiles:
            pygame.draw.circle(screen, (255, 92, 72), (projectile.centerx - camera, projectile.centery), 7)
        for projectile in player.projectiles: pygame.draw.circle(screen, (255, 230, 112), (projectile.centerx - camera, projectile.centery), 6)
        if boss: boss.draw(screen, camera); pygame.draw.rect(screen, (225, 75, 73), (470, 60, max(0, 360 * boss.health // 12), 14))
        # Calculate difficulty for current level
        difficulty_level = min(5, world + stage + 1)
        timer_seconds = level_timer // 60
        player.draw(screen, camera)
        label(screen, f"HP {'|' * max(0, player.health)}  SCORE {score:05d}  RELICS {3 - len(specials)}/3", (28, 70))
        label(screen, f"DIFFICULTY {'★' * difficulty_level}{'☆' * (5 - difficulty_level)}  TIME {timer_seconds}s", (SCREEN_WIDTH - 420, 70))
        if state == "title":
            draw_title_screen(screen)
        elif state == "map":
            draw_map(screen, progress, selected, stage)
        elif state != "play":
            pygame.draw.rect(screen, (16, 29, 40), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 185)
            heading = {"title": "LUMENWILD", "pause": "PAUSED", "dead": "FALLEN", "clear": "FRONTIER CLEAR", "win": "THE WILD IS SAFE"}.get(state, "")
            label(screen, heading, (SCREEN_WIDTH // 2 - big_font.size(heading)[0] // 2, 245), (255, 227, 113), True)
            if state == "pause":
                # Enhanced pause menu with game info
                label(screen, f"WORLD {world + 1} / LEVEL {stage + 1}", (SCREEN_WIDTH // 2 - font.size(f"WORLD {world + 1} / LEVEL {stage + 1}")[0] // 2, 335))
                label(screen, f"SCORE: {score:05d}  HP: {player.health}  TIME: {level_timer // 60}s", (SCREEN_WIDTH // 2 - font.size(f"SCORE: {score:05d}  HP: {player.health}  TIME: {level_timer // 60}s")[0] // 2, 365))
                label(screen, "ESC/SPACE resume   R restart   M menu", (350, 425))
            else:
                label(screen, "SPACE/ENTER continue   ESC pause   R restart", (350, 335))
        pygame.display.flip(); clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__": main()
""" Legacy demo retained below for reference only.
import math
import random
import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE, WORLD_THEMES
from enemy import Enemy
from level import Level
from player import Player
from progression import Progress

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Lumenwild: The Five Frontiers")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 27)
big_font = pygame.font.Font(None, 72)


def label(surface, value, position, color=(244, 244, 228), large=False):
    surface.blit((big_font if large else font).render(value, True, color), position)


def load_stage(world, stage, abilities):
    level = Level.campaign(world, stage)
    player = Player(96, 19 * TILE_SIZE - 48, abilities | ({"dash"} if world else set()))
    enemies = [Enemy(item["x"], item["y"], kind=item["kind"]) for item in level.entities["enemies"]]
    boss = None
    if level.entities.get("boss"):
        data = level.entities["boss_data"]
        boss = Enemy(data["x"], data["y"], 1, 0, "armored")
        boss.width, boss.height, boss.health = 70, 70, 12
    return level, player, enemies, boss


def draw_world(surface, camera, world, stage):
    theme = WORLD_THEMES[world]
    surface.fill(theme["sky"])
    for layer, color in enumerate((theme["far"], theme["near"])):
        spacing = 250 - layer * 50
        offset = int(camera * (0.12 + layer * 0.08)) % spacing
        for x in range(-spacing - offset, SCREEN_WIDTH + spacing, spacing):
            pygame.draw.circle(surface, color, (x + spacing // 2, 360 + layer * 120), 150 - layer * 40)
    pygame.draw.rect(surface, theme["ground"], (0, 610, SCREEN_WIDTH, 70))
    label(surface, f"WORLD {world + 1} / LEVEL {stage + 1}  {theme['short']}", (28, 22))


def draw_map(surface, progress, selected):
    surface.fill((18, 29, 42))
    label(surface, "THE FIVE FRONTIERS", (SCREEN_WIDTH // 2 - 210, 60), (255, 220, 116), True)
    label(surface, "Choose a cleared route", (SCREEN_WIDTH // 2 - 105, 140), (188, 212, 216))
    for number, theme in enumerate(WORLD_THEMES):
        x = 120 + number * 205
        unlocked = progress.unlocked(number, 0)
        color = theme["accent"] if number == selected else ((90, 104, 121) if unlocked else (53, 59, 70))
        pygame.draw.circle(surface, color, (x, 300), 42 if number == selected else 32)
        label(surface, str(number + 1), (x - 8, 290), (20, 30, 35), True)
        label(surface, theme["short"], (x - 36, 365), theme["accent"] if unlocked else (110, 112, 120))
        label(surface, f"{sum((number, item) in progress.completed for item in range(3))}/3", (x - 12, 400))
    label(surface, "A/D or arrows select   ENTER launch", (SCREEN_WIDTH // 2 - 170, 535), (188, 212, 216))


def main():
    progress = Progress()
    world = stage = selected = 0
    abilities = set()
    state = "title"
    level, player, enemies, boss = load_stage(world, stage, abilities)
    coins, gems = set(level.entities["coins"]), set(level.entities["gems"])
    specials, powerups = set(level.entities["specials"]), set(level.entities["powerups"])
    checkpoint = None
    score = shake = 0

    def restart():
        nonlocal level, player, enemies, boss, coins, gems, specials, powerups, checkpoint
        level, player, enemies, boss = load_stage(world, stage, abilities)
        coins, gems = set(level.entities["coins"]), set(level.entities["gems"])
        specials, powerups = set(level.entities["specials"]), set(level.entities["powerups"])
        checkpoint = None

    running = True
    while running:
        jump_pressed = attack_pressed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                jump_pressed |= event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP)
                attack_pressed |= event.key in (pygame.K_z, pygame.K_x)
                if event.key == pygame.K_ESCAPE and state in ("play", "pause"):
                    state = "pause" if state == "play" else "play"
                elif event.key == pygame.K_r and state in ("play", "pause", "dead"):
                    restart(); state = "play"
                elif state == "title" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    state = "map"
                elif state == "map":
                    if event.key in (pygame.K_LEFT, pygame.K_a): selected = max(0, selected - 1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d): selected = min(4, selected + 1)
                    elif event.key == pygame.K_RETURN and progress.unlocked(selected, 0):
                        world, stage, state = selected, 0, "play"; restart()
                elif event.key == pygame.K_m and state == "play":
                    state = "map"
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and state in ("dead", "clear", "win"):
                    if state == "clear":
                        progress.complete(world, stage, len(level.entities["coins"]) - len(coins)); stage += 1
                        if stage >= 3:
                            state = "win" if world == 4 else "map"; selected = min(4, world + 1)
                        else:
                            restart(); state = "play"
                    else:
                        world = stage = score = 0; abilities.clear(); restart(); state = "play"

        if state == "play":
            keys = pygame.key.get_pressed()
            dash = getattr(pygame, "K_LSHIFT", 304)
            key_map = {pygame.K_a: keys[pygame.K_a] or keys[pygame.K_LEFT], pygame.K_d: keys[pygame.K_d] or keys[pygame.K_RIGHT], pygame.K_SPACE: keys[pygame.K_SPACE] or jump_pressed, dash: keys[dash] if dash < len(keys) else False}
            player.update(key_map, level.colliders)
            if attack_pressed: player.attack()
            for enemy in enemies: enemy.update(player)
            for item in list(coins):
                if player.colliderect(pygame.Rect(item[0] - 3, item[1] - 10, 22, 22)): coins.remove(item); score += 100
            for item in list(gems):
                if player.colliderect(pygame.Rect(item[0] - 10, item[1] - 12, 20, 24)): gems.remove(item); score += 500
            for item in list(specials):
                if player.colliderect(pygame.Rect(item[0] - 12, item[1] - 12, 24, 24)): specials.remove(item); score += 1000
            for item in list(powerups):
                if player.colliderect(pygame.Rect(item[0] - 12, item[1] - 12, 24, 24)): powerups.remove(item); abilities.add(item[2]); player.powerups.add(item[2])
            for marker in level.entities["checkpoints"]:
                if player.centerx > marker[0]: checkpoint = marker
            hitbox = player.get_attack_hitbox()
            for enemy in enemies[:]:
                if hitbox and hitbox.colliderect(enemy): enemy.health -= 1
                elif player.colliderect(enemy) and player.vel_y > 0 and player.bottom - enemy.top < 20: enemies.remove(enemy); player.vel_y = -10; score += 250
                elif player.colliderect(enemy) and player.take_damage(): player.topleft = checkpoint or (96, 19 * TILE_SIZE - 48); shake = 8
                if enemy.health <= 0 and enemy in enemies: enemies.remove(enemy); score += 250
            if boss:
                boss.update(player)
                if hitbox and hitbox.colliderect(boss) and not boss.telegraph: boss.health -= 1; boss.phase = boss.health < 8; shake = 6
                if player.colliderect(boss) and player.take_damage(): shake = 10
                if boss.health <= 0: state = "clear"
            if any(player.colliderect(hazard) for hazard in level.hazards) or player.top > level.pixel_height:
                if player.take_damage(): player.topleft = checkpoint or (96, 19 * TILE_SIZE - 48)
            if player.health <= 0: state = "dead"
            elif player.colliderect(pygame.Rect(*level.entities["goal"], 46, 80)) and not boss: state = "clear"

        camera = max(0, min(player.centerx - SCREEN_WIDTH // 2, level.pixel_width - SCREEN_WIDTH))
        shake = max(0, shake - 1)
        draw_world(screen, camera + random.randint(-shake, shake), world, stage)
        level.draw(screen, camera)
        for item in coins: draw_collectible(screen, item, camera, WORLD_THEMES[world]["accent"])
        for item in gems: draw_collectible(screen, item, camera, (87, 238, 218), True)
        for item in specials: draw_collectible(screen, item[:2], camera, (255, 111, 206), True)
        for item in powerups: draw_collectible(screen, item[:2], camera, (232, 245, 255), True)
        for enemy in enemies: enemy.draw(screen, camera)
        if boss: boss.draw(screen, camera); pygame.draw.rect(screen, (225, 75, 73), (SCREEN_WIDTH // 2 - 180, 60, max(0, 360 * boss.health // 12), 14))
        player.draw(screen, camera)
        label(screen, f"HP {'|' * max(0, player.health)}  SCORE {score:05d}  RELICS {3 - len(specials)}/3", (28, 70))
        if state == "map": draw_map(screen, progress, selected)
        elif state in ("title", "pause", "dead", "clear", "win"):
            pygame.draw.rect(screen, (16, 29, 40), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 185)
            heading = {"title": "LUMENWILD", "pause": "PAUSED", "dead": "FALLEN", "clear": "FRONTIER CLEAR", "win": "THE WILD IS SAFE"}[state]
            label(screen, heading, (SCREEN_WIDTH // 2 - big_font.size(heading)[0] // 2, 245), (255, 227, 113), True)
            label(screen, {"title": "Five worlds. Fifteen trails. One bright spark.", "pause": "ESC resume   R restart", "dead": "SPACE restart   R retry", "clear": "ENTER continue", "win": "All five worlds complete"}[state], (320, 335))
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


def draw_collectible(surface, item, camera, color, gem=False):
    x, y = item[:2]
    point = (int(x - camera), int(y + math.sin(pygame.time.get_ticks() / 180 + x) * 4))
    if gem: pygame.draw.polygon(surface, color, ((point[0], point[1] - 12), (point[0] + 10, point[1]), (point[0], point[1] + 12), (point[0] - 10, point[1])))
    else: pygame.draw.circle(surface, color, point, 8); pygame.draw.circle(surface, (255, 244, 154), point, 4)


if __name__ == "__main__": main()import math
import random
import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE
from enemy import Enemy
from level import Level
from player import Player

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Lumenwild: Meadow Run")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 72)
random.seed(8)


def text(surface, message, position, color=(255, 255, 255), large=False):
    surface.blit((big_font if large else font).render(message, True, color), position)


def new_stage(stage):
    level = Level.world_one(stage)
    player = Player(96, 19 * TILE_SIZE - 48)
    enemies = [Enemy(item["x"], item["y"], kind=item.get("kind", "walker")) for item in level.entities["enemies"]]
    return level, player, enemies


def draw_background(surface, camera_x, stage):
    surface.fill((126, 204, 225))
    for layer, (color, y, radius, spacing) in enumerate([((91, 177, 126), 360, 150, 250), ((55, 139, 101), 455, 105, 190)]):
        offset = int(camera_x * (0.12 + layer * 0.08)) % spacing
        for x in range(-spacing - offset, SCREEN_WIDTH + spacing, spacing):
            pygame.draw.circle(surface, color, (x + spacing // 2, y), radius)
    pygame.draw.rect(surface, (73, 151, 91), (0, 610, SCREEN_WIDTH, 70))
    text(surface, f"WORLD 1  /  STAGE {stage + 1}", (28, 22))


def draw_collectible(surface, x, y, camera_x, color, gem=False):
    point = (int(x - camera_x), int(y + math.sin(pygame.time.get_ticks() / 180 + x) * 4))
    if gem:
        pygame.draw.polygon(surface, color, [(point[0], point[1] - 11), (point[0] + 9, point[1]), (point[0], point[1] + 11), (point[0] - 9, point[1])])
    else:
        pygame.draw.circle(surface, color, point, 8)
        pygame.draw.circle(surface, (255, 244, 154), point, 4)


def main():
    stage = 0
        world, stage, selected = 0, 0, 0
        abilities = set()
        state = "title"
        level, player, enemies, boss = new_stage(world, stage, abilities)
        coins = set(level.entities["coins"])
        gems = set(level.entities["gems"])
        specials = set(level.entities["specials"])
        powerups = set(level.entities["powerups"])
        checkpoint = None
        score, shake = 0, 0

        def load_stage():
            nonlocal level, player, enemies, boss, coins, gems, specials, powerups, checkpoint
            level, player, enemies, boss = new_stage(world, stage, abilities)
            coins, gems = set(level.entities["coins"]), set(level.entities["gems"])
            specials, powerups = set(level.entities["specials"]), set(level.entities["powerups"])
            checkpoint = None

        running = True
        while running:
            jump_pressed = attack_pressed = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    jump_pressed |= event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP)
                    attack_pressed |= event.key in (pygame.K_z, pygame.K_x)
                    if event.key == pygame.K_ESCAPE and state in ("play", "pause"):
                        state = "pause" if state == "play" else "play"
                    elif event.key == pygame.K_r and state in ("play", "pause", "dead"):
                        load_stage(); state = "play"
                    elif state == "title" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        state = "map"
                    elif state == "map":
                        if event.key in (pygame.K_LEFT, pygame.K_a): selected = max(0, selected - 1)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d): selected = min(4, selected + 1)
                        elif event.key == pygame.K_RETURN and progress.unlocked(selected, 0):
                            world, stage, state = selected, 0, "play"; load_stage()
                    elif event.key == pygame.K_m and state == "play": state = "map"
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and state in ("dead", "clear", "win"):
                        if state == "clear":
                            progress.complete(world, stage, len(level.entities["coins"]) - len(coins)); stage += 1
                            if stage >= 3:
                                if world == 4: state = "win"
                                else: selected, state = world + 1, "map"
                            else: load_stage(); state = "play"
                        else:
                            world, stage, score, abilities = 0, 0, 0, set(); load_stage(); state = "play"

            if state == "play":
                keys = pygame.key.get_pressed()
                dash_key = getattr(pygame, "K_LSHIFT", 304)
                key_map = {pygame.K_a: keys[pygame.K_a] or keys[pygame.K_LEFT], pygame.K_d: keys[pygame.K_d] or keys[pygame.K_RIGHT], pygame.K_SPACE: keys[pygame.K_SPACE] or jump_pressed, dash_key: keys[dash_key] if dash_key < len(keys) else False}
                player.update(key_map, level.colliders)
                if attack_pressed: player.attack()
                for enemy in enemies: enemy.update(player)
                for item in list(coins):
                    if player.colliderect(pygame.Rect(item[0] - 3, item[1] - 10, 22, 22)): coins.remove(item); score += 100
                for item in list(gems):
                    if player.colliderect(pygame.Rect(item[0] - 10, item[1] - 12, 20, 24)): gems.remove(item); score += 500
                for item in list(specials):
                    if player.colliderect(pygame.Rect(item[0] - 12, item[1] - 12, 24, 24)): specials.remove(item); score += 1000
                for item in list(powerups):
                    if player.colliderect(pygame.Rect(item[0] - 12, item[1] - 12, 24, 24)): powerups.remove(item); abilities.add(item[2]); player.powerups.add(item[2])
                for marker in level.entities["checkpoints"]:
                    if player.centerx > marker[0]: checkpoint = marker
                hitbox = player.get_attack_hitbox()
                for enemy in enemies[:]:
                    if hitbox and hitbox.colliderect(enemy): enemy.health -= 1
                    elif player.colliderect(enemy) and player.vel_y > 0 and player.bottom - enemy.top < 20: enemies.remove(enemy); player.vel_y = -10; score += 250
                    elif player.colliderect(enemy) and player.take_damage(): player.topleft = checkpoint or (96, 19 * TILE_SIZE - 48); shake = 8
                    if enemy.health <= 0 and enemy in enemies: enemies.remove(enemy); score += 250
                if boss:
                    boss.update(player)
                    if hitbox and hitbox.colliderect(boss) and not boss.telegraph: boss.health -= 1; boss.phase = boss.health < 8; shake = 6
                    if player.colliderect(boss) and player.take_damage(): shake = 10
                    if boss.health <= 0: state = "clear"
                if any(player.colliderect(hazard) for hazard in level.hazards) or player.top > level.pixel_height:
                    if player.take_damage(): player.topleft = checkpoint or (96, 19 * TILE_SIZE - 48)
                if player.health <= 0: state = "dead"
                elif player.colliderect(pygame.Rect(*level.entities["goal"], 46, 80)) and not boss: state = "clear"

            camera_x = max(0, min(player.centerx - SCREEN_WIDTH // 2, level.pixel_width - SCREEN_WIDTH))
            shake = max(0, shake - 1)
            draw_background(screen, camera_x + random.randint(-shake, shake), world, stage)
            level.draw(screen, camera_x)
            for item in coins: draw_collectible(screen, item[0], item[1], camera_x, WORLD_THEMES[world]["accent"])
            for item in gems: draw_collectible(screen, item[0], item[1], camera_x, (87, 238, 218), True)
            for item in specials: draw_collectible(screen, item[0], item[1], camera_x, (255, 111, 206), True)
            for x, y, kind in powerups: draw_collectible(screen, x, y, camera_x, (232, 245, 255), True); text(screen, kind[0].upper(), (x - camera_x - 5, y - 8), (30, 50, 60))
            for enemy in enemies: enemy.draw(screen, camera_x)
            if boss: boss.draw(screen, camera_x); pygame.draw.rect(screen, (225, 75, 73), (SCREEN_WIDTH // 2 - 180, 60, max(0, 360 * boss.health // 12), 14))
            player.draw(screen, camera_x)
            text(screen, f"HP {'|' * player.health}{'.' * (player.max_health - max(0, player.health))}  SCORE {score:05d}  RELICS {3 - len(specials)}/3", (28, 70))
            if state == "map": draw_map(screen, progress, selected)
            elif state in ("title", "pause", "dead", "clear", "win"):
                pygame.draw.rect(screen, (16, 29, 40), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 185)
                heading = {"title": "LUMENWILD", "pause": "PAUSED", "dead": "FALLEN", "clear": "FRONTIER CLEAR", "win": "THE WILD IS SAFE"}[state]
                subtitle = {"title": "Five worlds. Fifteen trails. One bright spark.", "pause": "ESC resume   R restart", "dead": "SPACE restart   R retry", "clear": "ENTER continue", "win": "All five worlds complete"}[state]
                text(screen, heading, (SCREEN_WIDTH // 2 - big_font.size(heading)[0] // 2, 245), (255, 227, 113), True)
                text(screen, subtitle, (SCREEN_WIDTH // 2 - font.size(subtitle)[0] // 2, 335))
                if state == "title": text(screen, "A/D move   SPACE jump   Z attack   SHIFT dash   M map", (SCREEN_WIDTH // 2 - 220, 390), (207, 237, 224))
            pygame.display.flip(); clock.tick(FPS)
        pygame.quit()

    if __name__ == "__main__": main()
    coins = set(level.entities["coins"])
    gems = set(level.entities["gems"])
    checkpoint = None
    score = 0
    lives = 3
    state = "title"
    running = True

    while running:
        jump_pressed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    jump_pressed = True
                if event.key == pygame.K_ESCAPE and state in ("play", "pause"):
                    state = "pause" if state == "play" else "play"
                if event.key == pygame.K_r and state == "play":
                    level, player, enemies = new_stage(stage)
                    coins = set(level.entities["coins"])
                    gems = set(level.entities["gems"])
                    checkpoint = None
                if event.key in (pygame.K_RETURN, pygame.K_SPACE) and state in ("title", "pause", "dead", "complete", "win"):
                    if state == "title":
                        state = "play"
                    elif state == "pause":
                        state = "play"
                    elif state == "complete":
                        stage += 1
                        if stage >= 3:
                            state = "win"
                        else:
                            level, player, enemies = new_stage(stage)
                            coins = set(level.entities["coins"])
                            gems = set(level.entities["gems"])
                            checkpoint = None
                            state = "play"
                    else:
                        stage = 0
                        score = 0
                        lives = 3
                        level, player, enemies = new_stage(stage)
                        coins = set(level.entities["coins"])
                        gems = set(level.entities["gems"])
                        checkpoint = None
                        state = "play"

        if state == "play":
            keys = pygame.key.get_pressed()
            key_map = {pygame.K_a: keys[pygame.K_a], pygame.K_d: keys[pygame.K_d], pygame.K_SPACE: keys[pygame.K_SPACE] or jump_pressed}
            player.update(key_map, level.colliders)
            for enemy in enemies:
                enemy.update(player)
            for coin in list(coins):
                if player.colliderect(pygame.Rect(coin[0] - 3, coin[1] - 10, 22, 22)):
                    coins.remove(coin)
                    score += 100
            for gem in list(gems):
                if player.colliderect(pygame.Rect(gem[0] - 10, gem[1] - 12, 20, 24)):
                    gems.remove(gem)
                    score += 500
            for marker in level.entities["checkpoints"]:
                if player.centerx > marker[0] and checkpoint is None:
                    checkpoint = marker
            for enemy in enemies[:]:
                if player.colliderect(enemy):
                    if player.vel_y > 0 and player.bottom - enemy.top < 20:
                        enemies.remove(enemy)
                        player.vel_y = -10
                        score += 250
                    elif player.invincible_timer == 0:
                        lives -= 1
                        player.invincible_timer = 100
                        if lives <= 0:
                            state = "dead"
                        else:
                            player.topleft = checkpoint or (96, 19 * TILE_SIZE - 48)
            if any(player.colliderect(hazard) for hazard in level.hazards) or player.top > level.pixel_height:
                lives -= 1
                if lives <= 0:
                    state = "dead"
                else:
                    player.topleft = checkpoint or (96, 19 * TILE_SIZE - 48)
            if player.colliderect(pygame.Rect(*level.entities["goal"], 46, 80)):
                state = "complete"

        camera_x = max(0, min(player.centerx - SCREEN_WIDTH // 2, level.pixel_width - SCREEN_WIDTH))
        draw_background(screen, camera_x, stage)
        level.draw(screen, camera_x)
        for coin in coins:
            draw_collectible(screen, coin[0], coin[1], camera_x, (255, 207, 54))
        for gem in gems:
            draw_collectible(screen, gem[0], gem[1], camera_x, (87, 238, 218), True)
        for enemy in enemies:
            enemy.draw(screen, camera_x)
        player.draw(screen, camera_x)
        goal = pygame.Rect(*level.entities["goal"], 46, 80)
        pygame.draw.rect(screen, (244, 226, 114), (goal.x - camera_x, goal.y, goal.width, goal.height), border_radius=10)
        pygame.draw.circle(screen, (255, 255, 255), (goal.x - camera_x + 23, goal.y + 24), 8)
        pygame.draw.rect(screen, (27, 65, 71), (18, 62, 410, 38), border_radius=12)
        text(screen, f"SCORE {score:05d}   COINS {len(level.entities['coins']) - len(coins)}   LIVES {lives}", (30, 69), (255, 244, 205))

        if state in ("title", "pause", "dead", "complete", "win"):
            pygame.draw.rect(screen, (20, 47, 58), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 180)
            heading = {"title": "LUMENWILD", "pause": "PAUSED", "dead": "TRY AGAIN", "complete": "STAGE CLEAR", "win": "MEADOW MASTER"}[state]
            subtitle = {"title": "A bright little adventure", "pause": "ESC to resume", "dead": "SPACE to restart", "complete": "SPACE for the next stage", "win": "All three stages complete"}[state]
            text(screen, heading, (SCREEN_WIDTH // 2 - big_font.size(heading)[0] // 2, 245), (255, 227, 113), True)
            text(screen, subtitle, (SCREEN_WIDTH // 2 - font.size(subtitle)[0] // 2, 335))
            if state == "title":
                text(screen, "A / D move    SPACE jump    R restart    ESC pause", (SCREEN_WIDTH // 2 - 190, 390), (207, 237, 224))
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
"""
