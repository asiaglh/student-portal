"""Path converter for valid ECTS letters."""


class EctsConverter:
    regex = "A|B|C|D|E|Fx"

    def to_python(self, value: str) -> str:
        return value

    def to_url(self, value: str) -> str:
        return value
