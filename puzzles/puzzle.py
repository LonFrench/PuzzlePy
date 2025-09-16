"""
This module contains abstract base classes, enumerations, and constants
for implementing various types of 2-D puzzles.
""" 
from abc import ABC, abstractmethod
import copy
from enum import Enum, unique, auto
import random


# TODO: identify internal only variables/methods and add underscore ('_')to front of name

default_placeholder = ' '
default_value_options = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
tab_size = 5

class LineType(Enum):
    ROW = 0
    COL = 1

class CellContext(Enum):
    ROW = auto()
    COLUMN = auto()
    BOX = auto()    
    DIAGONAL_MAIN = auto()   # running from left down to right
    DIAGONAL_MINOR = auto()   # running from right down to left
    NONE = auto()


class PuzzleExcept(Exception):
    def __init__(self, err_msg):
        super().__init__(err_msg)

class CellExcept(Exception):
    def __init__(self, err_msg):
        super().__init__(err_msg)

class BuildError(Exception):
    def __init__(self, err_msg):
        super().__init__(err_msg)


class Cell(ABC):
    """
    This class represents the smallest element in a puzzle.
    Cells are circularly linked to neighbors by row and column, each 
    referred to as a "context". Subclasses may define their own cell contexts.
    
    """

    @abstractmethod       # using abstract class
    def __init__(self, raw_value = None, row_index = -1, column_index = -1, placeholder = default_placeholder):
        """
        Base ctor

        :param raw_value: Cell's value; if not placeholder Cell will be 
            marked as immutable
        :type raw_value: any value type
        :param row_index: Index of row within puzzle matrix to place this
            Cell; required
        :type row_index: int (0 relative)
        :param column_index: Index of column within puzzle matrix to 
            place this Cell; required
        :type column_index: int (0 relative)
        :param placeholder: Value for empty Cell (defaults to single space)
        :type placeholder: char
        """
