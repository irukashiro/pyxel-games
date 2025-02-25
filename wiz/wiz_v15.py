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
        self.in_guild = False  # ギルドウィンドウを開いているか
        self.guild_selection = 0  # ギルドメニューのカーソル位置
        self.current_quest = None  # 現在受注している依頼
        self.quest_progress = 0  # 依頼の進行度
        self.available_quests = []  # 受注可能な依頼
        self.generate_guild_quests()  # 初期依頼生成
        self.in_guild_quest = False  # 依頼選択ウィンドウが開いているか
        self.guild_quest_selection = 0  # 依頼選択のカーソル位置

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
                    maze[ny - dy // 2][nx - dx // 2] = 0
                    maze[ny][nx] = 0
                    carve(nx, ny)

        maze[1][1] = 0  # スタート地点
        carve(1, 1)
        maze[height - 2][width - 2] = 3  # 下層への階段
        maze[1][width - 2] = 2  # 地上への階段
        return maze


    def generate_guild_quests(self):
        self.available_quests = []
        
        # 敵撃破依頼を追加
        target_enemy = random.choice(["Goblin", "Skeleton", "Orc"])
        enemy_kill_count = random.randint(1, 3)
        enemy_kill_quest = {
            "type": "enemy_kill",
            "target": target_enemy,
            "count": enemy_kill_count,
            "reward": random.randint(30, 100),
            "description": f"Defeat {target_enemy} x {enemy_kill_count}"
        }
        self.available_quests.append(enemy_kill_quest)

        # 宝箱回収依頼を追加
        chest_count = random.randint(1, 3)  # 先に値を取得
        chest_collect_quest = {
            "type": "chest_collect",
            "count": chest_count,
            "reward": random.randint(20, 80),
            "description": f"Open {chest_count} treasure chests"  # ここで参照
        }
        self.available_quests.append(chest_collect_quest)



    def load_floor(self):
        if self.floor not in self.dungeon_maps:
            self.dungeon_maps[self.floor] = self.generate_maze(16, 16)
        self.dungeon_map = self.dungeon_maps[self.floor]
        self.player_x, self.player_y = 1, 1
        self.enemies = [Enemy(random.randint(2, 14), random.randint(2, 14), 30, random.randint(1, 10), random.randint(10, 50)) for _ in range(3)]

        # 宝箱の配置
        self.chests = [(random.randint(2, 14), random.randint(2, 14)) for _ in range(2)]
        self.trapped_chests = {chest: random.choice([None, "alarm", "bomb"]) for chest in self.chests}  # 罠の種類設定
        self.chest_log = ""
        self.chest_opened = False
        self.chest_state = None
        self.chest_selection = 0
    

    def update(self):
        if self.in_guild:
            self.update_guild()
        elif self.chest_opened and pyxel.btnp(pyxel.KEY_RETURN):
            self.chest_log = ""
            self.chest_opened = False
        elif self.chest_state:
            self.update_chest()
        else:
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
            self.town_menu = (self.town_menu - 1) % 4  # ギルドを追加したので 4 つに変更
        elif pyxel.btnp(pyxel.KEY_DOWN):
            self.town_menu = (self.town_menu + 1) % 4
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
            elif self.town_menu == 3:  # ギルド
                self.in_guild = True  # ギルドウィンドウを開く


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

    def update_guild(self):
        if self.in_guild_quest:
            self.update_guild_quest()  # 依頼選択モード
            return
        
        if pyxel.btnp(pyxel.KEY_UP):
            self.guild_selection = (self.guild_selection - 1) % 3
        elif pyxel.btnp(pyxel.KEY_DOWN):
            self.guild_selection = (self.guild_selection + 1) % 3
        elif pyxel.btnp(pyxel.KEY_RETURN):
            if self.guild_selection == 0:  # 依頼
                self.in_guild_quest = True  # 依頼選択ウィンドウを開く
                self.guild_quest_selection = 0  # カーソルをリセット
            elif self.guild_selection == 1:  # 報告
                if self.current_quest:
                    if (self.current_quest["type"] == "enemy_kill" and self.quest_progress >= self.current_quest["count"]) or \
                    (self.current_quest["type"] == "chest_collect" and self.quest_progress >= self.current_quest["count"]):
                        self.gold += self.current_quest["reward"]
                        self.current_quest = None
                        self.generate_guild_quests()  # 新しい依頼を生成
                    else:
                        self.current_quest = None  # 失敗
            elif self.guild_selection == 2:  # 街に戻る
                self.in_guild = False  # ギルドを閉じる

        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.in_guild = False  # ギルドを閉じる

    def update_guild_quest(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.guild_quest_selection = (self.guild_quest_selection - 1) % (len(self.available_quests) + 1)
        elif pyxel.btnp(pyxel.KEY_DOWN):
            self.guild_quest_selection = (self.guild_quest_selection + 1) % (len(self.available_quests) + 1)
        elif pyxel.btnp(pyxel.KEY_RETURN):
            if self.guild_quest_selection < len(self.available_quests):  # 依頼を受注
                if self.current_quest is None:
                    self.current_quest = self.available_quests.pop(self.guild_quest_selection)
                    self.quest_progress = 0
                self.in_guild_quest = False  # ギルドウィンドウへ戻る
            else:  # 「やめる」を選択した場合
                self.in_guild_quest = False  # ギルドウィンドウへ戻る

        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.in_guild_quest = False  # ギルドウィンドウへ戻る


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
        # 敵を倒したときに依頼を進める
        if self.in_battle and self.battle_state == "player_log" and self.current_enemy and self.current_enemy.hp <= 0:
            if self.current_quest and self.current_quest["type"] == "enemy_kill":
                if self.current_enemy.__class__.__name__ == self.current_quest["target"]:
                    self.quest_progress += 1  # 討伐数カウント
        # 宝箱を開けたときに依頼を進める
        if self.chest_state == "result":
            if self.current_quest and self.current_quest["type"] == "chest_collect":
                self.quest_progress += 1  # 宝箱回収数カウント


    def update_chest(self):
        if self.chest_state == "selection":
            if pyxel.btnp(pyxel.KEY_UP):
                self.chest_selection = (self.chest_selection - 1) % 3
            elif pyxel.btnp(pyxel.KEY_DOWN):
                self.chest_selection = (self.chest_selection + 1) % 3
            elif pyxel.btnp(pyxel.KEY_RETURN):
                if self.chest_selection == 0:  # 「開ける」
                    trap = self.trapped_chests.get((self.player_x, self.player_y))
                    if trap == "alarm":
                        self.chest_log = "Alarm! Enemy appears!"
                        # ランダムな敵を生成
                        new_enemy = Enemy(self.player_x, self.player_y, 30, random.randint(1, 10), random.randint(10, 50))
                        self.enemies.append(new_enemy)  # リストに追加
                        self.current_enemy = new_enemy  # 戦闘対象に設定
                        self.in_battle = True  # 戦闘開始
                    elif trap == "bomb":
                        damage = random.randint(10, 30)
                        self.player_hp -= damage
                        self.chest_log = f"Bomb! Took {damage} damage!"
                    else:
                        self.chest_log = "The chest was safe!"
                        # アイテムorゴールド取得
                        if random.random() < 0.5:
                            item = random.choice(["Potion", "Fireball Scroll"])
                            self.inventory.append(item)
                            self.chest_log = f"Found {item}!"
                        else:
                            gold_found = random.randint(10, 50)
                            self.gold += gold_found
                            self.chest_log = f"Found {gold_found} Gold!"
                    
                    self.chests = [(cx, cy) for cx, cy in self.chests if (cx, cy) != (self.player_x, self.player_y)]
                    self.chest_state = "result"


                elif self.chest_selection == 1:  # 「調べる」
                    trap = self.trapped_chests.get((self.player_x, self.player_y))
                    self.chest_log = "No traps found!" if not trap else "A trap might be here..."
                    self.chest_state = "inspect"

                elif self.chest_selection == 2:  # 「やめる」
                    self.chest_state = None  # ウィンドウを閉じる

        elif self.chest_state in ["result", "inspect"]:
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.chest_state = None  # ログを閉じる


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
                        self.battle_state = "item_selection"
                        self.menu_selection = 0  # アイテム選択開始
                elif self.battle_command == 2:  # Run
                    self.battle_log = "Escaped!"
                    self.enemies.remove(self.current_enemy)
                    self.in_battle = False

        elif self.battle_state == "item_selection":
            if pyxel.btnp(pyxel.KEY_UP):
                self.menu_selection = (self.menu_selection - 1) % len(self.inventory)
            elif pyxel.btnp(pyxel.KEY_DOWN):
                self.menu_selection = (self.menu_selection + 1) % len(self.inventory)
            elif pyxel.btnp(pyxel.KEY_RETURN):
                item = self.inventory.pop(self.menu_selection)
                if item == "Potion":
                    self.player_hp = min(self.player_hp + 20, self.player_max_hp)
                    self.battle_log = "Used Potion! HP restored!"
                elif item == "Fireball Scroll":
                    damage = random.randint(20, 30)
                    self.current_enemy.hp -= damage
                    self.battle_log = f"Used Fireball! {damage} damage!"
                self.battle_state = "player_log"
            elif pyxel.btnp(pyxel.KEY_ESCAPE):
                self.battle_state = "player_action"

        elif self.battle_state == "player_log":
            if pyxel.btnp(pyxel.KEY_RETURN):
                if self.current_enemy.hp <= 0:
                    self.battle_log = "Enemy defeated!"
                    self.gold += self.current_enemy.gold
                    # current_enemy が enemies 内に存在する場合のみ削除
                    if self.current_enemy in self.enemies:
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

        # 宝箱コマンドウィンドウを開く（即座に罠やアイテム取得をしない）
        for cx, cy in self.chests:
            if (self.player_x, self.player_y) == (cx, cy):
                self.chest_state = "selection"  # ウィンドウを開く
                self.chest_selection = 0  # カーソルをリセット
                return  # 他の処理をしない


    def draw(self):
        pyxel.cls(0)
        if self.show_menu:
            self.draw_menu()
        elif self.in_battle:
            self.draw_battle()
        elif self.in_guild:  # ギルドウィンドウの表示
            self.draw_guild()
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
        options = ["Inn", "Shop", "Dungeon", "Guild"]
        pyxel.text(40, 20, "-- Town --", 7)
        for i, option in enumerate(options):
            prefix = "> " if i == self.town_menu else "  "
            pyxel.text(20, 80 + i * 20, prefix + option, 7)
        pyxel.text(5, 240, f"Gold: {self.gold}", 7)

    def draw_guild(self):
        if self.in_guild_quest:
            self.draw_guild_quest()
            return

        pyxel.rect(40, 60, 180, 100, 1)  # 背景
        pyxel.rectb(40, 60, 180, 100, 7)  # 枠
        pyxel.text(50, 70, "-- Guild --", 7)

        options = ["Accept Quest", "Report Quest", "Return to Town"]
        for i, option in enumerate(options):
            prefix = "> " if i == self.guild_selection else "  "
            pyxel.text(60, 90 + i * 10, prefix + option, 7)
        
        if self.current_quest:
            pyxel.text(50, 140, f"Current Quest:", 7)
            pyxel.text(50, 150, self.current_quest["description"], 7)
            pyxel.text(50, 160, f"Progress: {self.quest_progress}/{self.current_quest['count']}", 7)

    def draw_guild_quest(self):
        pyxel.rect(40, 60, 180, 100, 1)  # 背景
        pyxel.rectb(40, 60, 180, 100, 7)  # 枠
        pyxel.text(50, 70, "-- Select Quest --", 7)

        for i, quest in enumerate(self.available_quests):
            prefix = "> " if i == self.guild_quest_selection else "  "
            pyxel.text(60, 90 + i * 10, prefix + quest["description"], 7)

        # 「やめる」の選択肢を追加
        prefix = "> " if self.guild_quest_selection == len(self.available_quests) else "  "
        pyxel.text(60, 90 + len(self.available_quests) * 10, prefix + "Cancel", 7)


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
        
        # 敵の描画
        for enemy in self.enemies:
            pyxel.rect(enemy.x * tile_size + 4, enemy.y * tile_size + 4, 8, 8, 8)

        # 宝箱の描画
        for cx, cy in self.chests:
            pyxel.rect(cx * tile_size + 4, cy * tile_size + 4, 8, 8, 10)

        # プレイヤーの描画
        px = self.player_x * tile_size + tile_size // 4
        py = self.player_y * tile_size + tile_size // 4
        pyxel.text(px, py, ARROWS[self.player_dir], 9)

        pyxel.text(5, 240, f"Floor: {'Ground' if self.floor == 0 else 'BF' + str(abs(self.floor))}", 7)
        pyxel.text(100, 240, f"Gold: {self.gold}", 7)

        # 宝箱のウィンドウ表示
        if self.chest_state:
            pyxel.rect(40, 80, 180, 60, 1)
            pyxel.rectb(40, 80, 180, 60, 7)
            if self.chest_state == "selection":
                pyxel.text(50, 90, "Open the chest?", 7)
                options = ["Open", "Inspect", "Cancel"]
                for i, option in enumerate(options):
                    prefix = "> " if i == self.chest_selection else "  "
                    pyxel.text(60, 110 + i * 10, prefix + option, 7)
            else:
                pyxel.text(50, 100, self.chest_log, 7)

    def draw_battle(self):
        pyxel.text(40, 20, "-- Battle --", 7)
        pyxel.rect(10, 10, 236, 60, 1)
        pyxel.rectb(10, 10, 236, 60, 7)
        pyxel.text(100, 30, f"Enemy: {self.current_enemy.__class__.__name__}", 7)
        

        pyxel.rect(10, 80, 120, 40, 1)
        pyxel.rectb(10, 80, 120, 40, 7)
        pyxel.text(20, 90, f"HP: {self.player_hp}/{self.player_max_hp}", 7)
        
        if self.battle_state == "player_action":
            pyxel.rect(140, 80, 106, 60, 1)
            pyxel.rectb(140, 80, 106, 60, 7)
            commands = ["Attack", "Use Item", "Run"]
            pyxel.text(150, 70, "Commands:", 7)
            for i, cmd in enumerate(commands):
                prefix = "> " if i == self.battle_command else "  "
                pyxel.text(150, 90 + i * 10, prefix + cmd, 7)

        
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

        if self.battle_state == "item_selection":
            pyxel.rect(50, 50, 160, 100, 1)
            pyxel.rectb(50, 50, 160, 100, 7)
            pyxel.text(60, 60, "Select Item:", 7)
            for i, item in enumerate(self.inventory):
                prefix = "> " if i == self.menu_selection else "  "
                pyxel.text(70, 80 + i * 10, prefix + item, 7)
        
App()
