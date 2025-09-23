"""
This module extends classes defined in the puzzle module and defines new classes used for building and solving Sudoku puzzles.
""" 
from puzzle import *
import math
import logging
from enum import Enum, auto      #, unique

__all__ = ['SudokuPuzzle','SudokuPuzzleBuilder','SudokuSolver','BoxIterator','SudokuCell','SudokuCellFactory','SudokuErrors','SudokuBuildError','PlaceStatus']

logger = logging.getLogger(__name__)    # logger uses name of module
logging.basicConfig(filename="builder.log", 
                    format="%(asctime)s (%(levelname)s) %(message)s",
                    encoding='utf-8', 
                    level=logging.DEBUG)

def log(func, *args):
    newMessage = (f"{__name__}: {args[0]}")  #using wrapper
    func(newMessage)


class SudokuErrors(Exception):
    def __init__(self, err_msg):
        super().__init__(err_msg)

class SudokuBuildError(Exception):
    def __init__(self, err_msg):
        super().__init__(err_msg)

class PlaceStatus(Enum):
    """
    Used to indicate results of attempt to place value in cell.
    """
    PASSED = auto()
    FAILED = auto()

class SudokuCell(Cell):
    """
    This concrete class builds upon the superclass by defining a "box" 
    context and methods to aid Sudoku puzzle solving. 
    """
    def __init__(self, value, row_index = -1, column_index = -1, placeholder = DEFAULT_PLACEHOLDER):

        if len(value) > 1:
            raise CellExcept(f"Initial Sudoku cell values must only be 1 character; '{value}' is too long.")
        
        super().__init__(value, row_index, column_index, placeholder)

    def set_next_cell_in_box(self, next_cell):
        self.next_cell_in_box = next_cell

    def set_box_number(self, box_number): 
        self.box_number = box_number

    def get_next_cell_in_box(self):
        return self.next_cell_in_box

    def box_iter(self):
        """
        Returns iterator for cell's box.

        :return: Iterator for cell's box
        :rtype: BoxIterator
        """
        return BoxIterator(self)

    def remove_value_from_view(self): 
        """
        Remove cell's value from all contexts, i.e., all cells within its view.
        """          
        self.remove_value_from_context(self.row_iter())
        self.remove_value_from_context(self.column_iter())
        self.remove_value_from_context(self.box_iter())

    def set_box_number(self, box_number):
        self.box_number = box_number

    # Returns True if able to set cell to value, False otherwise
    def set_if_no_conflict(self, value):
        if len(self) != 0:
            return False

        if self.value_exists_within_view(value) is True:
            return False
        
        self.contents = value
        return True
    
    def value_exists_within_view(self, value):           
        if self.value_in_context(self.row_iter(), value) is True:
            return True
        if self.value_in_context(self.column_iter(), value) is True:
            return True
        if self.value_in_context(self.box_iter(), value) is True:
            return True
        return False

class SudokuCellFactory(CellFactory):
    def __init__(self):
        self.type = "Sudoku"

    def new_cell(self, value, row_index = -1, column_index = -1, placeholder = DEFAULT_PLACEHOLDER):
        return SudokuCell(value, row_index, column_index, placeholder)

class BoxIterator(CellIterator):
    def __init__(self, cell):
        super().__init__(cell, CellContext.BOX)

    def __next__(self):
        if self.stop is True:
            raise StopIteration

        cell = self.next_cell
        self.next_cell = self.next_cell.get_next_cell_in_box()

        # The original cell was the first one returned. If we're back to it 
        # we've finished the circularly liked cell box list.
        if self.next_cell == self.first_cell:
            self.stop = True
 
        return cell

