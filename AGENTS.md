# Mini Redis Agent Guide

이 저장소에서 작업하는 AI 에이전트는 구현 전 아래 문서를 반드시 읽는다. 이 문서가 유일한 에이전트 진입점이다.

## Mandatory Read Order
1. `docs/spec/PROJECT_SPEC.md`
2. `docs/spec/API_CONTRACT.md`
3. `docs/architecture/SYSTEM_DESIGN.md`
4. `docs/process/TEAM_CONVENTIONS.md`
5. `docs/process/TEST_STRATEGY.md`
6. `docs/planning/WORKSTREAM_PLAN.md`
7. `docs/decisions/DECISION_LOG.md`
8. `README.md`

## Preflight Check
- 이번 작업이 어느 영역에 속하는지 확인할 것
- 이번 작업이 어느 workstream에 속하는지 확인할 것
- 현재 스레드와 브랜치가 1:1인지 확인할 것
- 현재 브랜치 이름이 `<kind>/<area>-<topic>-<initials>` 형식인지 확인할 것
- 어떤 문서가 현재 작업의 원본인지 먼저 확인할 것
- 본인 작업 영역 밖의 고충돌 파일 수정은 최소화할 것

## Working Rules
- 문서를 읽지 않은 상태에서 바로 구현을 시작하지 말 것
- 공개 API 계약을 바꾸는 변경은 관련 문서부터 먼저 갱신할 것
- 제품 범위와 정책은 `PROJECT_SPEC`를 원본으로 따를 것
- 구조적 판단은 `SYSTEM_DESIGN`을 원본으로 따를 것
- 브랜치, 커밋, 병합 규칙은 `TEAM_CONVENTIONS`를 원본으로 따를 것
- 구현 완료 판단 전에 `TEST_STRATEGY`를 확인할 것

## Stop And Recheck When
- 구현하려는 동작이 문서 계약에 없다
- 공개 API를 변경하려 한다
- 고충돌 파일을 동시에 수정해야 한다
- 테스트 계획에 없는 핵심 동작을 추가하려 한다
