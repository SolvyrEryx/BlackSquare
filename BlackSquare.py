import chess
import chess.pgn
import hashlib
import random
import argparse
import io

# ======================================================
# CONFIG
# ======================================================
ENCODING_PIECES = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK]
BITS_PER_MOVE = 3          # 2 bits piece + 1 bit square color
LENGTH_BITS = 16
MAX_MOVES_PER_GAME = 80    # optional – prevents overly long games

# ======================================================
# UTILITIES
# ======================================================
def text_to_bits(text: str) -> str:
    return ''.join(f'{b:08b}' for b in text.encode('utf-8'))

def bits_to_text(bits: str) -> str:
    bits = bits.ljust((len(bits) + 7) // 8 * 8, '0')
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8)).decode('utf-8', errors='replace')

def square_color_bit(square: int) -> int:
    return (chess.square_file(square) + chess.square_rank(square)) % 2

# ======================================================
# KEY HANDLING
# ======================================================
def key_to_seed(key: str) -> int:
    return int.from_bytes(hashlib.sha256(key.encode()).digest(), 'big')

def generate_piece_mapping(key: str):
    rng = random.Random(key_to_seed(key))
    pieces = ENCODING_PIECES[:]
    rng.shuffle(pieces)
    return {
        '00': pieces[0],
        '01': pieces[1],
        '10': pieces[2],
        '11': pieces[3],
    }

# ======================================================
# DETERMINISTIC MOVE SELECTION
# ======================================================
def deterministic_index(moves, key_seed, move_no, board, tag):
    seed = f"{key_seed}:{move_no}:{board.fen()}:{tag}"
    h = int.from_bytes(hashlib.sha256(seed.encode()).digest(), 'big')
    return random.Random(h).randrange(len(moves))

def legal_moves_by_piece(board, piece_type):
    return [
        m for m in board.legal_moves
        if board.piece_at(m.from_square)
        and board.piece_at(m.from_square).piece_type == piece_type
    ]

def legal_moves_by_piece_and_color(board, piece_type, wanted_color):
    return [
        m for m in legal_moves_by_piece(board, piece_type)
        if square_color_bit(m.to_square) == wanted_color
    ]

# ======================================================
# ENCODE – MULTI‑GAME, NEVER CRASH
# ======================================================
def encode_message_to_pgn(message: str, key: str) -> str:
    # Prepare bitstream
    bitstream = text_to_bits(message)
    bitstream = f"{len(bitstream):016b}" + bitstream
    while len(bitstream) % BITS_PER_MOVE != 0:
        bitstream += '0'

    piece_map = generate_piece_mapping(key)
    reverse_map = {v: k for k, v in piece_map.items()}
    key_seed = key_to_seed(key)

    all_games_output = []
    bit_idx = 0
    total_bits = len(bitstream)

    while bit_idx < total_bits:
        # Start a new game
        board = chess.Board()
        game = chess.pgn.Game()
        node = game
        move_no = 0

        while bit_idx < total_bits and move_no < MAX_MOVES_PER_GAME:
            # --- TRY DATA MOVE FIRST ---
            piece_bits = bitstream[bit_idx:bit_idx+2]
            color_bit = bitstream[bit_idx+2]
            target_piece = piece_map[piece_bits]
            wanted_color = int(color_bit)

            candidates = legal_moves_by_piece_and_color(board, target_piece, wanted_color)
            if candidates:
                # Data move exists – play it deterministically
                candidates = sorted(candidates, key=lambda m: m.uci())
                idx = deterministic_index(candidates, key_seed, move_no, board, "data")
                move = candidates[idx]
                board.push(move)
                node = node.add_variation(move)
                bit_idx += BITS_PER_MOVE
                move_no += 1
                continue

            # --- NO DATA MOVE – FIND A SAFE NOISE MOVE ---
            # Safe noise move = any move that the decoder will ignore.
            # It is safe if:
            #   a) it moves a non‑encoding piece (king, queen), OR
            #   b) it moves an encoding piece but is NOT the deterministic data move for that piece+color.

            all_legal = list(board.legal_moves)
            safe_moves = []

            for mv in all_legal:
                pc = board.piece_at(mv.from_square)
                # Non‑encoding piece → always safe
                if pc.piece_type not in reverse_map:
                    safe_moves.append(mv)
                    continue

                # Encoding piece – check if it would be misinterpreted
                ptype = pc.piece_type
                col = square_color_bit(mv.to_square)
                data_candidates = legal_moves_by_piece_and_color(board, ptype, col)
                if not data_candidates:
                    safe_moves.append(mv)   # no data move exists for this bits → safe
                    continue
                data_candidates = sorted(data_candidates, key=lambda m: m.uci())
                idx_data = deterministic_index(data_candidates, key_seed, move_no, board, "data")
                if mv != data_candidates[idx_data]:
                    safe_moves.append(mv)   # not the deterministic data move → safe

            if safe_moves:
                # Pick a safe noise move deterministically
                safe_moves = sorted(safe_moves, key=lambda m: m.uci())
                idx = deterministic_index(safe_moves, key_seed, move_no, board, "noise")
                move = safe_moves[idx]
                board.push(move)
                node = node.add_variation(move)
                move_no += 1
                # bit_idx does NOT advance
                continue

            # --- NO SAFE NOISE MOVE – END THIS GAME ---
            # We are stuck. Stop the current game and start a fresh one.
            break

        # End of current game
        game.headers["Result"] = "*"   # unfinished game
        all_games_output.append(str(game))

    return "\n\n".join(all_games_output)   # blank line between games

