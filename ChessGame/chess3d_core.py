#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chess3d_core.py -- rules engine, search, 3D geometry and a Pillow renderer.

Shared by the desktop pygame build and the Streamlit web app.  Contains no
pygame and no streamlit imports, so it is safe to import anywhere.

Sections 1-3 are lifted unchanged from the verified desktop build:
  1. chess rules      (passes perft on all standard test positions)
  2. evaluation/search(alpha-beta verified equal to brute-force negamax)
  3. meshes + camera
Section 4 replaces the pygame rasteriser with Pillow so it runs headless.
"""

import math
import random
import threading
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont


# =============================================================================
#  SECTION 1 -- CHESS RULES ENGINE
# =============================================================================

EMPTY = 0
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6
WHITE, BLACK = 0, 1

PIECE_LETTER = {PAWN: "P", KNIGHT: "N", BISHOP: "B",
                ROOK: "R", QUEEN: "Q", KING: "K"}
PIECE_NAME = {PAWN: "Pawn", KNIGHT: "Knight", BISHOP: "Bishop",
              ROOK: "Rook", QUEEN: "Queen", KING: "King"}

# move flags
F_NORMAL, F_DOUBLE, F_EP, F_CASTLE = 0, 1, 2, 3

# castling right bits
CR_WK, CR_WQ, CR_BK, CR_BQ = 1, 2, 4, 8


def make_piece(color, ptype):
    return (color << 3) | ptype


def pcolor(p):
    return p >> 3


def ptype(p):
    return p & 7


def sq_name(sq):
    return "abcdefgh"[sq & 7] + str((sq >> 3) + 1)


# ---- precomputed movement tables ---------------------------------------------

KNIGHT_DELTAS = [(1, 2), (2, 1), (2, -1), (1, -2),
                 (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
KING_DELTAS = [(1, 0), (1, 1), (0, 1), (-1, 1),
               (-1, 0), (-1, -1), (0, -1), (1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

KNIGHT_MOVES = [[] for _ in range(64)]
KING_MOVES = [[] for _ in range(64)]
ROOK_RAYS = [[] for _ in range(64)]      # list of 4 ray lists
BISHOP_RAYS = [[] for _ in range(64)]    # list of 4 ray lists

for _sq in range(64):
    _r, _c = _sq >> 3, _sq & 7
    for _dr, _dc in KNIGHT_DELTAS:
        _nr, _nc = _r + _dr, _c + _dc
        if 0 <= _nr < 8 and 0 <= _nc < 8:
            KNIGHT_MOVES[_sq].append(_nr * 8 + _nc)
    for _dr, _dc in KING_DELTAS:
        _nr, _nc = _r + _dr, _c + _dc
        if 0 <= _nr < 8 and 0 <= _nc < 8:
            KING_MOVES[_sq].append(_nr * 8 + _nc)
    for _dirs, _store in ((ROOK_DIRS, ROOK_RAYS), (BISHOP_DIRS, BISHOP_RAYS)):
        for _dr, _dc in _dirs:
            _ray = []
            _nr, _nc = _r + _dr, _c + _dc
            while 0 <= _nr < 8 and 0 <= _nc < 8:
                _ray.append(_nr * 8 + _nc)
                _nr += _dr
                _nc += _dc
            _store[_sq].append(_ray)

# castling rights are cleared when these squares are touched
CASTLE_MASK = [15] * 64
CASTLE_MASK[0] &= ~CR_WQ
CASTLE_MASK[7] &= ~CR_WK
CASTLE_MASK[4] &= ~(CR_WK | CR_WQ)
CASTLE_MASK[56] &= ~CR_BQ
CASTLE_MASK[63] &= ~CR_BK
CASTLE_MASK[60] &= ~(CR_BK | CR_BQ)

# ---- zobrist hashing ---------------------------------------------------------

_zrng = random.Random(0xC0FFEE)
ZOB_PIECE = [[_zrng.getrandbits(64) for _ in range(64)] for _ in range(16)]
ZOB_SIDE = _zrng.getrandbits(64)
ZOB_CASTLE = [_zrng.getrandbits(64) for _ in range(16)]
ZOB_EP = [_zrng.getrandbits(64) for _ in range(8)]

START_ORDER = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]


class Position:
    """Full chess position with make/unmake move."""

    __slots__ = ("board", "side", "castling", "ep", "halfmove", "fullmove",
                 "king_sq", "hash", "rep", "undo")

    def __init__(self):
        self.board = [EMPTY] * 64
        for c in range(8):
            self.board[8 + c] = make_piece(WHITE, PAWN)
            self.board[48 + c] = make_piece(BLACK, PAWN)
            self.board[c] = make_piece(WHITE, START_ORDER[c])
            self.board[56 + c] = make_piece(BLACK, START_ORDER[c])
        self.side = WHITE
        self.castling = 15
        self.ep = -1
        self.halfmove = 0
        self.fullmove = 1
        self.king_sq = [4, 60]
        self.hash = self.compute_hash()
        self.rep = [self.hash]
        self.undo = []

    # -- hashing --------------------------------------------------------------
    def compute_hash(self):
        h = 0
        for sq, p in enumerate(self.board):
            if p:
                h ^= ZOB_PIECE[p][sq]
        h ^= ZOB_CASTLE[self.castling]
        if self.ep >= 0:
            h ^= ZOB_EP[self.ep & 7]
        if self.side == BLACK:
            h ^= ZOB_SIDE
        return h

    def clone(self):
        p = Position.__new__(Position)
        p.board = list(self.board)
        p.side = self.side
        p.castling = self.castling
        p.ep = self.ep
        p.halfmove = self.halfmove
        p.fullmove = self.fullmove
        p.king_sq = list(self.king_sq)
        p.hash = self.hash
        p.rep = list(self.rep)
        p.undo = []
        return p

    # -- attack detection -----------------------------------------------------
    def attacked(self, sq, by):
        b = self.board
        r, c = sq >> 3, sq & 7

        # pawns
        pr = r - 1 if by == WHITE else r + 1
        if 0 <= pr < 8:
            wanted = make_piece(by, PAWN)
            if c > 0 and b[pr * 8 + c - 1] == wanted:
                return True
            if c < 7 and b[pr * 8 + c + 1] == wanted:
                return True

        wanted = make_piece(by, KNIGHT)
        for t in KNIGHT_MOVES[sq]:
            if b[t] == wanted:
                return True

        wanted = make_piece(by, KING)
        for t in KING_MOVES[sq]:
            if b[t] == wanted:
                return True

        rq = (make_piece(by, ROOK), make_piece(by, QUEEN))
        for ray in ROOK_RAYS[sq]:
            for t in ray:
                p = b[t]
                if p:
                    if p in rq:
                        return True
                    break

        bq = (make_piece(by, BISHOP), make_piece(by, QUEEN))
        for ray in BISHOP_RAYS[sq]:
            for t in ray:
                p = b[t]
                if p:
                    if p in bq:
                        return True
                    break
        return False

    def in_check(self, color=None):
        if color is None:
            color = self.side
        return self.attacked(self.king_sq[color], color ^ 1)

    # -- move generation ------------------------------------------------------
    def gen_pseudo(self, captures_only=False):
        moves = []
        add = moves.append
        b = self.board
        side = self.side
        opp = side ^ 1

        for sq in range(64):
            p = b[sq]
            if p == EMPTY or (p >> 3) != side:
                continue
            t = p & 7
            r, c = sq >> 3, sq & 7

            if t == PAWN:
                d = 1 if side == WHITE else -1
                promo_row = 7 if side == WHITE else 0
                start_row = 1 if side == WHITE else 6
                nr = r + d
                fwd = nr * 8 + c
                if b[fwd] == EMPTY:
                    if nr == promo_row:
                        for pr in (QUEEN, ROOK, BISHOP, KNIGHT):
                            add((sq, fwd, pr, F_NORMAL))
                    elif not captures_only:
                        add((sq, fwd, 0, F_NORMAL))
                        if r == start_row:
                            fwd2 = (r + 2 * d) * 8 + c
                            if b[fwd2] == EMPTY:
                                add((sq, fwd2, 0, F_DOUBLE))
                for dc in (-1, 1):
                    nc = c + dc
                    if 0 <= nc < 8:
                        to = nr * 8 + nc
                        tp = b[to]
                        if tp and (tp >> 3) == opp:
                            if nr == promo_row:
                                for pr in (QUEEN, ROOK, BISHOP, KNIGHT):
                                    add((sq, to, pr, F_NORMAL))
                            else:
                                add((sq, to, 0, F_NORMAL))
                        elif to == self.ep:
                            add((sq, to, 0, F_EP))

            elif t == KNIGHT:
                for to in KNIGHT_MOVES[sq]:
                    tp = b[to]
                    if tp == EMPTY:
                        if not captures_only:
                            add((sq, to, 0, F_NORMAL))
                    elif (tp >> 3) == opp:
                        add((sq, to, 0, F_NORMAL))

            elif t == KING:
                for to in KING_MOVES[sq]:
                    tp = b[to]
                    if tp == EMPTY:
                        if not captures_only:
                            add((sq, to, 0, F_NORMAL))
                    elif (tp >> 3) == opp:
                        add((sq, to, 0, F_NORMAL))
                if not captures_only:
                    if side == WHITE:
                        if (self.castling & CR_WK and b[5] == EMPTY
                                and b[6] == EMPTY and b[7] == make_piece(WHITE, ROOK)
                                and not self.attacked(4, BLACK)
                                and not self.attacked(5, BLACK)
                                and not self.attacked(6, BLACK)):
                            add((4, 6, 0, F_CASTLE))
                        if (self.castling & CR_WQ and b[3] == EMPTY
                                and b[2] == EMPTY and b[1] == EMPTY
                                and b[0] == make_piece(WHITE, ROOK)
                                and not self.attacked(4, BLACK)
                                and not self.attacked(3, BLACK)
                                and not self.attacked(2, BLACK)):
                            add((4, 2, 0, F_CASTLE))
                    else:
                        if (self.castling & CR_BK and b[61] == EMPTY
                                and b[62] == EMPTY and b[63] == make_piece(BLACK, ROOK)
                                and not self.attacked(60, WHITE)
                                and not self.attacked(61, WHITE)
                                and not self.attacked(62, WHITE)):
                            add((60, 62, 0, F_CASTLE))
                        if (self.castling & CR_BQ and b[59] == EMPTY
                                and b[58] == EMPTY and b[57] == EMPTY
                                and b[56] == make_piece(BLACK, ROOK)
                                and not self.attacked(60, WHITE)
                                and not self.attacked(59, WHITE)
                                and not self.attacked(58, WHITE)):
                            add((60, 58, 0, F_CASTLE))

            else:
                rays = ROOK_RAYS[sq] if t == ROOK else (
                    BISHOP_RAYS[sq] if t == BISHOP
                    else ROOK_RAYS[sq] + BISHOP_RAYS[sq])
                for ray in rays:
                    for to in ray:
                        tp = b[to]
                        if tp == EMPTY:
                            if not captures_only:
                                add((sq, to, 0, F_NORMAL))
                        else:
                            if (tp >> 3) == opp:
                                add((sq, to, 0, F_NORMAL))
                            break
        return moves

    def legal_moves(self):
        out = []
        for m in self.gen_pseudo():
            self.make(m)
            if not self.attacked(self.king_sq[self.side ^ 1], self.side):
                out.append(m)
            self.unmake(m)
        return out

    # -- make / unmake --------------------------------------------------------
    def make(self, m):
        frm, to, promo, flag = m
        b = self.board
        piece = b[frm]
        captured = b[to]
        color = piece >> 3
        h = self.hash

        self.undo.append((captured, self.castling, self.ep,
                          self.halfmove, self.hash, self.king_sq[color]))

        if self.ep >= 0:
            h ^= ZOB_EP[self.ep & 7]
        h ^= ZOB_CASTLE[self.castling]

        h ^= ZOB_PIECE[piece][frm]
        b[frm] = EMPTY

        if flag == F_EP:
            cap_sq = to - 8 if color == WHITE else to + 8
            cp = b[cap_sq]
            h ^= ZOB_PIECE[cp][cap_sq]
            b[cap_sq] = EMPTY
        elif captured:
            h ^= ZOB_PIECE[captured][to]

        if promo:
            newp = make_piece(color, promo)
        else:
            newp = piece
        b[to] = newp
        h ^= ZOB_PIECE[newp][to]

        if flag == F_CASTLE:
            if to == 6:
                rf, rt = 7, 5
            elif to == 2:
                rf, rt = 0, 3
            elif to == 62:
                rf, rt = 63, 61
            else:
                rf, rt = 56, 59
            rook = b[rf]
            b[rf] = EMPTY
            b[rt] = rook
            h ^= ZOB_PIECE[rook][rf] ^ ZOB_PIECE[rook][rt]

        if (piece & 7) == KING:
            self.king_sq[color] = to

        self.castling &= CASTLE_MASK[frm] & CASTLE_MASK[to]
        h ^= ZOB_CASTLE[self.castling]

        if flag == F_DOUBLE:
            self.ep = (frm + to) >> 1
            h ^= ZOB_EP[self.ep & 7]
        else:
            self.ep = -1

        if (piece & 7) == PAWN or captured or flag == F_EP:
            self.halfmove = 0
        else:
            self.halfmove += 1

        if color == BLACK:
            self.fullmove += 1

        self.side ^= 1
        h ^= ZOB_SIDE
        self.hash = h
        self.rep.append(h)

    def unmake(self, m):
        frm, to, promo, flag = m
        b = self.board
        captured, castling, ep, halfmove, h, ksq = self.undo.pop()
        self.rep.pop()

        self.side ^= 1
        color = self.side
        piece = b[to]
        if promo:
            piece = make_piece(color, PAWN)
        b[frm] = piece
        b[to] = EMPTY

        if flag == F_EP:
            cap_sq = to - 8 if color == WHITE else to + 8
            b[cap_sq] = make_piece(color ^ 1, PAWN)
        elif captured:
            b[to] = captured

        if flag == F_CASTLE:
            if to == 6:
                rf, rt = 7, 5
            elif to == 2:
                rf, rt = 0, 3
            elif to == 62:
                rf, rt = 63, 61
            else:
                rf, rt = 56, 59
            b[rf] = b[rt]
            b[rt] = EMPTY

        self.king_sq[color] = ksq
        self.castling = castling
        self.ep = ep
        self.halfmove = halfmove
        self.hash = h
        if color == BLACK:
            self.fullmove -= 1

    # -- game state -----------------------------------------------------------
    def insufficient_material(self):
        bishops = [[], []]
        knights = [0, 0]
        for sq, p in enumerate(self.board):
            if not p:
                continue
            t = p & 7
            if t in (PAWN, ROOK, QUEEN):
                return False
            if t == BISHOP:
                bishops[p >> 3].append(((sq >> 3) + (sq & 7)) & 1)
            elif t == KNIGHT:
                knights[p >> 3] += 1
        minors = len(bishops[0]) + len(bishops[1]) + knights[0] + knights[1]
        if minors <= 1:
            return True
        allb = bishops[0] + bishops[1]
        if knights[0] + knights[1] == 0 and len(set(allb)) <= 1:
            return True
        return False

    def repetition_count(self):
        lim = min(len(self.rep), self.halfmove + 1)
        if lim <= 1:
            return 1
        return self.rep[-lim:].count(self.hash)

    def status(self):
        """Returns (code, text).  code in: play, checkmate, stalemate, draw."""
        if not self.legal_moves():
            if self.in_check():
                win = "White" if self.side == BLACK else "Black"
                return "checkmate", "Checkmate - %s wins" % win
            return "stalemate", "Stalemate - draw"
        if self.halfmove >= 100:
            return "draw", "Draw - fifty move rule"
        if self.repetition_count() >= 3:
            return "draw", "Draw - threefold repetition"
        if self.insufficient_material():
            return "draw", "Draw - insufficient material"
        return "play", ""

    # -- algebraic notation ---------------------------------------------------
    def san(self, move):
        frm, to, promo, flag = move
        piece = self.board[frm]
        t = piece & 7
        captured = self.board[to] or flag == F_EP

        if flag == F_CASTLE:
            text = "O-O" if (to & 7) == 6 else "O-O-O"
        elif t == PAWN:
            text = ""
            if captured:
                text += "abcdefgh"[frm & 7] + "x"
            text += sq_name(to)
            if promo:
                text += "=" + PIECE_LETTER[promo]
        else:
            same_file = same_rank = ambiguous = False
            for m2 in self.legal_moves():
                if m2 == move or m2[1] != to:
                    continue
                p2 = self.board[m2[0]]
                if (p2 & 7) == t and (p2 >> 3) == (piece >> 3):
                    ambiguous = True
                    if (m2[0] & 7) == (frm & 7):
                        same_file = True
                    if (m2[0] >> 3) == (frm >> 3):
                        same_rank = True
            text = PIECE_LETTER[t]
            if ambiguous:
                if not same_file:
                    text += "abcdefgh"[frm & 7]
                elif not same_rank:
                    text += str((frm >> 3) + 1)
                else:
                    text += sq_name(frm)
            if captured:
                text += "x"
            text += sq_name(to)

        self.make(move)
        if self.in_check():
            text += "#" if not self.legal_moves() else "+"
        self.unmake(move)
        return text


def position_from_fen(fen):
    """Build a Position from a FEN string (used for tests / custom setups)."""
    parts = fen.split()
    board_part = parts[0]
    pos = Position()
    pos.board = [EMPTY] * 64
    row, col = 7, 0
    letters = {"p": PAWN, "n": KNIGHT, "b": BISHOP,
               "r": ROOK, "q": QUEEN, "k": KING}
    for ch in board_part:
        if ch == "/":
            row -= 1
            col = 0
        elif ch.isdigit():
            col += int(ch)
        else:
            color = WHITE if ch.isupper() else BLACK
            pos.board[row * 8 + col] = make_piece(color, letters[ch.lower()])
            col += 1
    pos.side = WHITE if len(parts) < 2 or parts[1] == "w" else BLACK
    rights = parts[2] if len(parts) > 2 else "KQkq"
    pos.castling = 0
    for ch, bit in (("K", CR_WK), ("Q", CR_WQ), ("k", CR_BK), ("q", CR_BQ)):
        if ch in rights:
            pos.castling |= bit
    if len(parts) > 3 and parts[3] != "-":
        pos.ep = "abcdefgh".index(parts[3][0]) + (int(parts[3][1]) - 1) * 8
    else:
        pos.ep = -1
    pos.halfmove = int(parts[4]) if len(parts) > 4 else 0
    pos.fullmove = int(parts[5]) if len(parts) > 5 else 1
    for sq, p in enumerate(pos.board):
        if p and (p & 7) == KING:
            pos.king_sq[p >> 3] = sq
    pos.hash = pos.compute_hash()
    pos.rep = [pos.hash]
    pos.undo = []
    return pos


# =============================================================================
#  SECTION 2 -- EVALUATION AND SEARCH (the computer opponent)
# =============================================================================

PIECE_VALUE = [0, 100, 320, 330, 500, 900, 0]
MATE = 30000

# Piece-square tables, written from Black's view (a8 first) for readability.
_PST_RAW = {
    PAWN: [
          0,  0,  0,  0,  0,  0,  0,  0,
         50, 50, 50, 50, 50, 50, 50, 50,
         10, 10, 20, 30, 30, 20, 10, 10,
          5,  5, 10, 25, 25, 10,  5,  5,
          0,  0,  0, 20, 20,  0,  0,  0,
          5, -5,-10,  0,  0,-10, -5,  5,
          5, 10, 10,-20,-20, 10, 10,  5,
          0,  0,  0,  0,  0,  0,  0,  0],
    KNIGHT: [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50],
    BISHOP: [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20],
    ROOK: [
          0,  0,  0,  0,  0,  0,  0,  0,
          5, 10, 10, 10, 10, 10, 10,  5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
          0,  0,  0,  5,  5,  0,  0,  0],
    QUEEN: [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
         -5,  0,  5,  5,  5,  5,  0, -5,
          0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20],
    KING: [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
         20, 20,  0,  0,  0,  0, 20, 20,
         20, 30, 10,  0,  0, 10, 30, 20],
}
_KING_END_RAW = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50]


def _flip_table(raw):
    """Convert an a8-first table into board indexing for white and black."""
    white = [0] * 64
    black = [0] * 64
    for i, v in enumerate(raw):
        r, c = i >> 3, i & 7
        white[(7 - r) * 8 + c] = v
        black[r * 8 + c] = v
    return white, black


PST = {}
for _t, _raw in _PST_RAW.items():
    PST[_t] = _flip_table(_raw)
KING_END = _flip_table(_KING_END_RAW)

FILE_MASKS = [[r * 8 + c for r in range(8)] for c in range(8)]


def evaluate(pos):
    """Static score in centipawns, from the side-to-move's point of view."""
    b = pos.board
    score = 0
    npm = [0, 0]           # non-pawn material
    bishops = [0, 0]
    pawn_files = [[0] * 8, [0] * 8]

    for sq in range(64):
        p = b[sq]
        if not p:
            continue
        c = p >> 3
        t = p & 7
        if t != KING:
            v = PIECE_VALUE[t]
            score += v if c == WHITE else -v
            if t != PAWN:
                npm[c] += v
            else:
                pawn_files[c][sq & 7] += 1
            if t == BISHOP:
                bishops[c] += 1
        if t != KING:
            pv = PST[t][c][sq]
            score += pv if c == WHITE else -pv

    endgame = (npm[WHITE] + npm[BLACK]) < 1800
    for c in (WHITE, BLACK):
        ks = pos.king_sq[c]
        kv = KING_END[c][ks] if endgame else PST[KING][c][ks]
        score += kv if c == WHITE else -kv
        if bishops[c] >= 2:
            score += 30 if c == WHITE else -30
        for f in range(8):
            n = pawn_files[c][f]
            if n > 1:
                score += (-12 * (n - 1)) if c == WHITE else (12 * (n - 1))

    return score if pos.side == WHITE else -score


