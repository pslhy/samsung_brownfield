# 정리 규칙을 코드 전체에 적용한 결과 (실습 E)

`<규칙 이름>/`에는 레거시에 그 규칙 하나를 적용할 수 있는 곳마다 모두 적용한 결과가, `All/`에는 셋을 모두 적용한 결과가 들어 있습니다(바뀐 파일만). "AI에게 이 정리 규칙을 코드 전체에 적용하라고 시킨 결과"에 해당합니다.

| 폴더 | 규칙 | 같은 뜻이 되는 조건 | 적용한 곳 |
|---|---|---|---|
| `IsEmpty/` | `list.size() == 0` → `list.isEmpty()` | 없음 | Metrics, PowerBudget, RuleEngine |
| `ForEach/` | 인덱스 반복 → for-each | 반복 중에 목록을 바꾸지 않음 | AuditLog(3곳), Metrics, RecoveryManager, HandlerRegistry, HomeHub.flushDerived, SafetyHandler |
| `InlineVariable/` | 한 번만 쓰는 지역 변수를 그 식으로 | 변수를 쓰는 동안 식의 값이 바뀌지 않음 | AuditLog.record, AuditLog.tail, **Dispatcher.evictOldestNonCritical** |

확인: `make rewrite-check R=<폴더 이름>` (기존 테스트, 기록해 둔 동작, 무작위 입력으로 레거시와 비교). 조건의 증명과 반례: `rewrite/RewriteRules.dfy`(`make rules`).
