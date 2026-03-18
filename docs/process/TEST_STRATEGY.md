# Test Strategy

이 문서는 구현 전에 고정하는 테스트 기준의 단일 원본이다.

## 테스트 계층
- 단위 테스트
  - 저장소 계층
  - 서비스 계층
- 기능 테스트
  - 공개 API 기준 end-to-end 흐름
- 성능 비교
  - 캐시 hit vs MongoDB no-cache

## 최소 통과선
- 단위 테스트:
  - store와 ttl 핵심 동작이 검증된다
  - 서비스 계층의 MongoDB origin cache-aside 흐름이 검증된다
- 기능 테스트:
  - KV API와 뉴스 캐싱 흐름이 검증된다
- 성능 비교:
  - 동일한 입력으로 MongoDB origin path와 cache hit를 한 번 이상 비교한다

## 테스트 데이터 원칙
- 뉴스 캐싱 시나리오는 외부 API stub 대신 MongoDB dummy seed data 기준으로 검증한다.
- 허용 topic별 seed dataset은 테스트 시작 전에 명시적으로 준비한다.
- empty result 케이스는 유효 topic에 대응하는 document가 없는 fixture로 검증한다.

## 필수 단위 테스트
- 값을 저장한 뒤 다시 조회할 수 있다
- 존재하지 않는 키 조회 시 miss를 반환한다
- 기존 키를 삭제한 뒤 다시 조회하면 존재하지 않는다
- 같은 키를 새 값으로 덮어쓴다
- TTL 만료 전에는 값을 조회할 수 있다
- TTL 만료 후에는 miss를 반환한다
- 조회 시 만료 키를 제거한다
- 잘못된 키 입력을 거부한다
- 잘못된 TTL 입력을 거부한다
- MongoDB origin 결과가 있으면 캐시 payload를 만들고 저장 흐름을 시작한다
- 유효한 topic인데 MongoDB 결과가 비면 빈 `articles`를 반환하고 캐시에 저장하지 않는다

최소 세트:
- KV 저장/조회/삭제
- TTL 만료 전/후
- lazy expiration
- MongoDB origin read -> cache write

## 필수 기능 테스트
- 공개 API로 값을 저장할 수 있다
- 공개 API로 저장된 값을 조회할 수 있다
- 공개 API로 키를 삭제할 수 있다
- 공개 API로 TTL을 설정할 수 있다
- 없는 키에 대해 일관된 miss 응답을 준다
- 뉴스 헤드라인 캐싱 시나리오에서 첫 호출은 `source = origin`을 반환한다
- 같은 topic 재호출에서 캐시 hit를 확인할 수 있다
- TTL 만료 후 MongoDB 재조회가 발생한다
- 지원하지 않는 `topic` 요청은 `400`과 `INVALID_TOPIC`을 반환한다
- 유효한 `topic`인데 MongoDB 결과가 비면 `200`과 빈 배열을 반환한다

최소 세트:
- `POST /kv` -> `GET /kv/{key}`
- `POST /kv/{key}/expire` 후 만료 전/후 조회
- `GET /demo/headlines-cache?topic=ai` 첫 호출과 재호출 비교
- invalid topic 응답
- empty MongoDB result 응답

## 동시성 검증 시나리오
- 동시에 여러 번 조회해도 값이 깨지지 않는다
- 동시에 쓰기 시도가 있어도 최종 상태가 일관된다
- 만료 경계 시점의 조회는 정상 값 또는 miss 중 하나만 반환한다
- 같은 topic에 대한 동시 캐시 miss 상황에서도 최종 응답 형식이 일관된다

## 성능 비교 규칙
- 동일한 요청 경로를 사용한다
- 동일한 환경에서 측정한다
- README에는 수치와 측정 조건을 함께 남긴다

최소 세트:
- `topic=ai` 기준 MongoDB origin path 1회 이상
- 같은 `topic` 기준 warm cache path 1회 이상
- 평균 시간 또는 총 시간 중 하나 이상 기록
