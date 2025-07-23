#!/usr/bin/env python3
"""
Opening Repertoire Extractor

This program reads a PGN file containing multiple games, automatically detects
the most frequent player, and extracts their opening repertoire for a specified
color up to a given depth. All variations are merged into a single PGN game
with branching variations, play percentage annotations {[%op X]}, and statistical data.

Requirements:
    pip install python-chess

Usage:
    python opening_repertoire.py input.pgn output.pgn --color white --depth 10
"""

import argparse
import chess.pgn
import io
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional


class OpeningRepertoireExtractor:
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.games = []
        self.player_counts = Counter()
        
    def load_games(self) -> None:
        """Load all games from the PGN file and count player occurrences."""
        print(f"Loading games from {self.input_file}...")
        
        with open(self.input_file, 'r', encoding='utf-8') as pgn_file:
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break
                    
                self.games.append(game)
                
                # Count player names
                white_player = game.headers.get("White", "")
                black_player = game.headers.get("Black", "")
                
                if white_player:
                    self.player_counts[white_player] += 1
                if black_player:
                    self.player_counts[black_player] += 1
        
        print(f"Loaded {len(self.games)} games")
        
    def get_most_frequent_player(self) -> str:
        """Return the most frequent player name."""
        if not self.player_counts:
            raise ValueError("No players found in PGN file")
            
        most_frequent = self.player_counts.most_common(1)[0]
        player_name, count = most_frequent
        
        print(f"Most frequent player: {player_name} ({count} games)")
        return player_name
    
    def filter_games_by_player_and_color(self, player_name: str, color: str) -> List[chess.pgn.Game]:
        """Filter games where the specified player played the given color."""
        filtered_games = []
        color_field = "White" if color.lower() == "white" else "Black"
        
        for game in self.games:
            if game.headers.get(color_field, "") == player_name:
                filtered_games.append(game)
        
        print(f"Found {len(filtered_games)} games where {player_name} played as {color}")
        return filtered_games
    
    def extract_opening_moves(self, games: List[chess.pgn.Game], depth: int) -> Dict[str, List[chess.pgn.Game]]:
        """Extract opening sequences up to specified depth and group identical openings."""
        openings = defaultdict(list)
        
        for game in games:
            moves = []
            node = game
            
            # Extract moves up to the specified depth
            for move_num in range(depth):
                if node.variations:
                    node = node.variations[0]
                    moves.append(node.move)
                else:
                    break
            
            # Create a key from the move sequence
            if moves:
                # Convert moves to SAN notation for readability
                board = chess.Board()
                san_moves = []
                for move in moves:
                    san_moves.append(board.san(move))
                    board.push(move)
                
                opening_key = " ".join(san_moves)
                openings[opening_key].append(game)
        
        return openings
    
    def create_repertoire_pgn(self, openings: Dict[str, List[chess.pgn.Game]], 
                            player_name: str, color: str, depth: int) -> str:
        """Create a PGN string containing the opening repertoire as a single game with variations.
        Each move includes play percentage annotations in the format {[%op X]} where X is 0.0-1.0."""
        print(f"Found {len(openings)} unique opening lines")
        
        # Create a single game to hold all variations
        repertoire_game = chess.pgn.Game()
        
        # Set up headers
        repertoire_game.headers["Event"] = f"Opening Repertoire - {color.title()}"
        repertoire_game.headers["Site"] = "Generated"
        repertoire_game.headers["Date"] = "????.??.??"
        repertoire_game.headers["Round"] = "?"
        repertoire_game.headers["White"] = player_name if color.lower() == "white" else "Opponent"
        repertoire_game.headers["Black"] = "Opponent" if color.lower() == "white" else player_name
        repertoire_game.headers["Result"] = "*"
        repertoire_game.headers["Annotator"] = "Opening Repertoire Extractor"
        
        total_games = sum(len(games) for games in openings.values())
        repertoire_game.headers["Description"] = f"Repertoire based on {total_games} games, depth {depth} moves"
        
        # Build variation tree
        self.build_variation_tree(repertoire_game, openings, player_name, color)
        
        # Convert to PGN string
        pgn_output = io.StringIO()
        print(repertoire_game, file=pgn_output)
        
        return pgn_output.getvalue()
    
    def build_variation_tree(self, game: chess.pgn.Game, openings: Dict[str, List[chess.pgn.Game]], 
                           player_name: str, color: str) -> None:
        """Build a tree of variations from all opening lines."""
        # Create a tree structure to organize moves
        move_tree = {}
        
        # Parse all opening lines and build the tree
        for opening_moves, games in openings.items():
            moves = opening_moves.split()
            current_level = move_tree
            
            # Navigate/create the tree path
            for i, san_move in enumerate(moves):
                if san_move not in current_level:
                    current_level[san_move] = {
                        'children': {},
                        'games_through': [],  # Games that went through this move
                        'games_ending': [],   # Games that ended at this move
                        'move_number': i + 1
                    }
                
                # Add games that went through this position
                current_level[san_move]['games_through'].extend(games)
                
                # Add games to this node if this is the end of the line
                if i == len(moves) - 1:
                    current_level[san_move]['games_ending'].extend(games)
                
                current_level = current_level[san_move]['children']
        
        # Convert tree to PGN variations
        total_games = sum(len(games) for games in openings.values())
        self.add_variations_to_node(game, move_tree, chess.Board(), player_name, color, total_games)
    
    def add_variations_to_node(self, node: chess.pgn.GameNode, move_tree: dict, 
                             board: chess.Board, player_name: str, color: str, 
                             parent_game_count: int) -> None:
        """Recursively add variations to a PGN node."""
        # Sort moves by frequency (number of games that went through this move)
        sorted_moves = sorted(move_tree.items(), 
                            key=lambda x: len(x[1]['games_through']), 
                            reverse=True)
        
        first_move = True
        for san_move, move_data in sorted_moves:
            try:
                # Parse the move
                move = board.parse_san(san_move)
                
                # Calculate play percentage
                games_through_this_move = len(move_data['games_through'])
                play_percentage = games_through_this_move / parent_game_count if parent_game_count > 0 else 0
                
                # Add as main line or variation
                if first_move:
                    variation_node = node.add_main_variation(move)
                    first_move = False
                else:
                    variation_node = node.add_variation(move)
                
                # Build comment with play percentage and statistics
                comment_parts = [f"[%op {play_percentage:.1f}]"]
                
                # Add statistics if there are games ending at this position
                if move_data['games_ending']:
                    games = move_data['games_ending']
                    win_count = sum(1 for g in games if self.get_result_for_player(g, player_name, color) == "1")
                    draw_count = sum(1 for g in games if self.get_result_for_player(g, player_name, color) == "1/2")
                    loss_count = sum(1 for g in games if self.get_result_for_player(g, player_name, color) == "0")
                    
                    stats_comment = f"{len(games)} games: {win_count}W-{draw_count}D-{loss_count}L"
                    
                    # Calculate win percentage
                    total_decisive = win_count + loss_count
                    if total_decisive > 0:
                        win_pct = (win_count / total_decisive) * 100
                        stats_comment += f" ({win_pct:.1f}% score)"
                    
                    comment_parts.append(stats_comment)
                
                # Set the comment
                variation_node.comment = " ".join(comment_parts)
                
                # Make the move on a copy of the board for the recursive call
                board_copy = board.copy()
                board_copy.push(move)
                
                # Recursively add child variations
                if move_data['children']:
                    self.add_variations_to_node(variation_node, move_data['children'], 
                                              board_copy, player_name, color, games_through_this_move)
                
            except Exception as e:
                print(f"Warning: Could not parse move '{san_move}': {e}")
                continue

    
    def get_result_for_player(self, game: chess.pgn.Game, player_name: str, color: str) -> str:
        """Get the result from the perspective of the specified player."""
        result = game.headers.get("Result", "*")
        
        if result == "*" or result == "1/2-1/2":
            return "1/2" if result == "1/2-1/2" else "*"
        
        # Determine if player won, lost, or drew
        player_is_white = game.headers.get("White", "") == player_name
        
        if color.lower() == "white" and player_is_white:
            return "1" if result == "1-0" else "0"
        elif color.lower() == "black" and not player_is_white:
            return "1" if result == "0-1" else "0"
        else:
            # Player is not the expected color in this game
            return "*"
    
    def extract_repertoire(self, color: str, depth: int, output_file: str, 
                          player_name: Optional[str] = None) -> None:
        """Main method to extract and save the opening repertoire."""
        # Load games and detect player if not specified
        self.load_games()
        
        if player_name is None:
            player_name = self.get_most_frequent_player()
        
        # Filter games by player and color
        filtered_games = self.filter_games_by_player_and_color(player_name, color)
        
        if not filtered_games:
            print(f"No games found for {player_name} playing as {color}")
            return
        
        # Extract opening moves
        openings = self.extract_opening_moves(filtered_games, depth)
        
        if not openings:
            print("No opening moves extracted")
            return
        
        # Create repertoire PGN
        repertoire_pgn = self.create_repertoire_pgn(openings, player_name, color, depth)
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(repertoire_pgn)
        
        print(f"Opening repertoire (single game with variations) saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract opening repertoire from PGN file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python opening_repertoire.py games.pgn repertoire.pgn --color white --depth 10
  python opening_repertoire.py games.pgn repertoire.pgn --color black --depth 15 --player "Carlsen, Magnus"

Output format includes play percentages: 1. e4 {[%op 1.0]} e5 {[%op 0.3]} (1... c5 {[%op 0.7]}) *
        """
    )
    
    parser.add_argument("input_pgn", help="Input PGN file containing multiple games")
    parser.add_argument("output_pgn", help="Output PGN file for the repertoire")
    parser.add_argument("--color", choices=["white", "black"], required=True,
                       help="Color for which to extract repertoire")
    parser.add_argument("--depth", type=int, default=10,
                       help="Number of moves to include in repertoire (default: 10)")
    parser.add_argument("--player", help="Specific player name (if not provided, most frequent player is used)")
    
    args = parser.parse_args()
    
    try:
        extractor = OpeningRepertoireExtractor(args.input_pgn)
        extractor.extract_repertoire(
            color=args.color,
            depth=args.depth,
            output_file=args.output_pgn,
            player_name=args.player
        )
    except FileNotFoundError:
        print(f"Error: Input file '{args.input_pgn}' not found")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