# ======================================================
# DECODE – MULTI‑GAME, AUTO‑ENCODING
# ======================================================
def read_pgn_file(filename: str) -> str:
    """Read a PGN file, auto‑detect common text encodings."""
    with open(filename, 'rb') as f:
        raw = f.read()
    for enc in ('utf-8-sig', 'utf-8', 'utf-16', 'latin1'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"Could not decode {filename} with any supported encoding.")

def decode_pgn_to_message(pgn_text: str, key: str) -> str:
    piece_map = generate_piece_mapping(key)
    reverse_map = {v: k for k, v in piece_map.items()}
    key_seed = key_to_seed(key)

    all_bits = []
    game = None
    pgn_stream = io.StringIO(pgn_text)

    while True:
        game = chess.pgn.read_game(pgn_stream)
        if game is None:
            break

        board = game.board()
        move_no = 0
        bits_this_game = []

        for move in game.mainline_moves():
            piece = board.piece_at(move.from_square)

            # Only encoding pieces can carry data
            if piece and piece.piece_type in reverse_map:
                candidate_bits = reverse_map[piece.piece_type] + str(square_color_bit(move.to_square))
                # Verify that this move is the deterministic data move for its bits
                target_piece = piece.piece_type
                wanted_color = square_color_bit(move.to_square)
                candidates = legal_moves_by_piece_and_color(board, target_piece, wanted_color)
                if candidates:
                    candidates = sorted(candidates, key=lambda m: m.uci())
                    idx = deterministic_index(candidates, key_seed, move_no, board, "data")
                    if candidates[idx] == move:
                        bits_this_game.append(candidate_bits)

            board.push(move)
            move_no += 1

        all_bits.extend(bits_this_game)

    bitstring = ''.join(all_bits)
    if len(bitstring) < LENGTH_BITS:
        return ""

    msg_len = int(bitstring[:LENGTH_BITS], 2)
    msg_bits = bitstring[LENGTH_BITS:LENGTH_BITS + msg_len]
    return bits_to_text(msg_bits)

# ======================================================
# CLI
# ======================================================
def main():
    parser = argparse.ArgumentParser(description="Hide messages inside chess games")
    sub = parser.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("encode")
    e.add_argument("message")
    e.add_argument("key")

    d = sub.add_parser("decode")
    d.add_argument("pgn_file")
    d.add_argument("key")

    args = parser.parse_args()

    if args.cmd == "encode":
        print(encode_message_to_pgn(args.message, args.key))
    else:
        pgn_text = read_pgn_file(args.pgn_file)
        print(decode_pgn_to_message(pgn_text, args.key))

if __name__ == "__main__":
    main()