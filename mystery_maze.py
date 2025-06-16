import curses
import random
import time
from enum import Enum

class Direction(Enum): 
    """
    Helper class for the Mystery Maze Game.
    These cardinal directions are used during maze generation
    as well as for user movement and gameplay.
    """
    NORTH = 1
    SOUTH = 2
    WEST = 3
    EAST = 4

class Maze_Tile:
    """
    A Mystery Maze instance will be mainly made up of
    a grid of Maze_Tile instances with useful attributes.
    """
    def __init__(self, coords):
        # While each Mystery_Maze instance will have a grid
        # mapping coordinates to tiles. It is also helpful to
        # be able to reference the coordinates from each tile.
        self.coords = coords

        # Tiles are instantiated as walls that are also shrouded.
        self.revealed = False #False when shrouded. True when stepped on.
        self.path = False #False when wall. True when path.

        # For use during maze generation.
        # This attribute will let us know if we have already
        # visited it during the recursive backtracking algorithm
        # and decided it it will be part of the path or not.
        self.visited = False 

class Mystery_Maze:
    """
    Each game will begin with a freshly generated Mystery Maze instance.
    A Mystery Maze is made up of a grid tiles. 
    Tiles are either part of the path or walls.
    Tiles are either revelead (have been stepped on by user) or shrouded.

    This class is not concerned with tracking user's position, 
    handling their movements, or other game interface concerns. An 
    instance of Game, however, will be able to access a Maze's grid and 
    mark Tiles as revealed or not.
    """

    def __init__(self, width, height):
        """
        Initialize what we need for a Maze:
        We generate a maze with recursive backtracking on a 
        grid of tiles and then add entrance and exit points.
        """

        # Ensure width and height are odd and sufficiently large for 
        # the generation algorithm to work.
        # The outer columns and rows of the grid will always be walls,
        # except for the entry and exit tiles.
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

        # Initialize the grid data structure 
        # Tiles are initialized as shrouded walls.
        self.grid = {}
        for x in range(width):
            for y in range(height):
                self.grid[(x,y)] = Maze_Tile((x,y))
    
        # Begin recursive maze generation, which carves out a maze
        # of paths in the the tiles. 
        # __visit() is a recursive function that only returns after
        # the algorithm finishes.
        self.__visit((1,1)) 

        # Add entry and exit to maze.
        exit_coords = (1,0) # Top left
        entry_coords = (self.width - 2, self.height - 1) # Bottom right

        self.exit = self.grid[exit_coords]
        self.entry = self.grid[entry_coords]

        self.exit.path = True
        self.exit.revealed = True

        self.entry.path = True
        self.entry.revealed = True
    
    def __visit(self, coords):
        """
        Based off recursive backtracking maze generation algorithm.
        
        Reference: https://inventwithpython.com/recursion/chapter11.html
        
        Carve out a cell as part of the path in the maze at coords
        and then recursively move to neighboring unvisited spaces. 
        This function backtracks whenever the mark has reached a dead end
        and returns when completed.
        """

        # Carve out space at coords where there was once a wall
        current_tile = self.grid[coords]
        current_tile.path = True # current_tile is now part of path
        
        # Mark as visited.
        current_tile.visited = True # won't be visited again by recursion

        # Recursive loop:
        (x,y) = coords
        while True:
            # Check which neighbors not yet visited.
            # For each direction, if current tile is not at the edge it has a neighbor.
            # If the neighbor hasn't been visited, add to list of unvisited.
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
                # Base case: If all neighbors visited, we're at
                # a dead end. Backtrack to an earlier space.
                # This will break completely out of the recursion
                # once we've visited everything.
                return
            else:
                # Recursive case: At least one neighbor we can visit, so
                # randomly pick an unvisited neighbor to be the next tile.
                # We'll also keep track of the hallway between neighbors.
                
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
                
                # Carve out the connection hallway first
                hallway_tile = self.grid[hallway_coords]
                hallway_tile.path = True

                # Visit the next coordinate recursively
                # (which will be marked carved and visited once called)
                self.__visit(next_tile_coords)

class Game_Line:
    """
    Helper class for Game.
    Text is part of most terminal-based games.
    Game Lines are made up of a script to display and a prompt 
    for user interaction.
    """
    def __init__(self):
        self.script = ""
        self.prompt = ""

