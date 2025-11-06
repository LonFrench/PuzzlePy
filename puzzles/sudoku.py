"""
This module extends classes defined in the puzzle module and defines new classes used for building and solving Sudoku puzzles.
"""
import copy
import random
import math
import logging
from enum import Enum, auto
from typing import Tuple
from puzzle import Puzzle, PuzzleBuilder, PuzzleExcept, DEFAULT_PLACEHOLDER, DEFAULT_VALUE_OPTIONS
from puzzle import Cell, CellContext, CellFactory, CellIterator, CellExcept

# TODO: test w/ letters & special chars to ensure cell contents are agnostic; update docstrings to reflect that passed values aren't integers.

__all__ = ['Sudoku','SudokuBuilder','SudokuSolver','BoxIterator','SudokuCell','SudokuCellFactory','SudokuErrors','SudokuBuildError','PlaceStatus']

logger = logging.getLogger(__name__)    # logger uses name of module
logging.basicConfig(filename="builder.log",
                    format="%(asctime)s (%(levelname)s) %(message)s",
                    encoding='utf-8',
                    level=logging.DEBUG)

def log(func, *args):
    """Log message."""
    new_message = f"{__name__}: {args[0]}"  #using wrapper
    func(new_message)

class SudokuErrors(Exception):
    """Used for general Sudoku errors."""
    def __init__(self, err_msg):
        super().__init__(err_msg)

class SudokuBuildError(Exception):
    """Used for Sudoku build related errors."""
    def __init__(self, err_msg):
        super().__init__(err_msg)

class PlaceStatus(Enum):
    """Used to indicate results of attempt to place value in cell."""
    PASSED = auto()
    FAILED = auto()

class SudokuCell(Cell):
    """
    This concrete class builds upon the superclass by defining a "box" 
    context and methods to aid Sudoku puzzle solving. 
    """
    def __init__(self, value, row_index = -1, column_index = -1, placeholder = DEFAULT_PLACEHOLDER):

        self.box_number = 0
        self.next_cell_in_box = 0
        super().__init__(value, row_index, column_index, placeholder)

    def set_next_cell_in_box(self, next_cell):
        """Sets next cell in linked box cell list."""
        self.next_cell_in_box = next_cell

    def set_box_number(self, box_number):
        """Sets box's number."""
        self.box_number = box_number

    def get_next_cell_in_box(self) -> Cell:
        """Returns next cell in Sudoku box."""
        return self.next_cell_in_box

    def box_iter(self):
        """
        Returns iterator for cell's box.

        :return: Iterator for cell's box
        :rtype: BoxIterator
        """
        return BoxIterator(self)

    def remove_value_from_view(self):
        """Remove cell's value from all contexts, i.e., all cells within its view."""          
        self.remove_value_from_context(self.row_iter())
        self.remove_value_from_context(self.column_iter())
        self.remove_value_from_context(self.box_iter())

    def set_if_no_conflict(self, value) -> bool:
        """
        Sets the cell's content to the given value if it is unique within all 
        of the cell's contexts.

        :parameter value: Potential contents
        :type value: char
        :return: True if value was set, False otherwise.
        :rtype: bool
        """
        if len(self) != 0:
            return False

        if self.value_exists_within_view(value) is True:
            return False

        self.contents = value
        return True

    def value_exists_within_view(self, value) -> bool:
        """
        Determines whether given value exists in any of the cell's contexts.

        :parameter value: Search value
        :type value: char
        :return: True if value can be found in at least one cell within the given cell's contexts.
        :rtype: bool
        """
        if self.value_in_context(self.row_iter(), value) is True:
            return True
        if self.value_in_context(self.column_iter(), value) is True:
            return True
        if self.value_in_context(self.box_iter(), value) is True:
            return True
        return False

# pylint: disable=too-few-public-methods
class SudokuCellFactory(CellFactory):
    """Used to create Sudoku cells."""
    def __init__(self):     # TODO: remove
        self.type = "Sudoku"

    def new_cell(self, value = None, row_index = -1, column_index = -1, placeholder = DEFAULT_PLACEHOLDER):
        if len(value) > 1:
            raise CellExcept(f"Initial Sudoku cell values must only be 1 character; '{value}' is too long.")

        return SudokuCell(value, row_index, column_index, placeholder)