class TimeUp(Exception):
    pass


class Engine:
    """Alpha-beta searcher with TT, killers, history and quiescence."""

    def __init__(self):
        self.tt = {}
        self.killers = [[None, None] for _ in range(64)]
        self.history = {}
        self.nodes = 0
        self.deadline = 0.0
        self.abort = False
        self.extensions = True

    # -- move ordering --------------------------------------------------------
    def order(self, pos, moves, ply, tt_move):
        b = pos.board
        k1, k2 = self.killers[ply] if ply < 64 else (None, None)
        scored = []
        for m in moves:
            frm, to, promo, flag = m
            if m == tt_move:
                s = 1 << 24
            else:
                victim = b[to]
                if victim or flag == F_EP:
                    vt = (victim & 7) if victim else PAWN
                    s = 1 << 20
                    s += PIECE_VALUE[vt] * 16 - PIECE_VALUE[b[frm] & 7]
                elif m == k1:
                    s = 1 << 19
                elif m == k2:
                    s = (1 << 19) - 1
                else:
                    s = self.history.get((b[frm], to), 0)
                if promo:
                    s += PIECE_VALUE[promo] * 8
            scored.append((-s, m))
        scored.sort(key=lambda x: x[0])
        return [m for _, m in scored]

    def check_time(self):
        self.nodes += 1
        if (self.nodes & 1023) == 0:
            if self.abort or time.time() > self.deadline:
                raise TimeUp()

    # -- quiescence -----------------------------------------------------------
    def quiesce(self, pos, alpha, beta, depth=0):
        self.check_time()
        stand = evaluate(pos)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand
        if depth > 6:
            return alpha

        caps = pos.gen_pseudo(captures_only=True)
        caps = self.order(pos, caps, 0, None)
        for m in caps:
            pos.make(m)
            if pos.attacked(pos.king_sq[pos.side ^ 1], pos.side):
                pos.unmake(m)
                continue
            score = -self.quiesce(pos, -beta, -alpha, depth + 1)
            pos.unmake(m)
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    # -- main search ----------------------------------------------------------
    def negamax(self, pos, depth, alpha, beta, ply, use_q):
        self.check_time()

        if ply > 0 and pos.halfmove >= 8:
            if pos.halfmove >= 100 or pos.repetition_count() >= 2:
                return 0

        alpha_orig = alpha
        key = pos.hash
        tt_move = None
        entry = self.tt.get(key)
        if entry is not None:
            e_depth, e_score, e_flag, e_move = entry
            tt_move = e_move
            if e_depth >= depth and ply > 0:
                if e_flag == 0:
                    return e_score
                if e_flag == 1 and e_score > alpha:
                    alpha = e_score
                elif e_flag == 2 and e_score < beta:
                    beta = e_score
                if alpha >= beta:
                    return e_score

        in_check = pos.in_check()
        if in_check and self.extensions:
            depth += 1                       # check extension

        if depth <= 0:
            return self.quiesce(pos, alpha, beta) if use_q else evaluate(pos)

        moves = self.order(pos, pos.gen_pseudo(), ply, tt_move)
        best = -MATE * 2
        best_move = None
        legal = 0

        for m in moves:
            pos.make(m)
            if pos.attacked(pos.king_sq[pos.side ^ 1], pos.side):
                pos.unmake(m)
                continue
            legal += 1
            score = -self.negamax(pos, depth - 1, -beta, -alpha, ply + 1, use_q)
            pos.unmake(m)

            if score > best:
                best = score
                best_move = m
            if score > alpha:
                alpha = score
            if alpha >= beta:
                if not pos.board[m[1]] and m[3] != F_EP and ply < 64:
                    kl = self.killers[ply]
                    if kl[0] != m:
                        kl[1] = kl[0]
                        kl[0] = m
                    pk = (pos.board[m[0]], m[1])
                    self.history[pk] = self.history.get(pk, 0) + depth * depth
                break

        if legal == 0:
            return -MATE + ply if in_check else 0

        flag = 0
        if best <= alpha_orig:
            flag = 2
        elif best >= beta:
            flag = 1
        if entry is None or entry[0] <= depth:
            self.tt[key] = (depth, best, flag, best_move)
        return best

    # -- top level ------------------------------------------------------------
    def search(self, pos, max_depth, time_limit, use_q=True):
        """Iterative deepening.  Returns (best_move, score, depth_reached)."""
        self.deadline = time.time() + time_limit
        self.nodes = 0
        self.killers = [[None, None] for _ in range(64)]
        self.history = {}
        if len(self.tt) > 400000:
            self.tt.clear()

        root = pos.legal_moves()
        if not root:
            return None, 0, 0
        best_move = root[0]
        best_score = 0
        reached = 0

        for depth in range(1, max_depth + 1):
            alpha, beta = -MATE * 2, MATE * 2
            cur_best, cur_score = None, -MATE * 2
            try:
                entry = self.tt.get(pos.hash)
                tt_move = entry[3] if entry else best_move
                for m in self.order(pos, root, 0, tt_move):
                    pos.make(m)
                    score = -self.negamax(pos, depth - 1, -beta, -alpha, 1, use_q)
                    pos.unmake(m)
                    if score > cur_score:
                        cur_score = score
                        cur_best = m
                    if score > alpha:
                        alpha = score
            except TimeUp:
                break
            if cur_best is not None:
                best_move, best_score, reached = cur_best, cur_score, depth
                self.tt[pos.hash] = (depth, best_score, 0, best_move)
            if abs(best_score) > MATE - 100:
                break
            if time.time() > self.deadline:
                break
        return best_move, best_score, reached


