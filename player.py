from multiprocessing.connection import Listener, Client
from multiprocessing import Process, Manager, Value, Lock
import traceback
import sys
import pygame as pg
from settings import*
from os import path
from tilemap import *
vec = pg.math.Vector2

def collide_hit_rect(one, two):
    return one.hit_rect.colliderect(two.rect)

class Player():
    def __init__(self, g_team, x, y,team,dt):
        self.team = team
        self.gteam = g_team
        self.dt = dt
        self.rot_speed = 0
        self.vel = vec(0, 0)
        self.pos = vec(x, y) * TILESIZE
        self.rot = 0

    def get_keys(self):
        if(self.gteam == self.team):
            self.rot_speed = 0
            self.vel = vec(0, 0)
            keys = pg.key.get_pressed()
            if keys[pg.K_LEFT] or keys[pg.K_a]:
                self.rot_speed = PLAYER_ROT_SPEED
            if keys[pg.K_RIGHT] or keys[pg.K_d]:
                self.rot_speed = -PLAYER_ROT_SPEED
            if keys[pg.K_UP] or keys[pg.K_w]:
                self.vel = vec(PLAYER_SPEED, 0).rotate(-self.rot)
            if keys[pg.K_DOWN] or keys[pg.K_s]:
                self.vel = vec(-PLAYER_SPEED / 2, 0).rotate(-self.rot)

    def collide_with_walls(self, dir,sprite,walls):
        if dir == 'x':
            hits = pg.sprite.spritecollide(sprite, walls, False,collide_hit_rect)
            if hits:
                if hits[0].rect.centerx > sprite.hit_rect.centerx:
                    self.pos.x = hits[0].rect.left - sprite.hit_rect.width / 2
                if hits[0].rect.centerx < sprite.hit_rect.centerx:
                    self.pos.x = hits[0].rect.right + sprite.hit_rect.width / 2
                self.vel.x = 0
                sprite.hit_rect.centerx = self.pos.x
        if dir == 'y':
            hits = pg.sprite.spritecollide(sprite, walls, False)
            if hits:
                if hits[0].rect.centery > sprite.hit_rect.centery:
                    self.pos.y = hits[0].rect.top - sprite.hit_rect.height / 2
                if hits[0].rect.centery < sprite.hit_rect.centery:
                    self.pos.y = hits[0].rect.bottom + sprite.hit_rect.height / 2
                self.vel.y = 0
                sprite.hit_rect.centery = self.pos.y

    def update(self,sprite,walls):
        self.get_keys()
        self.rot = (self.rot + self.rot_speed * self.dt) % 360
        sprite.image = pg.transform.rotate(sprite.original_image, self.rot)
        sprite.rect = sprite.image.get_rect()
        sprite.rect.center = self.pos
        self.pos += self.vel * self.dt
        sprite.hit_rect.centerx = self.pos.x
        self.collide_with_walls('x',sprite,walls)
        sprite.hit_rect.centery = self.pos.y
        self.collide_with_walls('y',sprite,walls)
        sprite.rect.center = sprite.hit_rect.center
    
    def get_pos(self):
        return([self.pos.x,self.pos.y,self.rot])
        
    def set_pos(self,pos):
        self.pos.x = pos[0]
        self.pos.y = pos[1]
        self.rot = pos[2]

class PlayerSprite(pg.sprite.Sprite):
    def __init__(self,player,game):
        self.game = game
        self.player = player
        self.groups = self.game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.original_image = pg.Surface((TILESIZE, TILESIZE),pg.SRCALPHA)
#        self.original_image = pg.image.load("mierda.png")
        self.image = self.original_image
        if self.player.team == 0:
            self.image.fill(BLUE)
        else:
            self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.hit_rect = PLAYER_HIT_RECT
        self.hit_rect.center = self.rect.center
        
    def update(self):
        self.image = pg.transform.rotate(self.original_image, self.player.rot)
        self.rect = self.image.get_rect()
        self.rect.center = self.player.pos