class SudokuPuzzle(Puzzle):
    """
    This class extends Puzzle by adding Sudoku specific processing: box
    searches, pattern operations, and other specific validation and actions.
    """
    def __init__(self, all_value_options, dimension):

        box_float_dimension = math.sqrt(dimension)
        self.box_dimension = int(box_float_dimension)
        self.all_value_options = all_value_options

        # Create dict to use as working structure for tracking which cells are used for each value
        self.empty_options_dict = {value : set() for value in all_value_options}            #using dict comprehension

        self.dimension = dimension
        super().__init__(dimension, dimension)

    def get_box_dimension(self):
        return self.box_dimension

    # Param is box number with the upper left being #1 down to the last on in the lower right
    # Returns the upper left cell of box
    def get_first_cell_in_box(self, box_number):
        if box_number < 1 and box_number > self.dimension:
            raise PuzzleExcept(f"Box number ({box_number}) must be between 1 and the puzzle dimension {self.dimension}.")

        puzzle_row    = int( (box_number - 1) / self.box_dimension) * self.box_dimension
        puzzle_column =    ( (box_number -1) * self.box_dimension ) % self.dimension
        return self.matrix[puzzle_row][puzzle_column]
    
    def get_context_iterator(self, context_type, number):

        if context_type == CellContext.ROW:
            first_cell = self.get_first_cell_in_row(number)            
            return first_cell.row_iter()

        if context_type == CellContext.COLUMN:
            first_cell = self.get_first_cell_in_column(number)            
            return first_cell.column_iter()

        if context_type == CellContext.BOX:
            first_cell = self.get_first_cell_in_box(number)            
            return first_cell.box_iter()
        
        return None

    def fill(self) -> PlaceStatus:
        """
        This method fills out a Sudoku puzzle which may start empty or
        with any number of values. Since native randomization is pseudo-
        random, two randomizing steps are used to increase randomness;
        value options are randomized and then assigned to random cells 
        within Sudoku boxes. A systematic, trial and error approach is  
        taken, moving through the boxes making assignments and applying  
        logic to determine minimum backtrack steps to optimize the process.

        :return: FAILED returned if unable to find cell in box to place value,
            PASSED otherwise.
        :rtype: PlaceStatus enum
        """
        try:
            # Generate a randomly sorted list of values to place
            rand_vals = self.all_value_options
            random.shuffle(rand_vals)

            for attempt in range(1, 1000):   # 8 is plenty when starting from scratch
                for val in rand_vals:
                    log(logger.debug, f"SudokuPuzzle.fill() Attempting to place {val} ...")   
                    status, cnt = self.place_value(val, 1)

                    if status == PlaceStatus.PASSED:
                        log(logger.debug, f"SudokuPuzzle.fill() Successfully placed all {val}s.")
                        log(logger.info, self.puzzle_log())
                    else:
                        log(logger.info, self.puzzle_log())
                        log(logger.warning, f"SudokuPuzzle.fill() Attempt {attempt} failed; starting over...")
                        self.clear()
                        break

                if status == PlaceStatus.PASSED:
                    break

            return status
        except Exception as ex:
            raise PuzzleExcept(f"SudokuPuzzle.place_value() {ex}.")

    #
    # TODO: use self.dimension to stop recursion
    #
    def place_value(self, value, box_num, backup_count = 0):
        """
        Recursively called method that places given value in the given puzzle
        box. If a value can't be placed the number of recursive steps to back
        up will be returned. The value is constant during this process but
        the box number is incremented for each call. Number of backup steps
        depends on location of box and returns the process to the point
        that a different placement will most likely be impactful.

        :parameter value: Value to place.
        :type value: Usually an integer, but could be anything.
        :parameter box_num: Box to place the given value. Boxes are numbered from 1 to 9 (typically) starting in upper left and going right then down until eventually reaching the 9th box in the lower right.
        :type box_num: Integer value from 1 to puzzle dimension, typically 9.
        :parameter backtrack: The number of recursion steps to go back up the call stack to redo.
        :type backup_count: Integer

        :return: FAILED returned if unable to find cell in box to place value, PASSED otherwise.
        :rtype: PlaceStatus enum
        """
        try:
            log(logger.debug, f"SudokuPuzzle.place_value() attempting to place {value} in box #{box_num}.")   
            get_backup_count = lambda: self.box_dimension if box_num % self.box_dimension == 1 else 1

            eligible_cells = self.eligible_box_cells(box_num, value)
            log(logger.debug, f"SudokuPuzzle.place_value() value {value}, box #{box_num}, eligible_cells size is {len(eligible_cells)}.")   
            if len(eligible_cells) == 0:
                backup_count = get_backup_count()
                log(logger.debug, f"SudokuPuzzle.place_value() Failed to find any eligible cells in box #{box_num} to place a {value}, backing up {backup_count} step(s).")   


                return PlaceStatus.FAILED, backup_count   
# !!!!! TODO: review this logic for encountering box that already has value in it            
            # This covers the case where box was initialized with this value and so doesn't need to be set
            elif len(eligible_cells) == 1 and value in eligible_cells[0].contents:
                log(logger.debug, f"SudokuPuzzle.place_value() {value} already exists in box #{box_num}.")   
                if box_num == self.dimension:
                    return PlaceStatus.PASSED, 0
                status, backup_count = self.place_value(value, box_num + 1)
                backup_count -= 1

                # Can't make changes here, but continue backtracking to a box where it can make a difference
                if backup_count == 0:
                    backup_count = get_backup_count()
