"""Friendly, rule-based hints for failed submissions.

Pure logic (no Docker/DB): given a verdict and the captured error message,
return a beginner-friendly Korean hint, or None when no hint applies
(AC / still judging / internal error).
"""
from app.judge import verdicts

# (substring to look for in the error message, hint). First match wins,
# so more specific errors are listed before broader ones.
_ERROR_HINTS: list[tuple[str, str]] = [
    ("IndentationError",
     "들여쓰기가 어긋났어요. if/for/while 아래 줄은 일정한 칸으로 들여써야 해요."),
    ("SyntaxError",
     "문법 오류예요. 괄호 ()나 콜론(:)이 빠지지 않았는지, 오타가 없는지 확인해보세요."),
    ("NameError",
     "정의되지 않은 이름을 썼어요. 변수나 함수 이름에 오타가 없는지 확인해보세요 "
     "(파이썬이 비슷한 이름을 제안하기도 해요)."),
    ("ZeroDivisionError",
     "0으로 나눴어요. 나누는 값이 0이 될 수 있는지 확인해보세요."),
    ("EOFError",
     "읽을 입력이 부족해요. input()을 필요한 횟수만큼만 호출했는지 확인해보세요."),
    ("ValueError",
     "값 변환에서 오류가 났어요. int()로 바꿀 때 입력 형식과 개수가 맞는지"
     "(공백으로 나눠 읽었는지) 확인해보세요."),
    ("IndexError",
     "리스트 범위를 벗어났어요. 인덱스가 리스트 길이를 넘지 않는지 확인해보세요."),
    ("KeyError",
     "딕셔너리에 없는 키를 찾았어요. 키 이름을 확인해보세요."),
    ("ModuleNotFoundError",
     "그 모듈은 사용할 수 없어요. 표준 라이브러리만 사용할 수 있어요."),
    ("ImportError",
     "그 모듈은 사용할 수 없어요. 표준 라이브러리만 사용할 수 있어요."),
    ("RecursionError",
     "재귀가 너무 깊어요. 반복문으로 바꾸거나 종료 조건을 확인해보세요."),
    ("TypeError",
     "타입이 맞지 않아요. 문자열과 숫자를 섞어 쓰거나 함수에 잘못된 값을 "
     "넘기지 않았는지 확인해보세요."),
]

_GENERIC: dict[str, str] = {
    verdicts.WA: "예제는 통과했더라도 다른 경우에서 틀렸어요. 경계값(0, 음수, "
                 "아주 큰 수)이나 출력 형식(공백·줄바꿈)을 다시 살펴보세요.",
    verdicts.TLE: "제한 시간을 넘겼어요. 반복문이 불필요하게 많이 돌지 않는지, "
                  "더 간단한 방법이 없는지 생각해보세요.",
    verdicts.MLE: "메모리를 너무 많이 썼어요. 아주 큰 리스트를 만들고 있지 "
                  "않은지 확인해보세요.",
    verdicts.RE: "코드가 실행 도중 멈췄어요. 에러 메시지의 마지막 줄을 읽어보면 "
                 "원인을 알 수 있어요.",
    verdicts.CE: "문법 오류가 있어요. 에러 메시지의 줄 번호를 확인해보세요.",
}


def hint_for(status: str, message: str | None) -> str | None:
    if status in (verdicts.RE, verdicts.CE) and message:
        for needle, hint in _ERROR_HINTS:
            if needle in message:
                return hint
    return _GENERIC.get(status)