class Game:
    """
    Encapsulates de entire terminal-based user experience.
    Contains logic for displaying instructions, handling user input,
    and displaying the current state of the maze after every move.

    Makes heavy use of the curses library (light wrapper over C's ncruses lib)
    to facilitate creating terminal-based user interfaces.
    """
    def __init__(self, stdscr):
        """
        Very little to setup at init. Most is done at start of each game.

        Params: stdscr is an instance of a curses object that is passed to the main function
        of the script through a wrapper function, which you'll see at end of file.
        """

        # Curses setup
        curses.curs_set(0) # Hide cursor to keep terminal clean. We never need it.
        self.screen = stdscr # Human readable attribute for curses object which corresponds to terminal screen.
        
        # Where to draw text and maze elements on the terminal
        self.__text_display_height = 5
        self.__maze_screen_coords = (10,self.__text_display_height)

    def start(self, width=17, height=9, intro=True):
        """Starts a new game with a fresh maze"""
        
        # We can modify the maze width and height parameters
        # to play with different sizes.
        #
        # Can set custom width and height in the params as well as a 
        # a bool to toggle playing the text intro or not.
        # TODO: Implement leveling up every time a game in completed.
        # 
        # CAUTION: curses will break if the terminal window can't 
        # fit the maze and text. The window will need to be resized.
        # I have no interest in diving into making the game responsive
        # and dynamic to the terminal window size. That's beyond scope.
        self.maze = Mystery_Maze(width,height) 

        # Self-explanatory attributes related to user and play
        self.player_position = self.maze.entry.coords
        self.start_time = time.time() 
        self.elapsed_time = 0

        # Clear out the terminal entirely between games.
        self.screen.clear()

        if intro:
            self.__play_intro() # Text-based introduction.

        self.__game_loop() # Main loop for play.

    def __play_intro(self):
        """
        The intro is made up of 3 lines, or screens of text.
        Each line has script text, and a prompt.
        This function mainly serves to setup.
        """
        line0, line1, line2 = Game_Line(), Game_Line(), Game_Line()
        line0.script = """You have entered the Mystery Maze... Welcome.\n...A shroud of fog engulfs you..."""
        line0.prompt = """(Press any key to continue)"""
        line1.script = """As you move, you may step into a clearing. A path forward? A dead end?\nOr... you may step into a wall!"""
        line1.prompt = """(Press any key to continue)"""
        line2.script = """With every move you map out the mystery.\n\nWith every move you step towards success."""
        line2.prompt = """(Press any key to begin)"""

        # For each line, display it
        intro = [line0,line1,line2]
        for line in intro:
            self.__display_line(line) # Where the display magic happens.

            # After display, wait for input before displaying next intro line.
            self.screen.nodelay(False) # This line ensures the call to getch() actually waits.
            self.screen.getch() # We won't check the input. Any character will sufice.

    def __display_line(self, line):
        """
        Displays text, one character at a time.
        """
        
        # Clear only the text area. This is helpful when we want to update
        # the text without needing to redraw the maze.
        for y in range(self.__text_display_height):
            self.screen.move(y, 0)
            self.screen.clrtoeol()
        
        # Re-position cursor at top left
        self.screen.move(0, 0)

        # Print one character at a time of the script, for typing-style effect. 
        # (a la Pokemon) ;)
        # If we receive any keystroke during line rendering, skip the typing effect
        # and render whole script quickly. 
        # (a la Pokemon) ;)
        self.screen.nodelay(True) # This ensures our call to getch() on line 281 ~does not~ wait
        types_quickly = False
        for char in line.script:
            # Render the type effect slowly as long as there has been no new user input
            # during the current loop or from a previous loop
            keystroke = self.screen.getch()
            types_quickly = types_quickly or keystroke != curses.ERR

            self.screen.addstr(char) 
            self.screen.refresh() # We want to refresh the screen as we go.
            if types_quickly:
                time.sleep(0.005) # We don't skip the animation entirely, but it's much quicker.
            elif char == "\n":
                time.sleep(0.75) # Longer pause, for dramatic effect, after a paragraph.
            else:
                time.sleep(0.05) # Standard speed.
        
        # The prompt won't have the typing effect. We display in one go i italics.
        if line.prompt:
            if not types_quickly:
                time.sleep(0.2) # But we do like our pauses.
            self.screen.addstr("\n\n"+line.prompt, curses.A_ITALIC) 
            self.screen.refresh()

    def __game_loop(self):
        """
        The main game logic. Includes display of instruction, maze, 
        and player position. Waits for player turn and updates the game state.
        Loops until game is completed.
        """

        # The main loop has the same instructions until game finish.
        loop_line = Game_Line() 
        loop_line.script = "You have entered the maze. How long will it take to find your way through?"
        loop_line.prompt = "Use the arrow keys to navigate your way through the shrouded maze."
        self.__display_line(loop_line) # Render text.

        # Reset time, so that the count begins only after the intro
        self.start_time = time.time() 
        self.screen.nodelay(True) # Don't wait at getch(), keep looping
        while True:
            # Update elapsed time
            self.elapsed_time = time.time() - self.start_time

            # Render each other element of the game.
            self.__display_maze()
            self.__display_user()
            self.__display_elapsed_time()

            # We can avoid refreshing the terminal view until after everything
            # is ready and save a bit of computation. This is unlike __display_line()
            self.screen.refresh() 

            # There's no waiting for input. char will be -1 if no input.
            # char == cursers.ERR == -1 if empty buffer
            # We want to keep looping to display close-to-live elapsed time
            char = self.screen.getch() 

            # If arrow key pressed, legal move. 
            # Note direction.
            if char == curses.KEY_RIGHT: 
                direction = Direction.EAST
            elif char == curses.KEY_LEFT: 
                direction = Direction.WEST
            elif char == curses.KEY_UP: 
                direction = Direction.NORTH
            elif char == curses.KEY_DOWN: 
                direction = Direction.SOUTH
            else:
                direction = False # Non-valid input. 
            
            if direction: 
                (was_success, new_position) = self.__take_step(direction)
                self.__display_step(direction, was_success)
                self.player_position = new_position # Move user only after step displayed
                # Note: new_position == player_position if was_success == False

                # Keep step displayed for a brief moment before continuing game loop
                # When loop continues, the step will disappear and the user will be 
                # displayed in latest position.
                self.screen.refresh()
                time.sleep(0.3) #TODO: I want to keep the step displayed while still refreshing the time...

            did_win = self.player_position == self.maze.exit.coords # Win condition

            if did_win:
                break # No need to continue game loop after win
        
        self.__display_finish()
 
    def __display_maze(self):
        """Displays the current state of the maze."""

        # The maze will be rendered below the text, so we need
        # some anchor coords.
        (maze_anchor_x, maze_anchor_y) = self.__maze_screen_coords

        # For each tile
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                tile = self.maze.grid[x,y]

                # Add grid coords (x, y relative to maze) to anchor coords
                display_x = maze_anchor_x + x 
                display_y = maze_anchor_y + y

                # Tile-specific display logic in other function
                self.__display_tile((display_x, display_y), tile)

            self.screen.addstr("\n") #newline after each row

        self.screen.addstr("\n") #newline after entire grid

    def __display_tile(self, coords, tile):
        """Displays a tile given its current state at given screen coords."""

        (screen_x, screen_y) = coords # Coordinates on terminal screen
        (tile_x, tile_y) = tile.coords
        

        # Some necessary setup for nice colors
        curses.start_color()
        curses.use_default_colors()

        curses.init_color(1, 500, 500, 500) # Gray
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE) # Black fg on white bg
        curses.init_pair(2, 1, curses.COLOR_BLACK) # Gray fg on black bg
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_WHITE) # White fg on white bg

        is_edge = tile_x == 0 or tile_x == self.maze.width - 1 or tile_y == 0 or tile_y == self.maze.height - 1
        is_entry = tile.coords == self.maze.entry.coords
        is_exit = tile.coords == self.maze.exit.coords

        if is_edge and not is_entry and not is_exit:
            # Edge tiles are solid white asterisks
            self.screen.addstr(screen_y, screen_x, "*", curses.color_pair(1))
        elif not tile.revealed:
            # Shrouded tiles are semi opaque gray 
            self.screen.addstr(screen_y, screen_x, "?", curses.color_pair(2) | curses.A_BOLD)
        elif not tile.path:
            # Wall tiles are solid white 
            self.screen.addstr(screen_y, screen_x, "█", curses.color_pair(3))
        else:
            # Revealed path tiles are blank.
            self.screen.addstr(screen_y, screen_x, " ", curses.color_pair(2))
        
        

    def __display_user(self):
        """Displays the current state of the user."""

        (maze_anchor_x, maze_anchor_y) = self.__maze_screen_coords
        (user_x, user_y) = self.player_position # Relative to maze

        # Some necessary setup for nice colors
        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK) # White foreground on black background

        user_char = "§" # "You are here"

        (x,y) = (maze_anchor_x + user_x, maze_anchor_y + user_y)
        self.screen.addstr(y, x, user_char, curses.color_pair(4) | curses.A_BOLD) # A nice bold, too

    def __display_elapsed_time(self):
        """Displays currently elapsed time."""

        play_time_str = str(round(self.elapsed_time,2)) # Keep to a couple of decimals
        display_str = f'Seconds: {play_time_str}'

        curses.start_color()
        curses.use_default_colors()
        
        (_, maze_anchor_y) = self.__maze_screen_coords
        x = 0 # Keep text flush to the left
        y = maze_anchor_y + self.maze.height + 2

        self.screen.addstr(y, x, display_str, 1)

    def __take_step(self, direction):
        """
        Reveals the tile under mark_coords.
        Returns tuple of (was_success, new_position).
        is_success true if the step was succesful, false otherwise.
        new_position only changes from player_position at success.
        """

        # Calculate destination coordinates for step from direction
        (x,y) = self.player_position
        if direction == Direction.NORTH:
            dest_coords = (x, y - 1)
        elif direction == Direction.SOUTH:
            dest_coords = (x, y + 1)
        elif direction == Direction.WEST:
            dest_coords = (x - 1, y)
        elif direction == Direction.EAST:
            dest_coords = (x + 1, y)

        (dest_x, dest_y) = dest_coords
        if dest_x < 0 or dest_x >= self.maze.width or dest_y < 0 or dest_y >= self.maze.height:
            # If steps outside of maze bounds, fail
            is_success = False
        else:
            # If step is legal, within grid, reveal destination tile.
            dest_tile = self.maze.grid[dest_coords]
            dest_tile.revealed = True
            
            # Success if stepping on path. Fail if wall.
            is_success = dest_tile.path

        if is_success: 
            next_position = dest_coords
        else:
            next_position = self.player_position
        
        return (is_success, next_position)

    def __display_step(self, direction, success):
        """Displays the last step."""

        (maze_anchor_x, maze_anchor_y) = self.__maze_screen_coords # Relative to terminal screen
        (user_x, user_y) = self.player_position # Relative to maze
        
        if direction == Direction.NORTH:
            (x, y) = (maze_anchor_x + user_x, maze_anchor_y + user_y - 1)
            user_char = "▲"
        elif direction == Direction.SOUTH:
            (x, y) = (maze_anchor_x + user_x, maze_anchor_y + user_y + 1)
            user_char = "▼"
        elif direction == Direction.WEST:
            (x, y) = (maze_anchor_x + user_x - 1, maze_anchor_y + user_y)
            user_char = "◄"
        elif direction == Direction.EAST:
            (x, y) = (maze_anchor_x + user_x + 1, maze_anchor_y + user_y)
            user_char = "►"

        # Some necessary setup for nice colors
        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_RED) # White fg, red bg. NOTE: Red not working locally
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_GREEN) # White fg, green bg.

        # Green for success. Red for failure.
        color_pair = curses.color_pair(6) if success else curses.color_pair(5)
        
        self.screen.addstr(y, x, user_char, color_pair | curses.A_BOLD) # Let's do bold, too.

    def __display_finish(self):
        """Displays the game finished screen."""

        play_time_str = str(round(self.elapsed_time,2))

        turn_line = Game_Line()
        turn_line.script = f'Congratulations. You made it to the exit in {play_time_str} seconds.'
        turn_line.prompt = "Press any key to play again."

        self.__display_line(turn_line)
        self.__display_maze()
        self.__display_user()

        # Wait for input of any character before we start a new game and intro
        self.screen.nodelay(False)
        self.screen.getch() # Any character will trigger.
        self.start(intro=False)

def main(stdscr):
    """Start of script. All logic lies within Game."""
    game = Game(stdscr)
    game.start()

curses.wrapper(main) # curses helper function to protect the terminal from breaking