#TODO: determine:
# should a bakcup_count decrement still happen, and if == 0 set to 1?

                return status, backup_count    # Just pass back up since nothing changed in this step

            # Introduce 2nd level of randomization
            rand_eligible_cells = random.sample(eligible_cells, len(eligible_cells))

            for ndx in range(len(rand_eligible_cells) - 1, -1, -1):
                log(logger.debug, f"SudokuPuzzle.place_value() setting {value} in box #{box_num}.")   
                if not rand_eligible_cells[ndx].set(value):
                    log(logger.debug, f"SudokuPuzzle.place_value() Cell is immutable; unable to set value.")   
               
                # Successfully placed value throughout puzzle, return up the recursion stack
                if box_num == self.dimension:
                    return PlaceStatus.PASSED, 0

                # Attempt to place value in next box; will end up back here if downstream step failed.
                status, backup_count = self.place_value(value, box_num + 1)
                if status == PlaceStatus.PASSED:
                    # Will only reach here if going back up stand if successfully placed value in ALL cells
                    return PlaceStatus.PASSED, 0

                # Some downstream attempt failed, undo all placements as rolling up the recursion stack
                rand_eligible_cells[ndx].clear()
                backup_count -= 1
                if backup_count != 0 and box_num != 1:
                    return PlaceStatus.FAILED, backup_count

                # Remove last candidate cell since it didn't turn out so well
                del rand_eligible_cells[ndx]
                log(logger.debug, f"SudokuPuzzle.place_value() Length of box #{box_num} eligible cells is {len(rand_eligible_cells)}.")   

            # End of loop

            backup_count = get_backup_count()
            log(logger.debug, f"SudokuPuzzle.place_value() Failed to place {value} in box #{box_num}, backing up {backup_count} step(s).")   
            return PlaceStatus.FAILED, backup_count
        except Exception as ex:
            raise PuzzleExcept(f"SudokuPuzzle.place_value() {ex}.")

    def eligible_box_cells(self, box_num, value):
        """
        Returns a list of Cells belonging to the given box that have  
        neither row nor column value conflicts.
        
        :parameter box_num: Number of box for which to build list.
        :type box_num: int from 1 to dimension
        :parameter value: Value for which to ensure there are no conflicts.
        :type value: int (typically, but could be anything)
        :return: List of Cells without row/column value conflicts
        :rtype: Cell list
        """
        try:
            box_iter = self.get_context_iterator(CellContext.BOX, box_num)
            open_cells = []
            for cell in box_iter:
                # If value already exists in box it must have been set when puzzle built, return this single cell to indicate this is the case
                if value in cell.contents:
                    return [cell]
                if cell.empty():
                    open_cells.append(cell)

            for ndx in range(len(open_cells) - 1, -1, -1):
                iter = open_cells[ndx].row_iter()
                if open_cells[ndx].value_in_context(iter, value):
                    del open_cells[ndx]
                    continue
                
                iter = open_cells[ndx].column_iter()
                if open_cells[ndx].value_in_context(iter, value):
                    del open_cells[ndx]
                    continue
                
            return open_cells
        except Exception as ex:
            raise PuzzleExcept(f"SudokuPuzzle.eligible_box_cells() {ex}.")

    def fill_empty_cells_with_options(self):
        """
        Helper method for solution algorithm that fills all empty cells
        with all possible values.
        """
        for row in range(1, self.row_dimension + 1):
            first_cell = self.get_first_cell_in_row(row)            
            cell_iter = first_cell.row_iter()
            for cell in cell_iter:
                if cell.empty():
                    cell.set(copy.deepcopy(self.all_value_options))

    def normalize(self):
        """
        Once a cell is solved this method is called to remove its value
        from all of its contexts maintaining the primary Sudoku rule that
        a value must not occur more than once in any row, column, or box.
        """
        for row in range(1, self.dimension + 1):
            first_cell = self.get_first_cell_in_row(row)            

            # For each "solved" cell, search through all the cell's contexts and remove instances of the given value
            cell_iter = first_cell.row_iter()
            for cell in cell_iter:
                if len(cell) == 1:
                    cell.remove_value_from_view()

    def apply_to_all_contexts(self, func_to_apply ):
        change_made = True
        overall_change_made = False
        count = 0

        while change_made:
            change_made = False
            for row in range(1, self.dimension + 1):
                change_made = func_to_apply(CellContext.ROW, row) or change_made

            for column in range(1, self.dimension + 1):
                change_made = func_to_apply(CellContext.COLUMN, column) or change_made

            for box in range(1, self.dimension + 1):
                change_made = func_to_apply(CellContext.BOX, box) or change_made

            count += 1
            overall_change_made = overall_change_made or change_made

        log(logger.debug, f"{count} passes required to finish.")
        return overall_change_made


    # Creates dictionary for given context with a value as the key and a list of cells that include that value in their contents
    def cells_per_value_dict(self, iter, min_size=1, max_size=100):   #TODO: determine more graceful way to specify max size, using self.dimension if possible
        try:

            options_dict = copy.deepcopy(self.empty_options_dict)
            for cell in iter:
                if cell.empty():
                    continue
                for value_key in cell:
                    options_dict[value_key].add(cell)  # include cell in set for value

            if min_size != 1 or max_size != 9:
                working_options_dict = copy.deepcopy(options_dict)
                for value, cell_list in working_options_dict.items():
                    if len(cell_list) < min_size or len(cell_list) > max_size:
                        del options_dict[value]

            # Sorting dictionary to aid testing
            return_dict = dict(sorted(options_dict.items()))
            return return_dict
        except Exception as ex:
            log(logger.info, f"cells_per_value_dict(): {ex}")
            

    # Method takes iterator of a context (row, column, or box), finds values that occur only once  
    # in that context (are unique) and replaces the found cell's contents with just that value
    def resolve_uniques_in_context(self, context_type, context_number) -> bool:
        """
        Searches all cells within passed in context for values that exist
        only once (are unique). Once a unique value is found, the containing
        cell's contents is set to just that value (removing all other values).

        :parameter context_type: 
        :type context_type: CellContext Enum
        :parameter context_number: Value from 1 to puzzle dimension that 
            represents the context number.
        :type context_number: int
        :return: True if any changes were made; otherwise False.
        :rtype: bool
        """
        iter = self.get_context_iterator(context_type, context_number)   
        working_options_dict = self.cells_per_value_dict(iter, max_size=1)

        # For any values that occur only once (are unique) in the context replace the host 
        # cell's contents with just that value and normalize all that cell's contexts
        change_made = False
        for key, cells in working_options_dict.items():          # dictionary iteration not using "key and value"
            # If value only exists in one cell of the context...
            for cell in cells:
                if len(cell) > 1:
                    cell.set(key)   # replace all values w/ the single, unique value
                    cell.remove_value_from_view()
                    change_made = True

        return change_made

    #
    def intersecting_context_resolution(self):
        change_made = True
        count = 0
        while change_made:            # For each row in puzzle ...
            change_made = False
            for row_num in range(1, self.dimension + 1):
                first_cell = self.get_first_cell_in_row(row_num)            
                cell_iter = first_cell.row_iter()
                change_made =  self.find_intersection_with_box(cell_iter) or change_made

            # For each column in puzzle ...
            for column_num in range(1, self.dimension + 1):
                first_cell = self.get_first_cell_in_column(column_num)            
                cell_iter = first_cell.column_iter()
                change_made = self.find_intersection_with_box(cell_iter) or change_made

            count += 1

        log(logger.debug, f"{count} passes required to solve puzzle.")

