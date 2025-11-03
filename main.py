"""
This module is a work in progress. After a major redesign 
from nascent proof of concept to a more mature architecture using
established design patterns much of the code here has either been
deprecated or has yet to be ported to the new design. Eventually,
all that will remian here is a command line interface for testing.
"""
import copy    # TODO: moved to puzzle module, remove if not needed after restructering
import random
from time import sleep
from enum import Enum, unique, auto         # TODO: moved to puzzle module, remove if not needed after restructering
import logging
import hashlib
import zlib
from importlib import import_module
from puzzles import *
from puzzles.sudoku import *
from tests import ut_data

# Globals
test_mode = True
logger = logging.getLogger(__name__)    # logger uses name of module
logging.basicConfig(filename="builder.log", 
                    format="%(asctime)s (%(levelname)s) %(message)s",
                    encoding='utf-8', 
                    level=logging.DEBUG)    #DEBUG   WARNING

def log(func, *args):   
    newMessage = (f"{__name__}: {args[0]}")  # using wrapper
    func(newMessage)

tab_size = 10

# Since we're dealing with squares, number of columns and rows (lines) are the same
BOX_LINE_SIZE = 3    # boxes are this number of cells across/high
GRID_LINE_SIZE = 9   # puzzle is this number of cells across/high

class LineType(Enum):
    ROW = 0
    COL = 1

@unique    # using this ensures unique values are assigned to enums, makes more sense if enum values are for masks
class TransformTypes(Enum):
    ROTATE_180 = auto()
    ROTATE_CW_90 = auto()
    ROTATE_CCW_90_old = auto()
    ROTATE_CCW_90 = auto()
    VERTICAL_FLIP = auto()
    HORIZONTAL_FLIP = auto()
    REFLECT_MAJOR = auto()       # Reflect matrix about major diagonal (upper left to lower right)
    REFLECT_MINOR = auto()       # Reflect matrix about minor diagonal (upper right to lower left)
    COLUMN_SWITCH_12 = auto()    # Switch 1st and 2nd columns
    COLUMN_SWITCH_13 = auto()    # Switch 1st and 3rd columns
    COLUMN_SWITCH_23 = auto()    # Switch 2nd and 3rd columns
    ROW_SWITCH_12 = auto()       # Switch 1st and 2nd rows
    ROW_SWITCH_13 = auto()       # Switch 1st and 3rd rows
    ROW_SWITCH_23 = auto()       # Switch 2nd and 3rd rows

@unique
class Difficulty(Enum):
    EASY = auto()
    MEDIUM = auto()
    HARD = auto()
    VERY_HARD = auto()



# The 9 letters considered most visually distinguishable in standard optical tests; helps testing
alpha_list = ['C', 'D', 'E', 'F', 'L', 'O', 'P', 'T', 'Z']  
numerals = ['1', '2', '3', '4', '5', '6', '7', '8', '9']