# TODO: determine if "contents" should be set by subclass if given; how it's being set for SudokuPuzzle is fuzzy when looking at the code: 
# default to string unless something different is passed as parameter. The base cell class should be as type agnostic as possible for "contents"

        self._placeholder = placeholder

        if row_index < 0 or column_index < 0:
            raise CellExcept(f"Valid cell indices must be provided.")
        
        # If initial, non-placeholder value given then set cell immutable
        self.immutable = False
        if raw_value == None or raw_value == placeholder:
            self.set(self._placeholder)
        else:
            self.set(raw_value)
            self.immutable = True

        # Make line numbers 1 relative
        self.row_number = row_index + 1
        self.column_number = column_index + 1

    def __str__(self):
        sorted_contents = sorted(self.contents)
        ret_str = ''.join(sorted_contents)
        return ret_str

    def __len__(self):
        if self.contents == {self._placeholder}:
            return 0
        else:
            return len(self.contents)

    def __contains__(self, value):
        return value in self.contents
        
    def __iter__(self):
        return iter(self.contents)

    def _set_immutable(self, state):
        self.immutable = state
 
    def _set_next_cell_in_row(self, next_cell):
        self.next_cell_in_row = next_cell

    def _set_next_cell_in_column(self, next_cell):
        self.next_cell_in_column = next_cell
   
    def _get_next_cell_in_row(self):
        return self.next_cell_in_row

    def _get_next_cell_in_column(self):
        return self.next_cell_in_column

    def set(self, raw_value) -> bool:
        """
        Sets contents of cell to a set containing the passed-in raw value.

        :param raw_value: New cell contents
        :type raw_value: value type
        :return: True if successful (if contents not immutable); otherwise False 
        :treturn: bool
        """
        if not self.immutable:
            self.contents = set(raw_value)
            return True
        else:
            return False

    def row_iter(self) -> "RowIterator":      # using double quotes since a forward reference 
        """
        Returns iterator for cell's row.

        :return: Iterator for cell's row
        :rtype: RowIterator
        """
        return RowIterator(self)

    def column_iter(self) -> "ColumnIterator": 
        """
        Returns iterator for cell's column.

        :return: Iterator for cell's column
        :rtype: ColumnIterator
        """
        return ColumnIterator(self)

    def empty(self) -> bool:
        """
        Tests whether cell contains anything other than the placeholder.

        :return: True if cell contains only the placeholder, otherwise False.
        :rtype: bool
        """
        if self.contents == {self._placeholder}:
            return True
        return False

    # Assuming if cell has a single, non-placeholder value it's solved.
    # May have to rethink this definition for future puzzle types
    def solved(self) -> bool:
        """
        Determines if Cell has been "solved", i.e., its contents
        contain a set with a single char other than the placeholder.

        :returns: True if Cell solved; otherwise False
        :rtype: bool
        """
        if self.contents == {self._placeholder} or len(self.contents) > 1:
            return False
        return True

    def value_in_context(self, context_iter, value) -> bool:
        """
        Determines if a value occurs anywhere else in this Cell for
        the given context.

        :param value: Search value
        :type value: char
        :return: True if value found in another Cell in context; otherwise
            False.
        :rtype: bool
        """    
        found = False
        for srch_cell in context_iter:
            if value in srch_cell:            # using set membership test
                found = True
                break
        return found

    def remove_value_from_context(self, context_iter):
        """
        Remove Cell's value from context using given iterator. 
        Expects cell contents to have single element. If removing this
        value leaves any Cells with only a single value, this method
        is recursively called to perform further clean up.

        :param context_iter: Iterator of context in which to remove this 
            Cell's value.
        :type context_iter: Context (row, column, etc.) iterator
        """
        if len(self.contents) != 1:
            raise CellExcept(f"Cell's content length is ({len(self.contents)}); must be 1.")
        next(context_iter)    # using iter explicit increment to move past current cell
        for srch_cell in context_iter:
            if len(srch_cell) != 1:
                srch_cell.remove_value(str(self))

                # If this results in cell having single value, repeat for this cell...
                if len(srch_cell) == 1:
                    srch_cell.remove_value_from_view()

    def clear(self):
        """
        Replaces cell contents with placeholder.
        """
        if not self.immutable:
            self.contents = {self._placeholder}

    # Returns True if a change was made
    def remove_all_but(self, keepers) -> bool:
        """
        Removes all values except the passed ones.

        :param keepers: values to keep
        :type keepers: set of value types
        :return: True if anything removed; False otherwise
        :rtype: bool
        """
        change_made = False
        temp = copy.deepcopy(self.contents)
        for value in temp:
            if value not in keepers:
                self.contents.discard(value)
                change_made = True

        return change_made

    # Returns True if value was actually removed from cell
    def remove_value(self, value) -> bool:
        """
        Removes the passed value from the cell's contents.

        :param value: Value to be removed
        :type value: char
        :return: True if any values removed; otherwise False
        :treturn: bool
        """
        if self.immutable is True:
            return False
        before_length = len(self.contents)
        self.contents.discard(value)
        return before_length != len(self.contents)

    def remove_values(self, values) -> bool:
        """
        Removes the passed values from the cell's contents.

        :param value: Values to be removed
        :type value: List of chars
        :return: True if any values removed; otherwise False
        :treturn: bool
        """
        if self.immutable is True:
            return False
        before_length = len(self.contents)
        for value in values:
            self.contents.discard(value)
        return before_length != len(self.contents)


class GenericCell(Cell):
    def __init__(self, s_value):
        super().__init__(value = s_value)


