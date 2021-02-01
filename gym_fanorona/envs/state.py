from typing import Tuple, Any, Optional, Union

import numpy as np

from .constants import MOVE_LIMIT, BOARD_COLS, BOARD_ROWS
from .enums import Direction, Piece, Reward
from .position import Position


class FanoronaState:
    def __init__(self, sample: tuple = None):
        self.board_state: Any = None
        self.turn_to_play: Piece = Piece.EMPTY
        self.last_dir: Direction = Direction.X
        self.visited: Any = None
        self.half_moves: int = 0

        if sample:
            self.board_state = sample[0]
            self.turn_to_play = Piece(sample[1])
            self.last_dir = Direction(sample[2])
            self.visited = sample[3]
            self.half_moves = sample[4]

    def __repr__(self):
        return f"<FanoronaState: {str(self)}>"

    def __str__(self):
        return self.get_board_str()

    def get_piece(self, position: Position) -> Piece:
        """Return type of piece at given position (specified in integer coordinates)."""
        return Piece(self.board_state[position.row][position.col])

    def count(self, side: Piece) -> int:
        """Return count of number of pieces of a side on the board."""
        return sum([1 for pos in Position.pos_range() if self.get_piece(pos) == side])

    def other_side(self) -> Piece:
        """Return the color of the opponent's pieces."""
        return self.turn_to_play.other()

    def in_capturing_seq(self) -> bool:
        """Returns True if current state is part of a capturing sequence i.e. at least one capture has already been made."""
        return bool(self.last_dir != Direction.X)

    def piece_exists(self, piece: Piece) -> bool:
        """Checks whether an instance of a piece exists on the game board."""
        for pos in Position.pos_range():
            if self.get_piece(pos) == piece:
                return True
        return False

    def is_done(self) -> bool:
        """
        Check whether the game is over (i.e. the current state is a terminal state).

        The game is over when -
        a) One side has no pieces left to move (loss for the side which has no pieces to move)
        b) The number of half-moves exceeds the limit (draw)
        """
        if self.half_moves >= MOVE_LIMIT:
            return True
        else:
            own_piece_exists = self.piece_exists(self.turn_to_play)
            other_piece_exists = self.piece_exists(self.other_side())
            # Conjecture: cannot have a situation in Fanorona where a piece exists but there are no valid moves
            if own_piece_exists and other_piece_exists:
                return False
            else:
                return True

    def utility(self, side: Piece) -> Union[Reward, int]:
        """Return the reward from a state if done else return None."""
        if self.half_moves >= MOVE_LIMIT:  # draw
            return Reward.DRAW
        elif self.is_done():
            if self.piece_exists(self.turn_to_play):
                winner = self.turn_to_play
            else:
                winner = self.other_side()
            if side == winner:
                return Reward.WIN
            else:
                return Reward.LOSS
        else:
            return self.count(side) - self.count(side.other())

    def reset_visited_pos(self) -> None:
        """Resets visited_pos of a state to indicate no visited positions."""
        for pos in Position.pos_range():
            row, col = pos.to_coords()
            self.visited[row][col] = 0

    @staticmethod
    def set_from_board_str(board_string: str) -> "FanoronaState":
        """Return a new state object using a board string."""

        def process_board_state_str(board_state_str: str):
            row_strings = board_state_str.split("/")
            board_state_chars = [list(row) for row in row_strings]
            board_state = np.zeros(shape=(BOARD_ROWS, BOARD_COLS), dtype=np.int8)
            for row, row_content in enumerate(board_state_chars):
                col_board = 0
                for cell in row_content:
                    if cell == "W":
                        board_state[row][col_board] = Piece.WHITE
                    elif cell == "B":
                        board_state[row][col_board] = Piece.BLACK
                    else:
                        for col_board in range(col_board, col_board + int(cell)):
                            board_state[row][col_board] = Piece.EMPTY
                    col_board += 1
            return board_state

        def process_visited_pos_str(visited_pos_str: str):
            visited = np.zeros(shape=(BOARD_ROWS, BOARD_COLS), dtype=np.int8)
            if visited_pos_str != "-":
                visited_pos_list = visited_pos_str.split(",")
                for human_pos in visited_pos_list:
                    row, col = Position(human_pos).to_coords()
                    visited[row][col] = True
            return visited

        (
            board_state_str,
            turn_to_play_str,
            last_dir_str,
            visited_pos_str,
            half_moves_str,
        ) = board_string.split()

        state = FanoronaState()
        state.board_state = process_board_state_str(board_state_str)
        state.turn_to_play = Piece.WHITE if turn_to_play_str == "W" else Piece.BLACK
        state.last_dir = Direction[last_dir_str] if last_dir_str != "-" else Direction.X
        state.visited = process_visited_pos_str(visited_pos_str)
        state.half_moves = int(half_moves_str)
        return state

    def get_board_str(self) -> str:
        """     
        ●─●─●─●─●─●─●─●─●
        │╲│╱│╲│╱│╲│╱│╲│╱│
        ●─●─●─●─●─●─●─●─●
        │╱│╲│╱│╲│╱│╲│╱│╲│
        ●─○─●─○─┼─●─○─●─○  
        │╲│╱│╲│╱│╲│╱│╲│╱│
        ○─○─○─○─○─○─○─○─○
        │╱│╲│╱│╲│╱│╲│╱│╲│
        ○─○─○─○─○─○─○─○─○
        """
        board_string = ""
        count = 0
        for row in self.board_state:
            for col in row:
                col_str = str(Piece(col))
                if col == Piece.EMPTY:
                    count += 1
                else:
                    if count > 0:
                        board_string += str(count)
                        count = 0
                    board_string += col_str
            if count > 0:
                board_string += str(count)
                count = 0
            board_string += "/"
        board_string = board_string.rstrip("/")
        if count > 0:
            board_string += str(count)

        turn_to_play_str = str(Piece(self.turn_to_play))
        last_dir_str = str(Direction(self.last_dir))

        visited_pos_list = []
        for row_idx, row in enumerate(self.visited):
            for col_idx, col in enumerate(row):
                if col:
                    visited_pos_list.append(Position((row_idx, col_idx)).to_human())
        visited_pos_str = ",".join(visited_pos_list)
        if not visited_pos_list:
            visited_pos_str = "-"

        return " ".join(
            [
                board_string,
                turn_to_play_str,
                last_dir_str,
                visited_pos_str,
                str(self.half_moves),
            ]
        )