DIFFICULTY = {
    "Easy":   dict(depth=2, time=0.8, noise=70, blunder=0.32, quiesce=False,
                   blurb="Plays fast and loose - great for learning"),
    "Medium": dict(depth=5, time=2.0, noise=18, blunder=0.05, quiesce=True,
                   blurb="Solid club player - punishes real mistakes"),
    "Hard":   dict(depth=7, time=4.0, noise=0, blunder=0.0, quiesce=True,
                   blurb="Deep search - you will need to work for it"),
}


class AIPlayer:
    """Wraps the engine with difficulty settings and runs it off-thread."""

    def __init__(self, level="Medium"):
        self.level = level
        self.engine = Engine()
        self.thread = None
        self.result = None
        self.info = ""
        self.started = 0.0
        self.gen = 0

    @property
    def cfg(self):
        return DIFFICULTY[self.level]

    def busy(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, pos):
        self.result = None
        self.info = ""
        self.started = time.time()
        self.gen += 1
        self.thread = threading.Thread(target=self._run,
                                       args=(pos.clone(), self.gen),
                                       daemon=True)
        self.thread.start()

    def stop(self):
        self.gen += 1
        self.engine.abort = True
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        self.engine.abort = False
        self.thread = None
        self.result = None

    def _run(self, pos, gen):
        cfg = self.cfg
        legal = pos.legal_moves()
        if not legal:
            return

        # deliberate mistakes at the easier levels
        if cfg["blunder"] and random.random() < cfg["blunder"]:
            quiet = [m for m in legal if not pos.board[m[1]]] or legal
            self._finish(random.choice(quiet), "played a loose move", gen)
            return

        try:
            move, score, depth = self.engine.search(
                pos, cfg["depth"], cfg["time"], cfg["quiesce"])
        except Exception:
            self._finish(random.choice(legal), "", gen)
            return
        if gen != self.gen:
            return

        # Vary play: sloppy levels wobble everywhere, strong levels only
        # shuffle between near-identical opening moves so games differ.
        sloppy = cfg["noise"] >= 40
        opening = len(pos.rep) <= 7
        if move is not None and (sloppy or opening):
            margin = cfg["noise"] if sloppy else 25
            chance = 0.6 if sloppy else 0.8
            cands = []
            for m in legal:
                pos.make(m)
                cands.append((-evaluate(pos), m))
                pos.unmake(m)
            top = max(sc for sc, _ in cands)
            pool = [m for sc, m in cands if sc >= top - margin]
            if len(pool) > 1 and random.random() < chance:
                move = random.choice(pool)

        if move is None:
            move = random.choice(legal)
        info = "depth %d  %s" % (depth, self._score_text(score, pos.side))
        self._finish(move, info, gen)

    @staticmethod
    def _score_text(score, side):
        if abs(score) > MATE - 100:
            n = (MATE - abs(score) + 1) // 2
            return "mate in %d" % n
        return "%+.2f" % (score / 100.0)

    def _finish(self, move, info, gen):
        elapsed = time.time() - self.started
        if elapsed < 0.35:                     # never answer instantly
            time.sleep(0.35 - elapsed)
        if gen != self.gen:                    # a newer request superseded us
            return
        self.info = info
        self.result = move


