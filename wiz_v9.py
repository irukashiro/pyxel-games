import pyxel
import random

# Directions (North, East, South, West)
DIRECTIONS = ['N', 'E', 'S', 'W']
DX = [0, 1, 0, -1]
DY = [-1, 0, 1, 0]
ARROWS = ['^', '>', 'v', '<']

class Enemy:
    def __init__(self, x, y, hp, speed):
        self.x = x
        self.y = y
        self.hp = hp
        self.speed = speed

class App:
    def __init__(self):
        pyxel.init(256, 256, title="Wizardry-like")
        self.font = pyxel  # Using Pyxel's default font
        self.floor = 0
        self.player_x = 1
        self.player_y = 1
        self.player_dir = 0
        self.in_town = True
        self.in_battle = False
        self.town_menu = 0
        self.gold = 100
        self.player_hp = 100
        self.player_speed = 5
        self.inventory = []
        self.shop_items = ["Sword", "Shield", "Healing Potion"]
        self.dungeon_maps = {}
        self.enemies = []
        self.current_enemy = None
        self.battle_command = 0
        self.battle_log = ""
        self.battle_turn = "player"
        self.battle_state = "player_action"
        self.load_floor()
        pyxel.run(self.update, self.draw)

    def generate_maze(self, width, height):
        maze = [[1 for _ in range(width)] for _ in range(height)]
        def carve(x, y):
            dirs = [(0, -2), (2, 0), (0, 2), (-2, 0)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 < nx < width and 0 < ny < height and maze[ny][nx] == 1:
                    maze[ny - dy//2][nx - dx//2] = 0
                    maze[ny][nx] = 0
                    carve(nx, ny)
        maze[1][1] = 0
        carve(1, 1)
        maze[height - 2][width - 2] = 3
        maze[1][width - 2] = 2
        return maze

    def load_floor(self):
        if self.floor not in self.dungeon_maps:
            self.dungeon_maps[self.floor] = self.generate_maze(16, 16)
        self.dungeon_map = self.dungeon_maps[self.floor]
        self.player_x, self.player_y = 1, 1
        self.enemies = [Enemy(random.randint(2, 14), random.randint(2, 14), 30, random.randint(1, 10)) for _ in range(3)]

    def update(self):
        if self.in_battle:
            self.update_battle()
        elif self.in_town:
            self.update_town()
        else:
            self.update_dungeon()

    def update_town(self):
        if self.town_menu == 0:
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.in_town = False
                self.floor = -1
                self.load_floor()

    def update_dungeon(self):
        if pyxel.btnp(pyxel.KEY_W):
            self.move(1)
        elif pyxel.btnp(pyxel.KEY_S):
            self.move(-1)
        elif pyxel.btnp(pyxel.KEY_A):
            self.turn(-1)
        elif pyxel.btnp(pyxel.KEY_D):
            self.turn(1)
        elif pyxel.btnp(pyxel.KEY_SPACE):
            self.use_tile()
        elif pyxel.btnp(pyxel.KEY_ESCAPE):
            self.in_town = True
            self.floor = 0

        for enemy in self.enemies:
            if self.player_x == enemy.x and self.player_y == enemy.y:
                self.current_enemy = enemy
                self.in_battle = True
                self.battle_log = "Battle start!"
                self.battle_turn = "player"
                self.battle_state = "player_action"
                break

    def update_battle(self):
        if self.battle_state == "player_action":
            if pyxel.btnp(pyxel.KEY_UP):
                self.battle_command = (self.battle_command - 1) % 2
            elif pyxel.btnp(pyxel.KEY_DOWN):
                self.battle_command = (self.battle_command + 1) % 2
            elif pyxel.btnp(pyxel.KEY_RETURN):
                if self.battle_command == 0:
                    damage = random.randint(5, 15)
                    self.current_enemy.hp -= damage
                    self.battle_log = f"Attacked! {damage} damage dealt!"
                    self.battle_state = "player_log"
                elif self.battle_command == 1:
                    self.battle_log = "Ran away!"
                    self.enemies.remove(self.current_enemy)
                    self.in_battle = False

        elif self.battle_state == "player_log":
            if pyxel.btnp(pyxel.KEY_RETURN):
                if self.current_enemy.hp <= 0:
                    self.battle_log = "Enemy defeated!"
                    self.enemies.remove(self.current_enemy)
                    self.in_battle = False
                else:
                    self.battle_state = "enemy_log"
                    self.enemy_turn()

        elif self.battle_state == "enemy_log":
            if pyxel.btnp(pyxel.KEY_RETURN):
                if self.player_hp <= 0:
                    self.battle_log = "You have fallen..."
                    pyxel.quit()
                else:
                    self.battle_state = "player_action"

    def enemy_turn(self):
        damage = random.randint(5, 15)
        self.player_hp -= damage
        self.battle_log = f"Enemy attack! {damage} damage taken!"

    def move(self, direction):
        nx = self.player_x + DX[self.player_dir] * direction
        ny = self.player_y + DY[self.player_dir] * direction
        if 0 <= nx < 16 and 0 <= ny < 16:
            if self.dungeon_map[ny][nx] != 1:
                self.player_x = nx
                self.player_y = ny

    def turn(self, direction):
        self.player_dir = (self.player_dir + direction) % 4

    def use_tile(self):
        current_tile = self.dungeon_map[self.player_y][self.player_x]
        if current_tile == 2:
            if self.floor == -1:
                self.in_town = True
                self.floor = 0
            else:
                self.floor += 1
                self.load_floor()
        elif current_tile == 3:
            self.floor -= 1
            self.load_floor()

    def draw(self):
        pyxel.cls(0)
        if self.in_battle:
            self.draw_battle()
        elif self.in_town:
            self.draw_town()
        else:
            self.draw_dungeon()

    def draw_town(self):
        self.font.text(40, 20, "-- Town --", 7)
        self.font.text(20, 80, "Go to Dungeon (Enter)", 7)
        self.font.text(5, 240, f"Gold: {self.gold}", 7)

    def draw_dungeon(self):
        tile_size = 16
        for y, row in enumerate(self.dungeon_map):
            for x, cell in enumerate(row):
                color = 0
                if cell == 1:
                    color = 5
                elif cell == 0:
                    color = 0
                elif cell == 2:
                    color = 11
                elif cell == 3:
                    color = 8
                pyxel.rect(x * tile_size, y * tile_size, tile_size, tile_size, color)
        for enemy in self.enemies:
            pyxel.rect(enemy.x * tile_size + 4, enemy.y * tile_size + 4, 8, 8, 8)
        px = self.player_x * tile_size + tile_size // 4
        py = self.player_y * tile_size + tile_size // 4
        self.font.text(px, py, ARROWS[self.player_dir], 9)
        self.font.text(5, 240, f"Floor: {'Surface' if self.floor == 0 else 'BF' + str(abs(self.floor))}", 7)
        self.font.text(100, 240, f"Gold: {self.gold}", 7)

    def draw_battle(self):
        self.font.text(40, 20, "-- Battle --", 7)
        pyxel.rect(10, 10, 236, 60, 1)
        pyxel.rectb(10, 10, 236, 60, 7)
        self.font.text(100, 30, "Enemy", 7)

        pyxel.rect(10, 80, 120, 40, 1)
        pyxel.rectb(10, 80, 120, 40, 7)
        self.font.text(20, 90, f"HP: {self.player_hp}", 7)

        pyxel.rect(10, 130, 236, 40, 1)
        pyxel.rectb(10, 130, 236, 40, 7)
        self.font.text(20, 140, self.battle_log, 7)

        if self.battle_state == "player_action":
            pyxel.rect(140, 80, 106, 40, 1)
            pyxel.rectb(140, 80, 106, 40, 7)
            commands = ["Attack", "Run"]
            self.font.text(150, 70, "Command:", 7)
            for i, cmd in enumerate(commands):
                prefix = "> " if i == self.battle_command else "  "
                self.font.text(150, 90 + i * 10, prefix + cmd, 7)

App()
