# FATO-KG Agent Query Templates

## 업무 계획

Input: target Task

Traversal:

```text
Task <-PRECEDES- predecessor tasks
Task -USES_INPUT-> required inputs
Task -PRODUCES-> expected outputs
Task -EVIDENCED_BY-> EvidenceSpan
```

## 체크리스트 생성

```text
Task -HAS_PRINCIPLE-> Principle
Task -HAS_CONDITION-> Condition
Task -HAS_CONSTRAINT-> Constraint
Task -HAS_RISK-> Risk
```

## 리스크 경고

```text
Task -HAS_RISK-> Risk
Task -MITIGATES-> Risk
Risk -EVIDENCED_BY-> EvidenceSpan
```

## 표준 매핑 설명

```text
Task -REQUIRES_CAPABILITY/PROCESS_CONTEXT-> MappingCandidate target
Task -EVIDENCED_BY-> EvidenceSpan
```
