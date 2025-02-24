import pyxel
import random

# 向き（北、東、南、西）
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
        self.shop_items = ["剣", "盾", "回復薬"]
        self.dungeon_maps = {}
        self.enemies = []
        self.current_enemy = None
        self.battle_command = 0
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
                break

    def update_battle(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.battle_command = (self.battle_command - 1) % 2
        elif pyxel.btnp(pyxel.KEY_DOWN):
            self.battle_command = (self.battle_command + 1) % 2
        elif pyxel.btnp(pyxel.KEY_RETURN):
            if self.battle_command == 0:  # 戦う
                self.current_enemy.hp -= 10
                if self.current_enemy.hp <= 0:
                    self.enemies.remove(self.current_enemy)
                    self.in_battle = False
            elif self.battle_command == 1:  # 逃げる
                self.in_battle = False

        if self.player_hp <= 0:
            print("ゲームオーバー")
            pyxel.quit()

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
        pyxel.text(40, 20, "-- Town --", 7)
        pyxel.text(20, 80, "ダンジョンへ (Enter)", 7)
        pyxel.text(5, 240, f"Gold: {self.gold}", 7)

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
        pyxel.text(px, py, ARROWS[self.player_dir], 9)
        pyxel.text(5, 240, f"Floor: {'Ground' if self.floor == 0 else 'BF' + str(abs(self.floor))}", 7)
        pyxel.text(100, 240, f"Gold: {self.gold}", 7)

    def draw_battle(self):
        pyxel.text(40, 20, "-- Battle --", 7)
        pyxel.text(100, 80, "Enemy", 8)
        pyxel.text(20, 180, f"HP: {self.player_hp}", 7)
        commands = ["戦う", "逃げる"]
        for i, cmd in enumerate(commands):
            color = 7 if i == self.battle_command else 5
            pyxel.text(180, 150 + i * 10, cmd, color)

App()
