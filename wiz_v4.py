import pyxel
import random

# 向き（北、東、南、西）
DIRECTIONS = ['N', 'E', 'S', 'W']
DX = [0, 1, 0, -1]
DY = [-1, 0, 1, 0]
ARROWS = ['^', '>', 'v', '<']

class App:
    def __init__(self):
        pyxel.init(256, 256, title="Wizardry-like")
        self.floor = 0  # 0: 地上, -1: BF1, -2: BF2, ...
        self.player_x = 1
        self.player_y = 1
        self.player_dir = 0  # 0:北, 1:東, 2:南, 3:西
        self.in_town = True
        self.in_battle = False
        self.town_menu = 0  # 0: メイン, 1: 露天商, 2: ギルド, 3: 宿屋
        self.gold = 100
        self.inventory = []
        self.shop_items = ["剣", "盾", "回復薬"]
        self.dungeon_maps = {}  # 各階層ごとのマップ
        self.enemy = None
        self.battle_log = ""
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
        maze[height - 2][width - 2] = 3  # 地下へ進む階段
        maze[1][width - 2] = 2  # 地上に戻る階段
        return maze

    def load_floor(self):
        if self.floor not in self.dungeon_maps:
            self.dungeon_maps[self.floor] = self.generate_maze(16, 16)
        self.dungeon_map = self.dungeon_maps[self.floor]
        self.player_x, self.player_y = 1, 1

    def update(self):
        if self.in_town:
            self.update_town()
        elif self.in_battle:
            self.update_battle()
        else:
            self.update_dungeon()

    def update_town(self):
        if self.town_menu == 0:
            if pyxel.btnp(pyxel.KEY_1):
                self.town_menu = 1  # 露天商
            elif pyxel.btnp(pyxel.KEY_2):
                self.town_menu = 2  # ギルド
            elif pyxel.btnp(pyxel.KEY_3):
                self.town_menu = 3  # 宿屋
            elif pyxel.btnp(pyxel.KEY_RETURN):
                self.in_town = False
                self.floor = -1  # BF1から開始
                self.load_floor()
        elif self.town_menu == 1:
            if pyxel.btnp(pyxel.KEY_Q):
                self.town_menu = 0
            elif pyxel.btnp(pyxel.KEY_1):
                item = self.shop_items[0]
                self.buy_item(item)
            elif pyxel.btnp(pyxel.KEY_2):
                item = self.shop_items[1]
                self.buy_item(item)
            elif pyxel.btnp(pyxel.KEY_3):
                item = self.shop_items[2]
                self.buy_item(item)
        elif self.town_menu == 2:
            if pyxel.btnp(pyxel.KEY_Q):
                self.town_menu = 0
        elif self.town_menu == 3:
            if pyxel.btnp(pyxel.KEY_R):
                self.rest_inn()
            elif pyxel.btnp(pyxel.KEY_Q):
                self.town_menu = 0

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
            self.floor = 0  # 地上に戻る

        # ランダムエンカウント
        if random.randint(1, 20) == 1:
            self.start_battle()

    def start_battle(self):
        self.in_battle = True
        self.enemy = {"name": "スライム", "hp": 10}
        self.battle_log = "敵が現れた！"

    def update_battle(self):
        if pyxel.btnp(pyxel.KEY_1):  # 戦う
            damage = random.randint(2, 5)
            self.enemy["hp"] -= damage
            self.battle_log = f"敵に{damage}のダメージ！"
            if self.enemy["hp"] <= 0:
                self.battle_log = "敵を倒した！"
                self.in_battle = False
        elif pyxel.btnp(pyxel.KEY_2):  # 逃げる
            self.battle_log = "逃げ出した！"
            self.in_battle = False

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
        if current_tile == 2:  # 地上に戻る階段
            if self.floor == -1:
                self.in_town = True
                self.floor = 0
            else:
                self.floor += 1
                self.load_floor()
        elif current_tile == 3:  # 地下へ進む階段
            self.floor -= 1
            self.load_floor()

    def buy_item(self, item):
        cost = 30
        if self.gold >= cost:
            self.gold -= cost
            self.inventory.append(item)
        else:
            print("お金が足りません！")

    def rest_inn(self):
        cost = 10
        if self.gold >= cost:
            self.gold -= cost
            print("HPが回復しました！")
        else:
            print("お金が足りません！")

    def draw(self):
        pyxel.cls(0)
        if self.in_town:
            self.draw_town()
        elif self.in_battle:
            self.draw_battle()
        else:
            self.draw_dungeon()

    def draw_town(self):
        pyxel.text(40, 20, "-- Town --", 7)
        pyxel.text(20, 40, "1. 露天商", 7)
        pyxel.text(20, 50, "2. ギルド", 7)
        pyxel.text(20, 60, "3. 宿屋", 7)
        pyxel.text(20, 80, "ダンジョンへ (Enter)", 7)
        pyxel.text(5, 240, f"Gold: {self.gold}", 7)

    def draw_dungeon(self):
        tile_size = 16
        for y, row in enumerate(self.dungeon_map):
            for x, cell in enumerate(row):
                color = 0
                if cell == 1:
                    color = 5  # 壁
                elif cell == 0:
                    color = 0  # 通路
                elif cell == 2:
                    color = 11  # 地上に戻る階段
                elif cell == 3:
                    color = 8  # 地下へ進む階段
                pyxel.rect(x * tile_size, y * tile_size, tile_size, tile_size, color)
        # プレイヤー描画
        px = self.player_x * tile_size + tile_size // 4
        py = self.player_y * tile_size + tile_size // 4
        pyxel.text(px, py, ARROWS[self.player_dir], 9)

        pyxel.text(5, 240, f"Floor: {'Ground' if self.floor == 0 else 'BF' + str(abs(self.floor))}", 7)
        pyxel.text(100, 240, f"Gold: {self.gold}", 7)

    def draw_battle(self):
        pyxel.text(100, 50, f"{self.enemy['name']}", 8)  # 敵表示
        pyxel.text(10, 200, f"敵HP: {self.enemy['hp']}", 7)  # ステータス
        pyxel.text(10, 10, f"{self.battle_log}", 7)  # 行動ログ
        pyxel.text(10, 220, "1. 戦う", 7)
        pyxel.text(10, 230, "2. 逃げる", 7)

App()