#######################################################################################################################
#######################################################################################################################
#######################################################################################################################
#######################################################################################################################
#
#           Everything below here is "old" stuff. Once it's updated move to above.
#
#
#######################################################################################################################
#######################################################################################################################
#######################################################################################################################
#######################################################################################################################
class Sudoku_old:
    # matrix has the following structure:
    #     [[Box Instance, Box Instance, Box Instance], [Box Instance, Box Instance, Box Instance], [Box Instance, Box Instance, Box Instance]]
    matrix = []  # THE matrix that gets populated with all (1 - 9) numerals
    flattened_matrix = []
    flattened_puzzle = []
    matrix_by_rows = []
    inventory = {}

    def init():
        Sudoku.matrix.clear()
        for row in range(3):   #!!!!!!!!!!!! Range stop values are EXCLUSIVE, so this iterates 0 - 2
            box_row = []       #!!!!!!!!!!!! Setting to open list actually creates a NEW (open) list and leaves the one previously appended to matrix alone
            for col in range(3):      #!!!!!!!!!!!!!! col is never incremented to 3; leaves loop at 2
                box_row.append(Box(row, col))
            Sudoku.matrix.append(box_row)


    def __str__(self):
        return Sudoku.create_puzzle_string(Sudoku.flattened_matrix)

    # Build the puzzle key with alpha chars; they'll get replaced w/ numerals later.
    def generate_matrix():
        for attempt in range(20):    # the number of iterations accomodates retries for failures
            status =  Status.PASSED
            Sudoku.init()
            for letter in alpha_list:   # iterate from 0 through 8
                status, backup_steps = place_char(0, 0, [], [], letter)
                # show_numbers()
                if status == Status.FAILED:
                    log(logger.debug, f"Failed to populate the matrix with '{letter}'s. Starting over...")
                    break           
            if status ==  Status.PASSED:
                break
            # else try to create puzzle key again

        Sudoku.flatten_grid()
        return status, Sudoku.create_puzzle_string(Sudoku.flattened_matrix)


    # Builds a single list of chars that represent all values in matrix
    # Used when drawing filled matrix
    def flatten_grid():
        rows = []
        Sudoku.flattened_matrix.clear()
           
        # Break out individual values from their rows
        for grid_row in range(3):
            for value_row in range(3):
                full_row = []
                for grid_col in range(3):
                    box = Sudoku.matrix[grid_row][grid_col]

                    row_of_values = box.get_row(value_row)
                    rows.append(row_of_values)

                    for value_col in range(3):
                        full_row.append(row_of_values[value_col])
    
                Sudoku.matrix_by_rows.append(full_row)           # persisting intermediate result for later use

        # Break out individual values from their rows
        for row in rows:
            for value in row:
                Sudoku.flattened_matrix.append(value)

    # Combine the separate box rows into single row for all matrix rows
    def reflect_major(list_to_reflect):
        reflected_list = [ [0 for _ in range(9)] for _ in range(9)]
        for row in range(len(list_to_reflect)):
            for col in range(len(list_to_reflect[row])):
                reflected_list[col][row] = list_to_reflect[row][col]
        return reflected_list

    @staticmethod
    def flatten_2d(puzzle_to_flatten):
        flat_puzzle = []
        for row in puzzle_to_flatten:
            for value in row:
                flat_puzzle.append(value)
        return flat_puzzle

    # Take a flattened puzzle and turn it into 9 rows of 9 values
    @staticmethod
    def unflatten_puzzle(flat_puzzle_to_expand):
        working_puzzle = copy.deepcopy(flat_puzzle_to_expand)
        flat_puzzle_to_expand.clear() 
        # changed_puzzle = []
        for row in range(9):
            working_row = []
            for value in range(9):
                working_row.append(working_puzzle[row * 9 + value])
                if value == 8:
                    # changed_puzzle.append(working_row)
                    flat_puzzle_to_expand.append(working_row)
                    continue

    def replace_with_numerals():
        # Randomly assign numerals to the characters used to build puzzle
        random.shuffle(numerals)    # mix up numeral list before using to substitute for alpha chars
        char_to_numeral_dict = {alpha_list[num] : numerals[num] for num in range(len(alpha_list))}   # dictionary comprehension

        new_puzzle = []
        for char in Sudoku.flattened_matrix:
            new_puzzle.append(char_to_numeral_dict[char] )

        return Sudoku.create_puzzle_string(new_puzzle)

    # this method doesn't access any class data so its use makes sense here
    @staticmethod 
    def create_puzzle_string(flattened_matrix):
        flat_grid_string = ""
        for char in flattened_matrix:
            flat_grid_string += str(char)

        encoded_puzzle = flat_grid_string.encode('utf-8')
        hashed_puzzle = hashlib.sha256(encoded_puzzle)
        compressed_puzzle = zlib.compress(encoded_puzzle)

        # log(logger.debug, f"Before string = {flat_grid_string}")
        # log(logger.debug, f"Encoded string = {encoded_puzzle}")
        # log(logger.debug, f"Hashed string = {hashed_puzzle.hexdigest()}")
        # log(logger.debug, f"Compressed string = {compressed_puzzle}")


        return flat_grid_string
    # Parameter is value of enum TranformType
    # Keep in mind the "flat puzzle" is a single list that is basically all the rows appended to the row(s) above it
    # Parameters:
    #       puzzle - puzzle to be transformed; a list of 9 matrix rows, each row is a list of 9 values
    #       transform_type - see class TransformTypes for the values
    #
    # Returns:
    #       tranformed puzzle in the same format (9 rows of 9 values) as was passed in