# =============================================================================
#  SECTION 3 -- 3D GEOMETRY, MESHES AND CAMERA
# =============================================================================

def _norm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / l, v[1] / l, v[2] / l)


LIGHT_KEY = _norm((-0.45, -0.40, 0.80))
LIGHT_FILL = _norm((0.65, 0.55, 0.30))
AMBIENT, KEY_I, FILL_I = 0.36, 0.60, 0.22


class Mesh:
    """Triangle/quad soup with baked per-face lighting."""

    def __init__(self):
        self.verts = []
        self.faces = []          # (index tuple, normal)

    def vert(self, p):
        self.verts.append(p)
        return len(self.verts) - 1

    def face(self, idxs, normal):
        self.faces.append((idxs, normal))

    def rotate_z(self, ang):
        ca, sa = math.cos(ang), math.sin(ang)
        self.verts = [(x * ca - y * sa, x * sa + y * ca, z)
                      for (x, y, z) in self.verts]
        self.faces = [(i, (n[0] * ca - n[1] * sa, n[0] * sa + n[1] * ca, n[2]))
                      for (i, n) in self.faces]

    def finalize(self):
        self.V = np.array(self.verts, dtype=np.float64)
        self.idx = [f[0] for f in self.faces]
        N = np.array([f[1] for f in self.faces], dtype=np.float64)
        self.N = N
        self.C = np.array([self.V[list(i)].mean(axis=0) for i in self.idx])
        d1 = np.clip(N @ np.array(LIGHT_KEY), 0, None)
        d2 = np.clip(N @ np.array(LIGHT_FILL), 0, None)
        self.shade = AMBIENT + KEY_I * d1 + FILL_I * d2
        self.height = float(self.V[:, 2].max())
        self._cache = {}
        return self

    def colors(self, base, tint=None, amount=0.0):
        """Per-face RGB list for a base colour, optionally tinted."""
        key = (base, tint, amount)
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        if tint is not None and amount > 0:
            base = tuple(base[i] * (1 - amount) + tint[i] * amount
                         for i in range(3))
        out = []
        for s in self.shade:
            out.append((min(255, max(0, int(base[0] * s))),
                        min(255, max(0, int(base[1] * s))),
                        min(255, max(0, int(base[2] * s)))))
        self._cache[key] = out
        return out


