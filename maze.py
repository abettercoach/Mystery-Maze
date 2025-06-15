# Maze by iris
# For Recurse Center Application, June 2025
#
# Inspired by an activity described in the book
# "Right Kind of Wrong" by Amy Edmondson
# 
# Small, terminal-based game. 
# The goal of the game is for the user to find their way 
# through a maze from entry to exit as quickly as possible. 
# 
# - The maze exists within a grid of tiles.
# - Path tiles are part of the maze.
# - Wall tiles are not.
# - There is an Entry tile and an Exit tile.
# - Except for the Entry, all tiles at first obscured, 
#   and the user must step on a tile before revealing if
#   it's a path tile or wall tile.
# - The user can only step on tiles adjacent to already 
#   revealed path tiles. 
# - The user takes steps using the WASD keys.
# - Stepping on a path tile is a success.
# - Stepping on a wall tile is a failure.
# - Some path tiles lead to dead ends.
# - The game is over and the user wins when they
#   reveal the Exit tile.
#
# There is no losing, only taking longer.

# Pseudo-Structure
# I'll need...
# (0) An intro prompt.
# (1) To print out the maze. Initially, and after every move.
# (2) To receive user input after printing out the maze.
# (3) To process input and update the maze.
# (4) To identify the win-condition and end the game.
# 
# For all of that I'll need.
# (A) To initialize the grid. Maze, path and barrier tiles, entry, exit.
# 
# What I can start with:
# - A grid made up of all path tiles.
#
# TODO: Implement easy interface with curses library

import random
import time
from enum import Enum

# The curses library supports pretty terminal display
# and facilitates reading user input. Hopefully using this
# library doesn't go against the "no frameworks" rule.
# If it does, please judge my submission on the merit of
# my classes.  
import curses
from curses import wrapper

def main(stdscr):
    game = Game(stdscr)
    game.start()

class Direction(Enum): 
    NORTH = 1
    SOUTH = 2
    WEST = 3
    EAST = 4

class Tile:
    def __init__(self, coords):
        self.coords = coords

        self.revealed = False #False when shrouded. True when stepped on.
        self.carved = False #False when wall. True when carved path.

        #For use during maze generation
        self.visited = False 

class Mystery_Maze:
    """
    A mystery maze is made up of a grid tiles. 
    Tiles are either carved (part of the path) or walls.
    Tiles are either revelead (have been stepped on by user) or shrouded.
    """

    def __init__(self, width, height):
        # Initialize grid for maze

        # Ensure width and height are odd and sufficiently large for 
        # Recursive Backtracking algorithm to work
        if (width < 3):
            width = 3
        elif (width % 2 != 1):
            width += 1
        self.width = width

        if (height < 3):
            height = 3
        elif (height % 2 != 1):
            height += 1
        self.height = height

        # Initialize grid data structure 
        # Tiles are initialized as shrouded walls.
        self.grid = {}
        for x in range(width):
            for y in range(height):
                self.grid[(x,y)] = Tile((x,y))
    
        # Begin recursive maze generation, which carves out a maze
        # of paths in the the tiles
        self.visit((1,1))

        # Add entrance and exit to maze.
        exit_coords = (1,0)
        entrance_coords = (self.width - 2, self.height - 1)

        self.exit = self.grid[exit_coords]
        self.entrance = self.grid[entrance_coords]

        self.exit.carved = True
        self.exit.revealed = True

        self.entrance.carved = True
        self.entrance.revealed = True
    
    def visit(self, coords):
        """Based off recursive backtracking maze generation
        algorithm.
        
        Reference: https://inventwithpython.com/recursion/chapter11.html
        
        Carve out a cell as part of the path in the maze at x, y
        and then recursively move to neighboring unvisited
        spaces. This function backtracks when the mark has
        reached a dead end."""

        #Carve out space where there was once a wall
        current_tile = self.grid[coords]
        current_tile.carved = True
        
        #Mark as visited.
        current_tile.visited = True

        (x,y) = coords

        while True:
            # Check which neighbors not yet visited
            # For each direction, if not at the edge there is a neighbor.
            # If there is a neighbor and it hasn't been visited, add to unvisited.
            unvisited_neighbors = []

            if y > 1 and not self.grid[(x, y - 2)].visited:
                unvisited_neighbors.append(Direction.NORTH)

            if y < self.height - 2 and not self.grid[(x, y + 2)].visited:
                unvisited_neighbors.append(Direction.SOUTH)

            if x > 1 and not self.grid[(x - 2, y)].visited:
                unvisited_neighbors.append(Direction.WEST)

            if x < self.width - 2 and not self.grid[(x + 2, y)].visited:
                unvisited_neighbors.append(Direction.EAST)

            if len(unvisited_neighbors) == 0:
                # Base case: If all neighbors visited.
                # Dead end. Backtrack to an earlier space.
                return
            else:
                # Recursive case: At least one neighbor we can visit
                # Randomly pick an unvisited neighbor to be the next tile
                
                next_tile_direction = random.choice(unvisited_neighbors)

                if next_tile_direction == Direction.NORTH:
                    next_tile_coords = (x, y - 2)
                    hallway_coords = (x, y - 1)
                elif next_tile_direction == Direction.SOUTH:
                    next_tile_coords = (x, y + 2)
                    hallway_coords = (x, y + 1)
                elif next_tile_direction == Direction.WEST:
                    next_tile_coords = (x - 2, y)
                    hallway_coords = (x - 1, y)
                elif next_tile_direction == Direction.EAST:
                    next_tile_coords = (x + 2, y)
                    hallway_coords = (x + 1, y)
                
                # Carve out the connection hallway too
                hallway_tile = self.grid[hallway_coords]
                hallway_tile.carved = True

                # Visit the next coordinate recursively
                self.visit(next_tile_coords)

    def display_grid(self):
        """Displays the grid, or underlying maze."""

        for y in range(self.height):
            for x in range(self.width):
                print(self.grid[x,y], end='') #WALL or PATH
            print() #newline after each row

        print() #newline after entire grid