#TODO: Throughout, find alternative word for "value" as it gets confused with keywords

    def find_intersection_with_box(self, line_iter):
        # ... build dictionary of counts for each possible value ...
        working_options_dict = self.cells_per_value_dict(line_iter, min_size=1, max_size=9)

        #  ... and for each value that shows up 2 or 3 times ...
        changed = False
        for value, cells in working_options_dict.items():          #using dictionary iteration
#TODO: is below test needed since the dict build should only return the right lengths?
            changed = False

            # If all found cells are in same box ...
            found_box_cells = set()
            for cell in cells:
                box_number = cell.box_number
                found_box_cells.add(box_number)

            if len(found_box_cells) != 1:
                continue   # If all found cells aren't in same box keep looking

            # Protect found cells from having this value removed while  
            # removing it from the rest of the relevant row/column and box
            for cell in cells:
                cell._set_immutable(True)

            cell_list = list(found_box_cells)
            only_cell = cell_list[0]
            # ...remove all instances of the value in other cells of the box
            changed = self.remove_value_from_context(CellContext.BOX, box_number, value) or changed

            # Make them all non-immutable again
            for cell in cells:
                cell._set_immutable(False)

        return changed

    
    # Identify value combinations within a context and use to remove extraneous values
    def combo_reduction(self, context_type, context_number):

        log(logger.debug, f"Original puzzle:")
        self.puzzle_log()   #TODO: debug only, remove once working
        change_made = False
        try:
            combo_size_max = 1
            # TODO: determine if set.intersection would be helpful here

            # loop thru list of counts, trying to find "reducable" combinations, starting with smallest combinations that involve groups of 2 values
            processed_value_combos = []
            while True:
                combo_size_max += 1
                build_context_itr = self.get_context_iterator(context_type, context_number)   

                # Get lists of the cells that each value is in
                cells_per_value = self.cells_per_value_dict(build_context_itr, min_size=2) # This may change from one iteration to the next; using param name in call

                # If the size of combinaitons we're looking for = the number of values that exist in > 1 cell, it's time to stop

                #TODO: could probably stop sooner here; come up with mathematical rationale for a lower number, 
                if combo_size_max == len(cells_per_value) - 2:
                    break

                while True:
                    change_just_made = False

                    for subject_value, cells in cells_per_value.items():          #using dictionary iteration

                        # Only interested in values that have a certain number/range of occurances

                                #TODO: !!!! Not sure whether to leave this logic in; thought is that it's cells with combo_size_max values turn as the previous sizes had their turn
                        if len(cells) != combo_size_max:
                            continue

                        # Start the list of values with the "subject" value; this will be built upon in the following loop(s) 
                        value_collection = {subject_value} 
                        cell_set = cells.copy()          #using ".copy()" instead of just ".copy" for shallow copy
                        cell_set = set()

                        log(logger.debug, f"\ncombo_reduction() calling find_combination() with value {subject_value}")
                        value_collection, cell_set = self.find_combination2(cells_per_value, subject_value)
                        log(logger.debug, f"combo_reduction(): find_combination() returned value combination {str(value_collection)}")

                        if len(value_collection) > 0 and set(value_collection) not in processed_value_combos:

                            # Combination already handled, let's not mess with it again
                            processed_value_combos.append(value_collection)

                            # Once we've found our reduction combination of values use them to remove values
                            for cell in cell_set:
                                change_just_made = cell.remove_all_but(value_collection) or change_just_made

                            # Protect found cells from having this value removed while removing it from the rest of the relevant row/column and box
                            for cell in cell_set:
                                cell._set_immutable(True)

                            # For all other cells in context remove the combination values
                            replacement_context_iterator = self.get_context_iterator(context_type, context_number)
                            change_just_made = self.remove_values_from_context(replacement_context_iterator, value_collection) or change_just_made

                            for cell in cell_set:
                                cell._set_immutable(False)

                            if change_just_made:
                                log(logger.debug, f"Puzzle updated:")
                                self.puzzle_log()   #TODO: debug only, remove once working

                        #   end of combo processing if block

                        if change_just_made:   # If context just modified leave loop and refresh the value count list
                            break

                    #   end of inner combo search loop

                    if change_just_made:        # If context just altered, refresh the values count list
                        change_made = True
                        change_just_made = False

                        build_context_itr = self.get_context_iterator(context_type, context_number)   
                        cells_per_value = self.cells_per_value_dict(build_context_itr, min_size=2) # This may change from one iteration to the next
                    else:
                        break
                #   end of outter combo search loop

                return change_made
            
        except Exception as ex:
            raise SudokuErrors(f"Exception in combo_reduction(): {ex}")


    def find_combination2(self, cells_per_value_dict, subject_value):

        root_cell_set = cells_per_value_dict[subject_value]
        number_unsolved_cells = len(cells_per_value_dict)

        # Build set of "other" values
        values = set()
        for cell in root_cell_set:
            for value in cell:
                if value != subject_value:
                    values.add(value)

        combo_cell_set = root_cell_set
        combo_values = {subject_value}
        for value in values:

            temp_cell_set = combo_cell_set.copy()
            for cell in cells_per_value_dict[value]:
                temp_cell_set.add(cell)

            if len(temp_cell_set) >= number_unsolved_cells - 1:
                continue
            else:
                combo_values.add(value)
                combo_cell_set = temp_cell_set.copy()

        # Number of values must match the number of cells or it's no good
        if len(combo_values) != len(combo_cell_set):
            return set(), set()

        return combo_values, combo_cell_set
    

    def find_combination(self, cells_per_value_dict, root_value, value_set, cell_set, iter=0):
        iter += 1
        found_value_set = found_cell_set = set()
        try:

            # root_value is start of next recursive branch
            working_cell_set = cells_per_value_dict[root_value]
            log(logger.debug, f"find_combination({iter}) TOP: root value {root_value}   value set {value_set}   cell set {[str(c) for c in cell_set]}   working cell set {[str(c) for c in working_cell_set]}")  #using list comprehension
            new_cell_found = False
            for cell in working_cell_set:

                if cell not in cell_set:
                    new_cell_found = True
                    cell_set.add(cell)
                    log(logger.debug, f"find_combination({iter}) \tAdded cell {str(cell)} to cell set {[str(c) for c in cell_set]}")   #using list comprehension

                    new_value_found = False
                    for value in cell:

                        # If adding another value would make the list beyond what is usefull don't continue
                        if len(value_set) == len(cells_per_value_dict) - 2:
                            break


                        if value not in value_set:    # if new value ...
                            new_value_found = True

                            # Add value to accumulation
                            value_set.add(value)
                            log(logger.debug, f"find_combination({iter}) \t\tadded {value} to value set {value_set}, number of cells = {len(cell_set)}")

                            ret_value_set, ret_cell_set = self.find_combination(cells_per_value_dict, value, value_set.copy(), cell_set.copy(), iter)
                            log(logger.debug, f"find_combination({iter}) \t\tBack from recursive call; returned combo value set = {ret_value_set}  returned combo cell set = {[str(c) for c in ret_cell_set]}")

                            # Persist returned combination iff it's smaller than the previous
                            if len(ret_value_set) != 0:
                                if len(found_value_set) == 0 or len(ret_value_set) < len(found_value_set):
                                    log(logger.debug, f"find_combination({iter}) \t\tPersisting returned combo value set {ret_value_set} and cell set {[str(c) for c in ret_cell_set]}")
                                    found_value_set = ret_value_set
                                    found_cell_set = ret_cell_set

                        else:
                            log(logger.debug, f"find_combination({iter}) \t\t{value} already in value set {value_set}")

                    # Finished processing this cell's values
                    if not new_value_found:
                        log(logger.debug, f"find_combination({iter}) \t\tNo values were added to {value_set}")

                    if len(found_value_set) == 0:
                        # If the # of values matches the # of cells AND the sets don't include all unsolved cells use them
                        if len(value_set) == len(cell_set) and len(value_set) != len(cells_per_value_dict):
                            log(logger.debug, f"find_combination({iter}) \t\tFound combo; value set =  {value_set}, cell set = {[str(c) for c in cell_set]}")
                            found_value_set = value_set
                            found_cell_set = cell_set

                    elif len(found_value_set) > len(value_set):
                        if len(value_set) == len(cell_set):
                            log(logger.debug, f"find_combination({iter}) \t\tFound new combo; value set =  {value_set}, cell set = {[str(c) for c in cell_set]}")
                            found_value_set = value_set
                            found_cell_set = cell_set

                    log(logger.debug, f"find_combination({iter}) \t\tReturning found value set = {found_value_set}, found_cell set = {[str(c) for c in found_cell_set]}")
                    return found_value_set, found_cell_set

                else:  # Cell already recursed over
                    log(logger.debug, f"find_combination({iter}) \tcell {str(cell)} already in cell set")
                    pass    


            #   END of cell loop
