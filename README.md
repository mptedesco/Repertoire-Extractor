# Repertoire-Extractor
Python script to extract repertoire files from a player's game database.  Adds play percentages that can be read by the platform Noctie.ai so if you upload the resulting repertoire to Noctie and play against it, it will make different moves at roughtly the same frequency as the player.  Then when it exits the repertoire it plays on its own.

# Opening Repertoire Extractor - User Instructions

## Overview

The Opening Repertoire Extractor is a Python program that analyzes PGN files containing multiple chess games and creates a comprehensive opening repertoire for a specific player. The program automatically detects the most frequent player in the database and extracts their opening choices with detailed statistics and play percentages.

## What This Program Does

- **Analyzes multiple games** from a PGN file to understand a player's opening choices
- **Auto-detects the main player** by finding the most frequent name in the database
- **Creates a single repertoire game** with all opening variations merged into one tree structure
- **Adds play percentages** showing how often each move was chosen from each position
- **Provides detailed statistics** including win/draw/loss records for each opening line
- **Generates professional PGN output** that can be opened in any chess software

## Installation Requirements

### Prerequisites
- Python 3.6 or higher installed on your system
- Basic familiarity with command-line operations

### Required Python Package
```bash
pip install python-chess
```

If you don't have pip installed, you can also install using:
```bash
python -m pip install python-chess
```

## Program Files
- `opening_repertoire.py` - The main program file
- Your PGN file containing multiple games (input)
- Output PGN file that will be created (repertoire)

## Command-Line Usage

### Basic Syntax
```bash
python opening_repertoire.py <input_pgn> <output_pgn> --color <white|black> [options]
```

### Required Arguments
- `input_pgn` - Path to your PGN file containing multiple games
- `output_pgn` - Path where the repertoire PGN will be saved
- `--color` - Specify either "white" or "black" for the repertoire color

### Optional Arguments
- `--depth <number>` - Number of moves to analyze (default: 10)
- `--player <name>` - Specific player name (if not provided, auto-detects most frequent)

## Usage Examples

### Example 1: Basic Usage (Auto-detect Player)
```bash
python opening_repertoire.py mygames.pgn white_repertoire.pgn --color white --depth 10
```
This will:
- Analyze `mygames.pgn`
- Find the most frequent player automatically
- Create a white opening repertoire
- Analyze up to 10 moves deep
- Save the result to `white_repertoire.pgn`

### Example 2: Specific Player
```bash
python opening_repertoire.py database.pgn carlsen_black.pgn --color black --depth 15 --player "Carlsen, Magnus"
```
This will:
- Analyze games where Magnus Carlsen played black
- Create a repertoire up to 15 moves deep
- Save to `carlsen_black.pgn`

### Example 3: Deep Analysis
```bash
python opening_repertoire.py lichess_games.pgn my_repertoire.pgn --color white --depth 20
```
This creates a very detailed repertoire analyzing up to 20 moves.

## Understanding the Output

### Output Format
The program creates a single PGN game with the following features:

#### Headers
- **Event**: "Opening Repertoire - White" or "Opening Repertoire - Black"
- **White/Black**: Shows the analyzed player vs "Opponent"
- **Description**: Summary of total games and depth analyzed

#### Move Annotations
Each move includes multiple pieces of information:

```
1. e4 {[%op 1.0]} e5 {[%op 0.3] 15 games: 10W-3D-2L (83.3% score)}
    (1... c5 {[%op 0.7] 35 games: 20W-8D-7L (74.1% score)})
```

**Play Percentage**: `{[%op X]}`
- Shows how often this move was played from the parent position
- X ranges from 0.0 (never played) to 1.0 (always played)
- Example: `{[%op 0.7]}` means this move was played in 70% of games reaching this position

**Statistics**: `X games: YW-ZD-AL (B% score)`
- X = Total number of games that reached this position and ended here
- Y = Wins, Z = Draws, A = Losses from the player's perspective
- B% = Win percentage in decisive games (excluding draws)

### Reading the Tree Structure

**Main Lines**: Most frequently played moves appear as the main continuation
**Variations**: Alternative moves appear in parentheses as variations
**Depth**: The tree shows how moves connect and branch at each decision point

### Example Interpretation
```
1. e4 {[%op 0.8]} e5 {[%op 0.4]} 2. Nf3 {[%op 1.0]} Nc6 {[%op 0.6] 12 games: 8W-2D-2L}
    (2... d6 {[%op 0.4] 5 games: 3W-1D-1L})
    (1... c5 {[%op 0.6] 25 games: 15W-5D-5L})
```

This shows:
- Player chose 1.e4 in 80% of white games
- Against 1.e4, opponents played 1...e5 40% of the time, 1...c5 60% of the time
- After 1.e4 e5 2.Nf3, opponents chose 2...Nc6 60% of the time, 2...d6 40% of the time
- The player had good results with the 2...Nc6 line (8 wins out of 10 decisive games)

## Using the Output

### Compatible Software
The output PGN can be opened in anything that reads a PGN file - in particular, it can be loaded into Noctie.ai as a repertoire and Noctie will play moves based on the frequency of play.
Can be loaded into any PGN reader or program.

## Technical Notes

### Performance
- Processing time scales with: number of games × average game length × depth
- Memory usage is generally modest unless analyzing very large databases
- Output file size depends on the complexity of the opening tree

### Accuracy
- Statistics are calculated from actual game results in your database
- Play percentages reflect historical choices, not theoretical optimality
- The program maintains precision to one decimal place for readability

### Limitations
- Does not analyze position quality or theoretical soundness
- Cannot detect transpositions between different move orders
- Statistics reflect your specific game database, not universal chess knowledge

The program provides detailed console feedback during processing, which can help identify specific issues with your PGN file or command syntax.