# TODO: make this dimension agnostic; it's currently geared toward 9 x 9 puzzles
    @staticmethod
    def transform_puzzle(puzzle, transform_type):
        transformed_puzzle = []

        if transform_type == TransformTypes.ROTATE_180:
            flattened_matrix = Sudoku.flatten_2d(puzzle)
            for item in reversed(flattened_matrix):
                transformed_puzzle.append(item)
            Sudoku.unflatten_puzzle(transformed_puzzle)
        
        elif transform_type == TransformTypes.ROTATE_CW_90:
            flattened_matrix = Sudoku.flatten_2d(puzzle)
            for itr in range(9):
                for item in range(8 - itr, len(flattened_matrix) , 9):
                    transformed_puzzle.append(flattened_matrix[item])
            Sudoku.unflatten_puzzle(transformed_puzzle)

        elif transform_type == TransformTypes.ROTATE_CCW_90_old:
            flattened_matrix = Sudoku.flatten_2d(puzzle)
            for row in range(9):
                for item in range(8 - row, len(flattened_matrix) , 9):
                    transformed_puzzle.append(flattened_matrix[item])
            Sudoku.unflatten_puzzle(transformed_puzzle)
        
        # 1st pass: 8,17,26,35,44,53,62,71,80,(89) 2nd: 7,16,25,34,43,52,61,70,79,(88) 3rd: 6,15,24,33,42,51,60,69,78,(87) 4th: 5,
        elif transform_type == TransformTypes.ROTATE_CCW_90:
            flattened_matrix = Sudoku.flatten_2d(puzzle)
            indx_generator = ( (x * 9 - 1) % 82 for x in range(1, len(flattened_matrix) + 1)  )
            for indx in indx_generator:
                transformed_puzzle.append(flattened_matrix[indx])
            Sudoku.unflatten_puzzle(transformed_puzzle)
        
        elif transform_type == TransformTypes.VERTICAL_FLIP:
        #NOTE: just reverse each row
            flattened_matrix = Sudoku.flatten_2d(puzzle)
            for row_end in range(8, len(flattened_matrix), 9):
                for cell in range(row_end, row_end - 9, -1):
                    transformed_puzzle.append(flattened_matrix[cell])
            Sudoku.unflatten_puzzle(transformed_puzzle)
    
        elif transform_type == TransformTypes.HORIZONTAL_FLIP:
            # Putting bottom row on top, next to botton to next to top, and so on...
            flattened_matrix = Sudoku.flatten_2d(puzzle)
            for row_ndx in range(72, -1, -9):
                transformed_puzzle += flattened_matrix[row_ndx : row_ndx + 9 : 1]    # string concatenation
            Sudoku.unflatten_puzzle(transformed_puzzle)

        elif transform_type == TransformTypes.REFLECT_MAJOR:
            transformed_puzzle = Sudoku.reflect_major(puzzle)
       
        elif transform_type == TransformTypes.REFLECT_MINOR:
            # First, reverse the order of the rows, then the values in each row ...
            puzzle.reverse()
            for row in puzzle:
                row.reverse()

            # ... then do the same transformation as the major reflection
            transformed_puzzle = Sudoku.reflect_major(puzzle)

        # Due to the way the tranformation is done no flattening is needed; it's being built flat
        elif transform_type == TransformTypes.COLUMN_SWITCH_12:
            for row in puzzle:
                for col in range(3, 6):
                    transformed_puzzle.append(row[col])
                for col in range(0, 3):
                    transformed_puzzle.append(row[col])
                for col in range(6, 9):
                    transformed_puzzle.append(row[col])
        
        # Due to the way the tranformation is done no flattening is needed; it's being built flat
        elif transform_type == TransformTypes.COLUMN_SWITCH_13:
            for row in puzzle:
                for col in range(6, 9):
                    transformed_puzzle.append(row[col])
                for col in range(3, 6):
                    transformed_puzzle.append(row[col])
                for col in range(0, 3):
                    transformed_puzzle.append(row[col])
        
        # Due to the way the tranformation is done no flattening is needed; it's being built flat
        elif transform_type == TransformTypes.COLUMN_SWITCH_23:
            for row in puzzle:
                for col in range(0, 3):
                    transformed_puzzle.append(row[col])
                for col in range(6, 9):
                    transformed_puzzle.append(row[col])
                for col in range(3, 6):
                    transformed_puzzle.append(row[col])
        
        elif transform_type == TransformTypes.ROW_SWITCH_12:
            for row in range(3):
                transformed_puzzle.append(puzzle[row + 3])
            for row in range(3):
                transformed_puzzle.append(puzzle[row])
            for row in range(3):
                transformed_puzzle.append(puzzle[row + 6])

        elif transform_type == TransformTypes.ROW_SWITCH_13:
            rows_switched = []
            for row in range(3):
                transformed_puzzle.append(puzzle[row + 6])
            for row in range(3):
                transformed_puzzle.append(puzzle[row + 3])
            for row in range(3):
                transformed_puzzle.append(puzzle[row])

        elif transform_type == TransformTypes.ROW_SWITCH_23:
            rows_switched = []
            for row in range(3):
                transformed_puzzle.append(puzzle[row])
            for row in range(3):
                transformed_puzzle.append(puzzle[row + 6])
            for row in range(3):
                transformed_puzzle.append(puzzle[row + 3])

        else:
            raise Exception("transform_puzzle() Unknown tranform requested.")

        return transformed_puzzle

    # Build dictionary where a char is the key and the value is a list of coordinates where that char occurs in the puzzle
    def take_inventory():
        Sudoku.inventory = {x : [] for x in alpha_list}
        for row in range( len(Sudoku.matrix_by_rows)):
            for col in range(len(Sudoku.matrix_by_rows[row])):
                Sudoku.inventory[Sudoku.matrix_by_rows[row][col]].append([col, row])


    def create_puzzle(difficulty):
        # mixup coordinate list for each char in matrix
        # Set up number of matrix values to remove based on difficulty
        if difficulty == Difficulty.EASY:
            # missing_values_distro = [7,6,6,5,5,5,5,4,4]   # the distro of occurances of values [2,3,3,4,4,4,4,5,5], so the occurances of empty spots is "9 - occurance"
            keep_distro = [2,3,3,4,4,4,4,5,5]    # TODO: more refinement needed here to be more random within a range
            random.shuffle(keep_distro)

        elif difficulty == Difficulty.MEDIUM:
            pass
        elif difficulty == Difficulty.HARD:
            pass
        else:
            pass

            # Create working list of coordinate lists where the coordinates per character have been shuffled to introduce randomness to cell locations being cleared 
        solved_puzzle = []
        for attempt in range(1000):

            working_inventory = []
            for key, value in Sudoku.inventory.items():
                random.shuffle(value)
                working_inventory.append(value)

            # Remove the number of entries that we want to keep for each character
            # this'll leave a list of coordinates of the cells to be blanked out
            complete_clear_list = []
            clear_list = []
            for itr in range(len(keep_distro)):
                del working_inventory[itr][0:keep_distro[itr]]
                clear_list.append(working_inventory[itr])  #remove clear_list and just use working_inventory
    
            #
            complete_clear_list = [coords for sublist in clear_list for coords in sublist]   # list comprehension
            for cell in complete_clear_list:
                Sudoku.matrix_by_rows[cell[1]][cell[0]] = " "    # Inventory coords are by [column][row], matrix_by_rows is [row] [column]   TODO: make consistent
        

            # run through "solver"
            solved_puzzle, successful = Sudoku.solve(Sudoku.matrix_by_rows)
            log(logger.info, f"Attempt {attempt} at solving puzzle {"was" if successful else "was not"} successfull.")   #ternary
            # Sudoku.matrix_by_rows = copy.deepcopy(solved_puzzle)

            if successful:
                break    

        show_numbers(Sudoku.matrix_by_rows)     


    # Determine if puzzle has unique solution
    # returns False if puzzle wasn't solved, True otherwise
    @staticmethod
    def solve(puzzle_by_rows):

        main_puzzle_updating = True
        while main_puzzle_updating:
        # Fill all the empty cells with options
            working_puzzle_by_rows = copy.deepcopy(puzzle_by_rows)
            for row in range(len(puzzle_by_rows)):
                for col in range(len(puzzle_by_rows[row])):
                    if puzzle_by_rows[row][col] == " ":
                        for char in alpha_list:
                            found = False
                        # iterate through each possible char to see if it exists in the box, row, or column and if not add it to the empty cell
                            # check row
                            for c in range(9):
                                if puzzle_by_rows[row][c] == char:
                                    found = True
                                    break
                            if found:
                                continue

                            # check column
                            for r in range(9):
                                if puzzle_by_rows[r][col] == char:
                                    found = True
                                    break
                            if found:
                                continue

                            # check box
                            box_col = col//3 * 3
                            box_row = row//3 * 3

                            for r in range(box_row, box_row + 3):
                                for c in range(box_col, box_col + 3):
                                    if puzzle_by_rows[r][c] == char:
                                        found = True
                                        break
                            if found:
                                continue

                            # if not there set as option for cell
                            if working_puzzle_by_rows[row][col] == ' ':
                                working_puzzle_by_rows[row][col] = char
                            else:
                                working_puzzle_by_rows[row][col] += char

            # For "solved" cells copy over values to main puzzle structure
            main_puzzle_updating = False
            for row in range(len(puzzle_by_rows)):
                for col in range(len(puzzle_by_rows[row])):
                    if len(working_puzzle_by_rows[row][col]) == 1:
                        if puzzle_by_rows[row][col] != working_puzzle_by_rows[row][col]:
                            puzzle_by_rows[row][col] = working_puzzle_by_rows[row][col]
                            main_puzzle_updating = True


        # Search all rows for singular occurance of chars in cells that have multiple candidates
        # When found replace the multi-candidate cell with that char
        changes_made = False
        for row_index in range(len(working_puzzle_by_rows)):
            if Sudoku.resolve_singulars(CellContext.ROW, row_index, working_puzzle_by_rows[row]):
                changes_made = True            
            else:   # clean up - below is for testing only
                pass

        # Search all columns for singular occurance of chars in cells that have multiple candidates
        # When found replace the multi-candidate cell with that char
        for column_index in range(len(working_puzzle_by_rows[0])):
            cell_column = []
            for row_index in range(len(working_puzzle_by_rows)):
                cell_column.append(working_puzzle_by_rows[row_index][column_index])

            if Sudoku.resolve_singulars(CellContext.COLUMN, column_index, cell_column):
                changes_made = True

                # move changes back to "official" copy of puzzle
                for row_i in range(len(working_puzzle_by_rows)):
                    working_puzzle_by_rows[row_i][column_index] =  cell_column[row_i]


            else:
                pass

        #!!!!!!!!!! TODO !!!!!!!!!!!!!!!!!  need to do what was done for rows and columns above for each box


        # Persist updated puzzle
        # puzzle_by_rows = copy.deepcopy(working_puzzle_by_rows)

        # Check to see if any indeterminate cells remain, which is an indication the puzzle isn't good
        for row_index in range(len(working_puzzle_by_rows)):
            for col_index in range(len(working_puzzle_by_rows[row_index])):
                if len(working_puzzle_by_rows[row_index][col_index]) > 1:
                    return working_puzzle_by_rows, False
        return working_puzzle_by_rows, True

    # searches the passed-in list for singular occurances of a char and replaces the cell's contents with that char
    @staticmethod
    def resolve_singulars(context, line_index, line):
        change_made = False
        search_str = ""
        for cell in line:
            if len(cell) > 1:
                search_str += cell

        #  Make list of chars that occur only once
        singular_chars = []
        for char in alpha_list:
            if search_str.count(char) == 1:
                singular_chars.append(char)
                
        for char in singular_chars:
            for cell in range(len(line)):
                if len(line[cell]) > 1:
                    if line[cell].find(char) != -1:
                        line[cell] = char
                        change_made =  True
                        break
        
        return change_made