class BoxIterator(CellIterator):
    """Derived class used to traverse cells in a Sudoku box."""
    def __init__(self, cell):
        super().__init__(cell, CellContext.BOX)

    def __iter__(self):
        return self

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

class Sudoku(Puzzle):
    """
    Extends Puzzle by adding Sudoku specific processing: box
    searches, pattern operations, and other validation and actions.

    :ivar box_dimension: Size of box side. 
    :vartype box_dimension: int
    :ivar dimension: Size of puzzle side.
    :vartype dimension: int
    :ivar value_options: All possible cell value options.
    :vartype value_options: list
    """
    def __init__(self, value_options, dimension):

        box_float_dimension = math.sqrt(dimension)
        self.box_dimension = int(box_float_dimension)
        self.value_options = value_options

        # Create dict to use as working structure for tracking which cells are used for each value
        self.empty_options_dict = {value : set() for value in value_options}            #using dict comprehension

        self.dimension = dimension
        super().__init__(dimension, dimension)

    def get_box_dimension(self) -> int:
        """Returns size of a box side."""
        return self.box_dimension

    # Param is box number with the upper left being #1 down to the last on in the lower right
    def _first_cell_in_box(self, box_number) -> SudokuCell:
        """
        Returns upper left cell of cell in box (last cell is in lower right).

        :parameter box_number: Id of box.
        :type box_number: int
        :return: Cell representing "first" cell in box.
        :rtype: SudokuCell
        """
        if 1 > box_number > self.dimension:
            raise PuzzleExcept(f"Box number ({box_number}) must be between 1 and the puzzle dimension {self.dimension}.")

        puzzle_row    = int( (box_number - 1) / self.box_dimension) * self.box_dimension
        puzzle_column =    ( (box_number -1) * self.box_dimension ) % self.dimension
        return self.matrix[puzzle_row][puzzle_column]

    def _get_context_iterator(self, context_type, number) -> CellIterator:
        """
        Returns iterator for the specific context.

        :parameter context_type: Type of iterator (ROW, COLUMN, or BOX) to return.
        :type context_type: CellContext
        :parameter number: Id of specific context
        :type number: int
        :return: Iterator from the first cell in specific context.
        :rtype: derivative types of CellIterator
        """
        if context_type == CellContext.ROW:
            first_cell = self.first_cell_in_row(number)
            return first_cell.row_iter()

        if context_type == CellContext.COLUMN:
            first_cell = self.first_cell_in_column(number)
            return first_cell.column_iter()

        if context_type == CellContext.BOX:
            first_cell = self._first_cell_in_box(number)
            return first_cell.box_iter()

        return None

    def fill(self) -> PlaceStatus:
        """
        Fills out a Sudoku puzzle which may start empty or
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
            rand_vals = list(self.value_options)
            random.shuffle(rand_vals)

            for attempt in range(1, 1000):   # 8 is plenty when starting from scratch
                for val in rand_vals:
                    log(logger.debug, f"Sudoku.fill() Attempting to place {val} ...")
                    status, _ = self._place_value(val, 1)   # using only single return value

                    if status == PlaceStatus.PASSED:
                        log(logger.debug, f"Sudoku.fill() Successfully placed all {val}s.")
                        log(logger.info, self.puzzle_log())
                    else:
                        log(logger.info, self.puzzle_log())
                        log(logger.warning, f"Sudoku.fill() Attempt {attempt} failed; starting over...")
                        self.clear()
                        break

                if status == PlaceStatus.PASSED:
                    break

            return status
        except Exception as ex:
            raise PuzzleExcept("Sudoku.place_value()") from ex

    def _backup_count(self, box_num):
        """ Returns how many steps to backtrack based on position within puzzle."""
# clean up:   get_backup_count = lambda: self.box_dimension if box_num % self.box_dimension == 1 else 1
        return self.box_dimension if box_num % self.box_dimension == 1 else 1

    #
    # TODO: use self.dimension to stop recursion
    #
    # pylint: disable=too-many-return-statements
    def _place_value(self, value, box_num, backup_count = 0):
        """
        Recursive method that places given value in the given
        box. If a value can't be placed the number of recursive steps to back
        up will be returned. The value is constant during this process but
        the box number is incremented for each call. Number of backup steps
        depends on location of box and returns the process to the point
        that a different placement will most likely be impactful.

        :parameter value: Value to place.
        :type value: Usually an integer, but could be any character.
        :parameter box_num: Box to place the given value. Boxes are numbered from 1 to 9 (typically) starting
            in upper left and going right then down until eventually reaching the 9th box in the lower right.
        :type box_num: Integer value from 1 to puzzle dimension, typically 9.
        :parameter backtrack: The number of recursion steps to go back up the call stack to redo.
        :type backup_count: Integer

        :return: FAILED returned if unable to find cell in box to place value, PASSED otherwise.
        :rtype: PlaceStatus enum
        """
        try:
            log(logger.debug, f"Sudoku.place_value() attempting to place {value} in box #{box_num}.")

            eligible_cells = self.eligible_box_cells(box_num, value)
            log(logger.debug, f"Sudoku.place_value() value {value}, box #{box_num}, eligible_cells size is {len(eligible_cells)}.")
            if len(eligible_cells) == 0:
                backup_count = self._backup_count(box_num)
                log(logger.debug, f"Sudoku.place_value() Failed to find any eligible cells in box #{box_num} to place a {value},"
                                  f" backing up {backup_count} step(s).")
                return PlaceStatus.FAILED, backup_count

# TODO: review this logic for encountering box that already has value in it
            # This covers the case where box was initialized with this value and so doesn't need to be set
            if len(eligible_cells) == 1 and value in eligible_cells[0].contents:
                log(logger.debug, f"Sudoku.place_value() {value} already exists in box #{box_num}.")
                if box_num == self.dimension:
                    return PlaceStatus.PASSED, 0
                status, backup_count = self._place_value(value, box_num + 1)
                backup_count -= 1

                # Can't make changes here, but continue backtracking to a box where it can make a difference
                if backup_count == 0:
                    backup_count = self._backup_count(box_num)
#TODO: determine:
# should a bakcup_count decrement still happen, and if == 0 set to 1?
                return status, backup_count    # Just pass back up since nothing changed in this step

            # Introduce 2nd level of randomization
            rand_eligible_cells = random.sample(eligible_cells, len(eligible_cells))

            for ndx in range(len(rand_eligible_cells) - 1, -1, -1):
                log(logger.debug, f"Sudoku.place_value() setting {value} in box #{box_num}.")
                if not rand_eligible_cells[ndx].set(value):
                    log(logger.debug, "Sudoku.place_value() Cell is immutable; unable to set value.")

                if box_num == self.dimension:   # Successfully placed value throughout puzzle, backtrack the recursion stack
                    return PlaceStatus.PASSED, 0

                # Attempt to place value in next box; will end up back here if downstream step failed.
                status, backup_count = self._place_value(value, box_num + 1)
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
                log(logger.debug, f"Sudoku.place_value() Length of box #{box_num} eligible cells is {len(rand_eligible_cells)}.")

            # End of loop
            backup_count = self._backup_count(box_num)
            log(logger.debug, f"Sudoku.place_value() Failed to place {value} in box #{box_num}, backing up {backup_count} step(s).")
            return PlaceStatus.FAILED, backup_count
        except Exception as ex:
            raise PuzzleExcept("Sudoku.place_value()") from ex

    def eligible_box_cells(self, box_num, value):
        """
        Returns a list of Cells belonging to the given box that have  
        neither row nor column value conflicts.
        
        :parameter box_num: Number of box for which to build list.
        :type box_num: int from 1 to dimension inclusive
        :parameter value: Value for which to ensure there are no conflicts.
        :type value: int (typically, but could be any character)
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
                cell_iter = open_cells[ndx].row_iter()
                if open_cells[ndx].value_in_context(cell_iter, value):
                    del open_cells[ndx]
                    continue

                cell_iter = open_cells[ndx].column_iter()
                if open_cells[ndx].value_in_context(cell_iter, value):
                    del open_cells[ndx]
                    continue

            return open_cells
        except Exception as ex:
            raise PuzzleExcept("Sudoku.eligible_box_cells()") from ex

    def _fill_empty_cells(self):
        """
        Helper method for solution algorithm that fills all empty cells
        with all possible values.
        """
        for row in range(1, self.row_dimension + 1):
            first_cell = self.first_cell_in_row(row)
            cell_iter = first_cell.row_iter()
            for cell in cell_iter:
                if cell.empty():
                    cell.set(copy.deepcopy(self.value_options))

    def normalize(self):
        """
        Once a cell is solved this method is called to remove its value
        from all of its contexts maintaining the primary Sudoku rule that
        a value must not occur more than once in any row, column, or box.
        """
        for row in range(1, self.dimension + 1):
            first_cell = self.first_cell_in_row(row)

            # For each "solved" cell, search through all the cell's contexts and remove instances of the given value
            cell_iter = first_cell.row_iter()
            for cell in cell_iter:
                if len(cell) == 1:
                    cell.remove_value_from_view()