def revolve(mesh, profile, segs=12):
    """Surface of revolution.  profile = [(radius, z), ...] bottom to top."""
    ca = [math.cos(2 * math.pi * j / segs) for j in range(segs)]
    sa = [math.sin(2 * math.pi * j / segs) for j in range(segs)]
    ma = [math.cos(2 * math.pi * (j + 0.5) / segs) for j in range(segs)]
    mb = [math.sin(2 * math.pi * (j + 0.5) / segs) for j in range(segs)]
    rings = []
    for (r, z) in profile:
        rings.append([mesh.vert((r * ca[j], r * sa[j], z)) for j in range(segs)])
    for i in range(len(profile) - 1):
        r0, z0 = profile[i]
        r1, z1 = profile[i + 1]
        if r0 == 0.0 and r1 == 0.0:
            continue
        nr, nz = (z1 - z0), -(r1 - r0)
        ln = math.hypot(nr, nz) or 1.0
        nr, nz = nr / ln, nz / ln
        for j in range(segs):
            k = (j + 1) % segs
            mesh.face((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]),
                      (nr * ma[j], nr * mb[j], nz))


def box(mesh, cx, cy, cz, sx, sy, sz):
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    v = []
    for dz in (-hz, hz):
        for dy in (-hy, hy):
            for dx in (-hx, hx):
                v.append(mesh.vert((cx + dx, cy + dy, cz + dz)))
    # v index bits: 0=x 1=y 2=z
    mesh.face((v[0], v[1], v[3], v[2]), (0, 0, -1))
    mesh.face((v[4], v[6], v[7], v[5]), (0, 0, 1))
    mesh.face((v[0], v[4], v[5], v[1]), (0, -1, 0))
    mesh.face((v[2], v[3], v[7], v[6]), (0, 1, 0))
    mesh.face((v[0], v[2], v[6], v[4]), (-1, 0, 0))
    mesh.face((v[1], v[5], v[7], v[3]), (1, 0, 0))


def extrude_xz(mesh, poly, thickness):
    """Extrude a 2D (x, z) outline along the y axis (used for the knight)."""
    area = 0.0
    for i in range(len(poly)):
        x0, z0 = poly[i]
        x1, z1 = poly[(i + 1) % len(poly)]
        area += x0 * z1 - x1 * z0
    if area < 0:
        poly = poly[::-1]
    h = thickness / 2.0
    a = [mesh.vert((x, -h, z)) for (x, z) in poly]
    b = [mesh.vert((x, h, z)) for (x, z) in poly]
    mesh.face(tuple(a[::-1]), (0, -1, 0))
    mesh.face(tuple(b), (0, 1, 0))
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        dx = poly[j][0] - poly[i][0]
        dz = poly[j][1] - poly[i][1]
        ln = math.hypot(dx, dz) or 1.0
        mesh.face((a[i], a[j], b[j], b[i]), (dz / ln, 0.0, -dx / ln))