# Puzzle end

#
# Contents of Box instances:
#
#  [[int, int, int], [int, int, int], [int, int, int]]
#
class Box:
    blank_box = [[0, 0, 0], [0, 0, 0], [0, 0, 0]] 
    open_cells = [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]]
    placement_mask = [[],[],[]]

    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.contents = copy.deepcopy(Box.blank_box)
        self.open_cells = copy.deepcopy(Box.open_cells)   # Accessing class variable

    def get_row(self, row_index):
        return self.contents[row_index]

    def open_list_is_empty(self):
        return True if len(self.open_cells) == 0 else False  # Ternary

    # remove line (row or column) already used by same number    
    def mask_line(self, line_type, line_nmbr):
        for ndx in range(len(self.open_cells) - 1, -1, -1):
            if self.open_cells[ndx][line_type.value] == line_nmbr:    # Line_index will place value on row (0) or column (1)
                del self.open_cells[ndx]
                if len(self.open_cells) == 0:
                    raise CellExcept("mask_line()")
 
    # Returns row and col of cell in which character was placed, or -1 for both if character couldn't be placed
    # Additionally, the chosen cell is removed from the open_cells list
    def randomly_place_char(self, num):
        try:
            cell_to_fill = self.open_cells[ random.randint( 0, len(self.open_cells) - 1 ) ]
        except ValueError as ex:
            raise CellExcept("randomly_place_char()")
     
        self.contents[cell_to_fill[0]][cell_to_fill[1]] = num     # Set value in box

        try:
            for ndx in range( len(self.open_cells) - 1, -1, -1):
                if self.open_cells[ndx][0] == cell_to_fill[0] and self.open_cells[ndx][1] == cell_to_fill[1]:
                    del self.open_cells[ndx]
        except:
            log(logger.warning, f"Could not find {cell_to_fill} to remove it from open_cells list.")  

        return cell_to_fill[0] , cell_to_fill[1]   # Return coordinates of cell just filled

    #
    def get_grid_coords(self):
        return self.row, self.col
 
    # TESTING: Puts numeral in given coord regardless of "open" status
    def set_numeral(self, row, col, numeral):
        self.contents[row][col] = numeral    # Set cell value 
    
        # If the cell was empty it's no longer empty so remove its entry from the open list
        if len(self.open_cells) == 0:
            return

        for ndx in range(len(self.open_cells) - 1, -1, -1):
            if self.open_cells[ndx][0] == row and self.open_cells[ndx][1] == col:
                del self.open_cells[ndx]