class CellFactory(ABC):
    """
    Implementing classes must instantiate and return a cell of the desired type.
    Objects of derived classes will be passed to builder classes which construct
    puzzles of the desired type.
    """
    @abstractmethod
    def new_cell(self, value = None, row_index = 0, column_index = 0, placeholder = default_placeholder) -> Cell:
        """
        This method will be used by corresponding "builder" classes to 
        create Cells of the proper type for the type of puzzle being
        constructed.

        :param value: Cell's value; if not placeholder Cell will be 
            marked as immutable
        :type value: any value type
        :param row_index: Index of row within puzzle matrix to place this
            Cell (defaults to 0)
        :type row_index: int (0 relative)
        :param column_index: Index of column within puzzle matrix to 
            place this Cell (defaults to 0)
        :type column_index: int (0 relative)
        :param placeholder: Value for empty Cell (defaults to single space)
        :type placeholder: char
        :return: Cell object 
        :rtype: Object of class derived from Class 
        """
        pass

class GenericCellFactory(CellFactory):
    def __init__(self):
        self.type = "Generic"

    def new_cell(self, value, row = -1, column = -1, immutable = False):
        return GenericCell(value, row, column, immutable)

class CellIterator(ABC):
    """
    Abstract base class for cell iterators. Extended for cell traversal within various
    contexts, e.g., rows, columns, diagonals, etc.
    """
    @abstractmethod
    def __init__(self, cell, context_type = CellContext.NONE):
        if context_type is CellContext.NONE:
            raise PuzzleExcept(f"CellIterator(): Invalid context type ({str(CellContext.NONE)}).")

        self.context = context_type
        self.first_cell = self.next_cell = cell
        self.stop = False

    def __iter__(self):
        return self
    
    def __next__(self):
        pass

class RowIterator(CellIterator):       
    """
    Iterator for traversing a cell's row; starts at current cell and, 
    since cells are circularly linked, breaks out of loop before 
    returning to current cell.
    """
    def __init__(self, cell):
        super().__init__(cell, CellContext.ROW)

    def __next__(self):
        if self.stop is True:
            raise StopIteration

        cell = self.next_cell
        self.next_cell = self.next_cell._get_next_cell_in_row()

        # The original cell was the first one returned. If we're back to it 
        # we've finished the circularly liked cell row list.
        if self.next_cell == self.first_cell:
            self.stop = True
 
        return cell

class ColumnIterator(CellIterator):
    """
    Iterator for traversing a cell's column; starts at current cell and,
    since cells are circularly linked, breaks out of loop before returning
    to current cell.
    """
    def __init__(self, cell):
        super().__init__(cell, CellContext.COLUMN)

    def __next__(self):
        if self.stop is True:
            raise StopIteration

        cell = self.next_cell
        self.next_cell = self.next_cell._get_next_cell_in_column()

        # The original cell was the first one returned. If we're back to it 
        # we've finished the circularly liked cell column list.
        if self.next_cell == self.first_cell:      # TODO: try using "is" instead of ==
            self.stop = True
 
        return cell


class Puzzle:

    def __init__(self, row_dimension, column_dimension):
        if row_dimension < 1:
            raise PuzzleExcept(f"Row dimension ({row_dimension}) must be positive integer.")
        if column_dimension < 1:
            raise PuzzleExcept(f"Column dimension ({column_dimension}) must be positive integer.")

        self.row_dimension = row_dimension
        self.column_dimension = column_dimension
        self.matrix = []
        self.length = row_dimension * column_dimension
        

    # Returns the puzzle as a single string where all the cell values have been concatenated
    # starting with the upper left and moving left to right and down till the bottom right cell
#TODO: fix this
    # def __str__(self):
    #     val = [str(self.matrix[row][col]) for row in range(self.row_dimension) for col in range(self.column_dimension)]   #using list comprehension
    #     pass