# ---- the six piece shapes ----------------------------------------------------

PAWN_PROFILE = [
    (0.00, 0.000), (0.30, 0.000), (0.30, 0.045), (0.24, 0.085),
    (0.165, 0.14), (0.135, 0.25), (0.145, 0.32), (0.205, 0.375),
    (0.145, 0.415), (0.115, 0.45), (0.185, 0.50), (0.195, 0.565),
    (0.155, 0.635), (0.085, 0.685), (0.00, 0.705)]

ROOK_PROFILE = [
    (0.00, 0.000), (0.325, 0.000), (0.325, 0.055), (0.265, 0.10),
    (0.215, 0.155), (0.205, 0.45), (0.235, 0.50), (0.30, 0.535),
    (0.30, 0.60), (0.255, 0.62), (0.00, 0.62)]

BISHOP_PROFILE = [
    (0.00, 0.000), (0.325, 0.000), (0.325, 0.05), (0.26, 0.095),
    (0.19, 0.155), (0.145, 0.29), (0.135, 0.40), (0.205, 0.455),
    (0.235, 0.495), (0.155, 0.535), (0.125, 0.575), (0.185, 0.645),
    (0.19, 0.715), (0.155, 0.79), (0.095, 0.845), (0.055, 0.875),
    (0.075, 0.895), (0.055, 0.925), (0.00, 0.945)]

QUEEN_PROFILE = [
    (0.00, 0.000), (0.355, 0.000), (0.355, 0.06), (0.29, 0.11),
    (0.22, 0.175), (0.165, 0.34), (0.155, 0.50), (0.225, 0.555),
    (0.255, 0.60), (0.17, 0.645), (0.14, 0.695), (0.235, 0.79),
    (0.275, 0.885), (0.215, 0.925), (0.105, 0.95), (0.065, 0.985),
    (0.09, 1.005), (0.065, 1.035), (0.00, 1.06)]

KING_PROFILE = [
    (0.00, 0.000), (0.365, 0.000), (0.365, 0.065), (0.30, 0.115),
    (0.23, 0.185), (0.175, 0.37), (0.165, 0.545), (0.235, 0.60),
    (0.265, 0.645), (0.18, 0.69), (0.15, 0.745), (0.245, 0.845),
    (0.275, 0.945), (0.215, 0.985), (0.13, 1.005), (0.105, 1.03)]

KNIGHT_OUTLINE = [
    (-0.215, 0.185), (0.215, 0.185), (0.165, 0.315), (0.095, 0.415),
    (0.205, 0.455), (0.295, 0.475), (0.305, 0.545), (0.235, 0.605),
    (0.155, 0.705), (0.055, 0.785), (-0.045, 0.805), (-0.085, 0.725),
    (-0.145, 0.835), (-0.205, 0.745), (-0.225, 0.60), (-0.265, 0.445),
    (-0.245, 0.285)]


def build_pawn():
    m = Mesh()
    revolve(m, PAWN_PROFILE, 12)
    return m.finalize()


def build_rook():
    m = Mesh()
    revolve(m, ROOK_PROFILE, 12)
    for i in range(6):
        a = 2 * math.pi * i / 6.0
        box(m, 0.245 * math.cos(a), 0.245 * math.sin(a), 0.665,
            0.115, 0.115, 0.09)
    return m.finalize()


def build_bishop():
    m = Mesh()
    revolve(m, BISHOP_PROFILE, 12)
    return m.finalize()


def build_queen():
    m = Mesh()
    revolve(m, QUEEN_PROFILE, 14)
    for i in range(8):
        a = 2 * math.pi * i / 8.0
        box(m, 0.275 * math.cos(a), 0.275 * math.sin(a), 0.90,
            0.075, 0.075, 0.075)
    return m.finalize()


def build_king():
    m = Mesh()
    revolve(m, KING_PROFILE, 14)
    box(m, 0, 0, 1.135, 0.075, 0.075, 0.24)
    box(m, 0, 0, 1.155, 0.20, 0.075, 0.075)
    return m.finalize()


def build_knight(facing):
    m = Mesh()
    revolve(m, [(0.00, 0.000), (0.335, 0.000), (0.335, 0.055),
                (0.275, 0.10), (0.225, 0.155), (0.215, 0.20)], 12)
    extrude_xz(m, KNIGHT_OUTLINE, 0.215)
    m.rotate_z(facing)
    return m.finalize()


# ---- camera ------------------------------------------------------------------

class Camera:
    def __init__(self):
        self.yaw = -math.pi / 2
        self.pitch = math.radians(46)
        self.dist = 11.4
        self.target = np.array([0.0, 0.0, 0.35])
        self.t_yaw = self.yaw
        self.t_pitch = self.pitch
        self.t_dist = self.dist
        self.t_target = self.target.copy()
        self.spin = False
        self.fov = math.radians(42)

    def fit(self, aspect):
        """Distance at which the whole board comfortably fills the view."""
        th = math.tan(self.fov * 0.5)
        return max(4.9 / th * 0.74, 4.9 / (th * max(0.42, aspect)))

    def look(self, yaw, pitch, dist=None, instant=False):
        while yaw - self.t_yaw > math.pi:
            yaw -= 2 * math.pi
        while yaw - self.t_yaw < -math.pi:
            yaw += 2 * math.pi
        self.t_yaw = yaw
        self.t_pitch = pitch
        if dist is not None:
            self.t_dist = dist
        self.t_target = np.array([0.0, 0.0, 0.35])
        if instant:
            self.yaw, self.pitch = self.t_yaw, self.t_pitch
            self.dist = self.t_dist
            self.target = self.t_target.copy()

    def update(self, dt):
        if self.spin:
            self.t_yaw += dt * 0.28
        k = min(1.0, dt * 9.0)
        self.yaw += (self.t_yaw - self.yaw) * k
        self.pitch += (self.t_pitch - self.pitch) * k
        self.dist += (self.t_dist - self.dist) * k
        self.target += (self.t_target - self.target) * k

    def orbit(self, dx, dy):
        self.t_yaw += dx
        self.t_pitch = max(math.radians(6), min(math.radians(88),
                                                self.t_pitch + dy))
        self.spin = False

    def pan(self, dx, dy):
        eye, right, up, fwd = self.basis()
        self.t_target = self.target - right * dx + up * dy
        self.t_target[0] = max(-6, min(6, self.t_target[0]))
        self.t_target[1] = max(-6, min(6, self.t_target[1]))
        self.t_target[2] = max(-2, min(4, self.t_target[2]))

    def zoom(self, f):
        self.t_dist = max(5.0, min(30.0, self.t_dist * f))

    def basis(self):
        cp = math.cos(self.pitch)
        eye = self.target + np.array([self.dist * cp * math.cos(self.yaw),
                                      self.dist * cp * math.sin(self.yaw),
                                      self.dist * math.sin(self.pitch)])
        fwd = self.target - eye
        fwd = fwd / (np.linalg.norm(fwd) or 1.0)
        wup = np.array([0.0, 0.0, 1.0])
        right = np.cross(fwd, wup)
        n = np.linalg.norm(right)
        right = np.array([1.0, 0.0, 0.0]) if n < 1e-9 else right / n
        up = np.cross(right, fwd)
        return eye, right, up, fwd


