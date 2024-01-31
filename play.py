from enum import IntEnum
import random
from collections import Counter, defaultdict, namedtuple


class Hand(IntEnum):
    """
    IntNum makes it possible to compare items.
    """

    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR = 8
    STRAIGHT_FLUSH = 9


class Party:
    """
    The kicker card (tie-breaker).
    Monte Carlo simulations.
    https://en.wikipedia.org/wiki/Kicker_(poker)
    Every player is evaluated against a set of 5 cards (a hand) that are composed of "main" cards and "side" cards.
    The pot will be split if multiple players have the same hand.
    In some cases, the hand is composed of community cards only (the hole cards are not taken
    into account).
    """

    def __init__(self, n_players=7):
        ordered_cards = list(range(1, 53))
        self.cards = random.shuffle(ordered_cards)
        self.hole_cards = [n_players * []]
        for i in range(2 * n_players):
            self.hole_cards[i % n_players].append(self.cards.pop())
        self.left_rounds = 3
        self.board = []

    def play(self):
        if not self.left_rounds:
            self.ordered_hands = self.sort_hands()
            return False
        if self.left_rounds == 3:
            self.board = [self.cards.pop(), self.cards.pop(), self.cards.pop()]
        else:
            self.board.append(self.cards.pop())
        self.left_rounds -= 1
        return True

    def sort_hands(self):
        records = []
        for player_code, two_cards in enumerate(self.hole_cards):
            hand = [*self.board, *two_cards]
            record = (assess_hand(hand), player_code)
            records.append(record)
        ordered_records = sorted(records, reverse=True)
        self.best_hand = ordered_records[0][0]
        # Hole cards.
        self.winners = [
            self.hole_cards(record[1])
            for record in ordered_records
            if record[0] == self.best_hand
        ]


def assess_hand(cards):
    """
    A simple algorithm for evaluating Texas hands. Every set of 7 cards is transformed
    into a comparable hand tuple. There should be exactly 7462 such tuples.

    One of the fastest technique is the Cactus Kev technique. Cards are encoded by
    a bit array. In this array, different ranges have different meanings.
    +--------+--------+--------+--------+
    |xxxbbbbb|bbbbbbbb|cdhsrrrr|xxpppppp|
    +--------+--------+--------+--------+
    p = prime number of rank (deuce=2,trey=3,four=5,...,ace=41)
    r = rank of card (deuce=0,trey=1,four=2,five=3,...,ace=12)
    cdhs = suit of card (bit turned on based on the suit: diamonds, spades...)
    b = bit turned on depending on rank of card (AKQJT98765432)
    x = unused bit
    Pairwise operations and prime multiplications are used to map hands to keys.
    A precomputed lookup table is used to map hand keys to ranks. Multiple hands can correspond to the same rank.
    There are only 7462 possible ranks.

    It may be possible to avoid conditional branches by mapping hands to comparable numeric keys.
    Considering all the "possible" hands deriving from a set of 7 cards and retaining the highest one...

    The descending order of side cards is important for the lexicographic
    sort of assessed hands (tuples).
    Equivalent hands are represented by the same tuple.
    """
    # Ordered sequence.
    seq_values, seq_cards = find_max_sequence(cards)
    duplicates = group_duplicates(cards)
    # flush_suite(seq_cards) instead of flush_suite(seq_values).
    if len(seq_values) == 5 and flush_suite(seq_cards) is not None:
        record = (Hand.STRAIGHT_FLUSH, seq_values[-1])
    elif duplicates[4]:
        side_cards = select_side_cards(cards, duplicates[4])
        record = (Hand.FOUR, duplicates[4][0], side_cards[0])
    elif duplicates[3] and duplicates[2]:
        record = (Hand.FULL_HOUSE, duplicates[3][0], duplicates[2][0])
    elif flush_suite(cards) is not None:
        flush_cards = sort_cards(cards, suit=flush_suite(cards), reverse=True)
        record = (Hand.FLUSH, *flush_cards[:5])
    elif len(seq_values) == 5:
        record = (Hand.STRAIGHT, seq_values[-1])
    elif duplicates[3]:
        side_cards = select_side_cards(cards, duplicates[3])
        record = (Hand.THREE, duplicates[3][0], *side_cards[:2])
    elif len(duplicates[2]) == 2:
        side_cards = select_side_cards(cards, duplicates[2])
        record = (
            Hand.TWO_PAIR,
            max_card(duplicates[2]),
            min_card(duplicates[2]),
            side_cards[0],
        )
    elif len(duplicates[2]) == 1:
        side_cards = select_side_cards(cards, duplicates[2])
        record = (Hand.PAIR, duplicates[2][0], *side_cards[:3])
    else:
        best_hand = sort_cards(cards, reverse=True)[:5]
        record = (Hand.HIGH_CARD, *best_hand)
    return record