# TODO: define interface for func
    def apply_to_all_contexts(self, func_to_apply ) -> bool:
        """
        Applies method to all contexts within Sudoku puzzle.
        
        :parameter func_to_apply: Method to apply across all contexts.
        :type func_to_apply: method
        :return: True if change was made, False otherwise.
        :rtype: bool
        """
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

   #TODO: determine more graceful way to specify max size, using self.dimension if possible
    def cells_per_value_dict(self, cell_iter, min_size=1, max_size=100) -> dict[str,list]:
        """
        Creates dictionary for given context with cell values as the keys and a list of 
        cells that include that value as the dictionary value.

        :parameter cell_iter: Iterator for cell context
        :type cell_iter: CellIterator
        :parameter min_size:
        :type min_size:
        :parameter max_size:
        :type max_size:
        :return: 
        :rtype: dictionary
        """
        try:
            options_dict = copy.deepcopy(self.empty_options_dict)
            for cell in cell_iter:
                if cell.empty():
                    continue
                for value_key in cell:
                    options_dict[value_key].add(cell)  # include cell in set for value

            if min_size != 1 or max_size != 9:   # TODO: necessary to check for this range?
                working_options_dict = copy.deepcopy(options_dict)
                for value, cell_list in working_options_dict.items():
                    if len(cell_list) < min_size or len(cell_list) > max_size:
                        del options_dict[value]

            return dict(sorted(options_dict.items()))  # Sorting dictionary to aid testing
        except Exception as ex:
            raise PuzzleExcept("cells_per_value_dict():") from ex

    # Method takes iterator of a context (row, column, or box), finds values that occur only once
    # in that context (are unique) and replaces the found cell's contents with just that value
    def resolve_uniques_in_context(self, context_type, context_number) -> bool:
        """
        Searches all cells within passed in context for values that exist
        only once (are unique). Once a unique value is found, the containing
        cell's contents is set to just that value (removing all other values).

        :parameter context_type: Type of context, e.g., row, column, box
        :type context_type: CellContext Enum
        :parameter context_number: Value from 1 to puzzle dimension that 
            represents the context number.
        :type context_number: int
        :return: True if any changes were made; otherwise False.
        :rtype: bool
        """
        cell_iter = self.get_context_iterator(context_type, context_number)
        working_options_dict = self.cells_per_value_dict(cell_iter, max_size=1)

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

    def resolve_intersecting_contexts(self):
        """
        Iterates through all rows and columns looking for opportunities to normalize 
        where they interset with boxes.
        """
        change_made = True
        count = 0
        while change_made:            # For each row in puzzle ...
            change_made = False
            for row_num in range(1, self.dimension + 1):
                first_cell = self.first_cell_in_row(row_num)
                cell_iter = first_cell.row_iter()
                change_made =  self.normalize_box_intersection(cell_iter) or change_made

            # For each column in puzzle ...
            for column_num in range(1, self.dimension + 1):
                first_cell = self.first_cell_in_column(column_num)
                cell_iter = first_cell.column_iter()
                change_made = self.normalize_box_intersection(cell_iter) or change_made

            count += 1

        log(logger.debug, f"{count} passes required to solve puzzle.")