class Viewport:
    """Perspective projection helper bound to a pixel rectangle."""

    def __init__(self, w, h, cam):
        self.resize(w, h)
        self.cam = cam

    def resize(self, w, h):
        self.w, self.h = max(1, w), max(1, h)
        self.cx, self.cy = self.w * 0.5, self.h * 0.5

    def prepare(self):
        cam = self.cam
        self.eye, self.right, self.up, self.fwd = cam.basis()
        self.focal = (self.h * 0.5) / math.tan(cam.fov * 0.5)
        self.M = np.array([self.right, self.up, self.fwd])

    def project(self, pts):
        """(n,3) world points -> (n,2) screen floats, (n,) depth."""
        cam = (pts - self.eye) @ self.M.T
        z = np.maximum(cam[:, 2], 1e-4)
        sx = self.cx + self.focal * cam[:, 0] / z
        sy = self.cy - self.focal * cam[:, 1] / z
        return np.stack([sx, sy], axis=1), cam[:, 2]

    def ray_to_board(self, mx, my, plane_z=0.0):
        """Screen pixel -> (x, y) point on the board plane, or None."""
        d = (self.fwd
             + self.right * ((mx - self.cx) / self.focal)
             + self.up * (-(my - self.cy) / self.focal))
        if abs(d[2]) < 1e-9:
            return None
        t = (plane_z - self.eye[2]) / d[2]
        if t <= 0:
            return None
        p = self.eye + d * t
        return float(p[0]), float(p[1])


# =============================================================================
#  SECTION 4 -- PILLOW RENDERER (headless, used by the web app)
# =============================================================================

CLR_BG_TOP = (26, 30, 42)
CLR_BG_BOT = (10, 12, 18)
CLR_LIGHT_SQ = (226, 205, 172)
CLR_DARK_SQ = (122, 84, 61)
CLR_FRAME = (92, 63, 42)
CLR_WHITE_PIECE = (238, 232, 219)
CLR_BLACK_PIECE = (78, 74, 90)

TINT_SEL = (245, 200, 70)
TINT_MOVE = (96, 186, 118)
TINT_CAP = (214, 96, 84)
TINT_LAST = (92, 138, 208)
TINT_CHECK = (222, 70, 62)

_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:\\Windows\\Fonts\\arial.ttf",
]


def _load_font(size):
    for p in _FONT_PATHS:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def blend(c, t, a):
    return (int(c[0] + (t[0] - c[0]) * a),
            int(c[1] + (t[1] - c[1]) * a),
            int(c[2] + (t[2] - c[2]) * a))


