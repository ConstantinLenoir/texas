"""
$ pytest test.py
TODO test Party
"""

import pytest

import play


SUITS = {"♠": 0, "♥": 1, "♦": 2, "♣": 3}

CARDS = {**{str(i + 1): i for i in range(10)}, "J": 10, "Q": 11, "K": 12}


def card_symb(s):
    value = s[:2] if len(s) == 3 else s[0]
    return CARDS[value] + 13 * SUITS[s[-1]]


def test_card_symb():
    assert tuple(card_symb(s) for s in ["K♠", "K♣", "1♠", "2♠", "3♠"]) == (
        12,
        51,
        0,
        1,
        2,
    )


def test_card_value():
    assert tuple(
        play.card_value(card_symb(s)) for s in ["K♠", "K♣", "1♠", "2♠", "3♠"]
    ) == (
        12,
        12,
        13,
        1,
        2,
    )


def test_range():
    # A range of 4 numbers starting from 3.
    assert tuple(range(3, 3 + 4)) == (3, 4, 5, 6)


def test_unzip():
    assert list(zip(*[(1, "a"), (2, "b")])) == [(1, 2), ("a", "b")]


class TestMaxSequence:
    """
    SEE test_range() and test_unzip()
    """

    test_cases = [
        ([12 + 26, 11 + 13, 10, 9], tuple(range(9, 13))),
        ([12 + 26, 11 + 13, 10, 9, 0], tuple(range(9, 13)) + (13,)),
        ([0, 1, 2, 3, 5, 6, 7], tuple(range(4))),
        ([0, 1, 2, 3, 5, 6, 7, 8, 9, 10], tuple(range(6, 6 + 5))),
    ]

    @pytest.mark.parametrize("test_input,expected", test_cases)
    def test_only_values(self, test_input, expected):
        value_seq, _ = play.find_max_sequence(test_input)
        assert value_seq == expected

    def test(self):
        value_seq, card_seq = play.find_max_sequence([0, 10, 14, 23, 28])
        assert value_seq == (0, 1, 2) and card_seq == (0, 14, 28)


def test_group_duplicates():
    # Full House
    duplicates = play.group_duplicates([0, 13, 26, 12, 51])
    assert duplicates[2] == [12] and duplicates[3] == [13]


@pytest.mark.parametrize(
    "test_input,expected",
    [([0, 1, 2, 3, 4], 0), ([0, 1, 2 + 13, 3, 4], None), ([0, 1, 2, 3], None)],
)
def test_flush_suite(test_input, expected):
    assert play.flush_suite(test_input) == expected


def test_sort_cards():
    assert play.sort_cards([39, 40, 41, 17], suit=3) == [1, 2, 13]


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (["1♠", "10♠", "K♠", "Q♠", "J♠", "2♦", "3♦"], (play.Hand.STRAIGHT_FLUSH, 13)),
        (
            ["1♠", "9♠", "K♠", "Q♠", "J♠", "2♥", "3♦"],
            (play.Hand.FLUSH, 13, 12, 11, 10, 8),
        ),
        (
            ["1♠", "10♥", "K♠", "Q♠", "J♠", "2♥", "3♦"],
            (play.Hand.STRAIGHT, 13),
        ),
        (
            ["1♠", "1♥", "Q♠", "Q♦", "8♠", "6♥", "3♦"],
            (play.Hand.TWO_PAIR, 13, 11, 7),
        ),
        (
            ["1♠", "1♥", "Q♠", "Q♦", "6♠", "6♥", "K♦"],
            (play.Hand.TWO_PAIR, 13, 11, 12),
        ),
    ],
)
def test_assess_hand(test_input, expected):
    test_input = [card_symb(c) for c in test_input]
    assert play.assess_hand(test_input) == expected


@pytest.mark.parametrize(
    "higher_cards,lower_cards",
    [
        (
            ["1♠", "10♠", "K♠", "Q♠", "J♠", "2♦", "3♦"],
            ["1♠", "10♥", "K♠", "Q♠", "J♠", "2♥", "3♦"],
        ),
        (
            ["1♠", "1♥", "K♠", "Q♠", "10♠"],
            ["1♠", "1♥", "K♦", "Q♣", "9♠"],
        ),
    ],
)
def test_hand_order(higher_cards, lower_cards):
    assert play.assess_hand([card_symb(c) for c in higher_cards]) > play.assess_hand(
        [card_symb(c) for c in lower_cards]
    )
