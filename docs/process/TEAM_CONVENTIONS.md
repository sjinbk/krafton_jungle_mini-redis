# Team Conventions

이 문서는 팀 운영, 스레드/브랜치/커밋 규칙, 병합 비용 최소화 규칙의 단일 원본이다.

## 핵심 원칙
- `1 thread = 1 branch`
- 새 스레드가 열리면 반드시 새 브랜치를 먼저 만든다
- 한 스레드 안에서는 브랜치를 바꾸지 않는다
- 작업 주제나 목적이 바뀌면 새 스레드와 새 브랜치를 연다
- 같은 사람이더라도 다른 작업이면 브랜치를 재사용하지 않는다
- 공통 계약 변경은 코드보다 문서를 먼저 수정한다
- README 기준 사양이 갱신되면 관련 원본 문서도 같은 턴에 함께 맞춘다

## 작업 영역
- `store`
- `ttl`
- `api`
- `test-docs`
- `repo`

## 브랜치 이름 규칙
- 형식: `<kind>/<area>-<topic>-<initials>`
- `kind`
  - `feature`
  - `fix`
  - `docs`
- `area`
  - `store`
  - `ttl`
  - `api`
  - `test-docs`
  - `repo`
- `topic`
  - 영어 kebab-case
  - 짧고 구체적으로 작성
- `initials`
  - 팀원 이니셜 소문자
  - 팀 내에서 중복 없이 미리 고정

예시:
- `feature/store-core-map-js`
- `feature/api-kv-endpoints-km`
- `fix/ttl-expire-check-jh`
- `docs/repo-collaboration-convention-cy`

## 커밋 메시지 규칙
- 형식: `<tag>(<area>): <summary>`
- `tag`
  - `feat`
  - `fix`
  - `docs`
- `area`
  - `store`
  - `ttl`
  - `api`
  - `test-docs`
  - `repo`
- `summary`
  - 짧은 영어 한 줄

예시:
- `feat(store): add map based set and get`
- `fix(ttl): delete expired key on read`
- `docs(repo): sync docs with readme`

## 태그 분류 기준
- `feat`
  - 기능 추가
  - 구조 추가
  - 기능 구현에 종속된 테스트 추가
- `fix`
  - 버그 수정
  - 회귀 수정
  - 실패 재현 테스트 추가
- `docs`
  - README
  - AGENTS
  - 스펙 문서
  - 구조 문서
  - 플레이북
  - 주석 정리

## 작업 시작 체크
- 새 스레드라면 새 브랜치를 먼저 만든다
- 현재 브랜치의 작업 영역을 먼저 정한다
- 현재 브랜치의 workstream을 먼저 정한다
- 작업 영역과 무관한 파일 수정은 보류한다
- 공개 계약 변경이 필요한지 먼저 판단한다
- 필요하면 문서를 먼저 수정한 뒤 구현에 들어간다

## 고충돌 파일
아래 파일은 동시에 여러 명이 수정하지 않는 것을 원칙으로 한다.
- 의존성 manifest
- 애플리케이션 엔트리포인트
- 공통 타입 / 공통 에러
- API 라우트 등록 파일
- CI 설정
- 벤치마크 실행 파일

## 운영 규칙
- 문서 전용 브랜치 `docs/*`에서는 코드 수정 금지
- `fix/*` 브랜치는 버그 수정 또는 회귀 대응만 포함
- 브랜치명과 실제 수정 영역의 `area`는 가능하면 동일하게 유지
- 여러 성격의 변경이 섞이면 커밋을 분리한다
- 새 작업인데 새 브랜치를 만들지 않은 상태라면 먼저 멈추고 브랜치부터 정리한다
- 사용자 또는 팀 리드가 명시적으로 요청한 경우에만 현재 브랜치에서 문서 정리를 진행할 수 있다
- 현재 브랜치 작업 예외는 일회성으로만 적용하고 기본 원칙을 대체하지 않는다

## 유효 사례
- 새 API 작업 스레드에서 `feature/api-kv-endpoints-js` 생성
- TTL 버그 수정 스레드에서 `fix/ttl-expire-check-jh` 생성
- 문서 정리 스레드에서 `docs/repo-collaboration-convention-cy` 생성
- 기능 구현 커밋 `feat(api): add kv endpoints`
- 버그 수정 커밋 `fix(ttl): remove expired key on read`
- 문서 커밋 `docs(repo): sync docs with readme`

## 실패 사례
- 한 스레드에서 브랜치 변경
- `feature/api-kv-endpoints`처럼 이니셜 없는 브랜치
- `feature/jh/api-kv-endpoints`처럼 형식이 다른 브랜치
- `chore`, `test`, `refactor` 같은 비공식 태그 사용
- `docs/*` 브랜치에서 코드 변경 포함