#TODO: change below to "if not new_cell_found" and test
            if new_cell_found == False:
                pass

            log(logger.debug, f"find_combination({iter}) \tReturning: found value set = {found_value_set}, found_cell set = {[str(c) for c in found_cell_set]}")   #using list comprehension
            return found_value_set, found_cell_set
        
        except Exception as ex:
            raise SudokuErrors(f"find_combination() {ex}")

    def remove_values_from_context(self, context_iter, values):
        changed = False
        # context_iter = self.get_context_iterator(context_type, context_number)
        for srch_cell in context_iter:
            if len(srch_cell) != 1:              # at this point we're not interested in single value cells

                changed = srch_cell.remove_values(values) or changed

                # As always, if an action results in a cell having only one value then remove it from all relevant contexts
                if changed and len(srch_cell) == 1:
                    srch_cell.remove_value_from_view()

        return changed

#TODO: decide what to call a cell's contents vs. what a single value is called and make the change througout
    def remove_value_from_context(self, context_type, context_number, value):
        changed = False
        context_iter = self.get_context_iterator(context_type, context_number)
        for srch_cell in context_iter:
            if len(srch_cell) != 1:              # at this point we're not interested in single value cells

                changed = srch_cell.remove_value(value) or changed

                # As always, if an action results in a cell having only one value then remove it from all relevant contexts
                if changed and len(srch_cell) == 1:
                    srch_cell.remove_value_from_view()

        return changed

    # Determining if the passed-in cells reside on the same row or column.
    # Returns the line type and number
    def find_shared_lines(self, cells):
        rows = set()               # using empty set to be added to later
        cols = set()

        for cell in cells:
            rows.add(cell.row_number)
            cols.add(cell.column_number)

        # working_options_dict[value_key].append(cell)

        if len(rows) == 1 and len(cols) == 1:
            raise PuzzleExcept("SudokuPuzzle.get_shared_lines() found rows and columns cannot both have length 1.")

        if len(rows) == 1:
            return CellContext.ROW, list(rows)[0]
        elif len(cols) == 1:
            return CellContext.COLUMN, list(cols)[0]

        return CellContext.NONE, 0
        

