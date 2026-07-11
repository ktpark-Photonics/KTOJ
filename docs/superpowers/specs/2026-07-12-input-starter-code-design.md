# KTOJ — 입력 스타터 코드 (설계)

- 작성일: 2026-07-12
- 목표: 왕초보가 "입력을 어떻게 읽지?"에서 막히지 않도록, 문제마다 입력 읽기 코드를 제출창에 미리 채워준다. stdin 방식은 유지(실제 입출력 스킬도 학습). 채점 로직은 불변.

## 접근

각 문제에 "입력을 올바르게 읽는 스타터 코드"를 두고, 문제 상세의 제출 `<textarea>`를 그 코드로 프리필한다. 사용자는 로직만 채운다.

## 구성 요소

1. **스타터 파일** `problems/<slug>/starter.py` (선택). 입력 읽기 코드 + `# 여기에 코드를 작성하세요` 마커. 15문제 전부 작성.
2. **DB:** `Problem.starter_code: Mapped[str | None]` 컬럼 추가(nullable Text).
3. **로더:** `sync_problem`이 `starter.py`가 있으면 읽어 `starter_code`에 저장, 없으면 `None`. `parse_problem_dir`은 반환 dict(meta)에 `starter_code` 키 포함.
4. **웹:** `problem_detail.html`의 textarea에 `problem.starter_code`를 프리필(없으면 빈 문자열). textarea 위에 안내 한 줄: "입력을 읽는 코드는 채워져 있어요. 로직만 완성하면 됩니다."
5. **재시딩:** 컬럼 추가로 스키마가 바뀌므로 기존 `ktoj.sqlite3` 삭제 후 `seed.py` 재실행(제출 기록은 테스트용이라 폐기 무방).

## 문제별 스타터 (입력 형태별)

- 입력 없음 (hello-world): `# 입력이 없습니다. 정답을 print 하세요`
- 정수 1개 (sum-1-to-n, fizzbuzz, even-or-odd, absolute-value, sum-even-to-n, factorial, stars-triangle):
  ```python
  n = int(input())
  # 여기에 코드를 작성하세요
  ```
- 정수 2개 (a-plus-b, subtract-two, multiply-two, four-operations, gcd-two):
  ```python
  a, b = map(int, input().split())
  # 여기에 코드를 작성하세요
  ```
- 정수 N개 (max-of-n):
  ```python
  n = int(input())
  nums = list(map(int, input().split()))
  # 여기에 코드를 작성하세요
  ```
- 문자열 (digit-sum):
  ```python
  n = input().strip()
  # 여기에 코드를 작성하세요
  ```

## 검증

- 로더 단위 테스트: `starter.py` 있으면 `starter_code`에 로드, 없으면 `None`.
- 웹 테스트: 문제 상세 응답의 textarea 안에 스타터 코드 문자열이 포함.
- 라이브: 15개 스타터가 전부 `compile()` 통과(문법 유효)하고, 샘플 입력을 주면 예외 없이 종료(입력만 읽음)하는지 확인.
- 전체 스위트 그린 유지. 재시딩 후 화면에서 프리필 렌더 확인.
```