#TODO: Throughout, find alternative word for "value" as it gets confused with keywords

    def normalize_box_intersection(self, line_iter) -> bool:
        """
        Normalizes sitations wheren all occurances of a specific line value occurs in the same box.
        
        :parameter line_iter:
        :type line_iter: Row or column iterator
        :return: True if a change was made, False otherwise.
        :rtype: bool
        """
        # ... build dictionary of counts for each possible value ...
        working_options_dict = self.cells_per_value_dict(line_iter, min_size=1, max_size=9)

        #  ... and for each value that shows up 2 or 3 times ...
        changed = False
        for value, cells in working_options_dict.items():    # using dictionary iteration
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
                cell.set_immutable(True)

            # ...remove all instances of the value in other cells of the box
            changed = self.remove_value_from_context(CellContext.BOX, box_number, value) or changed

            # Make them all non-immutable again
            for cell in cells:
                cell.set_immutable(False)

        return changed

    def combo_reduction(self, context_type, context_number) -> bool:
        """
        Identify value combinations within a context and use to remove extraneous values.

        :parameter context_type: Type of context; row, column, or box.
        :type context_type: CellContext
        :parameter context_number: Position of the context within puzzle.
        :type context_number: int
        :return: True if change was made to puzzle, False otherwise.
        :rtype: bool
        """
        log(logger.debug, "Original puzzle:")
        # Debug only: self.puzzle_log()
        change_made = False
        try:
            combo_size_max = 1
            # TODO: determine if set.intersection would be helpful here

            # loop thru list of counts, trying to find "reducable" combinations, starting with smallest combinations that involve groups of 2 values
            processed_value_combos = []
            while True:
                combo_size_max += 1

                # Get lists of the cells that each value is in
                # This may change from one iteration to the next; using param name in call
                cells_per_value = self.cells_per_value_dict(self.get_context_iterator(context_type, context_number), min_size=2)
                # If the size of combinaitons we're looking for = the number of values that exist in > 1 cell, it's time to stop

                #TODO: could probably stop sooner here; come up with mathematical rationale for a lower number
                if combo_size_max == len(cells_per_value) - 2:
                    break

                while True:
                    change_just_made = False

                    for subject_value, cells in cells_per_value.items():      # using dictionary iteration

                        # Only interested in values that have a certain number/range of occurances
                    #TODO: !!!! Not sure whether to leave this logic in; thought is that it's cells with...
                    #...combo_size_max values turn as the previous sizes had their turn
                        if len(cells) != combo_size_max:
                            continue

                        # Start the list of values with the "subject" value; this will be built upon in the following loop(s)
                        value_collection = {subject_value}
                        cell_set = set()

                        log(logger.debug, f"\ncombo_reduction() calling find_combination() with value {subject_value}")
                        value_collection, cell_set = self.find_combination(cells_per_value, subject_value)
                        log(logger.debug, f"combo_reduction(): find_combination() value combination {str(value_collection)}")

                        if len(value_collection) > 0 and set(value_collection) not in processed_value_combos:

                            # Combination already handled, let's not mess with it again
                            processed_value_combos.append(value_collection)

                            # Once we've found our reduction combination of values use them to remove values
                            for cell in cell_set:
                                change_just_made = cell.remove_all_but(value_collection) or change_just_made

                            # Protect found cells from having this value removed while removing it from the rest of the relevant row/column and box
                            for cell in cell_set:
                                cell.set_immutable(True)

                            # For all other cells in context remove the combination values
                            replacement_context_iterator = self.get_context_iterator(context_type, context_number)
                            change_just_made = self.remove_values_from_context(replacement_context_iterator, value_collection) or change_just_made

                            for cell in cell_set:
                                cell.set_immutable(False)

                        if change_just_made:   # If context just modified leave loop and refresh the value count list
                            break
                    #   end of inner combo search loop

                    if not change_just_made:
                        break
                    change_made = True
                    change_just_made = False

                     # This may change from one iteration to the next
                    cells_per_value = self.cells_per_value_dict(self.get_context_iterator(context_type, context_number), min_size=2)
                #   end of outter combo search loop

            return change_made

        except Exception as ex:
            raise SudokuErrors("Exception in combo_reduction()") from ex

    def find_combination(self, cells_per_value_dict, subject_value) -> Tuple[set, set]:
        """
        Searches for group of cells that contain a specific value within a distinct combination of values.

        :parameter cells_per_value_dict: Dictionary where each key represents a discrete value
            and the dictionary value is a list of cells that contains the value (key).
        :type cells_per_value_dict: Dictionary with chars as keys and Cell lists as values.
        :parameter subject_value: The value in which to find combinations for.
        :type subject_value: char
        :return: Set of values found in combination
        :rtype: set of chars
        :return: Set of cells containing the value combination
        :rtype: set of Cells
        """
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

            combo_values.add(value)
            combo_cell_set = temp_cell_set.copy()

        # Number of values must match the number of cells or it's no good
        if len(combo_values) != len(combo_cell_set):
            return set(), set()

        return combo_values, combo_cell_set

    def remove_values_from_context(self, context_iter, values):
        """Deletes all instances of a value from the given context."""
        changed = False
        # context_iter = self.get_context_iterator(context_type, context_number)
        for srch_cell in context_iter:
            if len(srch_cell) != 1:              # at this point we're not interested in single value cells

                changed = srch_cell.remove_values(values) or changed

                # As always, if an action results in a cell having only one value then remove it from all relevant contexts
                if changed and len(srch_cell) == 1:
                    srch_cell.remove_value_from_view()

        return changed

    def remove_value_from_context(self, context_type, context_number, value):
        """Removes given value from context and normalizes if any deletions made."""
        changed = False
        context_iter = self.get_context_iterator(context_type, context_number)
        for srch_cell in context_iter:
            if len(srch_cell) != 1:              # at this point we're not interested in single value cells

                changed = srch_cell.remove_value(value) or changed

                # As always, if action results in cell having only one value then remove it from all relevant contexts
                if changed and len(srch_cell) == 1:
                    srch_cell.remove_value_from_view()

        return changed

    def find_shared_lines(self, cells) -> Tuple[CellContext, int]:
        """Determines whether cells reside on same row or column and returns type of line and its number."""
        rows = set()               # using empty set to be added to later
        cols = set()

        for cell in cells:
            rows.add(cell.row_number)
            cols.add(cell.column_number)

        # working_options_dict[value_key].append(cell)     TODO: clean up

        if len(rows) == 1 and len(cols) == 1:
            raise PuzzleExcept("Sudoku.get_shared_lines() found rows and columns cannot both have length 1.")

        if len(rows) == 1:
            return CellContext.ROW, list(rows)[0]
        if len(cols) == 1:
            return CellContext.COLUMN, list(cols)[0]

        return CellContext.NONE, 0

