python 2.7.3

The parser looks in the "game_pages" folder for the files to parse and outputs files (utf-8) in the "questions" folder. To run: python parser.py

I haven't gotten around to doesn't properly parse pages with tiebreakers (if I recall correctly, there are 4), so the information on the final and tiebreaker question is incomplete for those pages. Everything else should be fine. There are pages that don't have any questions though, and pages with just one (either first or second) round.

sql.py uses sqlite3 to create the database called jeopardy. It looks in the "questions" folder for the files. To run: python sql.py
