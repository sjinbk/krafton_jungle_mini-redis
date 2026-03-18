# System Design

이 문서는 시스템 구조, 계층 책임, 데이터 모델, 디렉터리 구조의 단일 원본이다. 구조적 판단은 README와 이 문서를 기준으로 한다.

## 기본 구조
구현은 아래 3계층을 분리하는 방향으로 진행한다. 더미 데이터 캐싱 시나리오에서는 서비스 계층이 MongoDB origin 조회를 함께 오케스트레이션한다.

```mermaid
flowchart TD
    Client["External Caller"] --> API["FastAPI API Layer"]
    API --> Service["Service Layer"]
    Service --> Store["In-memory Store Layer"]
    Service --> Expiry["TTL / Expiration"]
    Service --> Origin["MongoDB Origin Adapter"]
    Origin --> MongoDB[("MongoDB")]
```

## 계층별 책임
- `API Layer`
  - FastAPI 라우트에서 외부 입력을 받는다.
  - 요청을 서비스 호출로 변환한다.
  - HTTP 응답을 조립한다.
- `Service Layer`
  - 명령 의미를 해석한다.
  - TTL 규칙과 삭제 규칙을 적용한다.
  - 저장소 접근 순서와 cache-aside 흐름을 통제한다.
  - MongoDB origin 조회 시점과 캐시 write 시점을 결정한다.
- `Store Layer`
  - 키 조회, 저장, 삭제 primitive를 제공한다.
  - 값과 만료 메타데이터를 보관한다.
  - Mini Redis의 인메모리 캐시 저장소 역할만 맡는다.
- `MongoDB Origin Adapter`
  - 사전 적재한 dummy document를 조회한다.
  - 주어진 조회 조건에 맞는 문서를 읽는다.
  - 서비스 계층이 사용할 기사 목록 형태로 변환한다.

## 데이터 모델
권장 개념 구조:

```text
Map<Key, Entry>

Entry = {
  value,
  expiresAt | null
}

DummyDocument = {
  _id,
  key,
  itemId,
  value,
  createdAt
}
```

고정 규칙:
- `key`는 문자열
- `value`는 직렬화 가능한 값
- `expiresAt`이 없으면 만료 없음
- MongoDB origin collection은 `dummy_items` 하나로 고정한다
- MongoDB의 `DummyDocument`는 데모용 origin read model이며 Mini Redis cache entry와 별개다

## TTL 흐름
- 기본 정책은 `lazy expiration`
- 조회 또는 접근 시 먼저 만료 여부를 검사
- 만료되었으면:
  - 저장소에서 제거
  - 외부에는 miss로 반환
- 주기적 cleanup은 선택 과제

## 더미 데이터 캐싱 요청 흐름
1. 클라이언트가 더미 데이터 캐싱 데모 API를 호출한다.
2. API 계층이 요청 값을 검증하고 서비스 계층에 전달한다.
3. 서비스 계층이 캐시 키 `data:{key}`를 계산한 뒤 인메모리 저장소에서 조회한다.
4. 캐시 hit면 남은 TTL과 함께 캐시 데이터를 반환한다.
5. 캐시 miss면 MongoDB origin adapter가 `dummy_items` collection에서 같은 `key`의 더미 데이터를 조회한다.
6. origin 결과가 있으면 저장소에 기본 TTL `15초`와 함께 저장한 뒤 `source = origin`으로 응답한다.
7. origin 결과가 비어 있으면 빈 배열 응답만 반환하고 캐시는 쓰지 않는다.

## 동시성 방향
- v1은 단일 프로세스와 프로세스 내부 단일 저장소를 전제로 한다.
- 저장소를 직접 여러 곳에서 수정하지 않고, 서비스 계층을 유일한 진입 경로로 둔다.
- 모든 명령 실행은 하나의 shared command executor thread에서 순차 처리한다.
- 같은 `key`, 다른 `key`, 다른 서비스 조합 모두 동시에 실행하지 않고 전역 직렬화한다.
- 요청 수신과 응답 대기는 동시일 수 있지만, 실제 서비스 로직 실행은 한 번에 하나의 명령만 진행한다.
- origin 조회도 명령 처리의 일부로 보고 직렬 실행에 포함한다.

## 권장 디렉터리 구조
기술 스택이 달라도 아래 구조에 최대한 대응되게 맞춘다.

```text
src/
  api/
  service/
  store/
  ttl/
  common/
tests/
  unit/
  integration/
benchmarks/
docs/
```

## 최소 파일 세트
- FastAPI API 엔트리 파일 1개
- 서비스 계층 파일 1개 이상
- MongoDB origin 조회 협력 파일 1개 이상
- 저장소 계층 파일 1개
- TTL 처리 파일 1개
- 공용 타입/에러 파일 1개
- 단위 테스트 파일 1개 이상
- 기능 테스트 파일 1개 이상
- 벤치마크 스크립트 파일 1개

## 디렉터리 책임
- `src/api/`
  - HTTP 엔드포인트
  - 요청/응답 DTO
  - 에러 응답 매핑
- `src/service/`
  - 명령 처리 흐름
  - 공개 규칙 적용
  - 저장소, TTL, MongoDB origin 조회 조합
- `src/store/`
  - 해시 테이블 기반 저장 구조
  - key/value 엔트리 모델
  - 기본 set/get/delete primitive
- `src/ttl/`
  - 만료 시간 계산
  - 만료 검사
  - lazy expiration 처리
- `src/common/`
  - 공용 타입
  - 공용 에러
  - 공용 유틸
  - MongoDB client 설정 보조 코드
- `tests/unit/`
  - store, service, ttl 단위 테스트
- `tests/integration/`
  - HTTP API 기준 기능 테스트
- `benchmarks/`
  - 캐시 hit / no-cache 비교 코드

## 파일 배치 규칙
- API 코드는 `src/api/` 밖으로 새지 않는다.
- TTL 코드는 `src/ttl/` 또는 service 내부 협력 코드로만 위치한다.
- 저장소 내부 엔트리 구조는 `src/store/` 밖에서 직접 변경하지 않는다.
- MongoDB origin 조회 코드는 `src/service/` 협력 모듈 또는 `src/common/` 보조 코드로만 둔다.
- 공용 타입은 반드시 `src/common/`에 모은다.
- 테스트 파일은 실제 코드 계층과 대응되도록 둔다.

## 작업 영역
- `store`
  - 저장 구조
  - key/value 보관
  - set/get/delete primitive
- `ttl`
  - expiresAt 계산
  - 만료 검사
  - lazy deletion
- `api`
  - FastAPI 외부 인터페이스
  - 요청/응답 형식
  - MongoDB 기반 더미 데이터 캐싱 흐름
- `test-docs`
  - 단위 테스트
  - 기능 테스트
  - 벤치마크
  - README 반영

## 아키텍처 금지사항
- API 계층에서 TTL 판단을 하지 말 것
- API 계층에서 MongoDB를 직접 조회하지 말 것
- 저장소 계층에서 외부 응답 형식을 만들지 말 것
- 저장소 계층에서 MongoDB origin을 직접 조회하지 말 것
- 영속성 로직을 핵심 저장 경로에 강하게 결합하지 말 것
- 선택 과제를 필수 구조처럼 선반영하지 말 것
