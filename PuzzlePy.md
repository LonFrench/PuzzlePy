# PuzzlePy package

## Modules

## puzzle

This module contains abstract base classes, enumerations, and constants
for implementing various types of 2-D puzzles.

### *class* puzzle.LineType(\*values)

Bases: `Enum`

#### ROW *= 0*

#### COL *= 1*

### *class* puzzle.CellContext(\*values)

Bases: `Enum`

#### ROW *= 1*

#### COLUMN *= 2*

#### BOX *= 3*

#### DIAGONAL_MAIN *= 4*

#### DIAGONAL_MINOR *= 5*

#### NONE *= 6*

### *exception* puzzle.PuzzleExcept(err_msg)

Bases: `Exception`

#### \_\_init_\_(err_msg)

### *exception* puzzle.CellExcept(err_msg)

Bases: `Exception`

#### \_\_init_\_(err_msg)

### *exception* puzzle.BuildError(err_msg)

Bases: `Exception`

#### \_\_init_\_(err_msg)

### *class* puzzle.Cell(raw_value=None, row_index=-1, column_index=-1, placeholder=' ')

Bases: `ABC`

This class represents the smallest element in a puzzle.
Cells are circularly linked to neighbors by row and column, each 
referred to as a “context”. Subclasses may define their own cell contexts.

#### *abstractmethod* \_\_init_\_(raw_value=None, row_index=-1, column_index=-1, placeholder=' ')

Base ctor

* **Parameters:**
  * **raw_value** (*any value type*) – Cell’s value; if not placeholder Cell will be 
    marked as immutable
  * **row_index** (*int* *(**0 relative* *)*) – Index of row within puzzle matrix to place this
    Cell; required
  * **column_index** (*int* *(**0 relative* *)*) – Index of column within puzzle matrix to 
    place this Cell; required
  * **placeholder** (*char*) – Value for empty Cell (defaults to single space)

#### \_\_str_\_()

Return str(self).

#### set(raw_value) → bool

Sets contents of cell to a set containing the passed-in raw value.

* **Parameters:**
  **raw_value** (*value type*) – New cell contents
* **Returns:**
  True if successful (if contents not immutable); otherwise False
* **Treturn:**
  bool

#### row_iter() → [RowIterator](#puzzle.RowIterator)

Returns iterator for cell’s row.

* **Returns:**
  Iterator for cell’s row