#TODO: stop using getters for simple object attribute retreival, just access attribute directly
#  ALSO, use @property decorator for getting/setting object values if some code is required for getting/setting

# Return the number of unsolved cells or -1 if the puzzle has no cell solved (and so is unsolvable)
    def unsolved_cell_count(self):
        """Returns the number of unsolved cells."""
        unsolved_count = 0
        for row in range(self.dimension):
            for col in range(self.dimension):
                if not self.matrix[row][col].solved():
                    unsolved_count += 1
        return unsolved_count

    # Returns formatted string with all cell values listed by row
    def puzzle_log(self):
        """
        Returns puzzle contents as a string appropriate for logging. The 
        string is formatted for readability; layout adjusted per puzzle
        dimension and white space dynamically adapted to cell content size.
        """
        spacer_front = "\n\t\t\t "
        longest = self.max_contents_size()
        contents_spacer = " "
        box_spacer = " | "

# TODO: fix, content of length 5 looks good, but length 1 has separater rows stopping a tab too early;
#  "self.box_dimension - x" below needs to be looked at
# 0 works for 9 & 16 sized pzls with single char, but need to see how it looks for multi-char cell contents
# spacer_row =  f"{spacer_front}|{'-' * ((longest + len(contents_spacer)) * (self.dimension + (self.box_dimension * len(box_spacer))))}|"
        spacer_row =  f"{spacer_front}|{'-' * ((longest + len(contents_spacer)) * (self.dimension + (self.box_dimension * len(box_spacer))))}|"

        log_str = "\n\tPuzzle:"
        log_str += spacer_row
        for row in range(1, self.row_dimension + 1):
            row_label = f"\n\tRow {row}:"
            total_prefix_len = len(row_label) + 2

            # Ensure row contents start at the same place regardless of number of digits in row number
            log_str += f"{row_label.ljust(total_prefix_len, contents_spacer)}{box_spacer}"

            first_cell = self.first_cell_in_row(row)
            cell_iter = first_cell.row_iter()
            column_cntr = 1
            for cell in cell_iter:

                sorted_contents = str(cell)     # cells can contain multiple characters

                log_str += f"{contents_spacer}{sorted_contents.ljust(longest + len(contents_spacer), contents_spacer)}"

                # Add delineator before next box cells
                if column_cntr % self.box_dimension == 0:
                    log_str += box_spacer

                column_cntr += 1

            # Add separator line after last row in box
            if row % self.box_dimension == 0:
                log_str += spacer_row

        return log_str

