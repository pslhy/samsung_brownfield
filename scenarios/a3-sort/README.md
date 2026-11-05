# 실습 A-2 ③: 정렬 기준 변경

요청: "기기 목록을 종류별로 묶어 보여 달라."
AI 패치: `DeviceRegistry`의 기기 정렬 비교 함수를 "종류 → 이름" 순서로 바꿈.

- `make impact V=scenarios/a3-sort` → 다시 돌릴 테스트 0개
- `make variant-test V=scenarios/a3-sort` → 38/38 통과
- `make variant V=scenarios/a3-sort && make trace TRACE_CP=work/a3-sort/build/classes` → 세 기록 모두 다름

비교 함수는 JDK의 `Collections.sort`가 부르므로, JDK 내부를 분석하지 않는 영향 분석은 그 반환값이 어디로 가는지 따라가지 못합니다.
