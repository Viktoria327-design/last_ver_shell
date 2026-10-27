"""Парсер командной строки: слова, одинарные и двойные кавычки, экранирование."""


class ParseError(Exception):
    pass


def parse(line):
    """Разбирает строку на аргументы, как это делает sh (без подстановок).

    * пробелы и табуляции разделяют слова;
    * '...' — всё внутри буквально; "..." — внутри допустим \\" \\\\ \\$ \\`;
    * \\x вне кавычек — буквальный символ x;
    * '#' в начале слова начинает комментарий;
    * "" и '' дают пустой аргумент.
    """
    tokens, cur = [], []
    in_token = False
    quote = None
    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if quote:
            if ch == quote:
                quote = None
            elif ch == "\\" and quote == '"' and i + 1 < n and line[i + 1] in '"\\$`':
                i += 1
                cur.append(line[i])
            else:
                cur.append(ch)
        elif ch in " \t":
            if in_token:
                tokens.append("".join(cur))
                cur, in_token = [], False
        elif ch in "'\"":
            quote = ch
            in_token = True
        elif ch == "\\":
            if i + 1 >= n:
                raise ParseError("неожиданный конец ввода после '\\'")
            i += 1
            cur.append(line[i])
            in_token = True
        elif ch == "#" and not in_token:
            break
        else:
            cur.append(ch)
            in_token = True
        i += 1
    if quote:
        raise ParseError("неожиданный конец ввода: не закрыта кавычка %s" % quote)
    if in_token:
        tokens.append("".join(cur))
    return tokens
