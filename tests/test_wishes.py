import pytest

# Temporarily add parent folder to python path so we can import wishes
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import wishes

def test_getPriorityOrderedWishes():
    wishlist = wishes.Wishlist()
    wishlist.addWish("Shenanigans", 3, "Für mehr Blödsinn!", link = "https://youtu.be/dQw4w9WgXcQ?si=B8g9pOJgWpztlIZw")
    wishlist.addWish("Weltfrieden", 5)
    wishlist.addWish("Wäre ganz nett", 1, desc="Das hier wäre auch ganz nett. Ist aber nicht besonders wichtig.")

    orderedWishes = wishlist.getPriorityOrderedWishes()
    assert [wish.title for wish in orderedWishes] == ["Weltfrieden", "Shenanigans", "Wäre ganz nett"]

