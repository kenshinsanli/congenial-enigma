import traceback
import sys

# 【防閃退安全網】啟動錯誤攔截
try:
    from ursina import *
    from ursina.prefabs.first_person_controller import FirstPersonController
    import random

    # 初始化應用
    app = Ursina()

    # ==========================================
    # 0. 全局變數與設定
    # ==========================================
    window.title = "MCR Arena: v2.9 UI Fixed"
    window.borderless = False
    window.exit_button.visible = False
    window.fps_counter.enabled = True

    game_state = "menu" # menu, playing, game_over
    enemies = []
    minimap_dots = []
    score = 0
    high_score = 0

    # 讀取最高分
    try:
        with open("highscore.txt", "r") as f:
            content = f.read()
            if content:
                high_score = int(content)
    except:
        high_score = 0

    # ==========================================
    # 1. 視覺特效 (VFX)
    # ==========================================

    class BulletTrail(Entity):
        def __init__(self, start_pos, end_pos):
            super().__init__(model='cube', color=color.yellow, shader='unlit_shader')
            dist = distance(start_pos, end_pos)
            self.position = lerp(start_pos, end_pos, 0.5)
            self.scale = (0.05, 0.05, dist)
            self.look_at(end_pos)
            self.animate_color(color.clear, duration=0.1, curve=curve.linear)
            invoke(destroy, self, delay=0.1)

    class ShellCasing(Entity):
        def __init__(self, position, direction):
            super().__init__(model='cube', color=color.rgb(255, 215, 0), scale=(0.02, 0.02, 0.06), position=position)
            self.rotation = Vec3(random.randint(0,360), random.randint(0,360), random.randint(0,360))
            self.velocity = direction * random.uniform(3, 5) + Vec3(0, 4, 0) + Vec3(random.uniform(-1,1), 0, random.uniform(-1,1))
            invoke(destroy, self, delay=1.5)

        def update(self):
            self.velocity.y -= 15 * time.dt
            self.position += self.velocity * time.dt
            self.rotation += Vec3(200, 200, 200) * time.dt
            if self.y < 0:
                self.y = 0
                self.velocity = Vec3(0)

    def create_muzzle_flash():
        if not gun: return
        flash = Entity(parent=gun, model='quad', texture='noise', scale=0.3, position=(0, 0, 0.6), 
                       rotation=(0, 0, random.randint(0, 360)), color=color.yellow, shader='unlit_shader')
        invoke(destroy, flash, delay=0.05)

    class ExplosionFX(Entity):
        def __init__(self, position):
            super().__init__(model='sphere', color=color.orange, position=position, scale=0.5, shader='unlit_shader')
            self.animate_scale(8, duration=0.5, curve=curve.out_expo)
            self.animate_color(color.clear, duration=0.5, curve=curve.linear)
            
            for i in range(10):
                p = Entity(model='cube', color=color.yellow, position=position, scale=0.2)
                direction = Vec3(random.uniform(-1,1), random.uniform(0.5, 1), random.uniform(-1,1)).normalized()
                p.animate_position(p.position + direction * 5, duration=0.5)
                p.animate_scale(0, duration=0.5)
                invoke(destroy, p, delay=0.5)
                
            invoke(destroy, self, delay=0.6)

    # ==========================================
    # 2. 武器與投擲物系統
    # ==========================================

    class Grenade(Entity):
        def __init__(self, start_pos, direction, force=25):
            try:
                super().__init__(
                    model='sphere', 
                    color=color.dark_gray, 
                    scale=0.3, 
                    position=start_pos, 
                    collider='box'
                )
                self.velocity = direction * force + Vec3(0, 2, 0)
                self.friction = 2.0
                self.gravity = 40
                self.bounciness = 0.5
                self.exploded = False
                self.indicator = Entity(parent=self, model='sphere', color=color.red, scale=1.2, alpha=0.5)
                invoke(self.explode, delay=2.0)
            except Exception as e:
                print(f"Grenade Init Error: {e}")
                destroy(self)

        def update(self):
            if self.exploded: return
            self.velocity.y -= self.gravity * time.dt
            self.position += self.velocity * time.dt
            self.rotation_x += self.velocity.z * 10 * time.dt
            
            if self.y < 0.15:
                self.y = 0.15
                self.velocity.y = -self.velocity.y * self.bounciness
                self.velocity.x *= (1 - self.friction * time.dt)
                self.velocity.z *= (1 - self.friction * time.dt)
                if abs(self.velocity.y) < 1: self.velocity.y = 0
                
        def explode(self):
            if not self or not self.enabled or self.exploded: return
            try:
                self.exploded = True
                ExplosionFX(self.position)
                hit_range = 8
                for e in enemies[:]: 
                    if not e or not e.enabled: continue
                    dist = distance(e.position, self.position)
                    if dist < hit_range:
                        dmg = 120 * (1 - (dist / hit_range))
                        if dmg < 50: dmg = 50 
                        e.take_damage(dmg)
            except Exception as e:
                print(f"Explosion Error: {e}")
            destroy(self)

    # ==========================================
    # 3. 掉落物與敵方投射物
    # ==========================================

    class EnemyProjectile(Entity):
        def __init__(self, position, target_pos):
            super().__init__(model='sphere', color=color.magenta, scale=0.5, position=position, collider='sphere')
            self.speed = 15
            self.damage = 20
            self.look_at(target_pos)
            invoke(destroy, self, delay=5)

        def update(self):
            if game_state != "playing": return
            self.position += self.forward * time.dt * self.speed
            hit_info = self.intersects()
            if hit_info.hit:
                if hit_info.entity == player:
                    player_take_damage(self.damage)
                    destroy(self)
                elif hit_info.entity and hit_info.entity.enabled:
                    if not isinstance(hit_info.entity, (Enemy, Sniper, Grenade, Loot)):
                        destroy(self)

    class Loot(Entity):
        def __init__(self, position, loot_type):
            super().__init__(
                model='cube', 
                position=position, 
                collider='box', 
                scale=0.8
            )
            self.loot_type = loot_type 
            if loot_type == 'health': self.color = color.green
            elif loot_type == 'ammo': self.color = color.azure
            elif loot_type == 'grenade': self.color = color.yellow
            self.texture = 'white_cube'
            self.picked_up = False 
            self.animate_rotation_y(360, duration=2, loop=True)
            self.y = 0.5 

        def update(self):
            if game_state != "playing" or self.picked_up: return
            if not player or not player.enabled: return
            if distance_xz(self.position, player.position) < 1.5:
                self.picked_up = True 
                self.collider = None
                self.visible = False
                try:
                    if self.loot_type == 'health':
                        player.health = min(player.health + 25, player.max_health)
                        update_health_ui()
                    elif self.loot_type == 'ammo':
                        player.ammo = min(player.ammo + 10, player.max_ammo)
                        update_ammo_ui()
                    elif self.loot_type == 'grenade':
                        player.grenades = min(player.grenades + 1, player.max_grenades)
                        update_grenade_ui()
                except Exception as e:
                    print(f"Loot Error: {e}")
                invoke(destroy, self, delay=0.1)

    # ==========================================
    # 4. 敵人 AI 
    # ==========================================

    class Enemy(Entity):
        def __init__(self, position):
            super().__init__(model='cube', texture='white_cube', color=color.red, scale=(1, 2, 1), position=position, collider='box')
            self.health = 100
            self.speed = 3.5
            self.score_value = 100
            self.minimap_dot = Entity(parent=minimap_content, model='circle', scale=0.1, color=color.red)
            minimap_dots.append(self)

        def update(self):
            if game_state != "playing": return
            if not player or not player.enabled: return
            dist = distance_xz(self.position, player.position)
            if dist > 45: return 

            origin = self.position + Vec3(0, 0.5, 0)
            detect_dist = 2.5
            
            # 手動過濾
            ignore_basic = (self, player)

            def is_blocked(ray_hit):
                if not ray_hit.hit: return False
                if isinstance(ray_hit.entity, (BulletTrail, EnemyProjectile, Loot, Grenade, ExplosionFX)):
                    return False
                return True

            hit_front = raycast(origin, self.forward, distance=detect_dist, ignore=ignore_basic)
            hit_left = raycast(origin, (self.forward - self.right).normalized(), distance=detect_dist, ignore=ignore_basic)
            hit_right = raycast(origin, (self.forward + self.right).normalized(), distance=detect_dist, ignore=ignore_basic)

            move_speed = self.speed
            rot_speed = 400 * time.dt
            
            if is_blocked(hit_front):
                if not is_blocked(hit_left) and not is_blocked(hit_right):
                    target_dir = player.position - self.position
                    if target_dir.dot(self.right) > 0: self.rotation_y += rot_speed
                    else: self.rotation_y -= rot_speed
                elif not is_blocked(hit_left): self.rotation_y -= rot_speed
                elif not is_blocked(hit_right): self.rotation_y += rot_speed
                else: self.rotation_y += rot_speed * 1.5
                move_speed *= 0.5 
            else:
                if dist > 2:
                    target_rot = Entity()
                    target_rot.position = self.position
                    target_rot.look_at(player.position)
                    self.rotation_y = lerp(self.rotation_y, target_rot.rotation_y, time.dt * 5)
                    destroy(target_rot)

            wall_check_dist = 1.2
            blocked_front = is_blocked(raycast(origin, self.forward, distance=wall_check_dist, ignore=ignore_basic))
            blocked_left = is_blocked(raycast(origin, (self.forward - self.right).normalized(), distance=0.8, ignore=ignore_basic))
            blocked_right = is_blocked(raycast(origin, (self.forward + self.right).normalized(), distance=0.8, ignore=ignore_basic))

            if not blocked_front and not blocked_left and not blocked_right:
                if dist > 2:
                    self.position += self.forward * time.dt * move_speed
            
            if dist < 2.5 and random.random() < 0.02: player_take_damage(10)
            self.update_minimap()

        def update_minimap(self):
            if not self.minimap_dot or not player: return
            rel_x = clamp((self.x - player.x) * 0.02, -0.45, 0.45)
            rel_y = clamp((self.z - player.z) * 0.02, -0.45, 0.45)
            self.minimap_dot.x, self.minimap_dot.y = rel_x, rel_y

        def take_damage(self, amount):
            self.health -= amount
            self.blink(color.white)
            if self.health <= 0:
                add_score(self.score_value)
                r = random.random()
                if r < 0.3:
                    if r < 0.1: type = 'health'
                    elif r < 0.2: type = 'ammo'
                    else: type = 'grenade'
                    Loot(self.position, type)
                if self.minimap_dot: destroy(self.minimap_dot)
                if self in minimap_dots: minimap_dots.remove(self)
                if self in enemies: enemies.remove(self)
                p = Entity(model='cube', scale=0.5, position=self.position, color=self.color)
                p.animate_position(p.position + Vec3(0,5,0), duration=1)
                p.animate_scale(0, duration=1)
                invoke(destroy, p, delay=1)
                destroy(self)

    class Sniper(Enemy):
        def __init__(self, position):
            super().__init__(position)
            self.color = color.blue
            self.minimap_dot.color = color.blue
            self.health = 50
            self.score_value = 200
            self.attack_cooldown = 2
            self.last_attack_time = 0
            self.min_dist = 15

        def update(self):
            if game_state != "playing": return
            if not player or not player.enabled: return
            dist = distance_xz(self.position, player.position)
            self.look_at_2d(player.position, 'y')
            ignore_basic = (self, player)
            
            def is_blocked(ray_hit):
                if not ray_hit.hit: return False
                if isinstance(ray_hit.entity, (BulletTrail, EnemyProjectile, Loot, Grenade, ExplosionFX)): return False
                return True

            hit_back = raycast(self.position + Vec3(0,0.5,0), -self.forward, distance=1.5, ignore=ignore_basic)
            
            if dist < self.min_dist and not is_blocked(hit_back):
                self.position -= self.forward * time.dt * self.speed
            elif dist > self.min_dist + 5:
                blocked = is_blocked(raycast(self.position + Vec3(0,0.5,0), self.forward, distance=1.5, ignore=ignore_basic))
                if not blocked:
                     self.position += self.forward * time.dt * self.speed

            self.update_minimap()
            
            if time.time() > self.last_attack_time + self.attack_cooldown:
                hit = raycast(self.position + Vec3(0,0.5,0), self.forward, distance=dist, ignore=(self,))
                if hit.hit and hit.entity == player:
                    self.shoot_projectile()

        def shoot_projectile(self):
            self.last_attack_time = time.time()
            EnemyProjectile(self.position + Vec3(0, 1, 0), player.position + Vec3(0,1,0))
            self.blink(color.white, duration=0.1)

    # ==========================================
    # 5. 遊戲系統
    # ==========================================

    class LevelGenerator(Entity):
        def __init__(self):
            super().__init__()
            self.obstacles = []
            
        def generate_arena(self):
            for ob in self.obstacles: destroy(ob)
            self.obstacles.clear()
            
            map_size = 100
            walls = [
                Entity(position=(0, 5, 50), scale=(map_size, 10, 1)),
                Entity(position=(0, 5, -50), scale=(map_size, 10, 1)),
                Entity(position=(50, 5, 0), scale=(1, 10, map_size)),
                Entity(position=(-50, 5, 0), scale=(1, 10, map_size))
            ]
            for w in walls:
                w.model, w.color, w.collider = 'cube', color.black50, 'box'
                self.obstacles.append(w)

            for i in range(40):
                x, z = random.randint(-45, 45), random.randint(-45, 45)
                if distance_2d((x, z), (0, 0)) < 10: continue
                
                if random.random() < 0.3: 
                    scale = (random.randint(2, 4), random.randint(4, 8), random.randint(2, 4))
                    tex, col = 'brick', color.dark_gray
                else: 
                    scale = (random.randint(2, 5), random.randint(1, 2), random.randint(2, 5))
                    tex, col = 'white_cube', color.gray
                    
                ob = Entity(model='cube', position=(x, scale[1]/2, z), scale=scale, texture=tex, color=col, collider='box', texture_scale=(scale[0], scale[2]))
                self.obstacles.append(ob)

    class WaveManager(Entity):
        def __init__(self):
            super().__init__()
            self.wave = 0
            self.wave_text = Text(text='', position=(0, 0.45), origin=(0, 0), scale=2, color=color.yellow, enabled=False)

        def update(self):
            if game_state == "playing" and len(enemies) == 0:
                self.start_next_wave()

        def start_next_wave(self):
            self.wave += 1
            count = 3 + (self.wave * 2)
            self.spawn_enemies(count)
            self.wave_text.text = f'WAVE {self.wave}'
            self.wave_text.enabled = True
            self.wave_text.animate_scale(2.5, duration=0.5)
            self.wave_text.animate_scale(0, duration=0.5, delay=1.5)

        def spawn_enemies(self, count):
            for i in range(count):
                valid = False
                attempts = 0
                while not valid and attempts < 20: 
                    x, z = random.randint(-40, 40), random.randint(-40, 40)
                    if player and distance_xz(Vec3(x, 0, z), player.position) > 10: 
                        valid = True
                    attempts += 1
                
                if self.wave >= 2 and random.random() < 0.3: 
                    e = Sniper(position=(x, 2, z))
                else:
                    e = Enemy(position=(x, 2, z))
                    e.health += (self.wave - 1) * 10
                enemies.append(e)

        def reset(self):
            self.wave = 0
            self.wave_text.enabled = False
            for e in enemies: 
                if e.minimap_dot: destroy(e.minimap_dot)
                destroy(e)
            enemies.clear()
            minimap_dots.clear()
            
            for e in scene.entities:
                if isinstance(e, (EnemyProjectile, Loot, BulletTrail, ShellCasing, Grenade, ExplosionFX)):
                    destroy(e)

    level_generator = LevelGenerator()
    wave_manager = WaveManager()

    # ==========================================
    # 6. 玩家與 UI (穩定紅屏與白底UI)
    # ==========================================

    ground = Entity(model='plane', collider='box', scale=100, texture='grass', texture_scale=(10,10), color=color.gray)
    player = FirstPersonController(y=2, origin_y=-.5)
    player.gun = None
    player.health = 100
    player.max_health = 100
    player.ammo = 30
    player.max_ammo = 30
    player.is_reloading = False
    player.grenades = 3
    player.max_grenades = 5

    gun = Entity(model='cube', parent=camera, position=(.5, -.25, .5), scale=(.2, .2, 1), origin_z=-.5, color=color.gray, on_cooldown=False)
    gun.original_position = gun.position

    # UI Elements
    health_bar = Entity(parent=camera.ui, model='quad', color=color.green, scale=(0.49, 0.04), position=(-0.6, 0.45))
    health_bg = Entity(parent=camera.ui, model='quad', color=color.black, scale=(0.5, 0.05), position=(-0.6, 0.45), z=1)
    health_text = Text(text='100 / 100', parent=camera.ui, position=(-0.65, 0.46), scale=1)

    ammo_text = Text(text='30 / 30', position=(0.65, -0.4), origin=(0, 0), scale=2, color=color.azure)
    grenade_text = Text(text='GRENADES: 3', position=(0.65, -0.32), origin=(0, 0), scale=1.5, color=color.yellow)
    reload_prompt = Text(text='PRESS [R] TO RELOAD', position=(0, -0.2), origin=(0, 0), scale=1.5, color=color.red, enabled=False)
    score_text = Text(text='SCORE: 0', position=(-0.85, 0.45), scale=1.5, color=color.gold)

    # Minimap
    minimap_bg = Entity(parent=camera.ui, model='quad', color=color.black90, scale=(0.3, 0.3), position=(0.7, 0.35))
    minimap_content = Entity(parent=minimap_bg, scale=(1,1))
    player_dot = Entity(parent=minimap_content, model='circle', scale=0.15, color=color.green)

    def update_health_ui():
        health_bar.scale_x = (player.health / player.max_health) * 0.49
        health_text.text = f'{int(player.health)} / {player.max_health}'

    def update_ammo_ui():
        ammo_text.text = f'{player.ammo} / {player.max_ammo}'
        ammo_text.color = color.red if player.ammo <= 5 else color.azure

    def update_grenade_ui():
        grenade_text.text = f'GRENADES: {player.grenades}'

    def add_score(points):
        global score
        score += points
        score_text.text = f'SCORE: {score}'

    def player_take_damage(amount):
        player.health -= amount
        update_health_ui()
        
        # 【相容性修復】使用 rgba 替代 .with_alpha()
        camera.overlay.color = color.red
        
        if player.health > 0:
            camera.overlay.animate_color(color.clear, duration=0.2)
        else:
            # 死亡紅屏
            camera.overlay.color = color.rgba(255, 0, 0, 150)
            show_game_over()

    def shoot():
        if not player.enabled or game_state != "playing" or player.is_reloading: return
        if player.ammo <= 0:
            reload_prompt.enabled = True
            return
        player.ammo -= 1
        update_ammo_ui()
        create_muzzle_flash()
        if gun:
            ShellCasing(position=gun.world_position + gun.right * 0.1, direction=gun.right + camera.forward * -0.5)
            gun.animate_position(gun.original_position + Vec3(0, 0, -0.1), duration=0.05, curve=curve.linear)
            gun.animate_position(gun.original_position, duration=0.05, delay=0.05, curve=curve.linear)

        hit_info = raycast(camera.world_position, camera.forward, distance=100, ignore=(player, gun))
        end_pos = hit_info.world_point if hit_info.hit else camera.world_position + (camera.forward * 50)
        
        if gun: BulletTrail(gun.world_position, end_pos)

        if hit_info.hit:
            if isinstance(hit_info.entity, (Enemy, Sniper)):
                hit_info.entity.take_damage(25)
                e = Entity(model='sphere', color=color.orange, scale=0.2, position=hit_info.world_point)
                e.animate_scale(0, duration=0.5)
                invoke(destroy, e, delay=0.5)

    def throw_grenade():
        try:
            if game_state != "playing" or player.grenades <= 0: return
            player.grenades -= 1
            update_grenade_ui()
            spawn_pos = camera.world_position + camera.forward * 1.5 + Vec3(0, 0.2, 0)
            Grenade(spawn_pos, camera.forward)
            if gun:
                gun.animate_rotation_x(30, duration=0.1)
                gun.animate_rotation_x(0, duration=0.1, delay=0.1)
        except Exception as e:
            print(f"Throw Error: {e}")

    def reload_weapon():
        if player.is_reloading or player.ammo == player.max_ammo: return
        player.is_reloading = True
        reload_prompt.enabled = False
        if gun:
            gun.animate_rotation_x(-360, duration=1, curve=curve.in_out_quad)
        invoke(finish_reload, delay=1)

    def finish_reload():
        player.ammo = player.max_ammo
        player.is_reloading = False
        if gun: gun.rotation_x = 0
        update_ammo_ui()

    # ==========================================
    # 7. 選單與流程控制 (黑底白字UI修正版)
    # ==========================================

    menu_bg = Entity(parent=camera.ui, model='quad', color=color.black66, scale=(2, 2), z=-1, ignore_paused=True)
    title_text = Text(text="MCR ARENA", parent=menu_bg, origin=(0,0), scale=3, y=0.3)
    start_button = Button(text='START GAME', color=color.azure, scale=(0.3, 0.1), y=0.05, parent=menu_bg, ignore_paused=True)
    exit_button = Button(text='EXIT', color=color.red, scale=(0.3, 0.1), y=-0.1, parent=menu_bg, ignore_paused=True)

    # GAME OVER UI - 【修正】黑底白字 (0.9 透明度)
    # color.rgba(0,0,0,230) -> 230/255 約為 0.901
    game_over_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 230), scale=(0.8, 0.5), z=-2, enabled=False, ignore_paused=True)

    # 文字顏色改為白色 (color.white) 或 淺灰
    game_over_text = Text(text="GAME OVER", parent=game_over_bg, origin=(0,0), scale=4, y=0.2, color=color.white)
    final_score_text = Text(text="Final Score: 0", parent=game_over_bg, origin=(0,0), scale=2, y=0.05, color=color.white)
    high_score_text = Text(text="High Score: 0", parent=game_over_bg, origin=(0,0), scale=1.5, y=-0.05, color=color.light_gray)

    # 按鈕設定：深黑色塊 + 白色文字
    restart_button = Button(text='RESTART GAME', color=color.black, scale=(0.4, 0.15), y=-0.25, parent=game_over_bg, ignore_paused=True)
    restart_button.text_entity.color = color.white 

    def start_game():
        global game_state, score
        game_state = "playing"
        score = 0
        add_score(0) 
        
        # 清除視覺效果
        camera.overlay.color = color.clear
        
        menu_bg.disable()
        game_over_bg.disable()
        player.enable()
        mouse.locked = True
        application.paused = False 
        
        level_generator.generate_arena()
        
        player.health = 100
        player.ammo = 30
        player.grenades = 3 
        player.position = Vec3(0, 2, 0)
        update_health_ui()
        update_ammo_ui()
        update_grenade_ui()
        
        wave_manager.reset()
        wave_manager.start_next_wave()

    def show_menu():
        global game_state
        game_state = "menu"
        menu_bg.enable()
        game_over_bg.disable()
        player.disable()
        mouse.locked = False
        application.paused = True

    def show_game_over():
        global game_state, high_score
        game_state = "game_over"
        
        if score > high_score:
            high_score = score
            try:
                with open("highscore.txt", "w") as f:
                    f.write(str(high_score))
            except:
                pass
                
        final_score_text.text = f'Final Score: {score}'
        high_score_text.text = f'High Score: {high_score}'
        
        game_over_bg.enable()
        player.disable()
        mouse.locked = False
        application.paused = True

    def quit_game(): application.quit()

    start_button.on_click = start_game
    exit_button.on_click = quit_game
    restart_button.on_click = start_game

    def input(key):
        try:
            if key == 'escape':
                if game_state == "playing": show_menu()
                elif game_state == "menu": start_game()
            
            if game_state == "playing":
                if key == 'left mouse down': shoot()
                if key == 'r': reload_weapon()
                if key == 'g': throw_grenade()
        except Exception as e:
            print(f"Input Error: {e}")

    # 初始啟動
    show_menu()
    app.run()

# 【防閃退安全網】
except Exception as e:
    with open("crash_log.txt", "w") as f:
        f.write(traceback.format_exc())
    print("Game Crashed! Check crash_log.txt for details.")
    input("Press Enter to exit...")