# end of Box




##################################################################################################################
# Place numeral in box if possible
# Recursively traverses matrix left to right, row by row
# Parameters:
#       grid_row, matrix col: matrix coordinates of box being modified
#       unavailable_rows, unavailable_cols: lists of rows/columns that intersect this box in which "numeral" has already been set
#                   Values are offsets relative to the matrix and so range from 0 to 8.
#                   Columns are relative from left side of matrix and rows are relative from top of matrix.
#       char - single alpha-numeric value being placed in box
#
# Return values:
#       status: Status.FAILED or Status.PASSED
#       back-track steps: the number of calls to back up in order to retry
def place_char(grid_row, grid_col, unavailable_rows, unavailable_cols, char):
    # Make all cells that lie on unavailable lines (rows and columns) unavailable
    # If this results in an empty available cell list for box we've got to back track
    masked_local_box_copy = copy.deepcopy(Sudoku.matrix[grid_row][grid_col])
    step_size = lambda col : 1 if col > 0 else 3     # using lambda

    try:
        for row_expanded in unavailable_rows:
            row = row_expanded - grid_row * 3     # adjust 0 - 8 row matrix-relative indices to 0 - 2 cell-relative indices
            if row >= 0 and row <=2:      # don't attempt to use any rows beyond box being worked on
                masked_local_box_copy.mask_line(LineType.ROW, row)
    
        for col_expanded in unavailable_cols:
            col = col_expanded - grid_col * 3       # adjust 0 - 8 col matrix-relative indices to 0 - 2 cell-relative indices
            if col >= 0 and col <=2:      # don't attempt to use any columns beyond box being worked on
                masked_local_box_copy.mask_line(LineType.COL, col)
    
    except CellExcept as ex:
        back_track_steps = step_size(grid_col)  # going back far enough to redo box above this one and forward
        log(logger.warning, f"After masking no empty cells were found; going back {back_track_steps} step(s).")
        return Status.FAILED, back_track_steps

    #
    # Find placement for this iteration as well as handle failed/passed returns from downstream recursive calls
    #
    for iteration in range(9):  # try a few times to find a placement if previous attempts failed

        # Attempt to find an empty cell to put numeral into
        try:
            found_row, found_col = masked_local_box_copy.randomly_place_char(char)
        except CellExcept as ex:
            back_track_steps = step_size(grid_col)  # going back far enough to redo box above this one and forward
            log(logger.warning, f"Failed to find empty cell for {char} in box [{grid_row}][{grid_col}], going back {back_track_steps} steps and retrying.")
            return Status.FAILED, back_track_steps

        # Start rolling up the recursion stack if we've made all the way through the matrix
        if grid_col == 2 and grid_row == 2:
            Sudoku.matrix[grid_row][grid_col].set_numeral(found_row, found_col, char)
            return Status.PASSED, 0

        unavailable_rows_to_pass_down = copy.deepcopy(unavailable_rows)
        found_row_expanded = found_row + 3 * grid_row     # Adjust box coords (0-2) to matrix coords (1-9)
        unavailable_rows_to_pass_down.append(found_row_expanded)

        unavailable_cols_to_pass_down = copy.deepcopy(unavailable_cols)
        found_col_expanded = found_col + 3 * grid_col     # Adjust box coords (0-2) to matrix coords (1-9)
        unavailable_cols_to_pass_down.append(found_col_expanded)

        # Determine next box to process, it's either next in same row or if just finished row go to the front of the next row
        next_grid_row = grid_row
        next_grid_col = grid_col
        if grid_col == 2:
            next_grid_col = 0
            next_grid_row += 1
        else:
            next_grid_col += 1   # same row, just move to right
    
        # 
        # Continue down the rabbit hole
        status, back_track_steps = place_char(next_grid_row, next_grid_col, unavailable_rows_to_pass_down, unavailable_cols_to_pass_down, char)

        if status == Status.FAILED:
            back_track_steps -= 1
            if back_track_steps == 0:
                continue   # Attempt to find another placement here in hopes it will avoid another downstream failure
            else:
                return Status.FAILED, back_track_steps
        else:
            break
    # End of recursion loop

    # Downstream placements were successful so make changes permanent as we roll up the recursion stack
    Sudoku.matrix[grid_row][grid_col].set_numeral(found_row, found_col, char)
    return Status.PASSED, 0

