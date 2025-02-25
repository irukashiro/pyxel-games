import pyxel
import random

# 向き（北、東、南、西）
DIRECTIONS = ['N', 'E', 'S', 'W']
DX = [0, 1, 0, -1]
DY = [-1, 0, 1, 0]
ARROWS = ['^', '>', 'v', '<']

class Enemy:
    def __init__(self, x, y, hp, speed, gold):
        self.x = x
        self.y = y
        self.hp = hp
        self.speed = speed
        self.gold = gold

class App:
    def __init__(self):
        pyxel.init(256, 256, title="Wizardry-like")
        self.floor = 0
        self.player_x = 1
        self.player_y = 1
        self.player_dir = 0
        self.in_town = True
        self.in_battle = False
        self.show_menu = False
        self.town_menu = 0
        self.gold = 100
        self.player_hp = 100
        self.player_max_hp = 100
        self.player_speed = 5
        self.inventory = []
        self.shop_items = ["Potion", "Fireball Scroll"]
        self.dungeon_maps = {}
        self.enemies = []
        self.current_enemy = None
        self.battle_command = 0
        self.battle_log = ""
        self.battle_turn = "player"
        self.battle_state = "player_action"
        self.menu_selection = 0
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
        self.enemies = [Enemy(random.randint(2, 14), random.randint(2, 14), 30, random.randint(1, 10), random.randint(10, 50)) for _ in range(3)]

    def update(self):
        if pyxel.btnp(pyxel.KEY_TAB):
            self.show_menu = not self.show_menu

        if self.show_menu:
            self.update_menu()
        elif self.in_battle:
            self.update_battle()
        elif self.in_town:
            self.update_town()
        else:
            self.update_dungeon()

    def update_menu(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.menu_selection = (self.menu_selection - 1) % len(self.inventory)
        elif pyxel.btnp(pyxel.KEY_DOWN):
            self.menu_selection = (self.menu_selection + 1) % len(self.inventory)
        elif pyxel.btnp(pyxel.KEY_RETURN) and self.inventory:
            item = self.inventory.pop(self.menu_selection)
            if item == "Potion":
                self.player_hp = min(self.player_hp + 20, self.player_max_hp)

    def update_town(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.town_menu = (self.town_menu - 1) % 3
        elif pyxel.btnp(pyxel.KEY_DOWN):
            self.town_menu = (self.town_menu + 1) % 3
        elif pyxel.btnp(pyxel.KEY_RETURN):
            if self.town_menu == 0:  # 宿屋
                if self.gold >= 30:
                    self.gold -= 30
                    self.player_hp = self.player_max_hp
            elif self.town_menu == 1:  # 露天商
                self.update_shop()
            elif self.town_menu == 2:  # ダンジョン
                self.in_town = False
                self.floor = -1
                self.load_floor()

    def update_shop(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.menu_selection = (self.menu_selection - 1) % len(self.shop_items)
        elif pyxel.btnp(pyxel.KEY_DOWN):
            self.menu_selection = (self.menu_selection + 1) % len(self.shop_items)
        elif pyxel.btnp(pyxel.KEY_RETURN):
            item = self.shop_items[self.menu_selection]
            cost = 10 if item == "Potion" else 20
            if self.gold >= cost:
                self.gold -= cost
                self.inventory.append(item)

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
                self.battle_log = "Battle Start!"
                self.battle_turn = "player"
                self.battle_state = "player_action"
                break

    def update_battle(self):
        if self.battle_state == "player_action":
            if pyxel.btnp(pyxel.KEY_UP):
                self.battle_command = (self.battle_command - 1) % 3
            elif pyxel.btnp(pyxel.KEY_DOWN):
                self.battle_command = (self.battle_command + 1) % 3
            elif pyxel.btnp(pyxel.KEY_RETURN):
                if self.battle_command == 0:  # Attack
                    damage = random.randint(5, 15)
                    self.current_enemy.hp -= damage
                    self.battle_log = f"Attacked! {damage} damage!"
                    self.battle_state = "player_log"
                elif self.battle_command == 1:  # Use Item
                    if self.inventory:
                        item = self.inventory.pop(self.menu_selection)
                        if item == "Potion":
                            self.player_hp = min(self.player_hp + 20, self.player_max_hp)
                            self.battle_log = "Used Potion! HP restored!"
                        elif item == "Fireball Scroll":
                            damage = random.randint(20, 30)
                            self.current_enemy.hp -= damage
                            self.battle_log = f"Used Fireball! {damage} damage!"
                        self.battle_state = "player_log"
                elif self.battle_command == 2:  # Run
                    self.battle_log = "Escaped!"
                    self.enemies.remove(self.current_enemy)
                    self.in_battle = False

        elif self.battle_state == "player_log":
            if pyxel.btnp(pyxel.KEY_RETURN):
                if self.current_enemy.hp <= 0:
                    self.battle_log = "Enemy defeated!"
                    self.gold += self.current_enemy.gold
                    self.enemies.remove(self.current_enemy)
                    self.in_battle = False
                else:
                    self.battle_state = "enemy_log"
                    self.enemy_turn()

        elif self.battle_state == "enemy_log":
            if pyxel.btnp(pyxel.KEY_RETURN):
                if self.player_hp <= 0:
                    self.battle_log = "You were defeated..."
                    pyxel.quit()
                else:
                    self.battle_state = "player_action"

    def enemy_turn(self):
        damage = random.randint(5, 15)
        self.player_hp -= damage
        self.battle_log = f"Enemy attacks! {damage} damage received!"

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
        if self.show_menu:
            self.draw_menu()
        elif self.in_battle:
            self.draw_battle()
        elif self.in_town:
            self.draw_town()
        else:
            self.draw_dungeon()

    def draw_menu(self):
        pyxel.rect(10, 10, 236, 236, 1)
        pyxel.text(20, 20, "-- Menu --", 7)
        pyxel.text(20, 40, f"HP: {self.player_hp}/{self.player_max_hp}", 7)
        
        # HPバー追加
        player_hp_ratio = max(self.player_hp / self.player_max_hp, 0)
        pyxel.rect(20, 50, 100, 5, 8)  # 背景（赤）
        pyxel.rect(20, 50, int(100 * player_hp_ratio), 5, 11)  # HP（緑）
        
        pyxel.text(20, 70, f"Gold: {self.gold}", 7)
        pyxel.text(20, 90, "Inventory:", 7)
        for i, item in enumerate(self.inventory):
            prefix = "> " if i == self.menu_selection else "  "
            pyxel.text(40, 110 + i * 10, prefix + item, 7)

    def draw_town(self):
        options = ["Inn", "Shop", "Dungeon"]
        pyxel.text(40, 20, "-- Town --", 7)
        for i, option in enumerate(options):
            prefix = "> " if i == self.town_menu else "  "
            pyxel.text(20, 80 + i * 20, prefix + option, 7)
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
        pyxel.rect(10, 10, 236, 60, 1)
        pyxel.rectb(10, 10, 236, 60, 7)
        pyxel.text(100, 30, f"Enemy: {self.current_enemy.__class__.__name__}", 7)
        
        # 敵のHPバー
        enemy_hp_ratio = max(self.current_enemy.hp / 30, 0)  # HP最大値30と仮定
        pyxel.rect(100, 40, 100, 5, 8)  # 背景（赤）
        pyxel.rect(100, 40, int(100 * enemy_hp_ratio), 5, 11)  # HP（緑）
        
        pyxel.rect(10, 80, 120, 40, 1)
        pyxel.rectb(10, 80, 120, 40, 7)
        pyxel.text(20, 90, f"HP: {self.player_hp}/{self.player_max_hp}", 7)
        
        # プレイヤーのHPバー
        player_hp_ratio = max(self.player_hp / self.player_max_hp, 0)
        pyxel.rect(20, 100, 100, 5, 8)  # 背景（赤）
        pyxel.rect(20, 100, int(100 * player_hp_ratio), 5, 11)  # HP（緑）
        
        pyxel.rect(10, 130, 236, 40, 1)
        pyxel.rectb(10, 130, 236, 40, 7)
        pyxel.text(20, 140, self.battle_log, 7)
        
        if self.battle_state == "player_action":
            pyxel.rect(140, 80, 106, 60, 1)
            pyxel.rectb(140, 80, 106, 60, 7)
            commands = ["Attack", "Use Item", "Run"]
            pyxel.text(150, 70, "Commands:", 7)
            for i, cmd in enumerate(commands):
                prefix = "> " if i == self.battle_command else "  "
                pyxel.text(150, 90 + i * 10, prefix + cmd, 7)

App()
