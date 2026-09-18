import pygame


class Enemy(pygame.Rect):
    def __init__(self, x, y, speed=2, move_range=80, kind="walker", difficulty=0):
        super().__init__(x, y, 24, 24)
        self.speed = speed * (1 + difficulty * 0.3)  # Scale speed with difficulty
        self.move_range = move_range
        self.direction = 1
        self.start_x = x
        self.start_y = y
        self.kind = kind
        self.difficulty = difficulty
        # Health scales with difficulty
        health_map = {"armored": 3, "phantom": 2}
        base_health = health_map.get(kind, 1)
        self.health = base_health + difficulty
        self.phase = 0
        self.telegraph = 0
        self.projectile_timer = 0
        self.jump_timer = 0

    def update(self, player=None):
        self.projectile_timer = max(0, self.projectile_timer - 1)
        self.jump_timer = max(0, self.jump_timer - 1)
        if self.kind == "ambusher" and player is not None and abs(player.centerx - self.centerx) < 180:
            self.y += -2 if self.y > player.y else 2
        if self.kind == "phantom" and player is not None:
            # Phantom: erratic, jumpy enemy that teleports closer
            dist = abs(player.centerx - self.centerx)
            if dist < 400 and self.jump_timer == 0:
                self.jump_timer = 40 + self.difficulty * 10
                self.x = player.centerx + (60 if player.centerx > self.centerx else -60)
                self.y = player.centery - 40
            if dist > 100:
                self.x += (1 if player.centerx > self.centerx else -1) * self.speed * 1.5
            return
        if self.kind == "flyer":
            self.y += 1.5 * self.direction
            if self.y > self.start_y + 45 or self.y < self.start_y - 45:
                self.direction *= -1
            return
        if self.kind == "thrower":
            self.telegraph = 20 if self.projectile_timer == 0 and player is not None and abs(player.centerx - self.centerx) < 360 else max(0, self.telegraph - 1)
            if self.telegraph == 0:
                self.projectile_timer = max(20, 80 - self.difficulty * 10)  # Faster projectiles with difficulty
            return
        if self.kind == "charger" and player is not None and abs(player.centerx - self.centerx) < 260:
            self.x += (1 if player.centerx > self.centerx else -1) * self.speed * 2.2
            return
        if player is not None and abs(player.centerx - self.centerx) <= 120:
            if player.centerx < self.centerx:
                self.x -= self.speed
            elif player.centerx > self.centerx:
                self.x += self.speed
            return

        self.x += self.speed * self.direction
        if self.x >= self.start_x + self.move_range:
            self.x = self.start_x + self.move_range
            self.direction = -1
        elif self.x <= self.start_x:
            self.x = self.start_x
            self.direction = 1

    def draw(self, surface, camera_x=0):
        draw_rect = self.copy()
        draw_rect.x -= camera_x
        x, y, w, h = draw_rect.x, draw_rect.y, draw_rect.width, draw_rect.height

        palette = {
            "walker": {"body": (46, 150, 96), "armor": (24, 79, 52), "skin": (214, 240, 200), "eye": (24, 24, 24), "accent": (168, 97, 56)},
            "flyer": {"body": (117, 88, 183), "armor": (64, 46, 126), "skin": (224, 211, 240), "eye": (20, 18, 24), "accent": (170, 218, 255)},
            "charger": {"body": (211, 101, 53), "armor": (130, 62, 30), "skin": (248, 214, 180), "eye": (26, 20, 18), "accent": (70, 32, 25)},
            "thrower": {"body": (212, 169, 73), "armor": (119, 90, 26), "skin": (242, 218, 152), "eye": (18, 18, 18), "accent": (120, 66, 41)},
            "ambusher": {"body": (66, 160, 135), "armor": (27, 75, 67), "skin": (202, 222, 201), "eye": (20, 20, 20), "accent": (60, 80, 74)},
            "armored": {"body": (128, 134, 152), "armor": (72, 77, 97), "skin": (216, 220, 224), "eye": (18, 18, 18), "accent": (59, 82, 102)},
            "phantom": {"body": (147, 112, 219), "armor": (100, 65, 165), "skin": (220, 200, 255), "eye": (255, 100, 200), "accent": (255, 150, 255)},
        }
        colors = palette.get(self.kind, palette["walker"])

        # shadow under the character
        pygame.draw.ellipse(surface, (16, 20, 26), (x + 3, y + h - 4, w - 6, 6))

        # legs and body
        body_y = y + 6
        pygame.draw.rect(surface, colors["armor"], (x + 5, body_y + 8, w - 10, h - 12), border_radius=7)
        pygame.draw.rect(surface, colors["body"], (x + 7, body_y + 2, w - 14, h - 8), border_radius=8)

        # head / face
        head_center = (x + w // 2, y + 8)
        pygame.draw.circle(surface, colors["skin"], head_center, 9)
        pygame.draw.circle(surface, colors["armor"], head_center, 10, 2)

        # specific face variations
        if self.kind == "flyer":
            pygame.draw.polygon(surface, colors["armor"], [(x + 2, y + 3), (x - 4, y + 10), (x + 2, y + 15), (x + 7, y + 10)])
            pygame.draw.polygon(surface, colors["armor"], [(x + w - 2, y + 3), (x + w + 4, y + 10), (x + w - 2, y + 15), (x + w - 7, y + 10)])
            pygame.draw.circle(surface, colors["eye"], (x + 9, y + 8), 2)
            pygame.draw.circle(surface, colors["eye"], (x + w - 9, y + 8), 2)
            pygame.draw.rect(surface, colors["accent"], (x + 9, y + 12, w - 18, 2), border_radius=2)
        elif self.kind == "charger":
            pygame.draw.polygon(surface, colors["accent"], [(x + 4, y + 1), (x + 8, y - 5), (x + 12, y + 1)])
            pygame.draw.polygon(surface, colors["accent"], [(x + w - 4, y + 1), (x + w - 8, y - 5), (x + w - 12, y + 1)])
            pygame.draw.circle(surface, colors["eye"], (x + 8, y + 8), 2)
            pygame.draw.circle(surface, colors["eye"], (x + w - 8, y + 8), 2)
            pygame.draw.rect(surface, colors["accent"], (x + 4, y + 12, w - 8, 3), border_radius=2)
        elif self.kind == "thrower":
            pygame.draw.circle(surface, colors["accent"], (x + 7, y + 8), 2)
            pygame.draw.circle(surface, colors["accent"], (x + w - 7, y + 8), 2)
            pygame.draw.rect(surface, colors["armor"], (x + 11, y + 2, 2, 7))
            pygame.draw.rect(surface, colors["accent"], (x + 8, y + 13, w - 16, 2), border_radius=2)
            pygame.draw.line(surface, colors["armor"], (x + w - 3, y + 13), (x + w - 3, y + 3), 2)
        elif self.kind == "ambusher":
            pygame.draw.rect(surface, colors["armor"], (x + 6, y + 5, w - 12, 5), border_radius=2)
            pygame.draw.circle(surface, colors["eye"], (x + 8, y + 8), 2)
            pygame.draw.circle(surface, colors["eye"], (x + w - 8, y + 8), 2)
            pygame.draw.rect(surface, colors["accent"], (x + 10, y + 12, w - 20, 2), border_radius=2)
        elif self.kind == "armored":
            pygame.draw.rect(surface, colors["armor"], (x + 4, y + 4, w - 8, 4), border_radius=2)
            pygame.draw.circle(surface, colors["eye"], (x + 8, y + 8), 2)
            pygame.draw.circle(surface, colors["eye"], (x + w - 8, y + 8), 2)
            pygame.draw.rect(surface, colors["accent"], (x + 7, y + 12, w - 14, 2), border_radius=2)
            pygame.draw.rect(surface, (210, 220, 240), draw_rect, 2, border_radius=8)
        elif self.kind == "phantom":
            pygame.draw.circle(surface, colors["body"], (x + 6, y + 6), 5)
            pygame.draw.circle(surface, colors["body"], (x + w - 6, y + 6), 5)
            pygame.draw.circle(surface, colors["body"], (x + w // 2, y + h - 5), 6)
            pygame.draw.circle(surface, colors["eye"], (x + 8, y + 7), 2)
            pygame.draw.circle(surface, colors["eye"], (x + w - 8, y + 7), 2)
            pygame.draw.rect(surface, colors["accent"], (x + 7, y + 12, w - 14, 2), border_radius=2)
            if self.jump_timer > 20:
                pygame.draw.circle(surface, colors["accent"], draw_rect.center, 14, 1)
        else:
            pygame.draw.circle(surface, colors["eye"], (x + 8, y + 8), 2)
            pygame.draw.circle(surface, colors["eye"], (x + w - 8, y + 8), 2)
            pygame.draw.rect(surface, colors["accent"], (x + 7, y + 12, w - 14, 2), border_radius=2)

        # small weapon or device depending on enemy role
        if self.kind in {"walker", "charger", "armored"}:
            pygame.draw.rect(surface, colors["accent"], (x + w - 2, y + 10, 6, 2), border_radius=1)
        elif self.kind == "thrower":
            pygame.draw.rect(surface, colors["armor"], (x + w - 1, y + 10, 7, 2), border_radius=1)
            pygame.draw.line(surface, colors["accent"], (x + w + 5, y + 10), (x + w + 1, y + 6), 2)
        elif self.kind == "flyer":
            pygame.draw.circle(surface, colors["accent"], (x + w // 2, y + h - 3), 3)

        if self.telegraph:
            pygame.draw.circle(surface, (255, 90, 70), draw_rect.center, 18, 2)
        if self.difficulty > 0:
            pygame.draw.circle(surface, (255, 200, 50), draw_rect.center, 20 + self.difficulty * 2, 1)
