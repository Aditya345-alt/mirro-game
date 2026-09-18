class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.velocity_y = 0
        self.is_jumping = False
        self.state = "IDLE"
        self.skill_cooldown = 0
        
    def update(self, gravity, keys):
        # 1. Apply Gravity
        self.velocity_y += gravity
        self.y += self.velocity_y
        
        # 2. Manage Skill Cooldowns
        if self.skill_cooldown > 0:
            self.skill_cooldown -= 1
            
        # 3. Handle Input & States
        if keys['ATTACK'] and self.skill_cooldown == 0:
            self.state = "ATTACKING"
            self.execute_combat_skill()
        elif keys['JUMP'] and not self.is_jumping:
            self.velocity_y = -15
            self.is_jumping = True
            self.state = "JUMPING"
            
    def execute_combat_skill(self):
        # Spawn hitbox, apply damage to overlapping enemies
        print("Skill activated! 50 damage dealt.")
        self.skill_cooldown = 60 # 60 frames (1 second at 60fps)