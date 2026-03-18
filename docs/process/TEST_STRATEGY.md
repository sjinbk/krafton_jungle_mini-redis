# Test Strategy

이 문서는 구현 전에 고정하는 테스트 기준의 단일 원본이다.

## 테스트 계층
- 단위 테스트
  - 저장소 계층
  - 서비스 계층
- 기능 테스트
  - 공개 API 기준 end-to-end 흐름
- 성능 비교
  - 캐시 hit vs no-cache

## 최소 통과선
- 단위 테스트:
  - store와 ttl 핵심 동작이 검증된다
  - 서비스 계층의 DB origin cache-aside 흐름이 검증된다
- 기능 테스트:
  - KV API와 더미 데이터 캐싱 흐름이 검증된다
- 성능 비교:
  - 동일한 입력으로 DB origin path와 cache hit를 한 번 이상 비교한다

## 테스트 데이터 원칙
- 더미 데이터 캐싱 시나리오는 외부 API stub 대신 MongoDB dummy seed data 기준으로 검증한다.
- 테스트 시작 전에 필요한 seed dataset을 명시적으로 준비한다.
- seed dataset은 `dummy_items` collection에 총 4개 document만 둔다.
- empty result 케이스는 `key=not-seeded`처럼 document가 없는 조회 조건으로 검증한다.

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
- 유효한 요청인데 MongoDB 결과가 비면 빈 `items`를 반환하고 캐시에 저장하지 않는다

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
- 더미 데이터 캐싱 시나리오에서 첫 호출은 `source = origin`을 반환한다
- 같은 조건의 재호출에서 캐시 hit를 확인할 수 있다
- TTL 만료 후 MongoDB 재조회가 발생한다
- `key` 누락 또는 빈 문자열은 `400` 계열 검증 오류를 반환한다
- 유효한 요청인데 MongoDB 결과가 비면 `200`과 빈 배열을 반환한다

최소 세트:
- `POST /kv` -> `GET /kv/{key}`
- `POST /kv/{key}/expire` 후 만료 전/후 조회
- `GET /demo/data-cache?key=sample` 첫 호출과 재호출 비교
- invalid request 응답
- empty MongoDB result 응답

## 동시성 검증 시나리오
- 같은 `key`에 대한 동시 요청에서도 상태와 응답 형식이 일관된다
- 다른 `key`에 대한 동시 요청도 전역 직렬화되어 순차 처리된다
- 만료 경계 시점의 조회는 정상 값 또는 miss 중 하나만 반환한다
- 같은 `key`에 대한 동시 캐시 miss 상황에서도 응답 형식과 상태 일관성을 검증한다
- `KV` 요청과 `demo cache` 요청이 동시에 들어와도 같은 실행 경로를 공유해 순차 처리된다

## 성능 비교 규칙
- 동일한 요청 경로를 사용한다
- 동일한 환경에서 측정한다
- README에는 수치와 측정 조건을 함께 남긴다

최소 세트:
- DB origin path 1회 이상
- 같은 입력 기준 warm cache path 1회 이상
- 평균 시간 또는 총 시간 중 하나 이상 기록