* **Return type:**
  [RowIterator](#puzzle.RowIterator)

#### column_iter() → [ColumnIterator](#puzzle.ColumnIterator)

Returns iterator for cell’s column.

* **Returns:**
  Iterator for cell’s column
* **Return type:**
  [ColumnIterator](#puzzle.ColumnIterator)

#### empty() → bool

Tests whether cell contains anything other than the placeholder.

* **Returns:**
  True if cell contains only the placeholder, otherwise False.
* **Return type:**
  bool

#### solved() → bool

Determines if Cell has been “solved”, i.e., its contents
contain a set with a single char other than the placeholder.

* **Returns:**
  True if Cell solved; otherwise False
* **Return type:**
  bool

#### value_in_context(context_iter, value) → bool

Determines if a value occurs anywhere else in this Cell for
the given context.

* **Parameters:**
  **value** (*char*) – Search value
* **Returns:**
  True if value found in another Cell in context; otherwise
  False.
* **Return type:**
  bool

#### remove_value_from_context(context_iter)

Remove Cell’s value from context using given iterator. 
Expects cell contents to have single element. If removing this
value leaves any Cells with only a single value, this method
is recursively called to perform further clean up.

* **Parameters:**
  **context_iter** (*Context* *(**row* *,* *column* *,* *etc.* *)* *iterator*) – Iterator of context in which to remove this 
  Cell’s value.

#### clear()

Replaces cell contents with placeholder.

#### remove_all_but(keepers) → bool

Removes all values except the passed ones.

* **Parameters:**
  **keepers** (*set* *of* *value types*) – values to keep
* **Returns:**
  True if anything removed; False otherwise
* **Return type:**
  bool

#### remove_value(value) → bool

Removes the passed value from the cell’s contents.

* **Parameters:**
  **value** (*char*) – Value to be removed
* **Returns:**
  True if any values removed; otherwise False
* **Treturn:**
  bool

#### remove_values(values) → bool

Removes the passed values from the cell’s contents.

* **Parameters:**
  **value** (*List* *of* *chars*) – Values to be removed
* **Returns:**
  True if any values removed; otherwise False
* **Treturn:**
  bool

### *class* puzzle.GenericCell(s_value)

Bases: [`Cell`](#puzzle.Cell)

#### \_\_init_\_(s_value)

Base ctor

* **Parameters:**
  * **raw_value** (*any value type*) – Cell’s value; if not placeholder Cell will be 
    marked as immutable
  * **row_index** (*int* *(**0 relative* *)*) – Index of row within puzzle matrix to place this
    Cell; required
  * **column_index** (*int* *(**0 relative* *)*) – Index of column within puzzle matrix to 
    place this Cell; required
  * **placeholder** (*char*) – Value for empty Cell (defaults to single space)

### *class* puzzle.CellFactory

Bases: `ABC`

Implementing classes must instantiate and return a cell of the desired type.
Objects of derived classes will be passed to builder classes which construct
puzzles of the desired type.

#### *abstractmethod* new_cell(value=None, row_index=0, column_index=0, placeholder=' ') → [Cell](#puzzle.Cell)

This method will be used by corresponding “builder” classes to 
create Cells of the proper type for the type of puzzle being
constructed.

* **Parameters:**
  * **value** (*any value type*) – Cell’s value; if not placeholder Cell will be 
    marked as immutable
  * **row_index** (*int* *(**0 relative* *)*) – Index of row within puzzle matrix to place this
    Cell (defaults to 0)
  * **column_index** (*int* *(**0 relative* *)*) – Index of column within puzzle matrix to 
    place this Cell (defaults to 0)
  * **placeholder** (*char*) – Value for empty Cell (defaults to single space)
* **Returns:**
  Cell object
* **Return type:**
  Object of class derived from Class

### *class* puzzle.GenericCellFactory

Bases: [`CellFactory`](#puzzle.CellFactory)

#### \_\_init_\_()

#### new_cell(value, row=-1, column=-1, immutable=False)

This method will be used by corresponding “builder” classes to 
create Cells of the proper type for the type of puzzle being
constructed.

* **Parameters:**
  * **value** (*any value type*) – Cell’s value; if not placeholder Cell will be 
    marked as immutable
  * **row_index** (*int* *(**0 relative* *)*) – Index of row within puzzle matrix to place this
    Cell (defaults to 0)
  * **column_index** (*int* *(**0 relative* *)*) – Index of column within puzzle matrix to 
    place this Cell (defaults to 0)
  * **placeholder** (*char*) – Value for empty Cell (defaults to single space)
* **Returns:**
  Cell object
* **Return type:**
  Object of class derived from Class

### *class* puzzle.CellIterator(cell, context_type=CellContext.NONE)

Bases: `ABC`

Abstract base class for cell iterators. Extended for cell traversal within various
contexts, e.g., rows, columns, diagonals, etc.

#### *abstractmethod* \_\_init_\_(cell, context_type=CellContext.NONE)

### *class* puzzle.RowIterator(cell)

Bases: [`CellIterator`](#puzzle.CellIterator)

Iterator for traversing a cell’s row; starts at current cell and, 
since cells are circularly linked, breaks out of loop before 
returning to current cell.

#### \_\_init_\_(cell)

### *class* puzzle.ColumnIterator(cell)

Bases: [`CellIterator`](#puzzle.CellIterator)

Iterator for traversing a cell’s column; starts at current cell and,
since cells are circularly linked, breaks out of loop before returning
to current cell.

#### \_\_init_\_(cell)

### *class* puzzle.Puzzle(row_dimension, column_dimension)

Bases: `object`

#### \_\_init_\_(row_dimension, column_dimension)

#### \_\_eq_\_(other) → bool

Compares contents of all cells against the other puzzle’s cells’ contents.

* **Parameters:**
  **other** (*Puzzle class* *or* *derivative.*) – Puzzle to compare this puzzle to
* **Returns:**
  True if dimensions of puzzles match and all their Cells’ contents are equal
* **Return type:**
  bool

#### as_list()

Returns puzzle as list of cells’ contents.

#### clear()

Sets contents of all non-immutable cells to placeholder.

#### empty_count()

Returns the number of empty Cells, i.e., those that only contain
the placeholder.

#### add_row(row)

#### max_contents_size()

Returns the highest number of elements found in any Cell.

#### get_random_empty()

#### get_first_cell_in_row(row_number) → [Cell](#puzzle.Cell)

Returns first cell in row.

* **Parameters:**
  **row_number** (*int*) – Row number (not index, i.e., starts at 1)
* **Returns:**
  First cell in given row
* **Return type:**
  [Cell](#puzzle.Cell)

#### get_first_cell_in_column(column_number) → [Cell](#puzzle.Cell)

Returns first cell in column.

* **Parameters:**
  **column_number** (*int*) – Column number (not index, i.e., starts at 1)
* **Returns:**
  First cell in given column
* **Return type:**
  [Cell](#puzzle.Cell)

#### log_line(context=CellContext.NONE) → str

Generates string representation appropriate for logging of all puzzle 
lines of the given type.

* **Parameters:**
  **context** ([*CellContext*](#puzzle.CellContext)) – Conext, i.e., row or column, in which to generate
  strings
* **Raises:**
  PuzzleExcept if invalid context passed

#### puzzle_log()

Returns puzzle contents in a format appropriate for logging.

### *class* puzzle.PuzzleBuilder(puzzle, cell_factory, num_rows, num_columns, values=None, all_possible_values=['1', '2', '3', '4', '5', '6', '7', '8', '9'], placeholder=' ')

Bases: `ABC`

Base puzzle builder that performs basic setup and validation. Most of the
details should be taken care of in derived classes.

#### *abstractmethod* \_\_init_\_(puzzle, cell_factory, num_rows, num_columns, values=None, all_possible_values=['1', '2', '3', '4', '5', '6', '7', '8', '9'], placeholder=' ')

Validates and initializes puzzle with any passed-in values.

* **Parameters:**
  * **starting_values** (*List* *of*  *(**typically* *)* *single char strings* *,* *e.g.* *,* 
     *[* *'7'* *,* *'2'* *,* *'9'* *,* *...* *,* *'7'* *]* *that represent all* 
    *(**typically 81* *)* *cell values in puzzle.*) – Lists of character lists to use for initial 
    puzzle state. If nothing passed the
    placeholder value will be used throughout.
  * **dimension** (*int* *(**must be square* *of* *an integer* *)*) – Puzzle dimension, i.e., length of rows and columns (defaults to 9)
  * **all_possible_values** ( *[**char* *]*) – List of all possible values if no starting values 
    given. Each value must be unique.
  * **placeholder** (*char*) – Char used to denote empty Cells (defaults to ‘ ‘)
* **Raises:**
  SudokuBuildError if invalid parameter enountered

### *class* puzzle.GenericPuzzleBuilder(values=None, rows=9, columns=9)

Bases: [`PuzzleBuilder`](#puzzle.PuzzleBuilder)

#### \_\_init_\_(values=None, rows=9, columns=9)

Validates and initializes puzzle with any passed-in values.

* **Parameters:**
  * **starting_values** (*List* *of*  *(**typically* *)* *single char strings* *,* *e.g.* *,* 
     *[* *'7'* *,* *'2'* *,* *'9'* *,* *...* *,* *'7'* *]* *that represent all* 
    *(**typically 81* *)* *cell values in puzzle.*) – Lists of character lists to use for initial 
    puzzle state. If nothing passed the
    placeholder value will be used throughout.
  * **dimension** (*int* *(**must be square* *of* *an integer* *)*) – Puzzle dimension, i.e., length of rows and columns (defaults to 9)
  * **all_possible_values** ( *[**char* *]*) – List of all possible values if no starting values 
    given. Each value must be unique.
  * **placeholder** (*char*) – Char used to denote empty Cells (defaults to ‘ ‘)
* **Raises:**
  SudokuBuildError if invalid parameter enountered

## sudoku

This module extends classes defined in the puzzle module and defines new classes used for building and solving Sudoku puzzles.

### sudoku.log(func, \*args)

### *exception* sudoku.SudokuErrors(err_msg)

Bases: `Exception`

#### \_\_init_\_(err_msg)

### *exception* sudoku.SudokuBuildError(err_msg)

Bases: `Exception`

#### \_\_init_\_(err_msg)

### *class* sudoku.Status(\*values)

Bases: `Enum`

Used to indicate results of attempt to place value in cell.

#### PASSED *= 1*

#### FINISHED *= 2*

#### FAILED *= 3*

#### FINISHED_FAILED *= 4*

### *class* sudoku.SudokuCell(value, row_index=-1, column_index=-1, placeholder=' ')

Bases: [`Cell`](#puzzle.Cell)

This concrete class builds upon the superclass by defining a “box” 
context and methods to aid Sudoku puzzle solving.

#### \_\_init_\_(value, row_index=-1, column_index=-1, placeholder=' ')

Base ctor

* **Parameters:**
  * **raw_value** (*any value type*) – Cell’s value; if not placeholder Cell will be 
    marked as immutable
  * **row_index** (*int* *(**0 relative* *)*) – Index of row within puzzle matrix to place this
    Cell; required
  * **column_index** (*int* *(**0 relative* *)*) – Index of column within puzzle matrix to 
    place this Cell; required
  * **placeholder** (*char*) – Value for empty Cell (defaults to single space)

#### set_next_cell_in_box(next_cell)

#### get_next_cell_in_box()

#### box_iter()

Returns iterator for cell’s box.

* **Returns:**
  Iterator for cell’s box
* **Return type:**
  [BoxIterator](#sudoku.BoxIterator)

#### remove_value_from_view()

Remove cell’s value from all contexts, i.e., all cells within its view.

#### set_box_number(box_number)

#### set_if_no_conflict(value)

#### value_exists_within_view(value)

### *class* sudoku.SudokuCellFactory

Bases: [`CellFactory`](#puzzle.CellFactory)

#### \_\_init_\_()

#### new_cell(value, row_index=-1, column_index=-1, placeholder=' ')

This method will be used by corresponding “builder” classes to 
create Cells of the proper type for the type of puzzle being
constructed.

* **Parameters:**
  * **value** (*any value type*) – Cell’s value; if not placeholder Cell will be 
    marked as immutable
  * **row_index** (*int* *(**0 relative* *)*) – Index of row within puzzle matrix to place this
    Cell (defaults to 0)
  * **column_index** (*int* *(**0 relative* *)*) – Index of column within puzzle matrix to 
    place this Cell (defaults to 0)
  * **placeholder** (*char*) – Value for empty Cell (defaults to single space)
* **Returns:**
  Cell object
* **Return type:**
  Object of class derived from Class

### *class* sudoku.BoxIterator(cell)

Bases: [`CellIterator`](#puzzle.CellIterator)

#### \_\_init_\_(cell)

### *class* sudoku.SudokuPuzzle(all_value_options, dimension)

Bases: [`Puzzle`](#puzzle.Puzzle)

This class extends Puzzle by adding Sudoku specific processing: box
searches, pattern operations, and other specific validation and actions.

#### \_\_init_\_(all_value_options, dimension)

#### get_box_dimension()

#### get_first_cell_in_box(box_number)

#### get_context_iterator(context_type, number)

#### fill() → [Status](#sudoku.Status)

This method fills out a Sudoku puzzle. The puzzle may start empty
or with any number of values. Since native randomization is pseudo-
random, two random steps are used to increase randomization; value
options are randomized and then assigned to random cells within
boxes. A systematic, trial and error approach is taken, moving 
through the boxes making assignments and applying logic to 
determine minimum backtrack steps to optimize the process.

* **Returns:**
  Status.FAILED returned if unable to find cell in box to place value, Status.PASSED otherwise.
* **Return type:**
  Status enum

#### place_value(value, box_num, backup_count=0)

Recursively called method that places given value in the given puzzle
box. If a value can’t be placed the number of recursive steps to back
up will be returned. The value is constant during this process but
the box number is incremented for each call. Number of backup steps
depends on location of box and returns the process to the point
that a different placement will most likely be impactful.

* **Parameters:**
  * **value** (*Usually an integer* *,* *but could be anything.*) – Value to place.
  * **box_num** (*Integer value from 1 to puzzle dimension* *,* *typically 9.*) – Box to place the given value. Boxes are numbered from 1 to 9 (typically) starting in upper left and going right then down until eventually reaching the 9th box in the lower right.
  * **backtrack** – The number of recursion steps to go back up the call stack to redo.
* **Returns:**
  Status.FAILED returned if unable to find cell in box to place value, Status.PASSED otherwise.
* **Return type:**
  Status enum

#### eligible_box_cells(box_num, value)

Returns a list of Cells belonging to the given box that have  
neither row nor column value conflicts.

* **Parameters:**
  * **box_num** (*int from 1 to dimension*) – Number of box for which to build list.
  * **value** (*int* *(**typically* *,* *but could be anything* *)*) – Value for which to ensure there are no conflicts.
* **Returns:**
  List of Cells without row/column value conflicts
* **Return type:**
  Cell list

#### fill_empty_cells_with_options()

#### normalize()

#### apply_to_all_contexts(func_to_apply)

#### cells_per_value_dict(iter, min_size=1, max_size=100)

#### resolve_uniques_in_context(context_type, context_number)

#### intersecting_context_resolution()

#### find_intersection_with_box(line_iter)

#### combo_reduction(context_type, context_number)

#### find_combination2(cells_per_value_dict, subject_value)

#### find_combination(cells_per_value_dict, root_value, value_set, cell_set, iter=0)

#### remove_values_from_context(context_iter, values)

#### remove_value_from_context(context_type, context_number, value)

#### find_shared_lines(cells)

#### unsolved_cell_count()

#### puzzle_log()

Returns puzzle contents as a string appropriate for logging. The 
string is formatted for readability; layout adjusted per puzzle
dimension and white space dynamically adapted to cell content size.

### *class* sudoku.SudokuPuzzleBuilder(starting_values=None, dimension=9, all_possible_values=['1', '2', '3', '4', '5', '6', '7', '8', '9'], placeholder=' ')

Bases: [`PuzzleBuilder`](#puzzle.PuzzleBuilder)

Creates a matrix of Sudoku cells that are circularly linked per 
the 3 relevant Sudoku contexts; row, column, box.

#### \_\_init_\_(starting_values=None, dimension=9, all_possible_values=['1', '2', '3', '4', '5', '6', '7', '8', '9'], placeholder=' ')

Validates and initializes puzzle with any passed-in values.

* **Parameters:**
  * **starting_values** (*List* *of*  *(**typically* *)* *single char strings* *,* *e.g.* *,* 
     *[* *'7'* *,* *'2'* *,* *'9'* *,* *...* *,* *'7'* *]* *that represent all* 
    *(**typically 81* *)* *cell values in puzzle.*) – Lists of character lists to use for initial 
    puzzle state. If nothing passed the
    placeholder value will be used throughout.
  * **dimension** (*int* *(**must be square* *of* *an integer* *)*) – Puzzle dimension, i.e., length of rows and columns (defaults to 9)
  * **all_possible_values** ( *[**char* *]*) – List of all possible values if no starting values 
    given. Each value must be unique.
  * **placeholder** (*char*) – Char used to denote empty Cells (defaults to ‘ ‘)
* **Raises:**
  SudokuBuildError if invalid parameter enountered

#### validate_dimension(dimension) → int

Validator to ensure passed-in dimension or size of starting value 
list is appropriate for Sudoku puzzles, that is, an integer square.

* **Parameters:**
  **dimension** ( *+ve int*) – Value to find square root for.
* **Returns:**
  Square root of puzzle size (dimension).
* **Return type:**
  int
* **Raises:**
  SudokuBuildError if dimension invalid

#### get_puzzle() → [SudokuPuzzle](#sudoku.SudokuPuzzle)

* **Returns:**
  Deep copy of puzzle.
* **Return type:**
  SudokuPuzzle object

### *class* sudoku.SudokuSolver(puzzle)

Bases: `object`

#### \_\_init_\_(puzzle)

#### get_puzzle()

#### solve_puzzle()

## kakuro

This module extends classes defined in the puzzle module and defines new classes used for building and solving Kakuro puzzles.

### *class* kakuro.KakuroCell(s_value, row=-1, column=-1, s_immutable=False)

Bases: [`Cell`](#puzzle.Cell)

This concrete class builds upon the superclass by …. (TBD)

#### \_\_init_\_(s_value, row=-1, column=-1, s_immutable=False)

Base ctor

* **Parameters:**
  * **raw_value** (*any value type*) – Cell’s value; if not placeholder Cell will be 
    marked as immutable
  * **row_index** (*int* *(**0 relative* *)*) – Index of row within puzzle matrix to place this
    Cell; required
  * **column_index** (*int* *(**0 relative* *)*) – Index of column within puzzle matrix to 
    place this Cell; required
  * **placeholder** (*char*) – Value for empty Cell (defaults to single space)

## test_puzzles

Unit tests for Sudoku related puzzle building and validation.

### *class* tests.test_puzzles.SudokuTest(methodName='runTest')

Bases: `TestCase`

#### test_build_exception_invalid_dimension()

#### test_build_exception_all_values_dimension_size_mismatch()

#### test_build_exception_invalid_all_values_size()

#### test_build_exception_invalid_placeholder()

#### test_build_exception_invalid_all_values_container()

#### test_cell_creation_no_indices()

#### test_cell_creation_bad_index()

#### test_cell_creation_val_too_large()

#### test_fill_empty_9x9_puzzle()

#### test_fill_empty_16x16_puzzle()

#### test_alternate_placeholder()

#### test_solve_easy()

#### test_solve_difficult()

#### test_solve_challenging()

#### test_fill_partial()

#### test_verify_difficult_solution()
