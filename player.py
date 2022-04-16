from multiprocessing.connection import Listener, Client
from multiprocessing import Process, Manager, Value, Lock
import traceback
import sys
import pygame as pg
from settings import*
from os import path
from tilemap import *


class Player(pg.sprite.Sprite):
    def __init__(self, game, x, y,team):
        self.team = team
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        if team == 0:
            self.image.fill(BLUE)
        else:
            self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.vx, self.vy = 0, 0
        self.x = x * TILESIZE
        self.y = y * TILESIZE

    def get_keys(self):
        self.vx, self.vy = 0, 0
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.vx = -PLAYER_SPEED
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.vx = PLAYER_SPEED
        if keys[pg.K_UP] or keys[pg.K_w]:
            self.vy = -PLAYER_SPEED
        if keys[pg.K_DOWN] or keys[pg.K_s]:
            self.vy = PLAYER_SPEED
        if self.vx != 0 and self.vy != 0:
            self.vx *= 0.7071
            self.vy *= 0.7071

    def collide_with_walls(self, dir):
        if dir == 'x':
            hits = pg.sprite.spritecollide(self, self.game.walls, False)
            if hits:
                if self.vx > 0:
                    self.x = hits[0].rect.left - self.rect.width
                if self.vx < 0:
                    self.x = hits[0].rect.right
                self.vx = 0
                self.rect.x = self.x
        if dir == 'y':
            hits = pg.sprite.spritecollide(self, self.game.walls, False)
            if hits:
                if self.vy > 0:
                    self.y = hits[0].rect.top - self.rect.height
                if self.vy < 0:
                    self.y = hits[0].rect.bottom
                self.vy = 0
                self.rect.y = self.y

    def update(self):
        self.get_keys()
        self.x += self.vx * self.game.dt
        self.y += self.vy * self.game.dt
        self.rect.x = self.x
        self.collide_with_walls('x')
        self.rect.y = self.y
        self.collide_with_walls('y')
    
    def get_pos(self):
        return([self.x,self.y])

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
        self.playing = 1
        self.clock = pg.time.Clock()
        self.dt = self.clock.tick(FPS) / 1000
        self.load_data()
        # initialize all variables and do all the setup for a new game
        self.all_sprites = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == '1':
                    Wall(self, col, row)
                elif tile == 'P':
                    self.player1 = Player(self, col, row,0)
                elif tile == 'Q':
                    self.player2 = Player(self, col, row,1)
        self.players = [self.player1,self.player2]

    def load_data(self):
        game_folder = path.dirname(__file__)
        self.map = Map(path.join(game_folder, 'map2.txt'))

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

    def update(self):
        # update portion of the game loop
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
            'score': list(self.score),
            'is_running': self.playing == 1
        }
        return info

    def show_start_screen(self):
        pass

    def show_go_screen(self):
        pass
    
class Display():
    
    def __init__(self,game,team):
        self.game = game
        self.player = self.game.players[team]
        self.all_sprites = self.game.get_all_sprites()
        self.walls =self.game. get_walls()
        self.map = self.game.get_map()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.camera = Camera(self.map.width, self.map.height)
        pg.init()
    
    def refresh(self):
        self.camera.update(self.player)
        self.draw()
        
    def draw(self):
        self.screen.fill(BGCOLOR)
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        pg.display.flip()
    
    def analyze_events(self):
        events = []
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    events.append("quit")
        return events
        
    @staticmethod
    def quit():
        pygame.quit()
        

def main(ip_address):
    try:
        with Client((ip_address, 6000), authkey=b'secret password') as conn:
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
                game.update()
                display.refresh()
#                display.tick()
    except:
        traceback.print_exc()
    finally:
        pg.quit()


if __name__=="__main__":
    ip_address = "127.0.0.1"
    if len(sys.argv)>1:
        ip_address = sys.argv[1]
    main(ip_address)