class Game:
    """Encapsulates de entire terminal-based user experience.
    Contrains logic for displaying instructions, handling user input,
    and displaying the current state of the maze."""
    def __init__(self, stdscr):
        
        # Curses setup
        curses.curs_set(0)
        self.screen = stdscr # curses module object that corresponds to terminal screen
        
        # Where to draw maze on the terminal (below script lines)
        self.__maze_screen_coords = (10,8)

    def start(self):
        """Starts a new game with a fresh maze"""
        self.maze = Mystery_Maze(13,7)
        self.player_position = self.maze.entrance.coords
        self.player_start_time = time.time() 
        self.play_time = 0

        self.screen.clear()

        self.__play_intro()
        self.__game_loop()

    def make_move(self, direction):
        """
        Reveals the tile under mark_coords.
        Returns true if the move was succesful, false otherwise.
        """

        # Calculate coordinates for step from direction
        (x,y) = self.player_position
        if direction == Direction.NORTH:
            step_coords = (x, y - 1)
        elif direction == Direction.SOUTH:
            step_coords = (x, y + 1)
        elif direction == Direction.WEST:
            step_coords = (x - 1, y)
        elif direction == Direction.EAST:
            step_coords = (x + 1, y)

        (step_x, step_y) = step_coords
        if step_x < 0 or step_x >= self.maze.width or step_y < 0 or step_y >= self.maze.height:
            # Fail if trying to ilegaly step outside of grid
            is_success = False
        else:
            # Legal move within grid. Reveal tile.
            stepped_tile = self.maze.grid[step_coords]
            stepped_tile.revealed = True
            
            # Success if stepping into carved path. Fail if wall.
            is_success = stepped_tile.carved

        if is_success:    
            next_position = step_coords
        else:
            next_position = self.player_position
        
        return (is_success, next_position)

    def __play_intro(self):
        line0, line1, line2 = Line(), Line(), Line()
        line0.script = """You have entered the Mystery Maze... Welcome.\n...A shroud of fog engulfs you..."""
        line0.prompt = """(Press any key to continue)"""
        line1.script = """As you move, you may step into a clearing. A path forward? A dead end?\nOr... you may step into a wall!"""
        line1.prompt = """(Press any key to continue)"""
        line2.script = """With every move you map out the mystery.

With every move you step towards success."""
        line2.prompt = """(Press any key to begin)"""

        intro = [line0,line1,line2]
        for line in intro:
            self.__display_line(line)

            # Wait for input of any character before next intro line
            self.screen.nodelay(False)
            self.screen.getch()
    
    def __display_line(self, line):
        """Display text one letter at a time"""
        
        # Clear only the script area (first 5 lines)
        for y in range(6):
            self.screen.move(y, 0)
            self.screen.clrtoeol()
        
        # Position cursor at top
        self.screen.move(0, 0)

        # Print one character at a time of the script for typing effect. 
        # If we receive any keystroke during line rendering, skip the typing effect
        # and render whole script in one go.
        self.screen.nodelay(True)
        skip_type_effect = False
        for char in line.script:
            # Render the type effect as long as there has been no new user input
            # during the current loop or from a previous loop
            keystroke = self.screen.getch()
            skip_type_effect = skip_type_effect or keystroke != curses.ERR #and not has_type_effect

            self.screen.addstr(char)
            self.screen.refresh()
            if skip_type_effect:
                time.sleep(0.005)
            elif char == "\n":
                time.sleep(0.75)
            else:
                time.sleep(0.05)
        
        # Print prompt with different style
        if line.prompt:
            if not skip_type_effect:
                time.sleep(0.2)
            self.screen.addstr("\n\n"+line.prompt, curses.A_ITALIC)

    def __display_tile(self, coords, tile):

        curses.start_color()
        curses.use_default_colors()

        curses.init_color(1, 500, 500, 500)
        curses.init_pair(1, 1, curses.COLOR_WHITE)

        (x,y) = coords
        if not tile.revealed:
            tile_char = "▓"
        elif not tile.carved:
            tile_char = "█"
        else:
            tile_char = " "
        
        self.screen.addstr(y,x, tile_char, curses.color_pair(1))

    def __display_maze(self):
        """Displays the current state of the game."""

        (maze_top_x, maze_top_y) = self.__maze_screen_coords

        for y in range(self.maze.height):
            for x in range(self.maze.width):
                tile = self.maze.grid[x,y]

                display_x = maze_top_x + x
                display_y = maze_top_y + y

                self.__display_tile((display_x, display_y), tile)

            self.screen.addstr("\n") #newline after each row

        self.screen.addstr("\n") #newline after entire grid

    def __display_user(self):
        """Displays the current state of the user."""

        (maze_top_x, maze_top_y) = self.__maze_screen_coords
        (user_x, user_y) = self.player_position

        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)

        (x,y) = (maze_top_x + user_x, maze_top_y + user_y)
        user_char = "¤"
        
        self.screen.addstr(y,x, user_char, curses.color_pair(2) | curses.A_BOLD)

    def __display_turn(self, direction, success):
        """Displays the last move."""

        (maze_top_x, maze_top_y) = self.__maze_screen_coords
        (user_x, user_y) = self.player_position
        
        if direction == Direction.NORTH:
            (x,y) = (maze_top_x + user_x, maze_top_y + user_y - 1)
            user_char = "^"
        elif direction == Direction.SOUTH:
            (x,y) = (maze_top_x + user_x, maze_top_y + user_y + 1)
            user_char = "v"
        elif direction == Direction.WEST:
            (x,y) = (maze_top_x + user_x - 1, maze_top_y + user_y)
            user_char = "<"
        elif direction == Direction.EAST:
            (x,y) = (maze_top_x + user_x + 1, maze_top_y + user_y)
            user_char = ">"

        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_GREEN)

        color_pair = curses.color_pair(4) if success else curses.color_pair(3)
        
        self.screen.addstr(y,x, user_char, color_pair | curses.A_BOLD)

    def __display_time_elapsed(self):
        self.play_time = time.time() - self.player_start_time
        play_time_str = str(round(self.play_time,2))
        display_str = f'Seconds: {play_time_str}'

        curses.start_color()
        curses.use_default_colors()
        
        (_, maze_y) = self.__maze_screen_coords
        x = 0
        y = maze_y + self.maze.height + 2

        self.screen.addstr(y,x, display_str, 1 | curses.A_BOLD)

    def __display_finish(self):
        play_time_str = str(round(self.play_time,2))

        turn_line = Line()
        turn_line.script = f'Congratulations. You made it to the exit in {play_time_str} seconds.'
        turn_line.prompt = "Press any key to play again."

        self.__display_line(turn_line)
        self.__display_maze()
        self.__display_user()

        # Wait for input of any character before next intro line
        self.screen.nodelay(False)
        self.screen.getch()
        self.start()

    def __game_loop(self):
        """
        The main game display. Includes instruction, and player position.
        Waits for player turn and updates the game state.
        """
        turn_line = Line()
        turn_line.script = "You have entered the maze. How long will it take to find your way through?"
        turn_line.prompt = "Use the arrow keys to navigate your way through the shrouded maze."
        self.__display_line(turn_line)

        self.player_start_time = time.time() # Reset time, so that the count begins only after the intro
        # self.screen.nodelay(False) # Wait until input every frame at .getch()
        while True:
            self.__display_maze()
            self.__display_user()
            self.__display_time_elapsed()
            self.screen.refresh()

            char = self.screen.getch()
            if char == curses.KEY_RIGHT: 
                direction = Direction.EAST
            elif char == curses.KEY_LEFT: 
                direction = Direction.WEST
            elif char == curses.KEY_UP: 
                direction = Direction.NORTH
            elif char == curses.KEY_DOWN: 
                direction = Direction.SOUTH
            else:
                direction = False
            
            if direction:
                (was_success, new_position) = self.make_move(direction)
                self.__display_turn(direction, was_success)
                self.player_position = new_position

                # Keep turn displayed for a brief moment before continuing game loop
                self.screen.refresh()
                time.sleep(0.3)

            did_win = self.player_position == self.maze.exit.coords

            if did_win:
                break
        
        self.__display_finish()

            

class Line:
    """Lines in the game are made up of a script and a prompt."""
    def __init__(self):
        self.script = ""
        self.prompt = ""

# while True:
#     prompt = """
#     Use the WASD keys to make your way through the maze.
#     Press a direction key and then Enter:"""
#     str_input = input(prompt).lower()
#     match str_input:
#         case "w":
#             maze.step(Direction.NORTH)
#         case "a":
#             maze.step(Direction.WEST)
#         case "s":
#             maze.step(Direction.SOUTH)
#         case "d":
#             maze.step(Direction.EAST)
#         case _:
#             print("Not a Valid direction")


wrapper(main) #Protects the terminal from breaking