#TODO: stop using getters for simple object attribute retreival, just access attribute directly
#  ALSO, use @property decorator for getting/setting object values if some code is required for getting/setting


# TODO: any way to keep track of "solved" cells while solving, i.e., if len(cell) == 1:  num_solved_cells += 1
# if doing this on the fly could check anytime to see if puzzle is solved and stop solution algorithm
# Return the number of unsolved cells or -1 if the puzzle has no cell solved (and so is unsolvable)
    def unsolved_cell_count(self):
        unsolved_count = 0
        for row in range(self.dimension):
            for col in range(self.dimension):
                if not self.matrix[row][col].solved():
                    unsolved_count += 1
        return unsolved_count

# TODO: should this be done upon initialization of empty cells (in SudokuCell class)? Then places like this would only need to do "str(cell)"
# not sure if set values get re-ordered when manipulated (values removed)
    # Returns formatted string with all cell values listed by row
    def puzzle_log(self):
        """
        Returns puzzle contents as a string appropriate for logging. The 
        string is formatted for readability; layout adjusted per puzzle
        dimension and white space dynamically adapted to cell content size.
        """
        spacer_front = f"\n\t\t\t "
        row_front = f"\n\t"
        longest = self.max_contents_size()
        contents_spacer = " "
        box_spacer = " | "

