import binascii
import os
import math
from typing import List, Iterable, Tuple, Callable, TypeVar

# Bridge order: clubs < diamonds < hearts < spades

def char_to_num(c: str) -> int:
    return ord(c) - 64

def num_to_char(n: int) -> str:
    return chr(normalize(n, 26) + 64)

def normalize(n: int, mod: int) -> int:
    return n % mod if n % mod != 0 else mod

def min_max(x: int, y: int) -> Tuple[int, int]:
    return (x, y) if x < y else (y, x)

def round_2(n: int) -> int:
    return 1 << int(math.floor(math.log2(n - 1)) + 1)

def num_bytes(n: int) -> int:
    return math.ceil((math.log(n+1)/math.log(2))/8)

def randint(a: int, b: int) -> int:
    "Algorithm from: http://crypto.stackexchange.com/a/8830"
    # TODO: Doesn't handle a
    def gen() -> int:
       return int(binascii.hexlify(os.urandom(num_bytes(b))), 16) % round_2(b)

    out = gen()
    while out >= b:
        out = gen()

    return out

S = TypeVar('S')
def shuffle(l: List[S]) -> None:
    # Fisher-Yates shuffle
    for i in range(len(l)-1, 0, -1):
        j = randint(0, len(l))
        l[i], l[j] = l[j], l[i]

JOKER_A = 53
JOKER_B = 54

def ordered_deck() -> List[int]:
    return list(range(1, 55))

def random_deck() -> List[int]:
    deck = ordered_deck()
    shuffle(deck)
    return deck

def keyed_deck(key: str) -> List[int]:
    raise NotImplemented('keyed_deck')

def move(deck: List[int], val: int, n: int) -> None:
    idx = deck.index(val)
    new_idx = normalize((idx + n), len(deck) - 1)
    deck.insert(new_idx, deck.pop(idx))

def triple_cut(deck: List[int]) -> List[int]:
    first_j, last_j = min_max(deck.index(JOKER_A), deck.index(JOKER_B))
    return deck[last_j+1:] + deck[first_j:last_j+1] + deck[:first_j]

def count_cut(deck: List[int]) -> List[int]:
    last_val = deck[-1]
    if last_val in [JOKER_A, JOKER_B]:
        return deck

    return deck[last_val:-1] + deck[:last_val] + [last_val]

def keystream(deck: List[int]) -> Iterable[int]:
    while True:
        move(deck, JOKER_A, 1)
        move(deck, JOKER_B, 2)

        deck = triple_cut(deck)
        deck = count_cut(deck)

        top = deck[0] if deck[0] not in [JOKER_A, JOKER_B] else 53
        val = deck[top:][0]
        if val in [JOKER_A, JOKER_B]:
            continue

        yield val

T = TypeVar('T')
def chunk(l: List[T], n: int) -> Iterable[List[T]]:
    for i in range(0, len(l), n):
        yield l[i:i+n]

def combine(deck: List[int], text: str, f: Callable[[int, int], int]) -> str:
    text_num = (char_to_num(c) for c in text.replace(' ', '').upper())
    out = (normalize(f(k, p), 26) for k, p in zip(keystream(deck), text_num))

    return ''.join(map(num_to_char, out))

def encrypt(deck: List[int], plaintext: str) -> str:
    plaintext = plaintext.replace(' ', '')
    if len(plaintext) % 5 != 0:
        plaintext += 'X' * (5 - (len(plaintext) % 5))

    return combine(deck, plaintext, lambda k, p: k + p)

def decrypt(deck: List[int], ciphertext: str) -> str:
    return combine(deck, ciphertext, lambda k, p: p - k)

if __name__ == '__main__':
    import sys
    import argparse
    import ast
    parser = argparse.ArgumentParser(description='Solitaire cipher.')
    actions = ['encrypt', 'decrypt', 'randdeck']
    parser.add_argument('action', choices=actions)
    parser.add_argument('message', type=str)
    parser.add_argument('-k', '--key', type=str,
                        help='use a keyed deck with this key')
    parser.add_argument('-d', '--deck', type=argparse.FileType('r'),
                        help='read deck from this file')
    args = parser.parse_args()

    if args.action == 'randdeck':
        print(random_deck())
        sys.exit(0)

    if args.deck and args.key:
        # TODO: Nicer and to stderr
        print('Can\'t use both deck from key and from file')
        sys.exit(1)

    if args.deck:
        deck = ast.literal_eval(''.join(args.deck.readlines()).strip())
        args.deck.close()
    elif args.key:
        deck = keyed_deck(args.key)
    else:
        print('Warning: Using a ordered deck') # TODO: stderr
        deck = ordered_deck()

    if args.action == 'encrypt':
        print(encrypt(deck, args.message))
        sys.exit(0)

    if args.action == 'decrypt':
        print(decrypt(deck, args.message))
        sys.exit(0)