def select_side_cards(cards, cards_to_exclude):
    """
    Exclude some cards and return the remaining ones in descending order.
    For the kickers.
    https://en.wikipedia.org/wiki/Kicker_(poker)
    """
    side_cards = {card_value(c) for c in cards}.difference(
        card_value(c) for c in cards_to_exclude
    )
    return sorted(side_cards, reverse=True)


def card_value(c):
    # A special case for the aces.
    return 13 if c % 13 == 0 else c % 13


def sort_cards(cards, suit=None, reverse=False, transform_cards=True):
    """
    suit is included in [0, 1, 2, 3]
    """
    cards = list(cards)
    if suit is not None:
        cards = filter(lambda c: c // 13 == suit, cards)
    if transform_cards:
        return sorted(map(card_value, cards), reverse=reverse)
    else:
        return sorted(cards, key=card_value, reverse=reverse)


def max_card(cards, suit=None, transform_cards=True):
    return sort_cards(cards, suit=suit, transform_cards=transform_cards)[-1]


def min_card(cards, transform_cards=True):
    return sort_cards(cards, transform_cards=transform_cards)[0]


def find_max_sequence(cards):
    """
    Test the presence of a straights.
    The role of the ace card (0) is complex regarding sequences.
    The output sequence is ordered.
    Only the first encountered longest sequence is selected. It's not a problem
    in the case of Texas hands.
    Only the top 5 elements of the longest sequence are returned.
    Two sequences are returned:
    one with the card values (0-13), the other with the card identifiers (0-52)
    For less than 14 cards, there is no risk of including both 0 and 13 in the
    returned sequence.
    Interesting use case of a dictionary.
    """
    Cards = namedtuple("Card", ["value", "id"])
    card_dict = {card_value(c): Cards(value=card_value(c), id=c) for c in cards}
    if len(card_dict) == 1:
        return []
    # The ace card plays two roles.
    if 13 in card_dict:
        # NOTE deque is faster for prepending.
        card_dict[0] = Cards(value=0, id=card_dict[13].id)
    cards = sorted(card_dict.values())
    sequence = [cards[0]]
    sequences = []
    for i in range(len(cards) - 1):
        if cards[i + 1].value == cards[i].value + 1:
            sequence.append(cards[i + 1])
        else:
            sequences.append(sequence)
            sequence = [cards[i + 1]]
    # The following instruction is easy to forget.
    sequences.append(sequence)
    max_sequence = sorted(sequences, key=len)[-1]
    # A Texas hand has only 5 cards.
    max_sequence = max_sequence[-5:]
    return list(zip(*max_sequence))


def group_duplicates(hand):
    """
    To count duplicates and group them.
    groups[2] is the list of card values that are repeated only two times.
    len(groups[2]) == 2 denotes a two pair hand.
    For n-of-a-kind hands.
    Naming problems. Some operations are hard to explain in English.
    Only the
    """
    counter = Counter(card_value(c) for c in hand)
    groups = defaultdict(list)
    for card, n in counter.most_common(2):
        groups[n].append(card)
    return groups


def flush_suite(hand):
    counter = Counter(c // 13 for c in hand)
    if counter.most_common(1)[0][1] == 5:
        return counter.most_common(1)[0][0]
    else:
        return None