class Bullet():
    def __init__(self,x,y,rot,dt):
        self.enable = 1
        self.pt = 0
        self.rot = rot
        self.pos = vec(x, y) + vec(TILESIZE//3 * 2,TILESIZE//2 + 1).rotate(-self.rot)
        self.dt = dt
        self.vel = vec(BULLET_SPEED, 0).rotate(-self.rot)
    
    def destroys(self):
        self.enable = 0
    
    def point(self):
        self.pt = 1
        
    def collide_with_walls(self,sprite,walls):
        hits = pg.sprite.spritecollide(sprite, walls, False)
        if hits:
            self.destroys()
    
    def collide_with_opponent(self,sprite,obj):
        hits = pg.sprite.collide_rect(sprite, obj)
        if hits:
            self.point()
            self.destroys()
    
    def update(self,sprite,walls,player):
        if self.enable:
            self.pos = self.pos + self.vel*self.dt
            self.collide_with_walls(sprite,walls)
            self.collide_with_opponent(sprite,player)
    
    def get_pos(self):
        return [self.pos.x,self.pos.y,self.rot]
        

class Bullet_sprite(pg.sprite.Sprite):
    def __init__(self,bullet,game):
        self.game = game
        self.bullet = bullet
        self.groups = self.game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.image = pg.Surface((BULLETSIZE,BULLETSIZE))
        self.image.fill(BGCOLOR)
        self.image.set_colorkey(BGCOLOR)
        pg.draw.circle(self.image, YELLOW, (BULLETSIZE/2,BULLETSIZE/2),BULLETSIZE/2)
        self.rect = self.image.get_rect()
        self.rect.x = self.bullet.pos.x
        self.rect.y = self.bullet.pos.y
    
    def update(self):
        self.rect.x = self.bullet.pos.x
        self.rect.y = self.bullet.pos.y

class Wall(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.walls
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

class Game():
    def __init__(self):
        self.team = -5
        self.playing = 1
        self.clock = pg.time.Clock()
        self.dt = self.clock.tick(FPS) / 1000
        self.load_data()
        
        self.all_sprites = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == '1':
                    Wall(self, col, row)
                elif tile == 'P':
                    self.player1 = [Player(self.team, col, row,0,self.dt)]
                    self.sprite1 = PlayerSprite(self.player1[0],self)
                elif tile == 'Q':
                    self.player2 = [Player(self.team, col, row,1,self.dt)]
                    self.sprite2 = PlayerSprite(self.player2[0],self)
        self.players = [self.player1,self.player2]
        self.p_sprites = [self.sprite2,self.sprite1]
        self.bullets = []
        self.bullets_sprites = []
        self.last_shot = pg.time.get_ticks()
        self.other_bullets = []
        self.other_bullets_sprites = []
        self.score = [0,0]
        self.ppoints = 0

    def load_data(self):
        game_folder = path.dirname(__file__)
        self.map = Map(path.join(game_folder, 'map2.txt'))
    
    def create_bullet(self,pos):
        bull = Bullet(pos[0],pos[1],pos[2],self.dt)
        self.bullets.append(bull)
        sp_bull = Bullet_sprite(bull,self)
        self.bullets_sprites.append(sp_bull)
    
    def create_oth_bullet(self,pos):
        bull = Bullet(pos[0],pos[1],pos[2],self.dt)
        self.other_bullets.append(bull)
        sp_bull = Bullet_sprite(bull,self)
        self.other_bullets_sprites.append(sp_bull)
    
    def elim_bull(self,a,b,i):
        if a[i].pt == 1:
            self.ppoints += 1
        del a[i]
        b[i].kill()
        del b[i]
    
    def adjust_other_bullets(self,otbull):
        n1 = len(otbull)
        n2 = len(self.other_bullets)
        if n1 >= n2:
            for i in range(n2):
                self.other_bullets[i].pos.x = otbull[i][0]
                self.other_bullets[i].pos.y = otbull[i][1]
            for i in range(n1-n2):
                self.create_oth_bullet(otbull[n2+i])
        else:
            for i in range(n1):
                self.other_bullets[i].pos.x = otbull[i][0]
                self.other_bullets[i].pos.y = otbull[i][1]
            for i in range(n2-n1):
                self.elim_bull(self.other_bullets,self.other_bullets_sprites,n1)
    
    def check_delet_bullets(self):
        i = 0
        while i < len(self.bullets):
            if (not self.bullets[i].enable):
                self.elim_bull(self.bullets,self.bullets_sprites,i)
            else:
                i = i + 1
    
    def get_keys(self):
        keys = pg.key.get_pressed()
        if keys[pg.K_SPACE]:
            now = pg.time.get_ticks()
            if now - self.last_shot > BULLET_RATE:
                self.last_shot = now
                self.create_bullet(self.players[self.team][0].get_pos())

    def run(self):
        # game loop - set self.playing = False to end the game
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update()
#            self.draw()
    
    def get_all_sprites(self):
        return self.all_sprites
    
    def get_walls(self):
        return self.walls
    
    def get_map(self):
        return self.map

    def quit(self):
        pg.quit()
        sys.exit()
    
    def stop(self):
        self.playing = 0
    
    def update(self,info):
        self.get_keys()
        self.playing = info['is_running']
        self.score = info['score']
        if self.team == 0:
            self.player1[0].update(self.sprite1,self.walls)
            self.player2[0].set_pos(info['pos_red_player'])
            self.adjust_other_bullets(info['bullets2'])
        if self.team == 1:
            self.player2[0].update(self.sprite2,self.walls)
            self.player1[0].set_pos(info['pos_blue_player'])
            self.adjust_other_bullets(info['bullets1'])
        for i in range(len(self.bullets)):
            bull = self.bullets[i]
            bull.update(self.bullets_sprites[i],self.walls,self.p_sprites[self.team])
        self.check_delet_bullets()
        self.all_sprites.update()

    def draw_grid(self):
        for x in range(0, WIDTH, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (0, y), (WIDTH, y))

    def draw(self):
        self.screen.fill(BGCOLOR)
        self.draw_grid()
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        pg.display.flip()

    def events(self):
        # catch all events here
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.quit()
    
    def is_running(self):
        return self.playing == 1
    
    def get_info(self):
        info = {
            'pos_blue_player': self.players[0].get_pos(),
            'pos_red_player': self.players[1].get_pos(),
            'is_running': self.playing == 1
        }
        return info

    def show_start_screen(self):
        pass

    def show_go_screen(self):
        pass
    
    def get_bullets_pos(self):
        l = []
        for i in self.bullets:
            l.append(i.get_pos())
        return l
    
    def get_score(self):
        return self.score
    
class Display():
    
    def __init__(self,game,team):
        self.team = team
        self.game = game
        self.game.team = team
        self.game.player1[0].gteam = team
        self.game.player2[0].gteam = team
        if team == 0:
            self.sprite = self.game.sprite1
        else:
            self.sprite = self.game.sprite2
        self.player = self.game.players[team]
        self.all_sprites = self.game.get_all_sprites()
        self.walls =self.game. get_walls()
        self.map = self.game.get_map()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.camera = Camera(self.map.width, self.map.height)
        pg.init()
    
    def refresh(self):
        self.camera.update(self.sprite)
        self.draw()
        
    def draw(self):
        self.screen.fill(BGCOLOR)
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        
        score = self.game.get_score()
        font = pg.font.Font(None, 74)
        text = font.render(f"{score[self.team]}", 1, COLOR[self.team])
        self.screen.blit(text, (250, 10))
        text = font.render(f"{score[int(not self.team)]}", 1, COLOR[int(not self.team)])
        self.screen.blit(text, (WIDTH-250, 10))
        pg.display.flip()
    
    def analyze_events(self):
        events = []
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    events.append("quit")
        if self.team == 0:
            events.append( 'a' + ','.join([str(x) for x in self.game.player1[0].get_pos()]) )
            events.append( 'c' + ','.join(['P'.join([str(x) for x in y]) for y in self.game.get_bullets_pos()]))
            events.append( 'e' + str(self.game.ppoints))
        if self.team == 1:
            events.append( 'b' + ','.join([str(x) for x in self.game.player2[0].get_pos()]) )
            events.append( 'd' + ','.join(['P'.join([str(x) for x in y]) for y in self.game.get_bullets_pos()]))
            events.append( 'f' + str(self.game.ppoints))
        return events
        
    @staticmethod
    def quit():
        pg.quit()
        

def main(ip_address):
    try:
        with Client((ip_address, 6020), authkey=b'secret password') as conn:
            game = Game()
            team,gameinfo = conn.recv()
            print(f"I am playing {TEAM[team]}")
            display = Display(game,team)
            while game.is_running():
                events = display.analyze_events()
                for ev in events:
                    conn.send(ev)
                    if ev == 'quit':
                        game.stop()
                conn.send("next")
                gameinfo = conn.recv()
                game.update(gameinfo)
                display.refresh()
#                display.tick()
    except:
        traceback.print_exc()
    finally:
        pg.quit()
        sys.exit()


if __name__=="__main__":
    ip_address = "127.0.0.1"
    if len(sys.argv)>1:
        ip_address = sys.argv[1]
    main(ip_address)