# TODO: fix, content of length 5 looks good, but length 1 has separater rows stopping a tab too early;   "self.box_dimension - x" below needs to be looked at
# 0 works for 9 & 16 sized pzls with single char, but need to see how it looks for multi-char cell contents
        # spacer_row =  f"{spacer_front}|{'-' * ((longest + len(contents_spacer)) * (self.dimension + (self.box_dimension * len(box_spacer))))}|"    
        spacer_row =  f"{spacer_front}|{'-' * ((longest + len(contents_spacer)) * (self.dimension + (self.box_dimension * len(box_spacer))))}|"    

        log_str = "\n\tPuzzle:"
        log_str += spacer_row
        for row in range(1, self.row_dimension + 1):
            row_label = f"{row_front}Row {row}:"
            total_prefix_len = len(row_label) + 2     

            # Ensure row contents start at the same place regardless of number of digits in row number
            log_str += f"{row_label.ljust(total_prefix_len, contents_spacer)}{box_spacer}"  

            first_cell = self.get_first_cell_in_row(row)            
            cell_iter = first_cell.row_iter()
            column_cntr = 1
            for cell in cell_iter:

                sorted_contents = str(cell)     # cells can contain multiple characters

                log_str += f"{contents_spacer}{sorted_contents.ljust(longest + len(contents_spacer), contents_spacer)}"    #using ternary operation in formatted string experssion

                # Add delineator before next box cells
                if column_cntr % self.box_dimension == 0:
                    log_str += box_spacer

                column_cntr += 1

            # Add separator line after last row in box
            if row % self.box_dimension == 0:
                log_str += spacer_row

        return log_str   


class SudokuPuzzleBuilder(PuzzleBuilder):
    """
    Creates a matrix of Sudoku cells that are circularly linked per 
    the 3 relevant Sudoku contexts; row, column, box.
    """
    def __init__(self, starting_values = None, dimension = 9, all_possible_values = DEFAULT_VALUE_OPTIONS, placeholder = DEFAULT_PLACEHOLDER):
        """
        Validates and initializes puzzle with any passed-in values.

        :param starting_values: Lists of character lists to use for initial 
                                 puzzle state. If nothing passed the
                                 placeholder value will be used throughout.
        :type starting_values:  List of (typically) single char strings , e.g., 
                                ['7','2','9',...,'7'] that represent all 
                                (typically 81) cell values in puzzle.
        :param dimension: Puzzle dimension, i.e., length of rows and columns (defaults to 9)
        :type dimension: int (must be square of an integer)
        :param all_possible_values: List of all possible values if no starting values 
                                    given. Each value must be unique.
        :type all_possible_values: [char]
        :param placeholder: Char used to denote empty Cells (defaults to ' ')
        :type placeholder: char
        :raises: SudokuBuildError if invalid parameter enountered
        """
        try:
#TODO: validate that incoming values are consistent w/ Sudoku rules, i.e., vals not duplicated in any context?

            # Validate passed-in puzzle
            if starting_values != None:
                log(logger.debug, f"SudokuPuzzleBuilder() applying initial value list; ignoring dimension and value options parameters.")

                if not isinstance(starting_values, list):
                    raise SudokuBuildError("Parameter starting_values must be list.")

                try:
                    dimension = self.validate_dimension(len(starting_values))
                except SudokuBuildError as ex:
                    raise SudokuBuildError(f"Size of passed-in puzzle invalid; {ex}.")

                # Validate initial values and build set of value options
                if len(placeholder) != 1:
                    raise SudokuBuildError(f"Placeholder '{placeholder}' must be single character.")

                all_possible_values_set = set()
                for element in starting_values:
                    if not isinstance(element, str):
                        raise SudokuBuildError("Parameter starting_values must be simple list.")
                    if len(element) != 1:
                        raise SudokuBuildError("Parameter starting_values must be list of single characters.")
          
                    # Build list of all possible values from those passed in
                    if element != placeholder:
                        all_possible_values_set.add(element)

                all_possible_values = list(all_possible_values_set)

            # Create filled puzzle of size dimension
            else:  
                log(logger.debug, f"No starting_values; applying dimension and value options list parameters.")

                try:
                    self.validate_dimension(dimension)
                except SudokuBuildError as ex:
                    raise SudokuBuildError(f"Error building Sudoku puzzle; dimension parameter: {ex}.")


                if dimension != len(all_possible_values):
                    raise SudokuBuildError(f"Number of possible values ({len(all_possible_values)}) must match dimension ({dimension}) of Sudoku puzzle.")

            # Create cells to hold all initial puzzle values (or placeholder if no data provided)
            puzzle = SudokuPuzzle(all_possible_values, dimension)

            cell_factory = SudokuCellFactory()

            super().__init__(puzzle, cell_factory, dimension, dimension, starting_values, all_possible_values, placeholder)   # does basic row/column set up and row and column linked lists

            # Base class builder linked cells by row and column. Since Sudoku 
            # has boxes, circular linked box lists need to be created.

            # The initial pass was done above (linking all cells by row)
            for row_index in range(dimension):
                for column_index in range(dimension - 1):
                    puzzle[row_index, column_index].set_next_cell_in_box(puzzle[row_index, column_index + 1])

            # Now to replace the "row" link for cells at the right side of their cell to the 1st box cell in the line below
            # Loop should execute 24 (3 x 8 since the last row isn't done) times
            box_dimension = puzzle.get_box_dimension()
            box_offset = box_dimension - 1    

            for row_index in range(dimension - 1):
                for column_index in range(box_offset, dimension, box_dimension):
                    next_cell_row = row_index + 1
                    next_cell_column = column_index - box_offset
                    puzzle[row_index, column_index].set_next_cell_in_box( puzzle[ next_cell_row, next_cell_column ] )
                    
            # Next, link last cell in box (bottom left) to 1st cell in box (upper right)
            # Loop should execute dimension times
            for row_index in range(box_offset, dimension, box_dimension):
                for column_index in range(box_offset, dimension, box_dimension):
                    next_cell_row = row_index - box_offset
                    next_cell_column = column_index - box_offset

                    puzzle[row_index, column_index].set_next_cell_in_box( puzzle[ next_cell_row, next_cell_column ] )

            # Set each cell's box number
            for row_index in range(dimension):
                for column_index in range(dimension):
                    box_number = box_dimension * int((row_index)//box_dimension) + int((column_index)//box_dimension) + 1
                    puzzle[row_index, column_index].set_box_number(box_number)

            self.puzzle = puzzle
 
        except Exception as ex:
            raise SudokuBuildError(f"SudokuPuzzleBuilder(): {ex}")

    def validate_dimension(self, dimension) -> int:
        """
        Validator to ensure passed-in dimension or size of starting value 
        list is appropriate for Sudoku puzzles, that is, an integer square.

        :parameter dimension: Value to find square root for.
        :type dimension: +ve int
        :return: Square root of puzzle size (dimension).
        :rtype: int
        :raises: SudokuBuildError if dimension invalid
        """
        if dimension < 0:
            raise SudokuBuildError(f"dimension ({dimension}) must be positive")

        float_sqrt = math.sqrt(dimension)
        dimension = int(float_sqrt)
        if (float_sqrt - dimension) != 0:
            raise SudokuBuildError(f"dimension ({dimension}) must be square of integer")
        
        return dimension

    def get_puzzle(self) -> SudokuPuzzle:
        """
        :return: Deep copy of puzzle.
        :rtype: SudokuPuzzle object
        """
#TODO: determine impact of returning deep copy here; is it even necessary?
        return self.puzzle



#TODO:  need to add "add" method or something to track size (set self.dimension), or maybe "finished_building" method for this!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

class SudokuSolver():

    def __init__(self, puzzle):
        self.puzzle = copy.deepcopy(puzzle)

    def get_puzzle(self):
        return self.puzzle

    def solve_puzzle(self):
        try:
            # fill empty cells with all possible options
            self.puzzle.fill_empty_cells_with_options()

            # remove initially given cell values from all relevant contexts
            # This step is usually all that's needed to solve an easy puzzle
            self.puzzle.normalize()

            num_unsolved = self.puzzle.unsolved_cell_count()
            if num_unsolved > 0:
                log(logger.debug, f"Still have {num_unsolved}  A cells to solve.")
            elif num_unsolved == -1:
                log(logger.error, "Puzzle had no initial values and so is unsolvable.")
            else:
                self.puzzle.puzzle_log()
                return
            
            # This phase is usually enough to solve med to hard puzzles
            self.puzzle.apply_to_all_contexts(self.puzzle.resolve_uniques_in_context)
            num_unsolved = self.puzzle.unsolved_cell_count()
            if num_unsolved > 0:
                log(logger.debug, f"{num_unsolved} cells to solve.")
            else:
                return

            changed = True
            iter = 0
            while changed:
                iter += 1
                changed = False

                #Look at bi-context intersections
                log(logger.debug, f"SudokuSolver() iteration {iter} of intersecting_context_resolution()")
                changed = self.puzzle.intersecting_context_resolution()

                log(logger.debug, f"SudokuSolver() iteration {iter} of  combination_reduction()")

                changed = self.puzzle.apply_to_all_contexts(self.puzzle.combo_reduction)
                self.puzzle.puzzle_log()

            #   End of while changed loop

            log(logger.debug, f"Still have {num_unsolved} C cells to solve.")

        except Exception as ex:
            raise SudokuErrors(f"Exception while solving sudoku puzzle {ex}.")