# Testing methods
# 1st
show_puzzle = True
def show_grid():
    if show_puzzle is True:
        soduku_drawing.draw_grid()

# 2nd
# parameter is a matrix of 9 rows of 9 values each
def show_numbers(puzzle_to_show):
        if show_puzzle is True:
            flattened_matrix = Sudoku.flatten_2d(puzzle_to_show)
            log(logger.info, f"\t\t   {flattened_matrix}")
            # if len(flattened_matrix) != 0 and not type(flattened_matrix[0]) is list:     # example of type() and logical operators
            soduku_drawing.fill_drawn_grid(flattened_matrix)
            sleep(15)
            # else:
            #     raise Exception("show_numbers() flattened_matrix is not a simple list.")

# 3rd
def wait_for_drawing_closure():
    if show_puzzle is True:
        soduku_drawing.wait_on_drawing()



########################################################################################
def main():

#TODO: debug why 16x16 puzzle threw "maximum recursion depth exceeded" exception

    try:

        print("Enter 'exit' to leave")
        print("Options: build, solve, ...")

        while True:
            command = input("What would you like to do?\n> ")
            if command == "exit":
                break

            # if command == "solve":
            #     try:
            #         file = input("Module containing puzzle to solve ([filename].py): ")
            #         pzl_module = import_module(file)
            #         pzl_name = input("Puzzle name: ")
            #         pzl = getattr(pzl_module, pzl_name)
                    
                    
            #         placeholder = input("Placeholder (defaults to space): ")

            #         builder = SudokuBuilder(pzl, placeholder)   # chal_puzzle_262   hard_puzzle_189 hard_puzzle_189x   easy_puzzle_21  puzzle_16x16_xx
            #         sudoku_puzzle = builder.get_puzzle()
            #         log(logger.info, sudoku_puzzle.puzzle_log())
            #         sudoku_solver = SudokuSolver(sudoku_puzzle)
            #         sudoku_solver.solve()
            #         solved_puzzle = sudoku_solver.get_puzzle()
            #         num_unsolved = solved_puzzle.unsolved_cell_count()
            #         log(logger.info, f"Number unsolved cells = {num_unsolved}")
            #         log(logger.info, solved_puzzle.puzzle_log())
            #         print(f"Number unsolved cells = {num_unsolved}")
            #         print(f"{solved_puzzle.puzzle_log()}")

            #     except Exception as ex:
            #         print(f"Error: {ex}; please try again.")

            # elif command == "build":
            #     pass
            # else:
            #     print(f"Unknown command {command}")

            # continue


