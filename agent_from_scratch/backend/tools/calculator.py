from enum import Enum
from dataclasses import dataclass


class TokenType(Enum):
    NUMBER = "NUMBER"
    PLUS = "PLUS"
    MINUS = "MINUS"
    MUL = "MUL"
    DIV = "DIV"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF = "EOF"


@dataclass
class Token:
    type: TokenType
    value: str | None = None


class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.text else None

    def advance(self):
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def number(self) -> Token:
        result = ""
        dot_count = 0

        while self.current_char is not None and (
            self.current_char.isdigit() or self.current_char == "."
        ):
            if self.current_char == ".":
                dot_count += 1
                if dot_count > 1:
                    raise ValueError("Invalid number")

            result += self.current_char
            self.advance()

        if result == ".":
            raise ValueError("Invalid number")

        return Token(TokenType.NUMBER, result)

    def get_next_token(self) -> Token:
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit() or self.current_char == ".":
                return self.number()

            if self.current_char == "+":
                self.advance()
                return Token(TokenType.PLUS, "+")

            if self.current_char == "-":
                self.advance()
                return Token(TokenType.MINUS, "-")

            if self.current_char == "*":
                self.advance()
                return Token(TokenType.MUL, "*")

            if self.current_char == "/":
                self.advance()
                return Token(TokenType.DIV, "/")

            if self.current_char == "(":
                self.advance()
                return Token(TokenType.LPAREN, "(")

            if self.current_char == ")":
                self.advance()
                return Token(TokenType.RPAREN, ")")

            raise ValueError(f"Invalid character: {self.current_char}")

        return Token(TokenType.EOF)


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def eat(self, token_type: TokenType):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            raise ValueError(
                f"Expected {token_type}, got {self.current_token.type}"
            )

    def factor(self) -> float:
        """
        factor = NUMBER | "(" expression ")"
        """
        token = self.current_token

        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return float(token.value)

        if token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            result = self.expression()
            self.eat(TokenType.RPAREN)
            return result

        raise ValueError(f"Unexpected token: {token}")

    def term(self) -> float:
        """
        term = factor ((* | /) factor)*
        """
        result = self.factor()

        while self.current_token.type in (TokenType.MUL, TokenType.DIV):
            token = self.current_token

            if token.type == TokenType.MUL:
                self.eat(TokenType.MUL)
                result *= self.factor()

            elif token.type == TokenType.DIV:
                self.eat(TokenType.DIV)
                divisor = self.factor()
                if divisor == 0:
                    raise ZeroDivisionError("Division by zero")
                result /= divisor

        return result

    def expression(self) -> float:
        """
        expression = term ((+ | -) term)*
        """
        result = self.term()

        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token

            if token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
                result += self.term()

            elif token.type == TokenType.MINUS:
                self.eat(TokenType.MINUS)
                result -= self.term()

        return result

    def parse(self) -> float:
        result = self.expression()

        if self.current_token.type != TokenType.EOF:
            raise ValueError(f"Unexpected token at end: {self.current_token}")

        return result


def calculator(expression: str) -> float:
    lexer = Lexer(expression)
    parser = Parser(lexer)
    return parser.parse()

# print(calculator("5 / 0"))