class SudokuBuilder(PuzzleBuilder):
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
#TODO: ensure incoming values are consistent w/ Sudoku rules, i.e., vals not duplicated in any context?

            # Validate passed-in puzzle
            if starting_values is not None:
                log(logger.debug, "SudokuBuilder() applying initial value list; ignoring dimension and value options parameters.")

                if not isinstance(starting_values, list):
                    raise SudokuBuildError("Parameter starting_values must be list.")

                try:
                    self.validate_dimension(len(starting_values))
                except SudokuBuildError as ex:
                    raise SudokuBuildError("SudokuBuilder initialization; size of passed-in puzzle invalid.") from ex

                # Validate initial values and build set of value options
                if len(placeholder) != 1:
                    raise SudokuBuildError(f"Placeholder '{placeholder}' must be single character.")

                all_possible_values_set = set()
                for element in starting_values:
                    if not isinstance(element, str):
                        raise SudokuBuildError("Parameter starting_values cannot contain nested list.")
                    if len(element) != 1:
                        raise SudokuBuildError("Parameter starting_values must be list of single characters.")

                    # Build list of all possible values from those passed in
                    if element != placeholder:
                        all_possible_values_set.add(element)

                # TODO: run starting values through normalization method to see if anything is changed, throw expection if so
                # Ensure incoming values represent normalized puzzle, i.e., follow Sudoku rules

                all_possible_values = list(all_possible_values_set)

            # Create filled puzzle of size dimension
            else:
                log(logger.debug, "No starting_values; applying dimension and value options list parameters.")

                try:
                    self.validate_dimension(dimension)
                except SudokuBuildError as ex:
                    raise SudokuBuildError("SudokuBuilder initialization: ") from ex

                if dimension != len(all_possible_values):
                    raise SudokuBuildError(f"Number of possible values ({len(all_possible_values)}) must match dimension"
                                           f" ({dimension}) of Sudoku puzzle.")
            cell_factory = SudokuCellFactory()

            # create puzzle and perform basic row/column set up and row and column linked lists
            super().__init__(Sudoku(all_possible_values, dimension), cell_factory, num_rows = dimension, num_columns = dimension,
                             values = starting_values, all_possible_values = all_possible_values, placeholder = placeholder)
            self.link_cells_by_box(dimension)

        except Exception as ex:
            raise SudokuBuildError("SudokuBuilder(): ") from ex

    def link_cells_by_box(self, dimension):
        """
        Circularly links all cells in a box for all boxes in puzzle. Builds upon lists
        built for rows in base class.

        :parameter dimension: Size of puzzle side.
        :type dimension: int
        """
        # Base class builder linked cells by row and column. Since Sudoku
        # has boxes, circular linked box lists need to be created.

        # The initial pass was done above (linking all cells by row)
        for row_index in range(dimension):
            for column_index in range(dimension - 1):
                self.puzzle[row_index, column_index].set_next_cell_in_box(self.puzzle[row_index, column_index + 1])

        # Now to replace the "row" link for cells at the right side of their cell to the 1st box cell in the line below
        # Loop should execute 24 (3 x 8 since the last row isn't done) times
        box_dimension = self.puzzle.get_box_dimension()
        box_offset = box_dimension - 1

        for row_index in range(dimension - 1):
            for column_index in range(box_offset, dimension, box_dimension):
                next_cell_row = row_index + 1
                next_cell_column = column_index - box_offset
                self.puzzle[row_index, column_index].set_next_cell_in_box( self.puzzle[ next_cell_row, next_cell_column ] )

        # Next, link last cell in box (bottom left) to 1st cell in box (upper right)
        # Loop should execute dimension times
        for row_index in range(box_offset, dimension, box_dimension):
            for column_index in range(box_offset, dimension, box_dimension):
                next_cell_row = row_index - box_offset
                next_cell_column = column_index - box_offset

                self.puzzle[row_index, column_index].set_next_cell_in_box( self.puzzle[ next_cell_row, next_cell_column ] )

        # Set each cell's box number
        for row_index in range(dimension):
            for column_index in range(dimension):
                box_number = box_dimension * int((row_index)//box_dimension) + int((column_index)//box_dimension) + 1
                self.puzzle[row_index, column_index].set_box_number(box_number)

    def validate_dimension(self, dimension):
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

    def get_puzzle(self) -> Sudoku:
        """
        :return: Deep copy of puzzle.
        :rtype: Sudoku object
        """
        return self.puzzle

class SudokuSolver():
    """Performs high level solution flow on working copy of puzzle."""
    def __init__(self, puzzle):
        if puzzle.unsolved_cell_count() == len(puzzle):
            raise SudokuErrors("Unable to solve empty puzzle.")

        self.puzzle = copy.deepcopy(puzzle)

    def get_puzzle(self):
        """Returns reference to solved puzzle."""
        return self.puzzle

    def solve(self):
        """Solves the puzzle in steps that range from basic through more advanced logic."""
        try:
            self.puzzle._fill_empty_cells()  # fill empty cells w/ all possible options

            # Remove initially given cell values from all relevant contexts
            self.puzzle.normalize()

            num_unsolved = self.puzzle.unsolved_cell_count()
            if num_unsolved > 0:
                log(logger.debug, f"Still have {num_unsolved} cells to solve.")
            else:   # An "easy" puzzle if this step solved it
                self.puzzle.puzzle_log()  # write puzzle to log
                return

            # This phase is usually enough to solve med to hard puzzles
            self.puzzle.apply_to_all_contexts(self.puzzle.resolve_uniques_in_context)
            num_unsolved = self.puzzle.unsolved_cell_count()
            if num_unsolved > 0:
                log(logger.debug, f"{num_unsolved} cells to solve.")
            else:
                return

            # Resolve remaining cells using trial and error
            puzzle_backup = self.puzzle
            for i in range(0,10):
                self.puzzle.clear_unsolved_cells()
                status = self.puzzle.fill()
                if status == PlaceStatus.PASSED:
                    log(logger.debug, f"{i} trial and error attempt(s) required to solve puzzle.")
                    break

                self.puzzle = puzzle_backup

            log(logger.info, f"Puzzle was {"successfully" if status == PlaceStatus.PASSED else "not"} solved.")

        except Exception as ex:
            raise SudokuErrors("SudokuSolver.solve()") from ex
