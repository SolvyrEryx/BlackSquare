# BlackSquare

> _High-Fidelity Steganographic Transport Layer via Chess PGNs_

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.8%2B-yellow.svg) ![Architecture](https://img.shields.io/badge/architecture-deterministic-purple.svg) ![Web](https://img.shields.io/badge/web-react-cyan.svg)

## 🌐 Web Interface

Access the signal visualization and conceptual overview:
**[View Deployment](https://solvyreryx.github.io/BlackSquare/)**

## 📜 Overview

**BlackSquare** implements a deterministic steganographic communication protocol that embeds encrypted binary data into fully legal chess games (PGN format). The system encodes information at the move-selection layer, using a key-derived, reproducible mapping between bit patterns and constrained classes of legal chess moves.

Unlike fragiles LSB techniques, BlackSquare treats the chess game as a state machine where every move is calculated to either carry payload or maintain protocol stability, all while maintaining perfect legality and PGN invariance.

## 🧠 Technical Architecture

### Deterministic Encoding Protocol

Each encoding move carries **3 bits of payload**, split across:

1.  **Piece-Type Selection:** (2 bits) Mapping to Pawn, Knight, Bishop, or Rook.
2.  **Destination Parity:** (1 bit) Mapping to Target Square Color.

Move choice is resolved via a cryptographically seeded **deterministic index** derived from the key, move number, and board state (FEN). This ensures encoder–decoder synchronization without runtime randomness.

### Noise-Resistant Move Selection

The design explicitly separates **Data Moves** from **Noise Moves**, enforcing decoder-side verification:

- A move is interpreted as **Data** _only if_ it matches the unique deterministic encoding move for its bit pattern.
- This eliminates desynchronization, false positives, and decoding corruption.

### Multi-Game Scalability & Deadlock Prevention

To guarantee forward progress and scalability, the encoder operates over a **multi-game architecture** with bounded game lengths. This allows arbitrarily long messages while preventing deadlocks where no legal encoding move exists.

### Cryptographic Robustness

When combined with pre-encryption of the payload, the system remains computationally resistant to message recovery even under full algorithm disclosure, aligning with **Kerckhoffs’ principle**. The result is a robust, key-dependent steganographic channel using chess as a covert, verifiable transport layer.

## 📦 Installation

Ensure you have Python installed.

```bash
pip install -r requirements.txt
```

## 💻 Usage

### 1. Encode Data

Embed a message into a generated PGN file. output is directed to stdout.

```bash
python BlackSquare.py encode "Secret Payload" "my_secure_key" > output.pgn
```

### 2. Decode Data

Extract the payload from a PGN file (local or remote).

```bash
python BlackSquare.py decode output.pgn "my_secure_key"
```

### 🔓 Binary Execution (No Python Required)

For environments without a Python runtime, use the standalone executable:

```cmd
BlackSquare.exe encode "Secret Payload" "my_secure_key" > output.pgn
BlackSquare.exe decode output.pgn "my_secure_key"
```

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.


