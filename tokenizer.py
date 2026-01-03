import re

class TokenType:
    Identifier = 1
    Number = 2
    String = 3
    Punctuator = 4
    EOF = 5


class Token:
    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {self.value}, line={self.line}, col={self.col})"


class Tokenizer:
    def __init__(self, file_obj):
        self.file = file_obj
        self.line = 1
        self.col = 0
        self.buffer = []

        self.whitespace = " \t\r\n"
        self.punctuators = ":,()[]/"  # <- inclui '/'

        self.int_regex = re.compile(r"^[+-]?\d+$")
        self.float_regex = re.compile(r"^[+-]?\d+(\.\d+)?$")

    # ------------------------------------------------------------
    # LOW-LEVEL CHAR HANDLING
    # ------------------------------------------------------------

    def _read_char(self):
        c = self.file.read(1)
        if c == "\n":
            self.line += 1
            self.col = 0
        else:
            self.col += 1
        return c

    def _peek_char(self):
        pos = self.file.tell()
        c = self.file.read(1)
        self.file.seek(pos)
        return c

    # ------------------------------------------------------------
    # SKIP WHITESPACE, COMMENTS, INVISIBLE CHARACTERS, BOM
    # ------------------------------------------------------------

    def _skip_whitespace_and_comments(self):
        while True:
            c = self._peek_char()

            # whitespace normal
            if c in " \t\r\n":
                self._read_char()
                continue

            # BOM UTF‑8
            if c == "\ufeff":
                self._read_char()
                continue

            # caracteres invisíveis (ASCII < 32)
            if c and ord(c) < 32:
                self._read_char()
                continue

            # comentários
            if c == "#":
                while c not in ("", "\n"):
                    c = self._read_char()
                continue

            break

    # ------------------------------------------------------------
    # TOKEN EXTRACTION
    # ------------------------------------------------------------

    def getToken(self):
        if self.buffer:
            return self.buffer.pop()

        self._skip_whitespace_and_comments()
        c = self._read_char()

        if c == "":
            return Token(TokenType.EOF, "", self.line, self.col)

        # Punctuators
        if c in self.punctuators:
            return Token(TokenType.Punctuator, c, self.line, self.col)

        # Strings
        if c == '"':
            s = c
            while True:
                ch = self._read_char()
                if ch == "":
                    break
                s += ch
                if ch == '"':
                    break
            return Token(TokenType.String, s, self.line, self.col)

        # Identifiers / numbers (incluindo 0x0000)
        if c.isalnum() or c in "+-._xX":
            s = c
            while True:
                ch = self._peek_char()
                if ch.isalnum() or ch in "+-._xX":
                    s += self._read_char()
                else:
                    break
            return Token(TokenType.Identifier, s, self.line, self.col)

        # fallback
        return Token(TokenType.Identifier, c, self.line, self.col)

    # ------------------------------------------------------------
    # PEEK TOKEN
    # ------------------------------------------------------------

    def peekToken(self):
        tok = self.getToken()
        self.buffer.append(tok)
        return tok

    # ------------------------------------------------------------
    # ASSERTIONS
    # ------------------------------------------------------------

    def assertIdentifier(self, expected):
        t = self.getToken()
        if not (t.type == TokenType.Identifier and t.value.upper() == expected.upper()):
            raise AssertionError(f"Expected identifier '{expected}', got {t}")

    def assertPunctuator(self, expected):
        t = self.getToken()
        if not (t.type == TokenType.Punctuator and t.value == expected):
            raise AssertionError(f"Expected punctuator '{expected}', got {t}")

    # ------------------------------------------------------------
    # NUMBER PARSING
    # ------------------------------------------------------------

    def getIntNumber(self):
        t = self.getToken()
        if t.type != TokenType.Identifier:
            raise AssertionError(f"Expected int number, got {t}!")

        s = t.value.strip()

        # Hexadecimal: 0x0000, 0X0040, etc.
        if s.lower().startswith("0x"):
            try:
                return int(s, 16)
            except ValueError:
                raise AssertionError(f"Expected hex int number, got {t}!")

        # Decimal: +10, -3, 42
        if not self.int_regex.match(s):
            raise AssertionError(f"Expected int number, got {t}!")

        return int(s)

    def getFloatNumber(self):
        t = self.getToken()
        if t.type != TokenType.Identifier or not self.float_regex.match(t.value.strip()):
            raise AssertionError(f"Expected float number, got {t}!")
        return float(t.value)

    # ------------------------------------------------------------
    # IDENTIFIERS & STRINGS
    # ------------------------------------------------------------

    def getIdentifier(self):
        t = self.getToken()
        if t.type != TokenType.Identifier:
            raise AssertionError(f"Expected identifier, got {t}")
        return t.value

    def getSpaceDelimitedString(self):
        t = self.getToken()
        return t.value

    # ------------------------------------------------------------
    # VECTORS
    # ------------------------------------------------------------

    def getVector4f(self):
        r = self.getFloatNumber()
        g = self.getFloatNumber()
        b = self.getFloatNumber()
        a = self.getFloatNumber()
        return (r, g, b, a)