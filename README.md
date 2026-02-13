# BlackSquare

> _Steganography aimed at the 64 squares._

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.8%2B-yellow.svg) ![Status](https://img.shields.io/badge/status-stable-green.svg)

**BlackSquare** is a high-grade steganography tool designed to conceal arbitrary encrypted messages within valid, replayable Chess Portable Game Notation (PGN) files. Unlike simple LSB techniques, BlackSquare orchestrates entire chess games where every move is calculated to encode data bits while maintaining game legality.

## 🛠️ Tech Stack

Built with precision and robustness in mind:

- **Core Language:** Python 3
- **Chess Logic:** `python-chess` (Move generation, validation, PGN handling)
- **Cryptography:** `hashlib` (SHA-256 for deterministic RNG seeding)
- **Architecture:** Multi-game state machine with deadlock avoidance

## 🚀 Key Features

- **Deterministic Encoding:** Identical keys and messages always produce the exact same games.
- **Multi-Game Support:** Automatically spans multiple chess games if the message exceeds the capacity of a single game.
- **Deadlock Avoidance:** Implements a "Noise Move" protocol. If the engine is cornered with no encoding moves, it plays a safe, non-encoding move or gracefully resigns the game to start a fresh one.
- **Collision Resistance:** Smart filtering ensures "noise" moves are never accidentally interpreted as data by the decoder.

## 🧠 Technical Deep Dive: How It Works

BlackSquare treats a chess game as a stream of data opportunities.

### 1. The Mapping Protocol

The system maps 3 bits of data to a single chess move:

- **Piece Selection (2 bits):**
  - `00` → Pawn
  - `01` → Knight
  - `10` → Bishop
  - `11` → Rook
    _(Mapping is shuffled based on the `key` hash)_
- **Target Square Color (1 bit):**
  - `0` → Light Square
  - `1` → Dark Square

### 2. Deterministic Move Selection

Multiple moves might match the criteria (e.g., multiple Knights moving to light squares). BlackSquare uses a SHA-256 hash of the current board state and key to **deterministically** select one specific move. This ensures the decoder (running the same logic) knows exactly which move was the "data" move.

### 3. Handling Complexity

In real chess games, you can't always move a specific piece to a specific color.

- **Solution:** If the required move isn't possible, the engine hunts for a **"Safe Noise Move"**.
- This is a move that uses a non-encoding piece (King/Queen) or a move that mathematically cannot be the deterministic choice for any data pattern.
- The decoder recognizes these as noise and skips them, preserving the bitstream integrity.

## 📦 Installation

Ensure you have Python installed.

```bash
pip install -r requirements.txt
```

_(Note: Requires `python-chess`)_

## 💻 Usage

### Encode a Message

Hide a secret message into a PGN file (printed to stdout).

```bash
python BlackSquare.py encode "Launch codes: 8842" "my_secret_key" > output.pgn
```

### Decode a Message

Extract the secret from a PGN file.

```bash
python BlackSquare.py decode output.pgn "my_secret_key"
```

## 📦 Binary Usage (No Python Required)

If you have the standalone `BlackSquare.exe`, you can run it directly from the command line without installing Python or dependencies.

```cmd
BlackSquare.exe encode "Launch codes: 8842" "my_secret_key" > output.pgn
BlackSquare.exe decode output.pgn "my_secret_key"
```

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

_Generated with precision by Solvyr Eryx_
