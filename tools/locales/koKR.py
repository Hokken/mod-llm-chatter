# -*- coding: utf-8 -*-
"""koKR locale data for mod-llm-chatter.

Split out of chatter_constants.py so the central module stays
readable: the language tables are bulk data that changes for
translation reasons, not logic that changes with the module.

Names here are unsuffixed -- the locale is the module. The
registry in this package maps locale codes onto these.
"""

ZONE_NAMES = {
    65: "용의 안식처",  # verified: official Blizzard ko-kr news source
    66: "줄드락",  # verified: official Blizzard ko-kr news source
    67: "폭풍우 봉우리",  # verified: official Blizzard ko-kr news source
    210: "얼음왕관",  # verified: official Blizzard ko-kr news source
    394: "회색 구릉지",  # verified: official Blizzard ko-kr news source
    495: "울부짖는 협만",  # verified: official Blizzard ko-kr news source
    3537: "북풍의 땅",  # verified: official Blizzard ko-kr news source
    3711: "숄라자르 분지",  # verified: official Blizzard ko-kr news source
}