#TODO: determine what this would be needed
    def __len__(self):
        return self.length

    def __setitem__(self, indices, value):       # Using tuple to pass in row and column indices
        row_index, column_index = indices        # Unpack indices
        self.matrix[row_index][column_index] = value

    def __getitem__(self, indices):
        row_index, column_index = indices
        return self.matrix[row_index][column_index]

    def __eq__(self, other) -> bool:
        """
        Compares contents of all cells against the other puzzle's cells' contents. 

        :param other: Puzzle to compare this puzzle to
        :type other: Puzzle class or derivative.
        :return: True if dimensions of puzzles match and all their Cells' contents are equal
        :rtype: bool
        """
        if self.row_dimension != other.row_dimension:
            return False
        if self.column_dimension != other.column_dimension:
            return False
        for row in range(self.row_dimension):
            for col in range(self.column_dimension):
                if str(self.matrix[row][col]) != str(other.matrix[row][col]):
                    return False
                
        return True


    def as_list(self):
        """
        Returns puzzle as list of cells' contents.
        """
        val = [self.matrix[row][col] for row in range(self.row_dimension) for col in range(self.column_dimension)]   #using list comprehension
        pass

    def clear(self):
        """
        Sets contents of all non-immutable cells to placeholder.
        """
        for row in self.matrix:
            for cell in row:
                cell.clear()

    def empty_count(self):
        """ 
        Returns the number of empty Cells, i.e., those that only contain
        the placeholder.
        """
        self._build_empty_cell_list()
        return len(self.empties)   

    def add_row(self, row):
        self.matrix.append(row)

    def max_contents_size(self):
        """
        Returns the highest number of elements found in any Cell.
        """
        max = 0
        for row in self.matrix:
            for cell in row:
                size = len(cell.contents)
                if size > max:
                    max = size
        return max

    def _build_empty_cell_list(self):
        self.empties = []
        for row in self.matrix:
            for cell in row:
                if cell.empty():
                    self.empties.append(cell) 


    def get_random_empty(self):
        self._build_empty_cell_list()        
        if len(self.empties) != 0:
            return random.sample(self.empties, len(self.empties))     #using random sample
        else:
            return None

    def get_first_cell_in_row(self, row_number) -> Cell:
        """
        Returns first cell in row.

        :parameter row_number: Row number (not index, i.e., starts at 1)
        :type row_number: int
        :return: First cell in given row
        :rtype: Cell
        """
        if row_number < 1 and row_number > self.dimension:
            raise PuzzleExcept(f"Row number ({row_number}) must be between 1 and the puzzle dimension {self.dimension}, inclusive.")
        return self.matrix[row_number - 1][0]
    
    def get_first_cell_in_column(self, column_number) -> Cell:
        """
        Returns first cell in column.

        :parameter column_number: Column number (not index, i.e., starts at 1)
        :type column_number: int
        :return: First cell in given column
        :rtype: Cell
        """
        if column_number < 1 and column_number > self.dimension:
            raise PuzzleExcept(f"Column number ({column_number}) must be between 1 and the puzzle dimension {self.dimension}, inclusive.")
        return self.matrix[0][column_number - 1]

#TODO: clean up  
    # # Returns formatted string with all cell values listed by row
    # def rows_log_str(self):
    #     log_str = "\n\tPuzzle rows:"
    #     for row in range(1, self.row_dimension + 1):
    #         log_str += f"\n\t\t\tRow {row.ljust(2," ")}:"

    #         first_cell = self.get_first_cell_in_row(row)            
    #         cell_iter = first_cell.row_iter()
    #         for cell in cell_iter:
    #             sorted_contents = "".join(sorted(str(cell)))     
    #             log_str += f"    {sorted_contents}"
    #     return log_str   

    # # Returns formatted string with all cell values listed by column
    # def columns_log_str(self):
    #     log_str = "\n\tPuzzle columns:"
    #     for column in range(1, self.column_dimension + 1):
    #         log_str += f"\n\t\tColumn {column}:"

    #         first_cell = self.get_first_cell_in_column(column)            
    #         cell_iter = first_cell.column_iter()
    #         for cell in cell_iter:
    #             sorted_contents = "".join(sorted(str(cell)))  
    #             log_str += f"    {sorted_contents}\t"
    #     return log_str   

    # Returns formatted string with all cell values listed by row    
    def log_line(self, context = CellContext.NONE) -> str:
        """
        Generates string representation appropriate for logging of all puzzle 
        lines of the given type.

        :param context: Conext, i.e., row or column, in which to generate
            strings
        :type context: CellContext
        :raises: PuzzleExcept if invalid context passed
        """
        end = 0
        if context is CellContext.ROW:
            end = self.row_dimension + 1
        elif context is CellContext.COLUMN:
            end = self.column_dimension + 1
        else:
            raise PuzzleExcept(f"log_line(): Invalid context type ({context.name}).")

        line_label = context.name
        log_str += f"\n\tPuzzle {line_label}S:"

        for line in range(1, end):
            log_str += f"\n\t\t\t{line_label} {line.ljust(2," ")}:"

            if context is CellContext.ROW:
                first_cell = self.get_first_cell_in_row(line)            
                cell_iter = first_cell.row_iter()
            else:
                first_cell = self.get_first_cell_in_column(line)            
                cell_iter = first_cell.column_iter()

            for cell in cell_iter:
                sorted_contents = "".join(sorted(str(cell)))     
                log_str += f"    {sorted_contents}"
        return log_str   

    def puzzle_log(self):
        """
        Returns puzzle contents in a format appropriate for logging.
        """
        return f"{self.log_line()}".expandtabs(tab_size)