# TODO: after building prompts for below tests remove
            # testing medium sudoku solution
            if command == '1':
                builder = SudokuBuilder(ut_data.hard_puzzle_189, placeholder = ' ')   # chal_puzzle_262   hard_puzzle_189 hard_puzzle_189x   easy_puzzle_21  puzzle_16x16_xx
                sudoku_puzzle = builder.get_puzzle()
                log(logger.info, sudoku_puzzle.puzzle_log())
                sudoku_solver = SudokuSolver(sudoku_puzzle)
                sudoku_solver.solve()
                solved_puzzle = sudoku_solver.get_puzzle()
                num_unsolved = solved_puzzle.unsolved_cell_count()
                log(logger.info, f"Number unsolved cells = {num_unsolved}")
                log(logger.info, solved_puzzle.puzzle_log())
                thing = str(solved_puzzle)
                # log(logger.info, f"!!!!!!!!! pzl string =  {str(solved_puzzle)}")


            #test puzzle creation
            elif command == '2':
                # builder = SudokuBuilder(all_possible_values = ['1', '2', '3', '4', '5', '6', '7', '8', '9'], placeholder = ' ')   # chal_puzzle_262   hard_puzzle_189   easy_puzzle_21  puzzle_16x16_xx
                builder = SudokuBuilder()
                sudoku_puzzle = builder.get_puzzle()

                if sudoku_puzzle.fill() == Status.FAILED:
                    log(logger.info, "Failed to generate puzzle.")
                else:
                    log(logger.info, sudoku_puzzle.puzzle_log())

            #test puzzle creation using partially filled puzzle
            elif command == '3':
                try:
                    builder = SudokuBuilder(ut_data.chal_puzzle_262)
                    sudoku_puzzle = builder.get_puzzle()
                    log(logger.info, sudoku_puzzle.puzzle_log())

                    if sudoku_puzzle.fill() == Status.FAILED:
                        log(logger.info, "Failed to generate puzzle.")
                    else:
                        log(logger.info, f"Puzzle successfully built.")
                except Exception as ex:
                    log(logger.error, f"main() Exception thrown while generating Sudoku puzzle: {ex}")


            elif command == '4':
                #sys.setrecursionlimit(2000)
                builder = SudokuBuilder(dimension = 16, all_possible_values = ['1','2','3','4','5','6','7','8','9','a','b','c','d','e','f','g'], placeholder = ' ')
                sudoku_puzzle = builder.get_puzzle()
                if sudoku_puzzle.fill() == Status.FAILED:
                    log(logger.info, "Failed to generate puzzle.")
                else:
                    log(logger.info, sudoku_puzzle.puzzle_log())

            elif command == '5':
                try:
                    builder = SudokuBuilder(ut_data.puzzle_16x16)
                    sudoku_puzzle = builder.get_puzzle()
                    log(logger.info, sudoku_puzzle.puzzle_log())

                except Exception as ex:
                    log(logger.error, f"main() Exception thrown while generating Sudoku puzzle: {ex}")


            elif command == '6':
                builder = SudokuBuilder(ut_data.hard_puzzle, placeholder = ' ')
                puzzle = builder.get_puzzle()
                solver = SudokuSolver(puzzle)
                solver.solve()
                solved_puzzle = solver.get_puzzle()

                builder = SudokuBuilder(ut_data.hard_puzzle_solved, placeholder = ' ')
                solution = builder.get_puzzle()
                if solved_puzzle == solution:
                    pass
                else:
                    pass
                # self.assertEqual(solved_puzzle, solution)

            elif command == '7':
                builder = SudokuBuilder()
                sudoku_puzzle = builder.get_puzzle()
                sudoku_puzzle.fill()
                log(logger.info, sudoku_puzzle.puzzle_log())


        # end of while

    except Exception as ex:
        log(logger.info, f"{ex}")


if __name__ == "__main__":
    main()