class WebScene:
    """Same geometry as the desktop build, rasterised with Pillow."""

    def __init__(self):
        self.meshes = {
            (WHITE, PAWN): build_pawn(), (BLACK, PAWN): build_pawn(),
            (WHITE, ROOK): build_rook(), (BLACK, ROOK): build_rook(),
            (WHITE, BISHOP): build_bishop(), (BLACK, BISHOP): build_bishop(),
            (WHITE, QUEEN): build_queen(), (BLACK, QUEEN): build_queen(),
            (WHITE, KING): build_king(), (BLACK, KING): build_king(),
            (WHITE, KNIGHT): build_knight(math.pi / 2),
            (BLACK, KNIGHT): build_knight(-math.pi / 2),
        }

        sq = np.zeros((64, 4, 3))
        for s in range(64):
            r, c = s >> 3, s & 7
            x0, y0 = c - 4.0, r - 4.0
            sq[s] = [(x0, y0, 0), (x0 + 1, y0, 0),
                     (x0 + 1, y0 + 1, 0), (x0, y0 + 1, 0)]
        self.sq_v = sq.reshape(-1, 3)

        o, i, d = 4.36, 4.0, -0.32
        frame = []
        for quad, n in (
            ([(-o, -o, 0), (o, -o, 0), (o, -i, 0), (-o, -i, 0)], (0, 0, 1)),
            ([(-o, i, 0), (o, i, 0), (o, o, 0), (-o, o, 0)], (0, 0, 1)),
            ([(-o, -i, 0), (-i, -i, 0), (-i, i, 0), (-o, i, 0)], (0, 0, 1)),
            ([(i, -i, 0), (o, -i, 0), (o, i, 0), (i, i, 0)], (0, 0, 1)),
            ([(-o, -o, d), (o, -o, d), (o, -o, 0), (-o, -o, 0)], (0, -1, 0)),
            ([(o, o, d), (-o, o, d), (-o, o, 0), (o, o, 0)], (0, 1, 0)),
            ([(-o, o, d), (-o, -o, d), (-o, -o, 0), (-o, o, 0)], (-1, 0, 0)),
            ([(o, -o, d), (o, o, d), (o, o, 0), (o, -o, 0)], (1, 0, 0)),
            ([(-o, -o, d), (-o, o, d), (o, o, d), (o, -o, d)], (0, 0, -1)),
        ):
            nn = np.array(n, dtype=float)
            sh = (AMBIENT + KEY_I * max(0.0, float(nn @ np.array(LIGHT_KEY)))
                  + FILL_I * max(0.0, float(nn @ np.array(LIGHT_FILL))))
            base = CLR_FRAME if n == (0, 0, 1) else tuple(int(v * 0.8) for v in CLR_FRAME)
            frame.append((quad, tuple(min(255, int(v * sh)) for v in base)))
        self.frame_v = np.array([p for q, _ in frame for p in q], dtype=float)
        self.frame_c = [c for _, c in frame]

        self.ring = np.array([(math.cos(2 * math.pi * k / 10.0),
                               math.sin(2 * math.pi * k / 10.0)) for k in range(10)])
        self.font = _load_font(15)

    # ------------------------------------------------------------------
    @staticmethod
    def square_center(sq):
        return ((sq & 7) - 3.5, (sq >> 3) - 3.5)

    def pick(self, vp, x, y):
        hit = vp.ray_to_board(x, y)
        if hit is None:
            return None
        c = int(math.floor(hit[0] + 4.0))
        r = int(math.floor(hit[1] + 4.0))
        return r * 8 + c if (0 <= r < 8 and 0 <= c < 8) else None

    # ------------------------------------------------------------------
    def render(self, vp, board, w, h, scale=2, selected=None, targets=(),
               last_move=None, check_sq=None, show_hints=True,
               show_coords=True):
        vp.prepare()
        eye = vp.eye
        W, H = int(w * scale), int(h * scale)
        img = Image.new("RGB", (W, H), CLR_BG_BOT)
        dr = ImageDraw.Draw(img)

        band = max(2, H // 56)
        for yy in range(0, H, band):
            f = yy / float(H)
            dr.rectangle([0, yy, W, yy + band],
                         fill=(int(CLR_BG_TOP[0] + (CLR_BG_BOT[0] - CLR_BG_TOP[0]) * f),
                               int(CLR_BG_TOP[1] + (CLR_BG_BOT[1] - CLR_BG_TOP[1]) * f),
                               int(CLR_BG_TOP[2] + (CLR_BG_BOT[2] - CLR_BG_TOP[2]) * f)))

        def poly(pts, colour):
            dr.polygon([(p[0] * scale, p[1] * scale) for p in pts], fill=colour)

        # board frame
        pts, dep = vp.project(self.frame_v)
        pl = np.clip(pts, -9999, 9999).tolist()
        for k in sorted(range(len(self.frame_c)),
                        key=lambda j: -float(dep[j * 4:j * 4 + 4].mean())):
            if dep[k * 4:k * 4 + 4].min() > 0.05:
                poly(pl[k * 4:k * 4 + 4], self.frame_c[k])

        # highlight map
        hl = {}
        if last_move:
            hl[last_move[0]] = (TINT_LAST, 0.26)
            hl[last_move[1]] = (TINT_LAST, 0.34)
        if show_hints:
            for t in targets:
                hl[t] = (TINT_CAP, 0.42) if board[t] else (TINT_MOVE, 0.32)
        if selected is not None:
            hl[selected] = (TINT_SEL, 0.48)
        if check_sq is not None:
            hl[check_sq] = (TINT_CHECK, 0.5)

        # squares
        pts, dep = vp.project(self.sq_v)
        pl = np.clip(pts, -9999, 9999).tolist()
        sdep = dep.reshape(64, 4).mean(axis=1)
        for s in np.argsort(-sdep):
            s = int(s)
            if dep[s * 4:s * 4 + 4].min() <= 0.05:
                continue
            r, c = s >> 3, s & 7
            col = CLR_DARK_SQ if (r + c) % 2 == 0 else CLR_LIGHT_SQ
            if s in hl:
                col = blend(col, hl[s][0], hl[s][1])
            poly(pl[s * 4:s * 4 + 4], col)

        # legal-move dots
        if show_hints and targets:
            quiet = [t for t in targets if not board[t]]
            if quiet:
                pts3 = np.array([(self.square_center(t)[0] + u * 0.15,
                                  self.square_center(t)[1] + v * 0.15, 0.012)
                                 for t in quiet for (u, v) in self.ring])
                mp, md = vp.project(pts3)
                mp = np.clip(mp, -9999, 9999).tolist()
                for k in range(0, len(pts3), 10):
                    if md[k] > 0.05:
                        poly(mp[k:k + 10], (58, 122, 74))

        # contact shadows on a translucent layer
        occupied = [s for s in range(64) if board[s]]
        if occupied:
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            pts3 = np.array([(self.square_center(s)[0] + u * 0.33 + 0.16,
                              self.square_center(s)[1] + v * 0.33 + 0.14, 0.006)
                             for s in occupied for (u, v) in self.ring])
            sp, sd = vp.project(pts3)
            sp = np.clip(sp, -9999, 9999).tolist()
            for k in range(0, len(pts3), 10):
                if sd[k] > 0.05:
                    ld.polygon([(p[0] * scale, p[1] * scale)
                                for p in sp[k:k + 10]], fill=(0, 0, 0, 72))
            img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
            dr = ImageDraw.Draw(img)

        # pieces, painter's algorithm
        items = []
        for s in range(64):
            p = board[s]
            if not p:
                continue
            mesh = self.meshes[(p >> 3, p & 7)]
            cx, cy = self.square_center(s)
            centre = np.array([cx, cy, mesh.height * 0.5])
            items.append((float((centre - eye) @ vp.fwd), s, p, cx, cy, mesh))
        items.sort(key=lambda t: -t[0])

        for depth, s, p, cx, cy, mesh in items:
            if depth <= 0.3:
                continue
            off = np.array([cx, cy, 0.0])
            pr, _ = vp.project(mesh.V + off)
            np.clip(pr, -9999, 9999, out=pr)
            pr *= scale
            cw = mesh.C + off
            fd = (cw - eye) @ vp.fwd
            vis = np.einsum("ij,ij->i", mesh.N, cw - eye) < 0
            ids = np.nonzero(vis)[0]
            ids = ids[np.argsort(-fd[ids])]
            base = CLR_WHITE_PIECE if (p >> 3) == WHITE else CLR_BLACK_PIECE
            if s == selected:
                cols = mesh.colors(base, TINT_SEL, 0.40)
            elif s == check_sq:
                cols = mesh.colors(base, TINT_CHECK, 0.38)
            else:
                cols = mesh.colors(base)
            plist = pr.tolist()
            faces = mesh.idx
            for k in ids.tolist():
                dr.polygon([tuple(plist[v]) for v in faces[k]], fill=cols[k])

        img = img.resize((int(w), int(h)), Image.LANCZOS)

        if show_coords:
            dr = ImageDraw.Draw(img)
            ex, ey = float(eye[0]), float(eye[1])
            gy = -4.75 if ey < 0 else 4.75
            gx = -4.75 if ex < 0 else 4.75
            anchors = [(c - 3.5, gy, 0.02) for c in range(8)] + \
                      [(gx, r - 3.5, 0.02) for r in range(8)]
            labels = list("abcdefgh") + [str(r + 1) for r in range(8)]
            ap, ad = vp.project(np.array(anchors))
            for k, t in enumerate(labels):
                if ad[k] > 0.5:
                    dr.text((ap[k][0], ap[k][1]), t, fill=(178, 170, 154),
                            font=self.font, anchor="mm")
        return img


# =============================================================================
#  SECTION 5 -- SYNCHRONOUS MOVE CHOICE (for request/response front ends)
# =============================================================================

def pick_move(pos, level, time_scale=1.0):
    """Choose a move for `level` on the calling thread.

    Same behaviour as the threaded desktop AIPlayer, but blocking, which is
    what a rerun-based framework such as Streamlit needs.  `time_scale`
    shrinks the thinking budget for slower shared hardware.
    Returns (move, info_text) or (None, "") when there is nothing to play.
    """
    cfg = DIFFICULTY[level]
    legal = pos.legal_moves()
    if not legal:
        return None, ""

    if cfg["blunder"] and random.random() < cfg["blunder"]:
        quiet = [m for m in legal if not pos.board[m[1]]] or legal
        return random.choice(quiet), "played a loose move"

    engine = Engine()
    move, score, depth = engine.search(pos, cfg["depth"],
                                       max(0.2, cfg["time"] * time_scale),
                                       cfg["quiesce"])
    sloppy = cfg["noise"] >= 40
    opening = len(pos.rep) <= 7
    if move is not None and (sloppy or opening):
        margin = cfg["noise"] if sloppy else 25
        chance = 0.6 if sloppy else 0.8
        cands = []
        for m in legal:
            pos.make(m)
            cands.append((-evaluate(pos), m))
            pos.unmake(m)
        top = max(sc for sc, _ in cands)
        pool = [m for sc, m in cands if sc >= top - margin]
        if len(pool) > 1 and random.random() < chance:
            move = random.choice(pool)

    if move is None:
        return random.choice(legal), ""
    if abs(score) > MATE - 100:
        txt = "mate in %d" % ((MATE - abs(score) + 1) // 2)
    else:
        txt = "%+.2f" % (score / 100.0)
    return move, "depth %d  %s" % (depth, txt)


def move_to_san_list(pos):
    """[(move, san), ...] for every legal move, sorted for menu display."""
    out = [(m, pos.san(m)) for m in pos.legal_moves()]
    out.sort(key=lambda t: t[1])
    return out


START_COUNTS = {PAWN: 8, KNIGHT: 2, BISHOP: 2, ROOK: 2, QUEEN: 1, KING: 1}
