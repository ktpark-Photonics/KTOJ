# KTOJ — 실패 원인별 힌트 (설계)

- 작성일: 2026-07-12
- 목표: 채점 실패 시 원인에 맞는 친근한 한국어 힌트를 보여준다. 규칙 기반(외부 의존성 없음).

## 구성

- `app/judge/hints.py` — 순수 함수 `hint_for(status, message) -> str | None`.
  - RE/CE: `message`(에러 텍스트)에서 흔한 초보 실수 패턴을 앞에서부터 매칭해 구체 힌트. 매칭 실패 시 판정별 일반 힌트.
  - WA/TLE/MLE: 판정별 일반 힌트.
  - AC/PENDING/JUDGING/IE: None.
  - 매칭 순서(구체→일반): IndentationError, SyntaxError, NameError, ZeroDivisionError, EOFError, ValueError, IndexError, KeyError, ModuleNotFound/ImportError, RecursionError, TypeError.
- `main.py`: `hint_for`를 Jinja 전역으로 등록.
- `_submission_status.html`: 실패(비-AC, 비-대기) 시 `hint_for(sub.status, sub.message)` 결과가 있으면 `.hint-fail`(앰버) 박스로 표시. 폴링 fragment·결과 상세 양쪽에 자동 적용.
- `base.html`: `.hint-fail` 스타일 추가(경고색).

## 검증

- `tests/test_hints.py` 단위 테스트: NameError→오타 힌트, ValueError→파싱 힌트, ZeroDivision, SyntaxError(CE), Indentation, RE(메시지 없음)→일반, WA→경계값, TLE→시간, AC→None, PENDING→None.
- 라이브: 실제 RE(오타)·WA·AC 제출에 힌트 노출/미노출 확인.
- 전체 스위트 그린(53 passed).
```