# TODO: make docstrings below specific to base class
class PuzzleBuilder(ABC):
    """
    Base puzzle builder that performs basic setup and validation. Most of the
    details should be taken care of in derived classes. 
    """
    @abstractmethod
    def __init__(self, puzzle, cell_factory, num_rows, num_columns, values = None, all_possible_values = default_value_options, placeholder = default_placeholder):
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
            if placeholder in all_possible_values:
                raise BuildError(f"Placeholder '{placeholder}' cannot be member of all_possible_values {all_possible_values}.")

            if len(placeholder) != 1:
                raise BuildError(f"Placeholder '{placeholder}' must be single character.")

            self.placeholder = placeholder

            for row_index in range(num_rows):
                row = []
                for column_index in range(num_columns):
                    if values is None:
                        cell_value = self.placeholder

# TODO: determine what usecase this is supposed to cover, remove if none found
                    # elif isinstance(values, str):
                    #     cell_value = values
                    #     immutable = True
                    else:
                        # cell_value = values[column_index + row_index * num_columns]
                        cell_value = values[column_index + row_index * num_columns]

                    # row.append(cell_factory.new_cell(cell_value, row_index, column_index, placeholder, immutable))
                    row.append(cell_factory.new_cell(cell_value, row_index, column_index, placeholder))

                puzzle.add_row(row)

            # Link all cells by row
            for row_index in range(num_rows):
                for column_index in range(num_columns - 1):
                    puzzle[row_index, column_index]._set_next_cell_in_row(puzzle.matrix[row_index][column_index + 1])
                puzzle[row_index, num_columns - 1]._set_next_cell_in_row(puzzle.matrix[row_index][0])    # link last cell back to 1st

            # Link all cells by column
            for column_index in range(num_columns):
                for row_index in range(num_rows - 1):
                    puzzle[row_index, column_index]._set_next_cell_in_column(puzzle.matrix[row_index + 1][column_index])
                puzzle[num_rows - 1, column_index]._set_next_cell_in_column(puzzle.matrix[0][column_index])   # link last cell back to 1st

        except Exception as ex:
            raise BuildError(f"PuzzleBuilder(): {ex}.")


class GenericPuzzleBuilder(PuzzleBuilder):
    def __init__(self, values = None, rows = 9, columns = 9):
        try:
            # create cells to hold all initial puzzle values (or space if no data provided)
#TODO: passing # rows/columns to SudokuPuzzle AND to the parent builder class seems redundant. 
# Maybe have the parent builder class derive dimensions from passed in puzzle? Change for all occurences.
            puzzle = Puzzle(rows, columns)
            cell_factory = GenericCellFactory()
            super().__init__(puzzle, cell_factory, rows, columns, values)   # does basic row/column set up and row and column linked lists

        except:
            raise

